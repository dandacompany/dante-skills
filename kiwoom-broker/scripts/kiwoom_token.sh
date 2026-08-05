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

# ── 자격증명 로딩 ────────────────────────────────────────────────
# 우선순위:
#   1. 이미 환경에 있으면 그대로 쓴다
#      (Hermes 프로필 .env / SecretSource(Bitwarden·1Password) 가 주입한 경우)
#   2. KIWOOM_AUTH_ENV 로 지정한 파일
#   3. 프로필 .env  ($HERMES_HOME/.env)
#   4. ~/.claude/auth/*.env  (로컬 개발 편의. 녹화·수강생 환경에서는 쓰지 않는다)
AUTH_SOURCE=""
if [ -n "${KIWOOM_REST_API_KEY:-}" ] && [ -n "${KIWOOM_REST_API_SECRET:-}" ]; then
  AUTH_SOURCE="env"
else
  for candidate in \
    "${KIWOOM_AUTH_ENV:-}" \
    "${HERMES_HOME:+$HERMES_HOME/.env}" \
    "$HOME/.claude/auth/$([ "$PROFILE" = real ] && echo kiwoom || echo kiwoom-mock).env"
  do
    [ -n "$candidate" ] && [ -f "$candidate" ] || continue
    # set -a: 이 구간에서 정의되는 변수를 자동 export 한다.
    # export 하지 않으면 아래 python3 서브프로세스가 값을 못 본다.
    set -a
    # shellcheck disable=SC1090
    source "$candidate"
    set +a
    AUTH_SOURCE="$candidate"
    break
  done
fi

if [ -z "$AUTH_SOURCE" ]; then
  cat >&2 <<EOF
ERROR: 키움 자격증명을 찾지 못했습니다.

  아래 중 하나로 주세요.
    1) Hermes 프로필 .env 에 넣기 (권장)
       ~/.hermes/profiles/<프로필>/.env
         KIWOOM_REST_API_KEY=...
         KIWOOM_REST_API_SECRET=...
         KIWOOM_API_BASE_URL=https://mockapi.kiwoom.com
    2) Bitwarden·1Password 등 SecretSource 로 주입 (Hermes v0.19.0+)
    3) KIWOOM_AUTH_ENV=/경로/.env 로 파일 지정
EOF
  exit 1
fi

: "${KIWOOM_REST_API_KEY:?KIWOOM_REST_API_KEY 미설정}"
: "${KIWOOM_REST_API_SECRET:?KIWOOM_REST_API_SECRET 미설정}"
# 서버 주소가 없으면 프로필 기본값. 모의가 기본이다.
if [ -z "${KIWOOM_API_BASE_URL:-}" ]; then
  case "$PROFILE" in
    real) KIWOOM_API_BASE_URL="https://api.kiwoom.com" ;;
    *)    KIWOOM_API_BASE_URL="https://mockapi.kiwoom.com" ;;
  esac
fi
export KIWOOM_REST_API_KEY KIWOOM_REST_API_SECRET KIWOOM_API_BASE_URL

# 캐시는 자격증명 출처별로 분리한다(같은 키를 쓰는 곳끼리만 토큰을 공유)
CACHE_TAG="$(printf '%s|%s' "$AUTH_SOURCE" "$KIWOOM_API_BASE_URL" | shasum | cut -c1-8)"
CACHE="${KIWOOM_TOKEN_CACHE:-${TMPDIR:-/tmp}/.kiwoom_${PROFILE}_${CACHE_TAG}_token.json}"
EXPIRY_MARGIN=600   # 만료 10분 전부터 재발급

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
