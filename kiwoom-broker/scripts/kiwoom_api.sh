#!/usr/bin/env bash
# 키움증권 REST API 범용 호출 래퍼
#
# 사용법:
#   kiwoom_api.sh [-p mock|real] [-k NEXT_KEY] API_ID PATH [JSON_BODY]
#
# 예시:
#   kiwoom_api.sh ka10081 /api/dostk/chart '{"stk_cd":"069500","base_dt":"20260805","upd_stkpc_tp":"1"}'
#   kiwoom_api.sh ka40002 /api/dostk/etf   '{"stk_cd":"069500"}'
#   kiwoom_api.sh kt00018 /api/dostk/acnt  '{"qry_tp":"1","dmst_stex_tp":"KRX"}'
#   kiwoom_api.sh -k "$NEXT_KEY" ka10081 /api/dostk/chart '{...}'   # 연속조회
#
# 동작:
#   - 기본 프로필은 mock. real 은 -p real 을 명시해야 열린다
#   - kiwoom_token.sh 캐시에서 토큰 자동 로드
#   - 키움은 HTTP 200 + 본문 return_code 로 오류를 표현하므로 둘 다 검사한다
#   - 인증 오류 시 토큰 1회 강제 재발급 후 재시도
#   - 429 시 지수 백오프로 최대 3회 재시도
#   - 주문 계열 API_ID 는 --confirm-order 없이는 거부한다
#   - 응답 JSON 을 stdout, 진단은 stderr, 연속조회 키는 stderr 에 표시
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PROFILE="mock"
NEXT_KEY=""
CONFIRM_ORDER=0
while [ $# -gt 0 ]; do
  case "$1" in
    -p) PROFILE="${2:?-p 뒤에 mock 또는 real}"; shift 2 ;;
    -k) NEXT_KEY="${2:-}"; shift 2 ;;
    --confirm-order) CONFIRM_ORDER=1; shift ;;
    *) break ;;
  esac
done

API_ID="${1:?API_ID 필요 (예: ka10081)}"
API_PATH="${2:?PATH 필요 (예: /api/dostk/chart)}"
BODY="${3:-{\}}"

# 주문·정정·취소 계열은 사고 시 되돌릴 수 없다. 명시적 확인 없이는 막는다.
# (kt10000 매수 · kt10001 매도 · kt10002 정정 · kt10003 취소)
case "$API_ID" in
  kt1000[0-3])
    if [ "$CONFIRM_ORDER" -ne 1 ]; then
      cat >&2 <<EOF
ERROR: '$API_ID' 는 주문 계열 API 입니다. 그냥 실행되지 않습니다.

  주문은 되돌릴 수 없습니다. 아래를 모두 확인한 뒤에만 --confirm-order 를 붙이세요.
    - 프로필: $PROFILE $([ "$PROFILE" = real ] && echo '  ⚠️ 실계좌입니다')
    - 본문:   $BODY

  확인했다면:  kiwoom_api.sh -p $PROFILE --confirm-order $API_ID $API_PATH '<본문>'
EOF
      exit 2
    fi
    if [ "$PROFILE" = "real" ]; then
      echo "⚠️  실계좌(real) 주문을 실행합니다: $API_ID" >&2
    fi
    ;;
esac

source_base_url() {
  local env_file
  case "$PROFILE" in
    mock) env_file="$HOME/.claude/auth/kiwoom-mock.env" ;;
    real) env_file="$HOME/.claude/auth/kiwoom.env" ;;
    *) echo "ERROR: 프로필은 mock 또는 real" >&2; exit 1 ;;
  esac
  # shellcheck disable=SC1090
  source "$env_file"
  echo "$KIWOOM_API_BASE_URL"
}
BASE_URL="$(source_base_url)"

call() {
  local token="$1"
  local args=(-s --max-time 30 -D /tmp/.kiwoom_hdr.$$ -w '\n%{http_code}'
              -X POST "$BASE_URL$API_PATH"
              -H "authorization: Bearer $token"
              -H "api-id: $API_ID"
              -H 'Content-Type: application/json;charset=UTF-8'
              -d "$BODY")
  [ -n "$NEXT_KEY" ] && args+=(-H "cont-yn: Y" -H "next-key: $NEXT_KEY")
  curl "${args[@]}"
}

TOKEN="$("$SCRIPT_DIR/kiwoom_token.sh" -p "$PROFILE")"
ATTEMPT=0
MAX_ATTEMPTS=3
TOKEN_REFRESHED=0

while :; do
  ATTEMPT=$((ATTEMPT + 1))
  RAW="$(call "$TOKEN")"
  HTTP="${RAW##*$'\n'}"
  RESP="${RAW%$'\n'*}"

  # 429 — 지수 백오프
  if [ "$HTTP" = "429" ] && [ "$ATTEMPT" -lt "$MAX_ATTEMPTS" ]; then
    WAIT=$((2 ** (ATTEMPT - 1)))
    echo "429 수신 — ${WAIT}s 대기 후 재시도 ($ATTEMPT/$MAX_ATTEMPTS)" >&2
    sleep "$WAIT"
    continue
  fi

  # 인증 오류 — 토큰 1회만 강제 재발급
  RC="$(printf '%s' "$RESP" | python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("return_code",""))
except Exception: print("")' 2>/dev/null || true)"
  if { [ "$HTTP" = "401" ] || [ "$RC" = "8001" ] || [ "$RC" = "8002" ]; } && [ "$TOKEN_REFRESHED" -eq 0 ]; then
    echo "인증 오류(HTTP $HTTP / return_code $RC) — 토큰 재발급 후 1회 재시도" >&2
    TOKEN="$("$SCRIPT_DIR/kiwoom_token.sh" -p "$PROFILE" --force)"
    TOKEN_REFRESHED=1
    continue
  fi
  break
done

# 연속조회 키 안내 (있을 때만)
if [ -f "/tmp/.kiwoom_hdr.$$" ]; then
  CONT="$(grep -i '^cont-yn:' "/tmp/.kiwoom_hdr.$$" | tr -d '\r' | awk '{print $2}' || true)"
  NK="$(grep -i '^next-key:' "/tmp/.kiwoom_hdr.$$" | tr -d '\r' | awk '{print $2}' || true)"
  [ "${CONT:-N}" = "Y" ] && [ -n "${NK:-}" ] && echo "연속조회 있음 — 다음 호출에 -k '$NK'" >&2
  rm -f "/tmp/.kiwoom_hdr.$$"
fi

echo "HTTP $HTTP" >&2
printf '%s\n' "$RESP"

# 키움은 HTTP 200 이어도 본문 return_code 가 0 이 아니면 실패다. 둘 다 본다.
if [ "$HTTP" != "200" ]; then
  exit 1
fi
KIWOOM_RESP="$RESP" python3 - <<'PY'
import json, os, sys
try:
    d = json.loads(os.environ["KIWOOM_RESP"])
except Exception:
    sys.exit(0)          # JSON 이 아니면 판정하지 않는다
rc = d.get("return_code")
if rc not in (0, None):
    msg = d.get("return_msg", "")
    print("return_code=%s %s" % (rc, msg), file=sys.stderr)
    sys.exit(1)
PY
