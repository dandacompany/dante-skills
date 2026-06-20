---
name: tally-api
description: Interact with the Tally.so form platform REST API and webhooks — list and read forms, fetch and export submissions, read analytics, manage workspaces and organization users, and create/verify webhooks. Use when the user mentions Tally, tally.so, a Tally form, Tally submissions/responses, Tally webhooks, or wants to pull form data from Tally or react to Tally form submissions. Trigger phrases include "Tally API", "Tally 폼", "Tally 제출/응답 가져와", "Tally webhook", "tally.so form data".
---

# Tally API

## Overview

Tally (tally.so) is a form builder. Its REST API (`https://api.tally.so`) exposes forms, submissions,
analytics, workspaces, organization members, and webhooks. This skill provides the endpoint map, exact
request/response shapes, a curl CLI wrapper, and webhook signature verification so another Claude
instance can read form data, sync submissions, or wire up real-time submission handling without
re-discovering the API each time.

## When to use

Use for any task touching Tally: pulling submissions/responses, reading a form's structure or
analytics, creating forms programmatically, managing workspaces/org users, or setting up and verifying
webhooks. For ongoing submission processing, prefer **webhooks over polling** (the API allows only
100 requests/minute).

## Authentication

- Get a key at Tally dashboard → **Settings → API keys → Create API key**. It is shown once; copy it.
- Key format `tly-xxxx`; send as `Authorization: Bearer tly-xxxx`.
- A key inherits the creating user's permissions (no fine-grained scopes). Workspace creation needs Pro.
- Store the key out of the repo. The CLI reads `$TALLY_API_KEY`, else `TALLY_API_KEY=` from
  `~/.claude/auth/tally.env` (override path with `$TALLY_ENV_FILE`). Never print the key in full.

## How to use

**Start by reading the reference**, then act:

- `references/api-reference.md` — every endpoint (forms, analytics, questions, submissions, webhooks,
  workspaces, organizations, users/me), pagination, status codes, submission response shape, curl examples.
- `references/webhooks.md` — webhook payload (`FORM_RESPONSE` + `data.fields[]`) and `Tally-Signature`
  HMAC-SHA256 verification.
- `references/examples/create-form.json` — a working `POST /forms` body with block structure.

**CLI wrapper** — `scripts/tally.sh` (curl + jq, key auto-loaded):

```bash
scripts/tally.sh me                                  # whoami
scripts/tally.sh forms                               # list forms
scripts/tally.sh questions <formId>                  # form questions
scripts/tally.sh submissions <formId> completed 100  # filter: all|completed|partial
scripts/tally.sh submission <formId> <submissionId>
scripts/tally.sh metrics <formId>                    # analytics
scripts/tally.sh form-create body.json               # create a form (POST /forms)
scripts/tally.sh form-update <formId> body.json      # PATCH /forms/{id}
scripts/tally.sh form-delete <formId>                # trash a form
scripts/tally.sh webhooks
scripts/tally.sh webhook-create <formId> <url> [signingSecret]   # connect a webhook
scripts/tally.sh raw GET /users/me                   # escape hatch for any endpoint
```

Run `scripts/tally.sh --help` for the full command list. For anything the wrapper does not cover, use
`raw <METHOD> <path> [json-body]` or hand-write curl from the reference.

**Webhook verification** — `scripts/verify_signature.py`:

```python
from verify_signature import verify   # verify(raw_body_bytes, tally_signature_header, signing_secret) -> bool
```

Always hash the **raw request body bytes**, never re-serialized JSON, or the signature won't match.

## Key gotchas

- **Two pagination styles:** offset (`page`/`limit`, check `hasMore`) and cursor (`afterId`). Use
  `afterId` for stable large backfills.
- **Submission answers are typed by question:** join `responses[].questionId` to `questions[]` to learn
  each answer's type/title. Only answered questions appear.
- **REST vs webhook shapes differ:** REST returns `responses[]` (`answer`/`formattedAnswer`); webhooks
  send `data.fields[]` (`label`/`type`/`value`, with `options[]` for choices). Don't assume they match.
- **Rate limit 100/min** → `429`. Batch with `limit` up to 500, or switch to webhooks.
- **Destructive ops:** `DELETE /workspaces/{id}` removes all its forms; `DELETE /forms/{id}` trashes a
  form. Confirm before running.
- Make webhook handlers **idempotent** (dedupe on `eventId`/`submissionId`); deliveries can retry.
