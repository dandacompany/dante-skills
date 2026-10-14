# Showing work in DanteTerm instead of the terminal scrollback

Long output buried in a scrollback is hard to read and easy to lose. DanteTerm blocks are a
better surface for anything the user will actually look at.

## Pick the block by what the content is

| Content                | Command                              |
| ---------------------- | ------------------------------------ |
| a file or directory    | `dsh view ./report.md`               |
| a file to edit         | `dsh edit ./config.json`             |
| a URL / rendered page  | `dsh web open https://…`             |
| a long-running command | `dsh run -- npm test`                |
| an arbitrary widget    | `dsh createblock <view> key=value …` |

`dsh view` renders markdown, images, CSVs and directories. For generated reports, write
a markdown file and open it — far more readable than printing to a terminal.

## Place it deliberately

Placement flags are on `dsh createblock` (v0.17.4+):

```bash
# a narrow pane on the right, 30% of the pair
dsh createblock preview "file=$PWD/report.md" --target 1 --position right --size 30   # file= 은 반드시 절대 경로

# `file=` 에 상대 경로를 주면 빈 프리뷰가 뜬다 (2026-09-25 실측). `dsh view` 만 상대 경로를 풀어 준다.

# replace what is in block 2
dsh createblock web url=https://example.com --target 2 --position replace
```

`--position` takes `right`, `left`, `up`, `down`, `replace`. `--size` is a percentage of
the resulting pair (1-99) and requires `--target`; it is invalid with `replace`.

Sizes are relative weights internally, not percentages — the CLI converts. Do not try to
set a raw weight.

## Signal without stealing attention

```bash
dsh badge -b 2 --set "3 errors"    # a badge on the block header
dsh notify "build finished"        # an OS notification
```

Prefer these over printing "DONE" into a terminal the user may not be looking at.

## Pull a command's output back out

```bash
dsh termscrollback -b 2                 # whole buffer
dsh termscrollback -b 2 --lastcommand   # just the last command's output (needs shell integration)
dsh termscrollback -b 2 -o out.txt      # to a file
```

`--lastcommand` depends on shell integration being active in that block; without it the
flag returns nothing useful, so fall back to the whole buffer.

## Persist small values between commands

```bash
dsh setvar BUILD_ID=abc123      # this block
dsh setvar -g DEPLOY_ENV=prod   # global
dsh getvar BUILD_ID
```

Use these rather than re-deriving state, and `dsh secret` rather than variables for
anything sensitive.
