---
name: waveterm
description: Drive Wave Terminal from the command line with wsh - create and arrange tabs and blocks, launch terminal agents (claude, codex, hermes) in their own blocks and delegate tasks to them, collect their results, show output in preview/web/editor blocks instead of scrollback, and manage remote connections, files, variables and secrets. Use when working inside a Wave terminal and the request involves arranging the workspace, running or delegating work in another pane, reading another block's output, or asking how to do something with wsh.
---

# Wave Terminal control via wsh

`wsh` is Wave Terminal's CLI. It can create tabs, place blocks, type into other
terminals, read their output, and open files or URLs in the right kind of block. That
makes Wave usable as a workspace an agent arranges and drives, not just a terminal.

## Check these two things first

**1. Running inside Wave.** `wsh` authenticates through `WAVETERM_JWT`, injected into
shells Wave starts. Outside a Wave block every command fails.

```bash
[ -n "$WAVETERM_JWT" ] && echo "inside Wave" || echo "not inside Wave"
```

**2. Version.** Tab management, `sendkeys`, and block placement need **v0.17.4+**:

```bash
wsh tab list >/dev/null 2>&1 && echo "v0.17.4+" || echo "too old: no tab/sendkeys/placement"
```

If either check fails, say so instead of running commands that will fail one by one.

## Delegating a task to another agent

The headline capability: open a block, run an agent CLI in it, hand it a task, collect
the answer. Use the script rather than rebuilding the loop:

```bash
scripts/wave_delegate.py --agent claude --prompt "audit ./pkg for data races"
scripts/wave_delegate.py --agent codex --prompt-file task.md --tab work --position right --size 40
scripts/wave_delegate.py --agent claude --prompt "..." --keep      # leave the block open
scripts/wave_delegate.py --agent codex --prompt "..." --cwd ~/projects/myrepo
```

It creates the block, waits for its shell, launches the agent with the prompt as an argv
argument, waits for completion, prints the answer to stdout, and closes the block.

Completion is detected by a **shell redirect** by default: the agent's non-interactive
form runs with its output redirected to a file, then a marker is touched, and the script
polls for the marker. The shell does the capturing, so nothing depends on the agent
cooperating. `--mode scrollback` instead waits for the screen to stop changing — a
heuristic, for agents with no non-interactive form.

Two things reliably break a delegation, both covered in the reference: using an agent's
**interactive** form (`claude '<prompt>'` opens a TUI and hangs; it needs `-p`), and
leaving the block in a directory the agent refuses to work in (pass `--cwd`).

**Read `references/agent-delegation.md`** before changing how delegation works, adding an
agent, or debugging a run that hangs or returns noise. It covers why argv beats typing
into the TUI, the tradeoffs of each completion mode, and fan-out.

## Arranging the workspace

```bash
wsh tab create logs                 # new tab (comes up with one terminal)
wsh tab move logs 1                 # 1-based position in the tab bar
wsh tab rename 2 build
wsh tab delete logs                 # refuses the last tab without --close-window

wsh createblock term --target 1 --position right --size 30
wsh view ./report.md                # preview block
wsh web open https://example.com    # web block
wsh run -- npm test                 # command in its own block
```

## Driving and reading another block

```bash
wsh sendkeys -b 2 --enter "npm run dev"     # text is literal, no escape processing
wsh sendkeys -b 2 --keys Up Enter           # named control keys
wsh sendkeys -b 2 --keys C-c
wsh sendkeys -b 2 --signal SIGINT
wsh termscrollback -b 2 --lastcommand       # read its output back
```

`wsh sendkeys --help` prints the full key-name table, which is generated from the same
table the parser uses, so it cannot drift.

## Addressing — where silent mistakes come from

Tabs take a number (1-based), an exact name, a uuid, or `this`. Blocks take a number, a
uuid, `view:N`, or `this`.

Two traps worth knowing before writing any script:

- **`this` never crosses a tab.** `--tab X` with a defaulted `-b` is rejected rather than
  quietly acting on the caller's own block.
- **Block numbers shift.** They come from the layout's leaf order, so adding or closing a
  block renumbers the rest. Scripts should capture uuids.

**Read `references/addressing.md`** before writing a script that targets blocks or tabs
by anything other than `this`. It also lists which commands lack `--tab` and the JSON
shapes to parse.

## Putting results where the user will see them

Prefer a block over scrollback for anything worth reading: write a markdown file and
`wsh view` it, open a URL in a web block, or push context to the AI sidebar with
`wsh ai`. Use `wsh badge` or `wsh notify` to signal completion without stealing focus.

**Read `references/output-to-wave.md`** for the block-type-by-content table, placement
flags, sidebar limits, and `wsh setvar`/`wsh secret` for state between commands.

## The rest of the surface

`wsh ssh` / `wsh wsl` connect a terminal to a remote or WSL host; `wsh file` moves files
between local and remote (`wsh://user@host/path`, or `/~/` for the local machine from a
remote block); `wsh conn` manages connections; `wsh editconfig` and `wsh setconfig` edit
settings; `wsh getmeta` / `wsh setmeta` read and write block metadata.

Run `wsh <command> --help` for exact flags rather than guessing — the help is
authoritative and several commands have flags that only exist on some of them.
