# Showing work in Wave instead of the terminal scrollback

Long output buried in a scrollback is hard to read and easy to lose. Wave blocks are a
better surface for anything the user will actually look at.

## Pick the block by what the content is

| Content                | Command                              |
| ---------------------- | ------------------------------------ |
| a file or directory    | `wsh view ./report.md`               |
| a file to edit         | `wsh edit ./config.json`             |
| a URL / rendered page  | `wsh web open https://…`             |
| a long-running command | `wsh run -- npm test`                |
| an arbitrary widget    | `wsh createblock <view> key=value …` |

`wsh view` renders markdown, images, CSVs and directories. For generated reports, write
a markdown file and open it — far more readable than printing to a terminal.

## Place it deliberately

Placement flags are on `wsh createblock` (v0.17.4+):

```bash
# a narrow pane on the right, 30% of the pair
wsh createblock preview file=./report.md --target 1 --position right --size 30

# replace what is in block 2
wsh createblock web url=https://example.com --target 2 --position replace
```

`--position` takes `right`, `left`, `up`, `down`, `replace`. `--size` is a percentage of
the resulting pair (1-99) and requires `--target`; it is invalid with `replace`.

Sizes are relative weights internally, not percentages — the CLI converts. Do not try to
set a raw weight.

## Send it to the AI sidebar

```bash
git diff | wsh ai -                              # attach, let the user ask
wsh ai -s -m "why did this fail?" ./build.log    # attach and submit
```

Limits: 15 files per call; 200KB text, 5MB PDF, 7MB image.

## Signal without stealing attention

```bash
wsh badge -b 2 --set "3 errors"    # a badge on the block header
wsh notify "build finished"        # an OS notification
```

Prefer these over printing "DONE" into a terminal the user may not be looking at.

## Pull a command's output back out

```bash
wsh termscrollback -b 2                 # whole buffer
wsh termscrollback -b 2 --lastcommand   # just the last command's output (needs shell integration)
wsh termscrollback -b 2 -o out.txt      # to a file
```

`--lastcommand` depends on shell integration being active in that block; without it the
flag returns nothing useful, so fall back to the whole buffer.

## Persist small values between commands

```bash
wsh setvar BUILD_ID=abc123      # this block
wsh setvar -g DEPLOY_ENV=prod   # global
wsh getvar BUILD_ID
```

Use these rather than re-deriving state, and `wsh secret` rather than variables for
anything sensitive.
