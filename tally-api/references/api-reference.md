# Tally API Reference

Source of truth: <https://developers.tally.so> (machine index: `https://developers.tally.so/llms.txt`,
OpenAPI: `https://developers.tally.so/api-reference/openapi.json`).

## Basics

| Item         | Value                                                                                      |
| ------------ | ------------------------------------------------------------------------------------------ |
| Base URL     | `https://api.tally.so` (HTTPS only — HTTP is rejected)                                     |
| Auth header  | `Authorization: Bearer tly-xxxxxxxx`                                                       |
| Content type | `application/json`                                                                         |
| Rate limit   | **100 requests / minute** → `429` when exceeded. Prefer webhooks over polling.             |
| API key      | Tally dashboard → **Settings → API keys → Create API key**. Shown once — copy immediately. |

**API key semantics:** a key inherits the permissions of the user who created it (no fine-grained
scopes yet). Removing that user from the organization deactivates all their keys.

### Status codes

`200` ok · `400` bad request · `401` unauthorized (bad/missing key) · `403` forbidden (no permission) ·
`404` not found · `429` rate limited · `500` server error.

### Pagination

Two styles coexist:

- **Offset:** `page` (default 1) + `limit`. Responses carry `page`, `limit`, `hasMore`.
- **Cursor:** `afterId=<lastSubmissionId>` — stable for syncing large submission sets (no skipped/duplicated rows when data changes mid-paging). Prefer this for backfills.

## Endpoints

### User

| Method | Path        | Purpose                     |
| ------ | ----------- | --------------------------- |
| GET    | `/users/me` | Current authenticated user. |

### Forms

| Method | Path          | Purpose                                                            |
| ------ | ------------- | ------------------------------------------------------------------ |
| POST   | `/forms`      | Create a form (optionally from `templateId` / into `workspaceId`). |
| GET    | `/forms`      | Paginated list of forms.                                           |
| GET    | `/forms/{id}` | Single form with all blocks + settings.                            |
| PATCH  | `/forms/{id}` | Update settings, blocks, or status.                                |
| DELETE | `/forms/{id}` | Delete form (moves to trash).                                      |

**Create form body:** `status` (`BLANK`|`DRAFT`|`PUBLISHED`|`DELETED`), `blocks` (array), optional
`workspaceId`, `templateId`, `settings`. Each block: `{ uuid, type, groupUuid, groupType, payload }`.
Common block types: `FORM_TITLE`, `INPUT_TEXT`, `TEXTAREA`, `INPUT_EMAIL`, `INPUT_NUMBER`,
`MULTIPLE_CHOICE`, `CHECKBOXES`, `DROPDOWN`, `LINEAR_SCALE`, `RATING`, `INPUT_DATE`, `FILE_UPLOAD`.
`groupType` is `FORM_TITLE` for the title block and `QUESTION` for inputs. See `examples/create-form.json`.

### Form analytics

| Method | Path                                | Purpose                                               |
| ------ | ----------------------------------- | ----------------------------------------------------- |
| GET    | `/forms/{id}/analytics/metrics`     | Aggregate: visits, submissions, completion rate, etc. |
| GET    | `/forms/{id}/analytics/visits`      | Visit counts over time.                               |
| GET    | `/forms/{id}/analytics/submissions` | Completed + partial counts over time.                 |
| GET    | `/forms/{id}/analytics/dimensions`  | Breakdown by source, browser, OS, device, location.   |
| GET    | `/forms/{id}/analytics/drop-off`    | Per-question drop-off stats.                          |

### Questions & blocks

| Method | Path                                 | Purpose                                                    |
| ------ | ------------------------------------ | ---------------------------------------------------------- |
| GET    | `/forms/{id}/questions`              | All questions in a form.                                   |
| PATCH  | `/forms/{id}/questions/{questionId}` | Update a single question.                                  |
| GET    | `/forms/{id}/blocks`                 | The form's raw blocks (lower level than `/questions`).     |
| PATCH  | `/forms/{id}/blocks`                 | Replace/update the form's blocks (full block-array edits). |

Block types and their `payload` shapes are documented per-block at
`https://developers.tally.so/blocks-reference/<block>.md` (40+ blocks: input-text, textarea,
multiple-choice-option, checkbox, dropdown-option, linear-scale, rating, matrix, file-upload, payment,
signature, hidden-fields, conditional-logic, calculated-fields, page-break, etc.). Step-by-step form
build guides live under `https://developers.tally.so/documentation/` (creating-a-form,
adding-blocks-to-a-form, creating-a-form-with-settings, creating-a-dropdown, creating-a-mention).

### Submissions

