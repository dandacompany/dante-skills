#!/usr/bin/env python3
"""키움증권 REST API 호출 래퍼.

모의투자(mock)가 기본이고 실전(real)은 명시해야만 열린다.
주문 계열은 --confirm-order 없이는 거부한다.

사용법
    python3 kiwoom.py call <API_ID> <PATH> [JSON_BODY] [-p mock|real] [-k NEXT_KEY]
    python3 kiwoom.py call kt10000 /api/dostk/ordr '{...}' --confirm-order
    python3 kiwoom.py token --status
    python3 kiwoom.py token --force

자격증명 (위에서 하나 잡히면 아래는 보지 않는다)
    1. 이미 환경에 있으면 그대로   ← Hermes 프로필 .env / SecretSource(Bitwarden·1Password)
    2. KIWOOM_AUTH_ENV=/경로/.env
    3. $HERMES_HOME/.env
    4. ~/.claude/auth/kiwoom-mock.env   (로컬 개발 폴백)

표준 라이브러리만 쓴다.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

MOCK_URL = "https://mockapi.kiwoom.com"
REAL_URL = "https://api.kiwoom.com"
EXPIRY_MARGIN = 600          # 만료 10분 전부터 재발급
ORDER_API_IDS = {"kt10000", "kt10001", "kt10002", "kt10003"}
AUTH_FAIL_CODES = {"8001", "8002", 8001, 8002}


def _err(msg: str) -> None:
    print(msg, file=sys.stderr)


def _parse_env_file(path: Path) -> dict:
    """KEY=VALUE 형식의 .env 를 읽는다. export 접두와 따옴표를 벗긴다."""
    out = {}
    try:
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            if line.startswith("export "):
                line = line[len("export "):]
            key, _, value = line.partition("=")
            value = value.strip().strip('"').strip("'")
            out[key.strip()] = value
    except OSError:
        pass
    return out


def load_credentials(profile: str) -> tuple[dict, str]:
    """자격증명과 그 출처를 돌려준다."""
    key = os.environ.get("KIWOOM_REST_API_KEY")
    secret = os.environ.get("KIWOOM_REST_API_SECRET")
    if key and secret:
        creds = {
            "KIWOOM_REST_API_KEY": key,
            "KIWOOM_REST_API_SECRET": secret,
            "KIWOOM_API_BASE_URL": os.environ.get("KIWOOM_API_BASE_URL", ""),
        }
        return creds, "env"

    fallback = "kiwoom.env" if profile == "real" else "kiwoom-mock.env"
    hermes_home = os.environ.get("HERMES_HOME")
    candidates = [
        os.environ.get("KIWOOM_AUTH_ENV"),
        f"{hermes_home}/.env" if hermes_home else None,
        str(Path.home() / ".claude" / "auth" / fallback),
    ]
    for candidate in candidates:
        if not candidate:
            continue
        path = Path(candidate).expanduser()
        if not path.is_file():
            continue
        parsed = _parse_env_file(path)
        if parsed.get("KIWOOM_REST_API_KEY") and parsed.get("KIWOOM_REST_API_SECRET"):
            return parsed, str(path)

    _err(
        "ERROR: 키움 자격증명을 찾지 못했습니다.\n\n"
        "  아래 중 하나로 주세요.\n"
        "    1) Hermes 프로필 .env 에 넣기 (권장)\n"
        "       ~/.hermes/profiles/<프로필>/.env\n"
        "         KIWOOM_REST_API_KEY=...\n"
        "         KIWOOM_REST_API_SECRET=...\n"
        "         KIWOOM_API_BASE_URL=https://mockapi.kiwoom.com\n"
        "    2) Bitwarden·1Password 등 SecretSource 로 주입 (Hermes v0.19.0+)\n"
        "    3) KIWOOM_AUTH_ENV=/경로/.env 로 파일 지정"
    )
    sys.exit(1)


def resolve_base_url(creds: dict, profile: str) -> str:
    url = creds.get("KIWOOM_API_BASE_URL") or ""
    if not url:
        return REAL_URL if profile == "real" else MOCK_URL
    # 프로필과 서버가 어긋나면 멈춘다. 실전 키로 모의를 부르거나 그 반대인 사고를 막는다.
    is_mock_url = "mockapi.kiwoom.com" in url
    if profile == "mock" and not is_mock_url:
        _err(f"ERROR: 프로필(mock)과 서버({url})가 어긋납니다. 자격증명을 확인하세요.")
        sys.exit(1)
    if profile == "real" and is_mock_url:
        _err(f"ERROR: 프로필(real)과 서버({url})가 어긋납니다. 자격증명을 확인하세요.")
        sys.exit(1)
    return url.rstrip("/")


def cache_path(profile: str, source: str, base_url: str) -> Path:
    override = os.environ.get("KIWOOM_TOKEN_CACHE")
    if override:
        return Path(override).expanduser()
    tag = hashlib.sha256(f"{source}|{base_url}".encode()).hexdigest()[:8]
    tmp = Path(os.environ.get("TMPDIR", "/tmp"))
    return tmp / f".kiwoom_{profile}_{tag}_token.json"


def read_cache(path: Path) -> dict | None:
    try:
        cached = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if cached.get("token") and time.time() < cached.get("expires_at", 0) - EXPIRY_MARGIN:
        return cached
    return None


def post_json(url: str, payload: dict, headers: dict, timeout: int = 30):
    """POST 후 (status, body_text, response_headers) 를 돌려준다."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json;charset=UTF-8")
    for name, value in headers.items():
        req.add_header(name, value)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8"), dict(resp.headers)
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace"), dict(exc.headers or {})
    except urllib.error.URLError as exc:
        _err(f"ERROR: 연결 실패 — {exc.reason}")
        sys.exit(1)


