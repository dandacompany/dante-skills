---
name: gpt-model-effort-advisor
description: Recommend which GPT-5.6 model tier (Luna/Terra/Sol) and reasoning effort (Low..Ultra) fits a task, learn from the user's own successes and failures, diagnose quality problems, and report the live session's model and effort. Advisory — it proposes a grounded starting point and an escalation rule; the human decides and switches. Load when the user asks which model or effort to use, starts a substantial task without deliberately choosing a tier, reports a poor or unsatisfying result, wants to reduce cost without losing quality, or asks what model the session is running. Triggers — "which model", "which effort", "reasoning effort", "cut cost", "is a bigger model worth it", "do I need max/ultra", "result is bad", "quality dropped", "what model am I on", "record this combo".
---

# GPT-5.6 Model & Effort Advisor

Help pick the right **model tier** and **reasoning effort** for a task, escalate only when needed, learn from real outcomes, and diagnose failures. It recommends and records; the user decides and switches.

## Two independent axes

- **Model tier = intelligence ceiling.** A larger tier knows more and reasons deeper, at a higher price per token. GPT-5.6 tiers: **Luna** (economy) → **Terra** (balanced) → **Sol** (frontier).
- **Reasoning effort = deliberation time.** More effort spends more thinking on the same problem, at more tokens. Levels: **Low → Medium → High → Max → Ultra**.

These are different dials. Turning both to the maximum by default wastes money without improving quality on most tasks. Choose each axis deliberately.

## Engine: `registry.py`

`registry.py` (same folder, standard library only) powers the three data functions. Always use this CLI — do not hand-edit the JSON.

```
python3 registry.py session                        # read the live session's model + effort
python3 registry.py query "<task>" [--axes ...]    # find similar past successes/failures
python3 registry.py record --task "..." --model gpt-5.6-<tier> --effort <e> \
        --outcome success|fail|partial [--axes ...] [--reason ...] [--cost N] [--minutes N] [--notes ...]
python3 registry.py stats                          # summary of the registry
```

The registry starts empty and fills from the user's real usage. **Recorded outcomes take priority over the static heuristics below** — personal history beats generic rules over time.

## Workflow for every task

### 1. Check the session (function: state)

```
python3 registry.py session   →  {"model": "...", "effort": "...", "source": "..."}
```

If the current setting is heavier than the task needs (expensive dial on an easy job) or lighter than it needs, say so. Codex does not auto-switch per turn — the user switches with `/model` or launches the next session with `-m`/`-c`.

### 2. Recommend (registry first, heuristics second)

```
python3 registry.py query "<the user's task>" --axes "<4-axis tags>"
```

- If `best_success_combos` exist, recommend that combo first ("a similar task succeeded with Terra + High").
- If `avoid_failures` exist, warn against those combos.
- If the registry has no similar record, fall back to the heuristics below.

Classify the task on **four axes** and pass them so matching is precise:
`--axes "verifiable=yes|partial|no,failcost=low|mid|high,volume=high|low,depth=shallow|mid|deep"`

- **verifiable** — can success be checked mechanically (tests, schema, exact numbers, render errors)?
- **failcost** — how costly is a wrong answer?
- **volume** — how many times will this run (batch → price-sensitive)?
- **depth** — deep world-knowledge / design, or mostly retrieval + assembly?

### 3. Record the outcome (functions: success + failure)

When the task ends, record it — this is how the advisor learns.

- **Success** (user satisfied / checks pass): `record --outcome success` — future similar tasks will get this combo first.
- **Failure / dissatisfaction / quality drop**: `record --outcome fail --reason "<what went wrong>"`, then diagnose with the table below.
- Ambiguous: `partial`.

## Heuristics for cold start (no registry match)

Reason from the task shape, not from fixed prices.

| Task shape                                                      | Start with                                           | Why                                                                                                                                        |
| --------------------------------------------------------------- | ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Formal, verifiable, high-volume (extract, reconcile, convert)   | **economy tier · Medium**                            | Quality holds when the task is formal; only cost differs, so pick the cheapest that passes.                                                |
| Judgment / analysis, mid failure cost                           | **balanced tier · High**                             | Effort helps up to a point; the balanced tier is usually enough.                                                                           |
| Human-reviewed draft (slides, docs)                             | **economy tier · High → human finishes**             | Cheap first pass, human does the last mile.                                                                                                |
| Complex build, mid–high failure cost (apps, simulations, media) | **balanced tier · Max**                              | The balanced tier at high effort often matches the frontier tier's quality for far less; the frontier tier rarely justifies its cost here. |
| Deep knowledge / physics / architecture                         | **frontier tier · High**                             | This is where model size genuinely decides the outcome. Stay at High.                                                                      |
| High failure cost / one correct answer (migration, security)    | **frontier tier · High**, escalate to Max on failure | Buy a safety margin. Still not Ultra by default.                                                                                           |

## Effort has a ceiling — a core principle

Reasoning effort shows **diminishing returns**, and past a point more effort can _hurt_:

- **Over-fitting to the letter of the spec** instead of its intent — optimizing to pass the check rather than to do the work well (reward hacking / benchmark gaming).
- **Runaway self-polishing** after the result is already acceptable — cost and wall-clock explode with no quality gain.
- **Delegation overhead** without added insight.

Consequences for choosing effort:

- **High is usually the effective ceiling.** Going beyond it is often waste.
- **Reserve the maximum effort levels for tasks that genuinely decompose into sub-tasks.** Otherwise they burn budget for nothing — verify before using them.
- **If you have hit the effort ceiling and still fail, raise the model tier, not the effort.**

## Failure diagnosis — pick the right fix

| Symptom                                                           | Likely cause                 | Fix                                                               |
| ----------------------------------------------------------------- | ---------------------------- | ----------------------------------------------------------------- |
| Wrong or shallow at low effort                                    | not enough deliberation      | **raise effort one step** (same tier first)                       |
| **Still wrong at High effort**                                    | intelligence ceiling reached | **raise the model tier — not the effort**                         |
| Games the check / literal-but-wrong (worse the higher the effort) | over-optimization            | **lower effort and sharpen the spec / strengthen the check**      |
| Passed but keeps polishing; time and cost balloon (top effort)    | no stop condition            | **drop to a bounded effort and state a clear Definition-of-Done** |
| Quality is fine but too slow or expensive                         | over-provisioned             | **lower the tier and/or effort**                                  |
| Delegates but no added insight                                    | delegation overhead          | **avoid the top effort; use a focused High run**                  |

After suggesting a fix, record the retry's outcome to close the loop.

## Applying it in codex

- Launch: `codex -m gpt-5.6-<tier> -c model_reasoning_effort=<effort>` (e.g. `-m gpt-5.6-terra -c model_reasoning_effort=high`).
- Switch mid-session: `/model`.
- Codex does not change the model per turn on its own. This skill recommends and records; the user makes the switch.

## Output format

Keep it short (3–5 lines) and framed as a proposal, not a verdict:

> **Recommend: `<tier> · <effort>`** — <one-line 4-axis read> (similar past success: <registry hit, or "none — heuristic">)
> Run this first; if **<verifiable check>** fails, escalate to **`<higher tier or fix>`**.
> Launch: `codex -m gpt-5.6-<tier> -c model_reasoning_effort=<effort>` · current session: `<session read>`
> I'll record the outcome so the next recommendation improves.