| Method | Path                                     | Purpose                                      |
| ------ | ---------------------------------------- | -------------------------------------------- |
| GET    | `/forms/{id}/submissions`                | Paginated submissions with responses.        |
| GET    | `/forms/{id}/submissions/{submissionId}` | One submission + responses + form questions. |
| DELETE | `/forms/{id}/submissions/{submissionId}` | Delete a submission.                         |

**List query params:** `page` (1), `limit` (1–500, default 50), `filter` (`all`|`completed`|`partial`),
`startDate` / `endDate` (ISO 8601), `afterId` (cursor).

**List response shape:**

```json
{
  "page": 1,
  "limit": 50,
  "hasMore": true,
  "totalNumberOfSubmissionsPerFilter": {
    "all": 250,
    "completed": 200,
    "partial": 50
  },
  "questions": [
    {
      "id": "q1",
      "type": "INPUT_TEXT",
      "title": "Question Title",
      "formId": "abc123",
      "numberOfResponses": 200
    }
  ],
  "submissions": [
    {
      "id": "sub123",
      "formId": "abc123",
      "isCompleted": true,
      "submittedAt": "2024-01-15T10:30:00Z",
      "previewUrl": "https://...",
      "pdfUrl": "https://...",
      "responses": [
        {
          "id": "resp1",
          "questionId": "q1",
          "respondentId": "...",
          "submissionId": "sub123",
          "sessionUuid": "...",
          "answer": "user response text",
          "formattedAnswer": "formatted version",
          "createdAt": "...",
          "updatedAt": "..."
        }
      ]
    }
  ]
}
```

- `responses[].answer` type **varies by question type** (string, number, boolean, array, or object).
  Join each response to `questions[]` via `questionId` to learn the type/title.
- Only **answered** questions appear in `responses`.
- The REST `responses[]` shape differs from the webhook `data.fields[]` shape — see `references/webhooks.md`.

### Webhooks

| Method | Path                              | Purpose                                                 |
| ------ | --------------------------------- | ------------------------------------------------------- |
| POST   | `/webhooks`                       | Create a webhook for a form.                            |
| GET    | `/webhooks`                       | List webhooks across accessible forms/workspaces.       |
| PATCH  | `/webhooks/{id}`                  | Update a webhook.                                       |
| DELETE | `/webhooks/{id}`                  | Delete a webhook.                                       |
| GET    | `/webhooks/{id}/events`           | Paginated delivery events for a webhook.                |
| POST   | `/webhooks/{id}/events/{eventId}` | Retry a failed delivery (note: **no** `/retry` suffix). |

**Create body:** `{ "formId", "url", "eventTypes": ["FORM_RESPONSE"], "signingSecret"?, "httpHeaders"?: [{"name","value"}], "externalSubscriber"? }`.
Required: `formId`, `url`, `eventTypes`. Only event type today: `FORM_RESPONSE`.
Payload + signature verification: `references/webhooks.md`.

### Workspaces

| Method | Path               | Purpose                                    |
| ------ | ------------------ | ------------------------------------------ |
| POST   | `/workspaces`      | Create workspace (**requires Pro**).       |
| GET    | `/workspaces`      | List workspaces + users + pending invites. |
| GET    | `/workspaces/{id}` | One workspace + members.                   |
| PATCH  | `/workspaces/{id}` | Update workspace.                          |
| DELETE | `/workspaces/{id}` | Delete workspace **and all its forms**.    |

### Organizations

All organization paths require the `{organizationId}` path segment (the llms.txt summary omits it, but
the OpenAPI spec requires it). Obtain the organization ID from `GET /users/me` / `GET /workspaces`.

| Method | Path                                                 | Purpose                              |
| ------ | ---------------------------------------------------- | ------------------------------------ |
| GET    | `/organizations/{organizationId}/users`              | List org users.                      |
| DELETE | `/organizations/{organizationId}/users/{userId}`     | Remove a user from the org.          |
| POST   | `/organizations/{organizationId}/invites`            | Invite users to specific workspaces. |
| GET    | `/organizations/{organizationId}/invites`            | List invites.                        |
| DELETE | `/organizations/{organizationId}/invites/{inviteId}` | Cancel a pending invite.             |

## curl examples

```bash
# Whoami
curl -sS https://api.tally.so/users/me -H "Authorization: Bearer $TALLY_API_KEY"

# List completed submissions, 100 at a time
curl -sS "https://api.tally.so/forms/$FORM_ID/submissions?filter=completed&limit=100" \
  -H "Authorization: Bearer $TALLY_API_KEY"

# Create a webhook
curl -sS -X POST https://api.tally.so/webhooks \
  -H "Authorization: Bearer $TALLY_API_KEY" -H "Content-Type: application/json" \
  -d '{"formId":"abc123","url":"https://example.com/hook","eventTypes":["FORM_RESPONSE"],"signingSecret":"whsec_..."}'
```
