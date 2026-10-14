# Addressing tabs and blocks in dsh

Getting this wrong is the most common way dsh scripts misbehave, because most of the
failure modes are silent — the command succeeds against the wrong thing.

## The rule that matters most

**`this` never crosses a tab.** `-b` defaults to `this`, and `this` always means the
block the command is running in. Combining `--tab` with a defaulted `-b` is rejected:

```
$ dsh sendkeys --tab logs --enter "npm run dev"
Error: --tab requires an explicit block (-b); "this" always means the current block
```

Before v0.17.4 this silently ran the command in the caller's own terminal.

## Tabs

Four forms, accepted by every `dsh tab` subcommand and by `--tab` on `sendkeys`,
`createblock` and `termscrollback`:

| Form             | Example                     | Notes                                               |
| ---------------- | --------------------------- | --------------------------------------------------- |
| omitted / `this` | `dsh tab rename this main`  | the tab the command runs in                         |
| number           | `dsh tab move 3 1`          | **1-based**, matches the tab bar and `dsh tab list` |
| name             | `dsh tab delete logs`       | exact match, current workspace only                 |
| tab id           | `dsh tab delete a0459921-…` | full uuid                                           |

Tab names are **not unique**. Creating a second `logs` succeeds (matching the GUI) but
warns, and from then on the name resolves to nothing usable:

```
Error: "logs" matches 2 tabs: 2 (4477406c-…), 3 (e30859ec-…) -- use a tab number or id
```

For scripts, resolve a name to an id once via `dsh tab list --json` and use the id.

## Blocks

`-b` accepts a 1-based number, a `view:N` form (`term:2`), a uuid, or `this`.

**Numbers are per-tab and positional.** They come from the layout's leaf order, so they
shift whenever a block is added, closed, or moved. A number captured at the start of a
script may point somewhere else by the end.

**Prefer uuids in scripts.** A uuid resolves from any tab, needs no `--tab`, and never
shifts. Get one from `dsh blocks list --workspace="$DANTETERM_WORKSPACEID" --tab "$DANTETERM_TABID" --json`
(`blockid` field).

**Always pass `--workspace`** (open defect,
re-confirmed 2026-10-12 on dsh v1.2.13): without it, `blocks list` queries only *named*
workspaces, so when any named workspace exists the caller's own unnamed one is skipped and
`--tab <own tab>` (uuid, number, name or `this`) prints `No blocks found`, while the unfiltered
list shows blocks from tabs that are not even in `dsh tab list`. `tab list`, `getmeta`,
`createblock` and `sendkeys` are unaffected. Second way to get a uuid inside the current
tab: `dsh getmeta -b <number> -v` prints `resolved-id: block:<uuid>`.

```bash
# capture the uuid of a block you just made, rather than assuming its number
list() { dsh blocks list --workspace="$DANTETERM_WORKSPACEID" --tab "$DANTETERM_TABID" --json \
  | python3 -c 'import sys,json;print(" ".join(b["blockid"] for b in json.load(sys.stdin)))'; }
before=$(list)
dsh createblock term --target this --position right
after=$(list)
NEW=""; for id in $after; do case " $before " in *" $id "*) ;; *) NEW=$id;; esac; done
[ -n "$NEW" ] || { echo "no new block id; aborting"; exit 2; }   # never let -b "" fall through
dsh sendkeys -b "$NEW" --enter "npm test"
```

**An empty `-b ""` is treated as `this`.** A script that fails to capture the uuid and still
calls `sendkeys` types into the caller's own block (seen 2026-10-12: a command landed in the
Claude Code session that ran the script). Guard the variable before every `sendkeys`.

### `--tab` coverage

As of **v0.17.6**, `--tab` takes the same forms (number, name, id, `this`) on `sendkeys`,
`createblock`, `termscrollback`, `deleteblock`, `focusblock`, and `blocks list`.

On **v0.17.4-v0.17.5** it existed only on `sendkeys`, `createblock` and `termscrollback`;
`deleteblock` and `focusblock` had no `--tab`, and `blocks list --tab` took a raw tab id.
Working in uuids sidesteps the difference on every version.

## JSON shapes scripts can rely on

`dsh tab list --json` → array of:

```json
{ "tabid": "…", "name": "T1", "num": 1, "active": true }
```

`dsh blocks list --json` → array of:

```json
{ "blockid": "…", "workspaceid": "…", "tabid": "…", "view": "term", "meta": {} }
```

## Freshly created tabs

A tab's block numbering comes from the layout, which the **frontend** computes as it
renders. Before v0.17.4 `--target 1` failed on a tab that had never been displayed
("leaf order is empty"); it now falls back to the tab's own block list. Even so, a new
tab needs a moment before its default terminal exists — poll `dsh blocks list` rather
than assuming.
