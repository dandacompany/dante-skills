#!/usr/bin/env bash
# 키움증권 REST API 접근토큰 발급 + 프로필별 캐싱
#
# 사용법:
#   kiwoom_token.sh                 # 모의(mock) 토큰 — 캐시 우선
#   kiwoom_token.sh -p real         # 실전 토큰 (주의: 실계좌)
#   kiwoom_token.sh --status        # 캐시 상태만 (토큰 미노출)
#   kiwoom_token.sh --force         # 강제 재발급
#
# 기본 프로필은 항상 mock 이다. real 은 -p real 을 명시해야만 열린다.
# 토큰 발급 자체에도 호출 제한이 있으므로 캐시를 통해 재사용한다.
set -euo pipefail

PROFILE="mock"
MODE=""
while [ $# -gt 0 ]; do
  case "$1" in
    -p) PROFILE="${2:?-p 뒤에 mock 또는 real}"; shift 2 ;;
    --status|--force) MODE="$1"; shift ;;
    *) echo "ERROR: 알 수 없는 인자 '$1'" >&2; exit 1 ;;
  esac
done

# 자격증명 파일 위치. KIWOOM_AUTH_ENV 로 덮어쓸 수 있다 —
# 에이전트 프로필마다 다른 파일을 가리키게 해서 "키를 가진 프로필"을 하나로 좁히는 용도.
if [ -n "${KIWOOM_AUTH_ENV:-}" ]; then
  AUTH_ENV="$KIWOOM_AUTH_ENV"
else
  case "$PROFILE" in
    mock) AUTH_ENV="$HOME/.claude/auth/kiwoom-mock.env" ;;
    real) AUTH_ENV="$HOME/.claude/auth/kiwoom.env" ;;
    *) echo "ERROR: 프로필은 mock 또는 real 이어야 한다 (받은 값: $PROFILE)" >&2; exit 1 ;;
  esac
fi

# 캐시는 자격증명 파일 경로별로 분리한다(같은 파일을 쓰는 곳끼리만 토큰을 공유)
CACHE_TAG="$(printf '%s' "$AUTH_ENV" | shasum | cut -c1-8)"
CACHE="${KIWOOM_TOKEN_CACHE:-$HOME/.claude/auth/.kiwoom_${PROFILE}_${CACHE_TAG}_token_cache.json}"
EXPIRY_MARGIN=600   # 만료 10분 전부터 재발급

[ -f "$AUTH_ENV" ] || { echo "ERROR: $AUTH_ENV 없음" >&2; exit 1; }
# shellcheck disable=SC1090
source "$AUTH_ENV"
: "${KIWOOM_REST_API_KEY:?KIWOOM_REST_API_KEY 미설정}"
: "${KIWOOM_REST_API_SECRET:?KIWOOM_REST_API_SECRET 미설정}"
: "${KIWOOM_API_BASE_URL:?KIWOOM_API_BASE_URL 미설정}"

# 안전장치: real 프로필인데 base_url 이 모의 서버이거나 그 반대인 경우 중단
case "$PROFILE:$KIWOOM_API_BASE_URL" in
  mock:*mockapi.kiwoom.com*) : ;;
  real:*//api.kiwoom.com*)   : ;;
  *) echo "ERROR: 프로필($PROFILE)과 서버($KIWOOM_API_BASE_URL)가 어긋난다. env 파일을 확인할 것" >&2; exit 1 ;;
esac

cache_valid() {
  [ -f "$CACHE" ] || return 1
  python3 - "$CACHE" "$EXPIRY_MARGIN" <<'PY'
import json, sys, time
try:
    c = json.load(open(sys.argv[1]))
    ok = c.get("token") and time.time() < c["expires_at"] - int(sys.argv[2])
    sys.exit(0 if ok else 1)
except Exception:
    sys.exit(1)
PY
}

if [ "$MODE" = "--status" ]; then
  if cache_valid; then
    python3 - "$CACHE" "$PROFILE" <<'PY'
import json, sys, time
c = json.load(open(sys.argv[1]))
remain = int(c["expires_at"] - time.time())
exp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(c['expires_at']))
print(f"[{sys.argv[2]}] VALID (남은 시간: {remain}s, 만료: {exp})")
PY
  else
    echo "[$PROFILE] EXPIRED_OR_MISSING"
  fi
  exit 0
fi

if [ "$MODE" != "--force" ] && cache_valid; then
  python3 -c "import json;print(json.load(open('$CACHE'))['token'])"
  exit 0
fi

RESP=$(curl -s --max-time 15 -X POST "$KIWOOM_API_BASE_URL/oauth2/token" \
  -H 'Content-Type: application/json;charset=UTF-8' \
  -d "$(python3 -c '
import json, os
print(json.dumps({
    "grant_type": "client_credentials",
    "appkey": os.environ["KIWOOM_REST_API_KEY"],
    "secretkey": os.environ["KIWOOM_REST_API_SECRET"],
}))')")

KIWOOM_TOKEN_RESP="$RESP" python3 - "$CACHE" <<'PY'
import json, os, sys, time
from datetime import datetime

resp = json.loads(os.environ["KIWOOM_TOKEN_RESP"])
if resp.get("return_code") != 0 or not resp.get("token"):
    msg = resp.get("return_msg", "(메시지 없음)")
    print(f"ERROR: 토큰 발급 실패 - return_code={resp.get('return_code')} {msg}", file=sys.stderr)
    sys.exit(1)

# expires_dt 는 'YYYYMMDDHHMMSS' 형식의 로컬시각 문자열
try:
    exp = datetime.strptime(resp["expires_dt"], "%Y%m%d%H%M%S").timestamp()
except Exception:
    exp = time.time() + 3600  # 파싱 실패 시 보수적으로 1시간

path = sys.argv[1]
with open(path, "w") as f:
    json.dump({"token": resp["token"], "expires_at": exp}, f)
os.chmod(path, 0o600)
print(resp["token"])
PY
