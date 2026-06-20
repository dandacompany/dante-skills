# Tally Webhooks

Webhooks are the **recommended** way to react to submissions (no polling, no rate-limit pressure).
Tally POSTs a JSON payload to your URL on each form submission.

Official help: <https://tally.so/help/webhooks>

## Setup paths

1. **API:** `POST /webhooks` with `{ formId, url, eventTypes:["FORM_RESPONSE"], signingSecret? }`
   (see `references/api-reference.md`). Manage events via `GET /webhooks/{id}/events` and retry a
   failed delivery with `POST /webhooks/{id}/events/{eventId}` (no `/retry` suffix).
2. **UI:** form → **Integrations → Webhooks** → add endpoint URL + optional signing secret.

## Payload (`FORM_RESPONSE`)

```json
{
  "eventId": "a4cb511e-d513-4fa5-baee-b815d718dfd1",
  "eventType": "FORM_RESPONSE",
  "createdAt": "2023-06-28T15:00:21.889Z",
  "data": {
    "responseId": "2wgx4n",
    "submissionId": "2wgx4n",
    "respondentId": "dwQKYm",
    "formId": "VwbNEw",
    "formName": "Webhook payload",
    "createdAt": "2023-06-28T15:00:21.000Z",
    "submissionPdfUrl": "https://...",
    "submissionPreviewUrl": "https://...",
    "fields": [
      {
        "key": "question_3EKz4n",
        "label": "Text",
        "type": "INPUT_TEXT",
        "value": "Hello"
      },
      {
        "key": "question_a1B2c3",
        "label": "Pick one",
        "type": "MULTIPLE_CHOICE",
        "value": ["opt_id_1"],
        "options": [
          { "id": "opt_id_1", "text": "Option A" },
          { "id": "opt_id_2", "text": "Option B" }
        ]
      }
    ]
  }
}
```

### Reading `data.fields[]`

- Each field: `key`, `label` (question text), `type`, `value`.
- For choice types (`MULTIPLE_CHOICE`, `CHECKBOXES`, `DROPDOWN`, `RANKING`, etc.) `value` is an
  **array of option IDs**; resolve human labels through the sibling `options[]` (`id` → `text`).
- `value` types by question: text/email → string; number/scale/rating → number; date → ISO string;
  file upload → array of file objects; matrix → object.
- This webhook `fields[]` shape is **flatter** than the REST `responses[]` shape — don't assume they match.
- `submissionId` == `responseId` for a given submission.

## Signature verification (`Tally-Signature`)

When a signing secret is set, Tally adds a `Tally-Signature` header: **base64(HMAC-SHA256(rawBody, secret))**.

**Rules:**

1. Compute HMAC over the **raw request body bytes** exactly as received — never over re-serialized JSON
   (key order / whitespace differences break the hash).
2. Base64-encode the digest.
3. Constant-time compare against the header (`hmac.compare_digest` / `crypto.timingSafeEqual`).
4. Reject (HTTP 401) on mismatch; respond `2xx` quickly on success and process async.

Ready-made checker: `scripts/verify_signature.py` (library `verify(raw, header, secret)` + stdin CLI).

### Node / Express

```js
const crypto = require("crypto");
// Mount with raw body so the bytes are untouched:
//   app.post("/hook", express.raw({ type: "application/json" }), handler)
function verify(rawBody, header, secret) {
  const expected = crypto
    .createHmac("sha256", secret)
    .update(rawBody)
    .digest("base64");
  const a = Buffer.from(expected),
    b = Buffer.from(header || "");
  return a.length === b.length && crypto.timingSafeEqual(a, b);
}
```

### Python / Flask

```python
import base64, hmac, hashlib
def verify(raw_body: bytes, header: str, secret: str) -> bool:
    digest = hmac.new(secret.encode(), raw_body, hashlib.sha256).digest()
    return hmac.compare_digest(base64.b64encode(digest).decode(), header)
# Use request.get_data() (raw) — NOT request.json — when verifying.
```

## Delivery & retries

- Tally auto-retries failed deliveries; inspect history via `GET /webhooks/{id}/events` and force a
  resend with `POST /webhooks/{id}/events/{eventId}` (no `/retry` suffix).
- Make handlers **idempotent** — key on `eventId` (or `submissionId`) to dedupe retried events.
