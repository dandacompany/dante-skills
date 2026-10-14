#!/usr/bin/env python3
"""Delegate a task to a terminal agent running in another DanteTerm block.

Creates a block, launches an agent CLI in it, injects a prompt, waits for the work
to finish, and prints the result to stdout.

Requires dsh v0.17.4+ (tab / sendkeys / createblock placement) and must run inside a
DanteTerm terminal block, since dsh authenticates through DANTETERM_JWT.

The agent block is tracked by its block UUID, never by its 1-based number. Numbers
are per-tab and shift when blocks are added or closed; a UUID resolves from any tab
and stays valid, which also means the cross-tab flags are not needed for it.

Two completion modes:

  file        (default) Runs the agent's NON-INTERACTIVE form with the shell
              redirecting its output to a result file, then touching a done marker.
              The orchestrator polls for the marker. The redirect is the shell's
              work, so this does not rely on the agent cooperating, and it survives
              TUI redraws, spinners, and output longer than the scrollback buffer.

  scrollback  Polls `dsh termscrollback` and calls it finished when the text stops
              changing for --quiet-for seconds. Use only when the output cannot be
              redirected -- for example an agent with no non-interactive mode.
              Heuristic by nature.

Examples:
  danteterm_delegate.py --agent claude --prompt "summarize ./README.md"
  danteterm_delegate.py --agent codex --prompt "..." --cwd ~/projects/myrepo
  danteterm_delegate.py --agent codex --prompt-file task.md --tab work --position right --size 40
  danteterm_delegate.py --agent claude --prompt "..." --mode scrollback --quiet-for 20
  danteterm_delegate.py --agent claude --prompt "..." --keep   # leave the block open
"""

import argparse
import json
import os
import shlex
import subprocess
import sys
import tempfile
import time

DEFAULT_LAUNCH = {"claude": "claude", "codex": "codex", "hermes": "hermes"}

# The NON-INTERACTIVE invocation for each agent, verified against their --help.
# Getting this wrong is the worst failure available here: an agent that defaults to an
# interactive session will sit at a TUI forever instead of erroring, so the delegation
# hangs until the timeout with nothing to show. `claude <prompt>` alone does exactly
# that -- it needs -p. Verify with `<agent> --help` before adding an entry.
ARGV_PROMPT = {
    "claude": "{cmd} -p {prompt}",
    "codex": "{cmd} exec {prompt}",
    "hermes": "{cmd} -z {prompt}",
}


def die(msg, code=1):
    print(f"danteterm_delegate: {msg}", file=sys.stderr)
    sys.exit(code)


def dsh(*args, timeout=30):
    p = subprocess.run(["dsh", *args], capture_output=True, text=True, timeout=timeout)
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def preflight():
    if not os.environ.get("DANTETERM_JWT"):
        die("not running inside a DanteTerm terminal block (DANTETERM_JWT unset)")
    rc, out = dsh("tab", "list")
    if rc != 0:
        die("`dsh tab list` failed -- dsh is older than v0.17.4 or not connected:\n" + out.strip())


def resolve_tab_id(tab):
    """Turn a tab number/name/uuid into a tab id. None means the current tab."""
    if not tab:
        return os.environ.get("DANTETERM_TABID") or None
    rc, out = dsh("tab", "list", "--json")
    if rc != 0:
        die("could not list tabs:\n" + out.strip())
    try:
        entries = json.loads(out)
    except json.JSONDecodeError:
        die("`dsh tab list --json` did not return JSON:\n" + out.strip())
    by_name = [e for e in entries if e.get("name") == tab]
    if len(by_name) == 1:
        return by_name[0]["tabid"]
    if len(by_name) > 1:
        die(f'"{tab}" matches {len(by_name)} tabs; pass a tab id instead')
    if tab.isdigit():
        for e in entries:
            if e.get("num") == int(tab):
                return e["tabid"]
    for e in entries:
        if e.get("tabid") == tab:
            return tab
    die(f'no tab matching "{tab}"')


def block_ids(tab_id):
    rc, out = dsh("blocks", "list", "--tab", tab_id, "--json")
    if rc != 0:
        die("could not list blocks:\n" + out.strip())
    try:
        return {b["blockid"] for b in json.loads(out)}
    except (json.JSONDecodeError, KeyError, TypeError):
        die("`dsh blocks list --json` did not return the expected shape:\n" + out.strip())


def create_agent_block(tab, tab_id, target, position, size, cwd):
    """Create a terminal block and return its block UUID."""
    before = block_ids(tab_id)

    args = ["createblock", "term"]
    if cwd:
        # agents commonly refuse to run outside a trusted/known directory, and a new
        # block does not inherit the caller's cwd
        args.append(f"cmd:cwd={cwd}")
    if tab:
        args += ["--tab", tab]
    if target:
        args += ["--target", target, "--position", position]
        if size:
            args += ["--size", str(size)]
    rc, out = dsh(*args)
    if rc != 0:
        die("could not create the agent block:\n" + out.strip())

    for _ in range(20):
        new = block_ids(tab_id) - before
        if len(new) == 1:
            return new.pop()
        if len(new) > 1:
            die("more than one block appeared; refusing to guess which is the agent's")
        time.sleep(0.5)
    die("the block was created but never showed up in `dsh blocks list`")