def issue_token(creds: dict, base_url: str, path: Path) -> str:
    status, body, _ = post_json(
        f"{base_url}/oauth2/token",
        {
            "grant_type": "client_credentials",
            "appkey": creds["KIWOOM_REST_API_KEY"],
            "secretkey": creds["KIWOOM_REST_API_SECRET"],
        },
        {},
        timeout=15,
    )
    try:
        resp = json.loads(body)
    except ValueError:
        _err(f"ERROR: 토큰 응답을 해석하지 못했습니다 (HTTP {status})")
        sys.exit(1)

    if resp.get("return_code") != 0 or not resp.get("token"):
        _err(
            "ERROR: 토큰 발급 실패 — "
            f"return_code={resp.get('return_code')} {resp.get('return_msg', '')}"
        )
        sys.exit(1)

    # expires_dt 는 'YYYYMMDDHHMMSS' 문자열이다
    try:
        expires_at = datetime.strptime(resp["expires_dt"], "%Y%m%d%H%M%S").timestamp()
    except (KeyError, ValueError):
        expires_at = time.time() + 3600      # 파싱 실패 시 보수적으로 1시간

    try:
        path.write_text(json.dumps({"token": resp["token"], "expires_at": expires_at}))
        path.chmod(0o600)
    except OSError as exc:
        _err(f"경고: 토큰 캐시를 저장하지 못했습니다 ({exc}). 매번 재발급됩니다.")
    return resp["token"]


def get_token(profile: str, force: bool = False) -> tuple[str, str]:
    creds, source = load_credentials(profile)
    base_url = resolve_base_url(creds, profile)
    path = cache_path(profile, source, base_url)
    if not force:
        cached = read_cache(path)
        if cached:
            return cached["token"], base_url
    return issue_token(creds, base_url, path), base_url


def cmd_token(args) -> int:
    if args.status:
        creds, source = load_credentials(args.profile)
        base_url = resolve_base_url(creds, args.profile)
        cached = read_cache(cache_path(args.profile, source, base_url))
        if cached:
            remain = int(cached["expires_at"] - time.time())
            when = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(cached["expires_at"]))
            print(f"[{args.profile}] VALID (남은 시간: {remain}s, 만료: {when})")
        else:
            print(f"[{args.profile}] EXPIRED_OR_MISSING")
        return 0
    token, _ = get_token(args.profile, force=args.force)
    print(token)
    return 0


