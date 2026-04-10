# Memory Schema Reference

This document defines the expected structure for memory files managed by the Dream skill.

---

## Directory Layout

A memory system consists of one index file and any number of individual memory files:

```
memory/
├── MEMORY.md           ← Index (always present, loaded first)
├── user_profile.md     ← user type
├── feedback_testing.md ← feedback type
├── project_auth.md     ← project type
├── ref_linear.md       ← reference type
└── ...
```

The index file `MEMORY.md` has **no frontmatter**. Each line is a pointer to a memory file:

```markdown
- [Title](filename.md) — one-line hook under 150 chars
```

Group by type and sort active items first:

```markdown
## Project
- [Auth System Status](project_auth.md) — JWT + RBAC complete, refresh tokens pending
- [API Rate Limiting](project_ratelimit.md) — Redis-based, 100 req/min per key

## Feedback
- [Test Strategy](feedback_testing.md) — integration tests must use real DB, not mocks

## User
- [User Profile](user_profile.md) — senior Go engineer, new to React frontend

## Reference
- [Issue Tracker](ref_linear.md) — bugs tracked in Linear project "BACKEND"

## Archive
- [Old Auth Design](archive_auth_v1.md) — superseded by JWT migration in 2025-03
```

---

## Memory File Format

Every memory file (except `MEMORY.md`) must have YAML frontmatter:

```markdown
---
name: Short human-readable name
description: One sentence — used to decide relevance in future conversations
type: user | feedback | project | reference
---

Body content here.
```

### Required Frontmatter Fields

| Field | Purpose | Rules |
|-------|---------|-------|
| `name` | Human-readable identifier | Short, title-case |
| `description` | Decides when the memory is loaded | One sentence, specific, no angle brackets |
| `type` | Categorizes the memory | Must be one of the four types below |

### Memory Types

**`user`** — Who the user is, their role, expertise, preferences.

```markdown
---
name: User Profile
description: Background and expertise of the primary user — informs explanation depth and framing
type: user
---

Senior backend engineer (10 years Go). New to the React side of this repo.
Frame frontend explanations using backend analogues.
```

---

**`feedback`** — Guidance the user gave about how to work — corrections and confirmed approaches.

```markdown
---
name: Testing Strategy
description: How to write tests in this project — real DB required, no mocks
type: feedback
---

Integration tests must hit a real database, not mocks.

**Why:** A prior incident where mock/prod divergence masked a broken migration.
**How to apply:** Always spin up the test database container before running integration tests.
```

---

**`project`** — Ongoing work, decisions, deadlines, incidents — not derivable from code alone.

```markdown
---
name: Payment Service Status
description: Current state of the payment service rewrite — compliance-driven, scope constraints
type: project
---

Auth middleware rewrite is driven by legal/compliance requirements around session token storage.

**Why:** Legal flagged existing middleware for storing session tokens in a non-compliant way.
**How to apply:** Scope decisions should favor compliance over ergonomics. Avoid reverting to old patterns.
```

---

**`reference`** — Pointers to external systems and where to find information.

```markdown
---
name: Issue Tracker
description: Where bugs and feature requests are tracked for the pipeline team
type: reference
---

Pipeline bugs are tracked in Linear project "INGEST".
API documentation lives at internal-docs.company.com/api.
Oncall Grafana dashboard: grafana.internal/d/api-latency.
```

---

## Staleness Indicators

A memory is likely stale when it:

- Names a file path that no longer exists (check with Glob)
- Names a function, class, or variable that no longer exists (check with Grep)
- Describes a "current sprint" or "this week" task that clearly concluded
- References a dependency version that has since been upgraded
- Describes infra state (ports, hostnames, container names) that conflicts with current config files

## What NOT to Store in Memory

Avoid saving things that can be derived from current code or git history:

- Code patterns or architecture visible by reading the repo
- Git history or who-changed-what (use `git log`/`git blame`)
- Debugging solutions or fix recipes (the fix is in the code)
- Anything already documented in CLAUDE.md / AGENTS.md
- Ephemeral task state or in-progress work for the current session