def wait_for_shell(block, timeout):
    deadline = time.time() + timeout
    while time.time() < deadline:
        rc, out = dsh("termscrollback", "-b", block)
        if rc == 0 and out.strip():
            return True
        time.sleep(1)
    return False


def send_line(block, text):
    rc, out = dsh("sendkeys", "-b", block, "--enter", text)
    if rc != 0:
        die("sendkeys failed:\n" + out.strip())


def agent_command(agent, cmd, prompt):
    template = ARGV_PROMPT.get(agent, "{cmd} {prompt}")
    return template.format(cmd=cmd, prompt=shlex.quote(prompt))


def launch_redirected(block, agent, cmd, prompt, result, done):
    """Run the agent non-interactively with the SHELL capturing the answer.

    The redirect and the marker are the shell's work, not the agent's, so this does
    not depend on the agent cooperating with any instruction about where to write.
    The marker is written last, so its existence implies the answer file is complete.
    """
    inner = agent_command(agent, cmd, prompt)
    send_line(block, f"{inner} > {shlex.quote(result)} 2>&1; touch {shlex.quote(done)}")


def launch_plain(block, agent, cmd, prompt):
    send_line(block, agent_command(agent, cmd, prompt))


def wait_file_mode(block, timeout, poll, result, done):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if os.path.exists(done):
            if os.path.exists(result):
                with open(result, encoding="utf-8", errors="replace") as f:
                    return f.read()
            return ""  # marker without a result file: the agent broke the contract
        time.sleep(poll)
    _, tail = dsh("termscrollback", "-b", block)
    die(f"timed out after {timeout}s waiting for {done}\n--- agent screen ---\n{tail[-2000:]}")


def wait_scrollback_mode(block, timeout, poll, quiet_for):
    deadline = time.time() + timeout
    last, last_change = None, time.time()
    while time.time() < deadline:
        rc, out = dsh("termscrollback", "-b", block)
        if rc == 0:
            if out != last:
                last, last_change = out, time.time()
            elif time.time() - last_change >= quiet_for:
                return out
        time.sleep(poll)
    die(f"timed out after {timeout}s; the screen never went quiet for {quiet_for}s")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--agent", default="claude", help="agent CLI (claude, codex, hermes, or any command)")
    ap.add_argument("--command", help="override the executable for --agent")
    ap.add_argument("--prompt", help="the task to delegate")
    ap.add_argument("--prompt-file", help="read the task from a file instead")
    ap.add_argument("--tab", help="tab to work in (number, name, id); defaults to the current tab")
    ap.add_argument("--target", help="existing block to place the agent block against")
    ap.add_argument("--position", default="right", choices=["right", "left", "up", "down"])
    ap.add_argument("--size", type=int, help="percentage of the split pair, 1-99")
    ap.add_argument("--cwd", default=os.getcwd(),
                    help="working directory for the agent block (defaults to the caller's cwd)")
    ap.add_argument("--mode", default="file", choices=["file", "scrollback"])
    ap.add_argument("--timeout", type=int, default=900, help="seconds to wait for completion")
    ap.add_argument("--poll", type=float, default=3, help="seconds between checks")
    ap.add_argument("--quiet-for", type=int, default=15,
                    help="scrollback mode: seconds without change that count as finished")
    ap.add_argument("--ready-timeout", type=int, default=30, help="seconds to wait for the block's shell")
    ap.add_argument("--keep", action="store_true", help="leave the agent block open when finished")
    args = ap.parse_args()

    if not args.prompt and not args.prompt_file:
        ap.error("one of --prompt or --prompt-file is required")
    prompt = args.prompt
    if args.prompt_file:
        with open(args.prompt_file, encoding="utf-8") as f:
            prompt = f.read()

    preflight()
    cmd = args.command or DEFAULT_LAUNCH.get(args.agent, args.agent)
    tab_id = resolve_tab_id(args.tab)
    if not tab_id:
        die("could not determine the target tab (DANTETERM_TABID unset and no --tab given)")

    block = create_agent_block(args.tab, tab_id, args.target, args.position, args.size, args.cwd)
    print(f"danteterm_delegate: agent block {block}", file=sys.stderr)

    if not wait_for_shell(block, args.ready_timeout):
        die(f"the new block never produced a shell prompt within {args.ready_timeout}s")

    if args.mode == "file":
        tmp = tempfile.mkdtemp(prefix="wave-delegate-")
        result, done = os.path.join(tmp, "result.md"), os.path.join(tmp, "DONE")
        launch_redirected(block, args.agent, cmd, prompt, result, done)
        out = wait_file_mode(block, args.timeout, args.poll, result, done)
    else:
        launch_plain(block, args.agent, cmd, prompt)
        out = wait_scrollback_mode(block, args.timeout, args.poll, args.quiet_for)

    if not args.keep:
        dsh("deleteblock", "-b", block)

    sys.stdout.write(out)
    if out and not out.endswith("\n"):
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
