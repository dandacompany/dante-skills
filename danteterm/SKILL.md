---
name: danteterm
description: Drive DanteTerm from the command line with dsh - create and arrange tabs and blocks, launch terminal agents (claude, codex, hermes) in their own blocks and delegate tasks to them, collect their results, show output in preview/web/editor blocks instead of scrollback, and manage remote connections, files, variables and secrets. Use when working inside a DanteTerm terminal and the request involves arranging the workspace, running or delegating work in another pane, reading another block's output, or asking how to do something with dsh.
---

# DanteTerm control via dsh

DanteTerm is Dante's fork of Wave Terminal (`dandacompany/danteterm`). The CLI is `dsh`
(Wave's `wsh` renamed), environment variables are `DANTETERM_*`, and the AI sidebar has
been removed, so `wsh ai` has no counterpart. Everything else maps one-to-one.

`dsh` is DanteTerm's CLI. It can create tabs, place blocks, type into other
terminals, read their output, and open files or URLs in the right kind of block. That
makes DanteTerm usable as a workspace an agent arranges and drives, not just a terminal.

## Check these two things first

**1. Running inside DanteTerm.** `dsh` authenticates through `DANTETERM_JWT`, injected into
shells DanteTerm starts. Outside a DanteTerm block every command fails.

```bash
[ -n "$DANTETERM_JWT" ] && echo "inside DanteTerm" || echo "not inside DanteTerm"
```

**2. Version.** Tab management, `sendkeys`, and block placement need **v0.17.4+**:

```bash
dsh tab list >/dev/null 2>&1 && echo "v0.17.4+" || echo "too old: no tab/sendkeys/placement"
```

If either check fails, say so instead of running commands that will fail one by one.

## Delegating a task to another agent

The headline capability: open a block, run an agent CLI in it, hand it a task, collect
the answer. Use the script rather than rebuilding the loop:

```bash
scripts/danteterm_delegate.py --agent claude --prompt "audit ./pkg for data races"
scripts/danteterm_delegate.py --agent codex --prompt-file task.md --tab work --position right --size 40
scripts/danteterm_delegate.py --agent claude --prompt "..." --keep      # leave the block open
scripts/danteterm_delegate.py --agent codex --prompt "..." --cwd ~/projects/myrepo
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
dsh tab create logs                 # new tab (comes up with one terminal)
dsh tab move logs 1                 # 1-based position in the tab bar
dsh tab rename 2 build
dsh tab delete logs                 # refuses the last tab without --close-window

dsh createblock term --target 1 --position right --size 30
dsh view ./report.md                # preview block (default placement; no --target/--position)
dsh createblock preview "file=$PWD/report.md" --target this --position right --size 50   # placed preview
dsh web open https://example.com    # web block
dsh run -- npm test                 # command in its own block
```

**새 창은 `dsh` 로 못 만든다(1.2.13 기준).** `dsh --help` 에 window 명령이 없고 `dsh workspace` 는 `list` 뿐이다.
macOS 에서는 `open -n -a DanteTerm` 으로 두 번째 실행을 걸면 앱의 `second-instance` 핸들러가
`createNewDanteWindow` 를 불러 새 창이 뜬다(2026-10-12 실측, `danteapp.log` 에 `creating new window`).
새 창의 windowId 는 돌려받지 못하고 `dsh workspace list` 에도 이름 없는 창은 안 나오므로, 확인은
`dsh dantepath log --tail` 이나 System Events 창 수로 한다. 정식 명령 추가는
DanteTerm 쪽에 요청해 두었다.

**`createblock preview` 의 `file=` 은 절대 경로로 준다.** 상대 경로를 주면 블록은 만들어지지만
프리뷰가 빈 화면이다 — 블록은 호출한 셸의 cwd 를 모른다 (2026-09-25 실측). `dsh view` 는 상대
경로를 알아서 풀어 주지만 `createblock` 은 그렇지 않다. 경로에 공백이 있으면 `file=…` 전체를 따옴표로 감싼다.

## Driving and reading another block

```bash
dsh sendkeys -b 2 --enter "npm run dev"     # text is literal, no escape processing
dsh sendkeys -b 2 --keys Up Enter           # named control keys
dsh sendkeys -b 2 --keys C-c
dsh sendkeys -b 2 --signal SIGINT
dsh termscrollback -b 2 --lastcommand       # read its output back
```

`dsh sendkeys --help` prints the full key-name table, which is generated from the same
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
`dsh view` it, or open a URL in a web block. Use `dsh badge` or `dsh notify` to signal
completion without stealing focus. (DanteTerm has no AI sidebar, so there is no `dsh ai`.)

**Read `references/output-to-danteterm.md`** for the block-type-by-content table, placement
flags, and `dsh setvar`/`dsh secret` for state between commands.

## The rest of the surface

`dsh ssh` / `dsh wsl` connect a terminal to a remote or WSL host; `dsh file` moves files
between local and remote (`dsh://user@host/path`, or `/~/` for the local machine from a
remote block); `dsh conn` manages connections; `dsh editconfig` and `dsh setconfig` edit
settings; `dsh getmeta` / `dsh setmeta` read and write block metadata.

Run `dsh <command> --help` for exact flags rather than guessing — the help is
authoritative and several commands have flags that only exist on some of them.
