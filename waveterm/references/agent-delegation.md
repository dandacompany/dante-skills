# Delegating work to terminal agents in Wave blocks

The pattern: open a block, run an agent CLI in it, hand it a task, collect the answer.
`scripts/wave_delegate.py` implements it; this file explains the decisions behind it so
the script can be adapted rather than guessed at.

## The loop

1. **Create the block** — `wsh createblock term` (it gets `controller=shell`, so a real
   shell runs in it; a bare `view=term` block has no shell and nothing to type into).
2. **Capture its uuid**, not its number — see `addressing.md`.
3. **Wait for the shell** — the block exists before its shell does. Poll
   `wsh termscrollback -b <uuid>` until it returns something.
4. **Launch with the prompt as an argv argument**, not by typing into a TUI:
   `wsh sendkeys -b <uuid> --enter "claude 'do the thing'"`.
5. **Wait for completion** — see below; this is the only genuinely hard part.
6. **Collect and clean up** — read the result, then `wsh deleteblock -b <uuid>` unless
   the block should stay for inspection.

## Use the agent's non-interactive form, as an argv argument

Two separate points, and getting either wrong wastes the whole timeout.

**Non-interactive form.** Most agent CLIs open a TUI when handed a bare prompt. `claude
'do the thing'` starts an interactive session and waits forever; `claude -p 'do the
thing'` prints and exits. An agent stuck at a TUI never errors, so the delegation just
hangs. Verified forms:

| Agent    | Non-interactive         | Verified                                   |
| -------- | ----------------------- | ------------------------------------------ |
| `claude` | `claude -p '<prompt>'`  | yes, end to end                            |
| `codex`  | `codex exec '<prompt>'` | reaches the agent; needs a trusted git dir |
| `hermes` | `hermes -z '<prompt>'`  | yes, end to end                            |

Check `<agent> --help` before adding an entry — a default-interactive CLI is the trap.

**argv, not typing.** Passing the prompt as a shell argument means the shell hands it
over at startup. Typing it afterwards races the TUI: the input box may not exist yet, the
agent may redraw mid-type, and bracketed-paste handling differs per agent. `wsh sendkeys`
writes bytes straight to the PTY with no escape processing, so shell-quote the prompt
(`shlex.quote`) and nothing else is needed.

## Completion detection

There is no completion signal in wsh. Two workable strategies:

### Shell redirect (default, reliable)

Let the **shell** capture the answer, not the agent:

```bash
claude -p '<prompt>' > /tmp/…/result.md 2>&1; touch /tmp/…/DONE
```

The orchestrator polls for the marker, then reads the result. Nothing here depends on the
agent cooperating with an instruction about where to write — a wrapper telling the agent
to "write your answer to this path" is one more thing it can ignore or get wrong. The
ordering matters: marker last, so its existence implies the answer is already on disk.

`2>&1` is deliberate. A failing agent then returns its error through the same path
instead of producing an empty file and a mysterious success — that is how an expired
codex token surfaced during testing rather than hanging until the timeout.

Requires the agent to have a non-interactive form. If it does not, use scrollback mode.

### Scrollback quiescence (fallback, heuristic)

Poll `wsh termscrollback -b <uuid>` and call it done when the text has not changed for N
seconds. Use only when the prompt cannot be modified — for example when attaching to an
agent session that is already running.

Why it is a fallback: a thinking agent can sit silent longer than N, and an animated
spinner can keep the text changing forever. Both directions are wrong. Also, the
scrollback is a rendered screen, so the answer arrives mixed with the agent's UI chrome.

## Timeouts belong on both ends

The script's `--timeout` bounds the wait; on expiry it prints the tail of the agent's
screen. Without that, a hung delegation looks identical to a slow one.

## The agent block's working directory

A new block does not inherit the caller's cwd, and several agents refuse to run outside a
directory they trust — codex rejects a non-git directory outright. Pass `--cwd`, which
sets `cmd:cwd` on the block:

```bash
wave_delegate.py --agent codex --prompt "..." --cwd ~/projects/myrepo
```

The script defaults `--cwd` to the caller's own cwd, which is usually what is meant.

## Returning the result to the caller

The script prints the answer to stdout, so the caller's own terminal receives it and it
can be piped like any other output:

```bash
wave_delegate.py --agent claude --prompt "audit ./pkg for races" > audit.md
wave_delegate.py --agent codex --prompt "..." | wsh ai -   # into the AI sidebar
```

To show it in a Wave block instead of the caller's scrollback, write it to a file and
open that file in a preview block (see `output-to-wave.md`).

## Fan-out

Multiple agents in one tab, each in its own block, all tracked by uuid:

```bash
for a in claude codex; do
  wave_delegate.py --agent "$a" --tab review --target 1 --position right \
    --prompt "review ./diff.patch" --keep > "review-$a.md" &
done
wait
```

`--keep` leaves the blocks open so the work stays visible. Without it each block closes
as it finishes, which is better for unattended runs.
