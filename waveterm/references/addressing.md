# Addressing tabs and blocks in wsh

Getting this wrong is the most common way wsh scripts misbehave, because most of the
failure modes are silent — the command succeeds against the wrong thing.

## The rule that matters most

**`this` never crosses a tab.** `-b` defaults to `this`, and `this` always means the
block the command is running in. Combining `--tab` with a defaulted `-b` is rejected:

```
$ wsh sendkeys --tab logs --enter "npm run dev"
Error: --tab requires an explicit block (-b); "this" always means the current block
```

Before v0.17.4 this silently ran the command in the caller's own terminal.

## Tabs

Four forms, accepted by every `wsh tab` subcommand and by `--tab` on `sendkeys`,
`createblock` and `termscrollback`:

| Form             | Example                     | Notes                                               |
| ---------------- | --------------------------- | --------------------------------------------------- |
| omitted / `this` | `wsh tab rename this main`  | the tab the command runs in                         |
| number           | `wsh tab move 3 1`          | **1-based**, matches the tab bar and `wsh tab list` |
| name             | `wsh tab delete logs`       | exact match, current workspace only                 |
| tab id           | `wsh tab delete a0459921-…` | full uuid                                           |

Tab names are **not unique**. Creating a second `logs` succeeds (matching the GUI) but
warns, and from then on the name resolves to nothing usable:

```
Error: "logs" matches 2 tabs: 2 (4477406c-…), 3 (e30859ec-…) -- use a tab number or id
```

For scripts, resolve a name to an id once via `wsh tab list --json` and use the id.

## Blocks

`-b` accepts a 1-based number, a `view:N` form (`term:2`), a uuid, or `this`.

**Numbers are per-tab and positional.** They come from the layout's leaf order, so they
shift whenever a block is added, closed, or moved. A number captured at the start of a
script may point somewhere else by the end.

**Prefer uuids in scripts.** A uuid resolves from any tab, needs no `--tab`, and never
shifts. Get one from `wsh blocks list --tab <tabid> --json` (`blockid` field).

```bash
# capture the uuid of a block you just made, rather than assuming its number
before=$(wsh blocks list --tab "$TABID" --json | python3 -c 'import sys,json;print(" ".join(b["blockid"] for b in json.load(sys.stdin)))')
wsh createblock term --target 1 --position right
# diff before/after to find the new blockid
```

### `--tab` coverage

As of **v0.17.6**, `--tab` takes the same forms (number, name, id, `this`) on `sendkeys`,
`createblock`, `termscrollback`, `deleteblock`, `focusblock`, and `blocks list`.

On **v0.17.4-v0.17.5** it existed only on `sendkeys`, `createblock` and `termscrollback`;
`deleteblock` and `focusblock` had no `--tab`, and `blocks list --tab` took a raw tab id.
Working in uuids sidesteps the difference on every version.

## JSON shapes scripts can rely on

`wsh tab list --json` → array of:

```json
{ "tabid": "…", "name": "T1", "num": 1, "active": true }
```

`wsh blocks list --json` → array of:

```json
{ "blockid": "…", "workspaceid": "…", "tabid": "…", "view": "term", "meta": {} }
```

## Freshly created tabs

A tab's block numbering comes from the layout, which the **frontend** computes as it
renders. Before v0.17.4 `--target 1` failed on a tab that had never been displayed
("leaf order is empty"); it now falls back to the tab's own block list. Even so, a new
tab needs a moment before its default terminal exists — poll `wsh blocks list` rather
than assuming.
