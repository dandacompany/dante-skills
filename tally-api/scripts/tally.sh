#!/usr/bin/env bash
# tally.sh — thin curl wrapper for the Tally API (https://api.tally.so)
#
# Auth: reads the API key from (in order):
#   1. $TALLY_API_KEY environment variable
#   2. a `TALLY_API_KEY=...` line in $TALLY_ENV_FILE (default: ~/.claude/auth/tally.env)
# The key looks like `tly-xxxxxxxx`. Create one at Tally > Settings > API keys.
#
# Usage:
#   tally.sh me
#   tally.sh forms [page] [limit]
#   tally.sh form <formId>
#   tally.sh form-create <body.json>                    # POST /forms (blocks/status/workspaceId)
#   tally.sh form-update <formId> <body.json>           # PATCH /forms/{id}
#   tally.sh form-delete <formId>                        # trash a form
#   tally.sh questions <formId>
#   tally.sh submissions <formId> [filter] [limit]      # filter: all|completed|partial
#   tally.sh submission <formId> <submissionId>
#   tally.sh metrics <formId>
#   tally.sh webhooks [page]
#   tally.sh webhook-create <formId> <url> [signingSecret]
#   tally.sh webhook-delete <webhookId>
#   tally.sh workspaces
#   tally.sh raw <METHOD> <path> [json-body]            # escape hatch, e.g. raw GET /users/me
#
# Every response is pretty-printed with jq when available, else raw JSON.
set -euo pipefail

BASE_URL="${TALLY_BASE_URL:-https://api.tally.so}"
ENV_FILE="${TALLY_ENV_FILE:-$HOME/.claude/auth/tally.env}"

load_key() {
  if [[ -n "${TALLY_API_KEY:-}" ]]; then return; fi
  if [[ -f "$ENV_FILE" ]]; then
    # shellcheck disable=SC1090
    TALLY_API_KEY="$(grep -E '^TALLY_API_KEY=' "$ENV_FILE" | tail -n1 | cut -d= -f2- | tr -d '"'"'"' ')"
  fi
  if [[ -z "${TALLY_API_KEY:-}" ]]; then
    echo "ERROR: no API key. Set TALLY_API_KEY or add TALLY_API_KEY=tly-... to $ENV_FILE" >&2
    exit 1
  fi
}

pp() { if command -v jq >/dev/null 2>&1; then jq .; else cat; fi; }

req() {
  local method="$1" path="$2" body="${3:-}"
  local args=(-sS -X "$method" "$BASE_URL$path"
              -H "Authorization: Bearer $TALLY_API_KEY"
              -H "Content-Type: application/json")
  if [[ -n "$body" ]]; then args+=(-d "$body"); fi
  curl "${args[@]}"
}

main() {
  load_key
  local cmd="${1:-}"; shift || true
  case "$cmd" in
    me)            req GET "/users/me" | pp ;;
    forms)         req GET "/forms?page=${1:-1}&limit=${2:-50}" | pp ;;
    form)          req GET "/forms/$1" | pp ;;
    form-create)   req POST "/forms" "$(cat "$1")" | pp ;;
    form-update)   req PATCH "/forms/$1" "$(cat "$2")" | pp ;;
    form-delete)   req DELETE "/forms/$1" | pp ;;
    questions)     req GET "/forms/$1/questions" | pp ;;
    submissions)   req GET "/forms/$1/submissions?filter=${2:-all}&limit=${3:-50}" | pp ;;
    submission)    req GET "/forms/$1/submissions/$2" | pp ;;
    metrics)       req GET "/forms/$1/analytics/metrics" | pp ;;
    webhooks)      req GET "/webhooks?page=${1:-1}" | pp ;;
    webhook-create)
      local fid="$1" url="$2" secret="${3:-}"
      local body
      body=$(printf '{"formId":"%s","url":"%s","eventTypes":["FORM_RESPONSE"]%s}' \
             "$fid" "$url" "${secret:+,\"signingSecret\":\"$secret\"}")
      req POST "/webhooks" "$body" | pp ;;
    webhook-delete) req DELETE "/webhooks/$1" | pp ;;
    workspaces)    req GET "/workspaces" | pp ;;
    raw)           req "$1" "$2" "${3:-}" | pp ;;
    ""|-h|--help|help)
      grep -E '^#( |$)' "$0" | sed 's/^# \{0,1\}//' ;;
    *) echo "Unknown command: $cmd (try: $0 --help)" >&2; exit 1 ;;
  esac
}

main "$@"