def cmd_call(args) -> int:
    if args.api_id in ORDER_API_IDS and not args.confirm_order:
        warn = "  ⚠️ 실계좌입니다" if args.profile == "real" else ""
        _err(
            f"ERROR: '{args.api_id}' 는 주문 계열 API 입니다. 그냥 실행되지 않습니다.\n\n"
            "  주문은 되돌릴 수 없습니다. 아래를 모두 확인한 뒤에만 --confirm-order 를 붙이세요.\n"
            f"    - 프로필: {args.profile}{warn}\n"
            f"    - 본문:   {args.body}\n\n"
            f"  확인했다면:  kiwoom.py call {args.api_id} {args.path} '<본문>' "
            f"-p {args.profile} --confirm-order"
        )
        return 2
    if args.api_id in ORDER_API_IDS and args.profile == "real":
        _err(f"⚠️  실계좌(real) 주문을 실행합니다: {args.api_id}")

    try:
        body = json.loads(args.body)
    except ValueError:
        _err(f"ERROR: 본문이 올바른 JSON 이 아닙니다: {args.body}")
        return 1

    token, base_url = get_token(args.profile)
    url = f"{base_url}{args.path}"
    refreshed = False
    attempt = 0

    while True:
        attempt += 1
        headers = {"authorization": f"Bearer {token}", "api-id": args.api_id}
        if args.next_key:
            headers["cont-yn"] = "Y"
            headers["next-key"] = args.next_key
        status, text, resp_headers = post_json(url, body, headers)

        if status == 429 and attempt < 3:
            wait = 2 ** (attempt - 1)
            _err(f"429 수신 — {wait}s 대기 후 재시도 ({attempt}/3)")
            time.sleep(wait)
            continue

        return_code = None
        try:
            return_code = json.loads(text).get("return_code")
        except ValueError:
            pass

        if (status == 401 or return_code in AUTH_FAIL_CODES) and not refreshed:
            _err(f"인증 오류(HTTP {status} / return_code {return_code}) — 토큰 재발급 후 1회 재시도")
            token, base_url = get_token(args.profile, force=True)
            refreshed = True
            continue
        break

    cont = (resp_headers.get("cont-yn") or resp_headers.get("Cont-Yn") or "N").strip()
    next_key = (resp_headers.get("next-key") or resp_headers.get("Next-Key") or "").strip()
    if cont == "Y" and next_key:
        _err(f"연속조회 있음 — 다음 호출에 -k '{next_key}'")

    _err(f"HTTP {status}")
    print(text)

    if status != 200:
        return 1
    # 키움은 HTTP 200 이어도 본문 return_code 가 0 이 아니면 실패다. 둘 다 본다.
    if return_code not in (0, None):
        try:
            message = json.loads(text).get("return_msg", "")
        except ValueError:
            message = ""
        _err(f"return_code={return_code} {message}")
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="키움증권 REST API 래퍼")
    sub = parser.add_subparsers(dest="command", required=True)

    p_token = sub.add_parser("token", help="접근토큰 발급·상태 확인")
    p_token.add_argument("-p", "--profile", default="mock", choices=["mock", "real"])
    p_token.add_argument("--status", action="store_true", help="캐시 상태만 (토큰 미노출)")
    p_token.add_argument("--force", action="store_true", help="강제 재발급")
    p_token.set_defaults(func=cmd_token)

    p_call = sub.add_parser("call", help="API 호출")
    p_call.add_argument("api_id", help="TR 식별자 (예: ka10081)")
    p_call.add_argument("path", help="경로 (예: /api/dostk/chart)")
    p_call.add_argument("body", nargs="?", default="{}", help="JSON 본문")
    p_call.add_argument("-p", "--profile", default="mock", choices=["mock", "real"])
    p_call.add_argument("-k", "--next-key", default="", help="연속조회 키")
    p_call.add_argument("--confirm-order", action="store_true",
                        help="주문 계열 API 를 실행할 때 필요")
    p_call.set_defaults(func=cmd_call)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
