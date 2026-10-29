#!/usr/bin/env python3
"""mail-watch — Gmail 받은편지함을 조건으로 감시해 새 메일이 있을 때만 에이전트를 깨운다.

Hermes cron 의 사전 점검 스크립트(--script)로 쓰면, 새 메일이 없을 때는
마지막 줄에 {"wakeAgent": false} 만 찍어 LLM 을 부르지 않는다(토큰 0).
새 메일이 있으면 {"wakeAgent": true, "context": {...}} 로 메시지 id·첨부 정보를 넘긴다.

읽기 전용이다. 메일을 보내거나 지우거나 라벨을 바꾸지 않는다.
Gmail 접근은 gws CLI 로 하며, Hermes 에서는 google-workspace 스킬의 gws_bridge.py 를 거쳐
Hermes OAuth 토큰을 그대로 쓴다(mail-campaign 과 같은 실행기 선택 규칙).
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

VERSION = "1.0.0"
SEEN_CAP = 3000
ERROR_WAKE_AT = 3


class WatchError(Exception):
    pass


# ── 경로 ───────────────────────────────────────────────────────────────
def hermes_home() -> Path:
    return Path(os.environ.get("HERMES_HOME", "").strip() or Path.home() / ".hermes")


def watch_root() -> Path:
    env = os.environ.get("MAIL_WATCH_HOME", "").strip()
    if env:
        return Path(env)
    if os.environ.get("HERMES_HOME", "").strip() or hermes_home().exists():
        return hermes_home() / "mail-watch"
    base = Path(os.environ.get("XDG_STATE_HOME", "").strip() or Path.home() / ".local" / "state")
    return base / "mail-watch"


def watch_dir(name: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9가-힣_-]{1,40}", name):
        raise WatchError("감시 이름은 영문·숫자·한글·-·_ 40자 이내로 씁니다.")
    return watch_root() / name


def now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


# ── gws 실행기(mail-campaign 과 같은 규칙) ─────────────────────────────
def bridge_python(home: Path) -> str:
    """gws_bridge.py 는 datetime.UTC 를 써서 Python 3.11 이상이 필요하다."""
    if sys.version_info >= (3, 11):
        return sys.executable
    cands = []
    for root in dict.fromkeys([home, Path.home() / ".hermes"]):
        cands += sorted(root.glob("installs/*/environments/*/venv/bin/python"), key=lambda p: p.stat().st_mtime,
                        reverse=True)
    cands += [Path(p) for n in ("python3.14", "python3.13", "python3.12", "python3.11") if (p := shutil.which(n))]
    for c in cands:
        try:
            if subprocess.run([str(c), "-c", "import sys; sys.exit(sys.version_info < (3, 11))"],
                              capture_output=True, timeout=10).returncode == 0:
                return str(c)
        except (OSError, subprocess.TimeoutExpired):
            continue
    raise WatchError("gws_bridge.py 를 실행할 Python 3.11 이상을 찾지 못했습니다. MAIL_WATCH_GWS 로 지정하세요.")


def find_gws_dir(home: Path):
    """gws 실행 파일이 있는 폴더. PATH 에 없어도 Hermes 프로필 bin 등 흔한 설치 위치를 본다.
    gws_bridge.py 는 PATH 에서만 gws 를 찾으므로, 찾은 폴더를 브리지 실행 PATH 앞에 넣는다."""
    found = shutil.which("gws")
    if found:
        return str(Path(found).parent)
    for d in (home / "bin", Path.home() / ".hermes" / "bin", Path.home() / ".local" / "bin",
              Path.home() / ".npm-global" / "bin", Path("/opt/homebrew/bin"), Path("/usr/local/bin")):
        if (d / "gws").is_file() and os.access(d / "gws", os.X_OK):
            return str(d)
    return None


def resolve_gws() -> list[str]:
    env = (os.environ.get("MAIL_WATCH_GWS") or os.environ.get("MAIL_CAMPAIGN_GWS") or "").strip()
    if env:
        return shlex.split(env)
    home = hermes_home()
    if (home / "google_token.json").exists():
        for root in (home, Path.home() / ".hermes", Path.home() / ".hermes" / "hermes-agent"):
            bridge = root / "skills" / "productivity" / "google-workspace" / "scripts" / "gws_bridge.py"
            if bridge.exists():
                gdir = find_gws_dir(home)
                if gdir is None:
                    raise WatchError("gws CLI 를 찾지 못했습니다(PATH·Hermes 프로필 bin). `npm i -g @googleworkspace/cli` 로 설치하세요.")
                path = gdir + os.pathsep + os.environ.get("PATH", "")
                return ["/usr/bin/env", "PATH=" + path, bridge_python(home), str(bridge)]
    gdir = find_gws_dir(Path(os.environ.get("HERMES_HOME", "").strip() or Path.home() / ".hermes"))
    if gdir:
        return [str(Path(gdir) / "gws")]
    raise WatchError("gws CLI 를 찾지 못했습니다. `npm i -g @googleworkspace/cli` 로 설치하세요.")


def gws(args: list[str], timeout=60):
    cmd = resolve_gws()
    try:
        p = subprocess.run(cmd + args, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise WatchError("gws 시간 초과")
    out = p.stdout.strip()
    data = None
    if out:
        i = out.find("{")
        try:
            data = json.loads(out[i:] if i >= 0 else out)
        except json.JSONDecodeError:
            data = None
    if p.returncode != 0 or (isinstance(data, dict) and "error" in data):
        raise WatchError((p.stderr or "").strip()[-300:] or json.dumps((data or {}).get("error"), ensure_ascii=False))
    return data or {}


# ── 설정·상태 ─────────────────────────────────────────────────────────
def load_json(path: Path, default):
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return default


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def load_watch(name: str):
    d = watch_dir(name)
    cfg = load_json(d / "watch.json", None)
    if cfg is None:
        raise WatchError(f"감시 '{name}' 이 없습니다. 먼저 init 하세요.")
    state = load_json(d / "state.json", {"seen": [], "pending": {}, "errors": 0})
    return d, cfg, state


def full_query(cfg) -> str:
    q = cfg["query"]
    exts = cfg.get("attach_ext") or []
    if exts:
        q += " (" + " OR ".join(f"filename:{e}" for e in exts) + ")"
    if cfg.get("window") and "newer_than:" not in q:
        q += f" newer_than:{cfg['window']}"
    return q


# ── Gmail 조회 ────────────────────────────────────────────────────────
def list_ids(cfg) -> list[dict]:
    data = gws(["gmail", "users", "messages", "list", "--params",
                json.dumps({"userId": "me", "q": full_query(cfg), "maxResults": cfg.get("max", 20)})])
    return data.get("messages", [])


def walk_parts(part, out):
    fn = part.get("filename")
    if fn:
        body = part.get("body", {})
        out.append({"filename": fn, "mimeType": part.get("mimeType", ""),
                    "attachmentId": body.get("attachmentId", ""), "size": body.get("size", 0)})
    for p in part.get("parts", []) or []:
        walk_parts(p, out)


def message_info(mid: str) -> dict:
    m = gws(["gmail", "users", "messages", "get", "--params", json.dumps({"userId": "me", "id": mid, "format": "full"})])
    headers = {h["name"].lower(): h["value"] for h in m.get("payload", {}).get("headers", [])}
    atts: list = []
    walk_parts(m.get("payload", {}), atts)
    return {"id": mid, "threadId": m.get("threadId", ""), "from": headers.get("from", ""),
            "subject": headers.get("subject", ""), "date": headers.get("date", ""),
            "snippet": m.get("snippet", ""), "labels": m.get("labelIds", []), "attachments": atts}


def ext_ok(cfg, info) -> bool:
    exts = [e.lower().lstrip(".") for e in cfg.get("attach_ext") or []]
    if not exts:
        return True
    return any(a["filename"].lower().rsplit(".", 1)[-1] in exts for a in info["attachments"])


# ── 명령 ───────────────────────────────────────────────────────────────
def cmd_init(a):
    d = watch_dir(a.name)
    if (d / "watch.json").exists() and not a.force:
        raise WatchError(f"이미 있습니다: {d} (--force 로 설정만 덮어씀, 본 메일 기록은 유지)")
    cfg = {"name": a.name, "query": a.query, "attach_ext": [e.strip().lstrip(".") for e in (a.attach_ext or "").split(",")
                                                             if e.strip()],
           "window": a.window, "max": a.max, "max_wakes": a.max_wakes, "created": now()}
    save_json(d / "watch.json", cfg)
    state = load_json(d / "state.json", {"seen": [], "pending": {}, "errors": 0})
    if not a.include_existing:
        ids = [m["id"] for m in list_ids(cfg)]
        state["seen"] = list(dict.fromkeys(state["seen"] + ids))[-SEEN_CAP:]
        print(f"지금 조건에 맞는 기존 메일 {len(ids)}통은 본 것으로 표시했습니다(--include-existing 이면 처리 대상).")
    save_json(d / "state.json", state)
    print(f"감시 '{a.name}' 을 만들었습니다: {d}")
    print("검색식:", full_query(cfg))
    return 0


def cmd_check(a):
    """cron 사전 점검. 마지막 줄은 항상 {"wakeAgent": ...} JSON 이다."""
    try:
        d, cfg, state = load_watch(a.name)
    except WatchError as e:
        print(f"mail-watch: {e}")
        print(json.dumps({"wakeAgent": False}))
        return 0
    try:
        found = list_ids(cfg)
    except WatchError as e:
        state["errors"] = state.get("errors", 0) + 1
        save_json(d / "state.json", state)
        print(f"mail-watch {a.name}: Gmail 조회 실패({state['errors']}회 연속): {e}")
        if state["errors"] == ERROR_WAKE_AT:
            print(json.dumps({"wakeAgent": True, "context": {"watch": a.name, "error": str(e)[:300],
                                                             "consecutive_errors": state["errors"]}},
                             ensure_ascii=False))
        else:
            print(json.dumps({"wakeAgent": False}))
        return 0
    state["errors"] = 0
    seen = set(state["seen"])
    pending = state.get("pending", {})
    max_wakes = cfg.get("max_wakes", 2)
    batch, gave_up = [], []
    for m in found:
        mid = m["id"]
        if mid in seen:
            continue
        p = pending.get(mid)
        if p and p["wakes"] >= max_wakes:
            gave_up.append(mid)
            seen.add(mid)
            state["seen"].append(mid)
            pending.pop(mid, None)
            continue
        try:
            info = message_info(mid)
        except WatchError as e:
            print(f"mail-watch {a.name}: 메시지 {mid} 읽기 실패: {e}")
            continue
        if not ext_ok(cfg, info):
            seen.add(mid)
            state["seen"].append(mid)
            continue
        pending[mid] = {"wakes": (p or {}).get("wakes", 0) + 1, "first": (p or {}).get("first", now())}
        info.pop("labels", None)
        info["wake"] = pending[mid]["wakes"]
        batch.append(info)
    state["pending"] = pending
    state["seen"] = state["seen"][-SEEN_CAP:]
    state["last_check"] = now()
    save_json(d / "state.json", state)
    if gave_up:
        print(f"mail-watch {a.name}: {max_wakes}번 깨워도 처리 표시(ack)가 없어 넘긴 메일 {len(gave_up)}통: {', '.join(gave_up)}")
    if not batch:
        print(json.dumps({"wakeAgent": False}))
        return 0
    for b in batch:
        names = ", ".join(x["filename"] for x in b["attachments"]) or "첨부 없음"
        print(f"새 메일 {b['id']} · {b['from']} · {b['subject']} · 첨부: {names}")
    ctx = {"watch": a.name, "count": len(batch), "messages": batch,
           "ack": f"처리한 뒤 mail_watch.py ack {a.name} <id> … 를 실행하세요."}
    print(json.dumps({"wakeAgent": True, "context": ctx}, ensure_ascii=False))
    return 0


def cmd_ack(a):
    d, cfg, state = load_watch(a.name)
    pend = state.get("pending", {})
    done = 0
    for mid in a.ids:
        if mid in pend or mid not in state["seen"]:
            pend.pop(mid, None)
            state["seen"].append(mid)
            done += 1
    state["seen"] = list(dict.fromkeys(state["seen"]))[-SEEN_CAP:]
    save_json(d / "state.json", state)
    print(f"처리 완료 표시 {done}통")
    return 0


def cmd_status(a):
    d, cfg, state = load_watch(a.name)
    print(f"감시: {a.name}  ({d})")
    print("검색식:", full_query(cfg))
    print(f"본 메일 {len(state['seen'])}통 · 처리 대기 {len(state.get('pending', {}))}통 · "
          f"연속 오류 {state.get('errors', 0)} · 마지막 점검 {state.get('last_check', '-')}")
    for mid, p in state.get("pending", {}).items():
        print(f"  대기 {mid}  깨운 횟수 {p['wakes']}  처음 {p['first']}")
    return 0


def cmd_fetch(a):
    """첨부를 내려받는다. 기본 위치: <감시 폴더>/inbox/<메시지 id>/"""
    d, cfg, state = load_watch(a.name)
    info = message_info(a.id)
    out = Path(a.out).expanduser() if a.out else d / "inbox" / a.id
    out.mkdir(parents=True, exist_ok=True)
    saved = []
    for att in info["attachments"]:
        if not att["attachmentId"]:
            continue
        safe = re.sub(r"[/\\\x00]", "_", att["filename"]).lstrip(".") or "attachment"
        data = gws(["gmail", "users", "messages", "attachments", "get", "--params",
                    json.dumps({"userId": "me", "messageId": a.id, "id": att["attachmentId"]})], timeout=180)
        raw = data.get("data", "")
        blob = base64.urlsafe_b64decode(raw + "=" * (-len(raw) % 4))
        (out / safe).write_bytes(blob)
        saved.append(str(out / safe))
    meta = {k: info[k] for k in ("id", "threadId", "from", "subject", "date", "snippet")}
    (out / "message.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"dir": str(out), "files": saved, **meta}, ensure_ascii=False, indent=2))
    return 0


WRAPPER = '''#!/usr/bin/env python3
# mail-watch 사전 점검 래퍼 — `mail_watch.py install` 이 만들었다. 감시: {name}
import os, runpy, sys
os.environ.setdefault("HERMES_HOME", {home!r})
sys.argv = ["mail_watch.py", "check", {name!r}]
runpy.run_path({script!r}, run_name="__main__")
'''


def cmd_install(a):
    watch_dir(a.name)
    load_watch(a.name)
    scripts = hermes_home() / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    target = scripts / f"mail-watch-{a.name}.py"
    target.write_text(WRAPPER.format(name=a.name, script=str(Path(__file__).resolve()), home=str(hermes_home())),
                      encoding="utf-8")
    target.chmod(0o755)
    print(f"사전 점검 스크립트: {target}  (Hermes 홈: {hermes_home()})")
    skill = " ".join(f"--skill {shlex.quote(s)}" for s in (a.skill or []))
    prompt = a.prompt or (f"mail-watch 가 새 메일을 넘겼다. context.messages 의 각 메일을 처리하고, "
                          f"끝난 메일은 mail_watch.py ack {a.name} <id> 로 처리 완료 표시를 해. 메일은 보내지 마.")
    print("예약 명령(사용자 확인 뒤 실행):")
    prof = os.environ.get("HERMES_HOME", "")
    prof_flag = f"-p {Path(prof).name}" if Path(prof).parent.name == "profiles" else ""
    parts = ["hermes", prof_flag, "cron create", shlex.quote("every " + a.every), shlex.quote(prompt),
             f"--name mail-watch-{a.name}", f"--script {shlex.quote(target.name)}", skill, f"--deliver {a.deliver}"]
    print("  " + " ".join(x for x in parts if x))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="mail_watch.py", description="Gmail 조건 감시(읽기 전용)")
    p.add_argument("--version", action="version", version=VERSION)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="감시 만들기")
    s.add_argument("name")
    s.add_argument("--query", required=True, help="Gmail 검색식(예: 'in:inbox -from:me')")
    s.add_argument("--attach-ext", help="이 확장자 첨부가 있는 메일만(쉼표). 예: hwp,hwpx,pdf")
    s.add_argument("--window", default="7d", help="검색 기간(newer_than). 기본 7d")
    s.add_argument("--max", type=int, default=20, help="한 번에 볼 최대 메일 수")
    s.add_argument("--max-wakes", type=int, default=2, help="처리 표시(ack)가 없을 때 다시 깨우는 최대 횟수")
    s.add_argument("--include-existing", action="store_true", help="지금 있는 메일도 처리 대상으로")
    s.add_argument("--force", action="store_true")
    s.set_defaults(fn=cmd_init)

    s = sub.add_parser("check", help="cron 사전 점검(마지막 줄 wakeAgent JSON)")
    s.add_argument("name")
    s.set_defaults(fn=cmd_check)

    s = sub.add_parser("ack", help="처리 완료 표시")
    s.add_argument("name")
    s.add_argument("ids", nargs="+")
    s.set_defaults(fn=cmd_ack)

    s = sub.add_parser("status", help="상태 보기")
    s.add_argument("name")
    s.set_defaults(fn=cmd_status)

    s = sub.add_parser("fetch", help="메일 첨부 내려받기")
    s.add_argument("name")
    s.add_argument("id")
    s.add_argument("--out")
    s.set_defaults(fn=cmd_fetch)

    s = sub.add_parser("install", help="Hermes 사전 점검 스크립트 설치 + 예약 명령 출력")
    s.add_argument("name")
    s.add_argument("--every", default="5m")
    s.add_argument("--skill", action="append", help="예약에 붙일 스킬(반복 가능)")
    s.add_argument("--prompt")
    s.add_argument("--deliver", default="origin")
    s.set_defaults(fn=cmd_install)

    a = p.parse_args(argv)
    try:
        return a.fn(a) or 0
    except WatchError as e:
        print(f"✖ {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
