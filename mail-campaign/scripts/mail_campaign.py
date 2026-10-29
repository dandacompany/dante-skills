#!/usr/bin/env python3
"""mail-campaign — 시트 명단으로 개인화 메일을 안전하게 보내는 결정론적 도우미.

판단(문구 작성, 답장 분류, 광고성 최종 판정)은 에이전트가 하고,
이 스크립트는 기계적인 일만 한다: 시트 읽기·열 매핑·행 검증·렌더·초안·테스트 발송·
승인 토큰·간격 발송·상태 기록·답장 수거. 표준 라이브러리만 쓴다.

발송·읽기는 전부 gws CLI 로 한다. Hermes 에서는 google-workspace 스킬의
gws_bridge.py 를 거쳐 Hermes OAuth 토큰을 그대로 쓴다(별도 키 없음).
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import random
import re
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

try:
    import fcntl
except ImportError:  # Windows
    fcntl = None

VERSION = "1.0.2"

# ── 상태 열 ────────────────────────────────────────────────────────────
COL_STATUS = "발송 상태"
COL_REASON = "보류 사유"
COL_DRAFT = "draftId"
COL_MSG = "messageId"
COL_THREAD = "threadId"
COL_SENT_AT = "발송 시각"
COL_REPLY = "답장 분류"
STATUS_COLUMNS = [COL_STATUS, COL_REASON, COL_DRAFT, COL_MSG, COL_THREAD, COL_SENT_AT, COL_REPLY]

ST_WAIT = ""
ST_HOLD = "보류"
ST_DRAFT = "초안"
ST_SENT = "보냄"
ST_ERR = "오류"
ST_CHECK = "확인 필요"
ST_SKIP = "제외"

DEFAULT_COLUMNS = {
    "email": ["이메일", "email", "e-mail", "메일"],
    "name": ["이름", "name", "성명"],
    "segment": ["세그먼트", "segment", "구분"],
    "consent": ["수신동의", "수신 동의", "consent"],
}
CONSENT_YES = {"y", "yes", "예", "동의", "o", "true", "1", "✓", "v"}
BUILTIN_REPLY_CLASSES = ["반송", "수신거부"]

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+'-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}$")
VAR_RE = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}")

# 광고성 신호(정보통신망법 제50조 판별 보조). 강한 신호가 있으면 '안내' 캠페인은 막는다.
AD_STRONG = [
    "쿠폰", "할인", "이벤트", "특가", "세일", "프로모션", "적립금", "마일리지", "포인트 적립",
    "증정", "사은품", "신상품", "신제품", "출시", "구매하기", "지금 구매", "한정 수량",
    "오픈 기념", "혜택", "무료 체험", "얼리버드", "최저가", "% off", "sale",
]
AD_WEAK = ["안부", "새해", "명절", "추석", "설날", "연말", "추천", "소개해 드", "뉴스레터", "무료", "구독"]

FATAL_PATTERNS = [
    "ratelimitexceeded", "userratelimitexceeded", "dailylimitexceeded", "sending limit",
    "quota", "5.4.6", "unusual sending", "autherror", "invalid authentication",
    "insufficient", "invalid_grant", "unauthorized", "\"code\": 429", "\"code\": 401", "\"code\": 403",
]

STATE_DIR = ".mail-campaign"


class CampaignError(Exception):
    pass


# ── 시간 ───────────────────────────────────────────────────────────────
def now_kst() -> dt.datetime:
    override = os.environ.get("MAIL_CAMPAIGN_NOW")
    if override:
        t = dt.datetime.fromisoformat(override)
        if t.tzinfo is None:
            t = t.replace(tzinfo=_kst())
        return t.astimezone(_kst())
    return dt.datetime.now(_kst())


def _kst():
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo("Asia/Seoul")
    except Exception:
        return dt.timezone(dt.timedelta(hours=9))


def is_night(t: dt.datetime) -> bool:
    return t.hour >= 21 or t.hour < 8


# ── campaign.md 파싱 ───────────────────────────────────────────────────
class Campaign:
    def __init__(self, folder: Path):
        self.folder = folder
        path = folder / "campaign.md"
        if not path.exists():
            raise CampaignError(f"campaign.md 가 없습니다: {path}  (먼저 init)")
        self.text = path.read_text(encoding="utf-8")
        self.meta, body = _split_frontmatter(self.text)
        self.segments: dict[str, dict] = {}
        self.footer = ""
        self._parse_body(body)

        self.name = self.meta.get("name", "").strip()
        if not self.name:
            raise CampaignError("campaign.md 머리말에 name 이 없습니다.")
        self.kind = self.meta.get("kind", "안내").strip()
        if self.kind not in ("안내", "광고"):
            raise CampaignError("kind 는 '안내' 또는 '광고' 만 씁니다.")
        self.source = self.meta.get("source", "").strip()
        if not self.source:
            raise CampaignError("campaign.md 머리말에 source(시트 ID·URL 또는 CSV 경로)가 없습니다.")
        self.tab = self.meta.get("tab", "").strip()
        self.html = self.meta.get("html", "false").strip().lower() in ("true", "yes", "예", "1")
        self.sender_from = self.meta.get("from", "").strip()
        self.test_to = self.meta.get("test_to", "").strip()
        self.daily_cap = int(self.meta.get("daily_cap", "400") or 400)
        self.interval = _parse_interval(self.meta.get("interval", "20-30"))
        self.override = self.meta.get("ad_check_override", "").strip()
        self.columns = _parse_columns(self.meta.get("columns", ""))
        cats = [c.strip() for c in self.meta.get("reply_categories", "확인, 문의, 기타").split(",") if c.strip()]
        self.reply_classes = cats + [c for c in BUILTIN_REPLY_CLASSES if c not in cats]
        self.sender_name = self.meta.get("sender_name", "").strip()
        self.sender_contact = self.meta.get("sender_contact", "").strip()
        self.unsubscribe = self.meta.get("unsubscribe", "").strip()
        if not self.segments:
            raise CampaignError("'## 세그먼트: 이름' 절이 하나도 없습니다.")
        if self.kind == "광고":
            missing = [k for k in ("sender_name", "sender_contact", "unsubscribe") if not getattr(self, k)]
            if missing:
                raise CampaignError(
                    "광고 캠페인은 머리말에 sender_name·sender_contact·unsubscribe 가 모두 있어야 합니다"
                    f"(없음: {', '.join(missing)}). 정보통신망법 제50조 제4항 표시 의무."
                )

    def _parse_body(self, body: str):
        current = None
        lines: list[str] = []

        def flush():
            if current is None:
                return
            kind, name = current
            chunk = "\n".join(lines).strip("\n")
            if kind == "footer":
                self.footer = chunk.strip()
                return
            subject, text = _parse_segment(name, chunk)
            self.segments[name] = {"subject": subject, "body": text}

        for line in body.splitlines():
            m = re.match(r"^##\s+세그먼트\s*[:：]\s*(.+?)\s*$", line)
            if m:
                flush()
                current, lines = ("segment", m.group(1)), []
                continue
            if re.match(r"^##\s+꼬리말\s*$", line):
                flush()
                current, lines = ("footer", ""), []
                continue
            if line.startswith("## ") or line.startswith("# "):
                flush()
                current, lines = None, []
                continue
            if current is not None:
                lines.append(line)
        flush()

    def variables(self, segment: str) -> list[str]:
        seg = self.segments[segment]
        found = VAR_RE.findall(seg["subject"] + "\n" + seg["body"] + "\n" + self.footer)
        return list(dict.fromkeys(v.strip() for v in found))

    def all_template_text(self) -> str:
        parts = [self.footer]
        for seg in self.segments.values():
            parts += [seg["subject"], seg["body"]]
        return "\n".join(parts)


def _split_frontmatter(text: str):
    if not text.startswith("---"):
        raise CampaignError("campaign.md 는 --- 로 둘러싼 머리말로 시작해야 합니다.")
    end = text.find("\n---", 3)
    if end < 0:
        raise CampaignError("campaign.md 머리말이 --- 로 닫히지 않았습니다.")
    meta = {}
    for raw in text[3:end].splitlines():
        line = raw.split(" #", 1)[0].rstrip()
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        k, v = line.split(":", 1)
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
            v = v[1:-1]
        meta[k.strip()] = v
    return meta, text[end + 4:]


def _parse_segment(name: str, chunk: str):
    m = re.search(r"^제목\s*[:：]\s*(.+)$", chunk, re.M)
    if not m:
        raise CampaignError(f"세그먼트 '{name}' 에 '제목:' 줄이 없습니다.")
    b = re.search(r"^본문\s*[:：]\s*$", chunk, re.M)
    if not b:
        raise CampaignError(f"세그먼트 '{name}' 에 '본문:' 줄이 없습니다.")
    return m.group(1).strip(), chunk[b.end():].strip("\n")


def _parse_interval(v: str):
    nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", v or "")]
    if not nums:
        return (20.0, 30.0)
    lo, hi = (nums[0], nums[1]) if len(nums) > 1 else (nums[0], nums[0])
    return (min(lo, hi), max(lo, hi))


def _parse_columns(v: str) -> dict:
    out = {}
    for part in v.split(","):
        if "=" in part:
            k, val = part.split("=", 1)
            out[k.strip()] = val.strip()
    return out


# ── gws 실행기 ─────────────────────────────────────────────────────────
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
    env = os.environ.get("MAIL_CAMPAIGN_GWS", "").strip()
    if env:
        return shlex.split(env)
    home = Path(os.environ.get("HERMES_HOME", "").strip() or Path.home() / ".hermes")
    if (home / "google_token.json").exists():
        roots = [home, Path.home() / ".hermes", Path.home() / ".hermes" / "hermes-agent"]
        for root in roots:
            bridge = root / "skills" / "productivity" / "google-workspace" / "scripts" / "gws_bridge.py"
            if bridge.exists():
                gdir = find_gws_dir(home)
                if gdir is None:
                    raise CampaignError("gws CLI 를 찾지 못했습니다(PATH·Hermes 프로필 bin). `npm i -g @googleworkspace/cli` 로 설치하세요.")
                path = gdir + os.pathsep + os.environ.get("PATH", "")
                return ["/usr/bin/env", "PATH=" + path, bridge_python(home), str(bridge)]
    gdir = find_gws_dir(Path(os.environ.get("HERMES_HOME", "").strip() or Path.home() / ".hermes"))
    if gdir:
        return [str(Path(gdir) / "gws")]
    raise CampaignError(
        "gws CLI 를 찾지 못했습니다. `npm i -g @googleworkspace/cli` 로 설치하세요"
        "(Hermes 도 gws_bridge.py 가 내부에서 gws 를 실행하므로 설치가 필요합니다)."
    )


def bridge_python(home: Path) -> str:
    """gws_bridge.py 는 `datetime.UTC` 를 써서 Python 3.11 이상이 필요하다.
    시스템 python3 가 더 낮으면(macOS 기본 3.9) Hermes 자체 venv 의 파이썬을 쓴다."""
    if sys.version_info >= (3, 11):
        return sys.executable
    cands = []
    for root in dict.fromkeys([home, Path.home() / ".hermes"]):
        cands += sorted(root.glob("installs/*/environments/*/venv/bin/python"), key=lambda p: p.stat().st_mtime,
                        reverse=True)
    cands += [Path(p) for n in ("python3.14", "python3.13", "python3.12", "python3.11") if (p := shutil.which(n))]
    for c in cands:
        try:
            ok = subprocess.run([str(c), "-c", "import sys; sys.exit(sys.version_info < (3, 11))"],
                                capture_output=True, timeout=10).returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            ok = False
        if ok:
            return str(c)
    raise CampaignError("gws_bridge.py 를 실행할 Python 3.11 이상을 찾지 못했습니다. MAIL_CAMPAIGN_GWS 로 직접 지정하세요.")


class Gws:
    def __init__(self):
        self.cmd = resolve_gws()

    def run(self, args: list[str], timeout: int = 120):
        try:
            p = subprocess.run(self.cmd + args, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return 124, None, "timeout"
        data = None
        out = p.stdout.strip()
        if out:
            try:
                data = json.loads(out)
            except json.JSONDecodeError:
                # gws 가 앞에 안내 줄을 찍는 경우 첫 { 부터 파싱
                i = out.find("{")
                if i >= 0:
                    try:
                        data = json.loads(out[i:])
                    except json.JSONDecodeError:
                        data = None
        err = (p.stderr or "").strip()
        if isinstance(data, dict) and "error" in data:
            return p.returncode or 1, data, err or json.dumps(data["error"], ensure_ascii=False)
        return p.returncode, data, err

    def ok(self, args, what):
        rc, data, err = self.run(args)
        if rc != 0:
            raise CampaignError(f"{what} 실패: {err or data}")
        return data

    def profile_email(self) -> str:
        data = self.ok(["gmail", "users", "getProfile", "--params", json.dumps({"userId": "me"})], "계정 확인")
        return (data or {}).get("emailAddress", "")


def is_fatal(err: str) -> bool:
    low = (err or "").lower()
    return any(p in low for p in FATAL_PATTERNS)


def is_definite_rejection(err: str, data) -> bool:
    """API 가 명확히 거절했는가(=메일이 나가지 않았음이 확실한가)."""
    return isinstance(data, dict) and "error" in data


# ── 명단(시트·CSV) ─────────────────────────────────────────────────────
class Roster:
    """헤더 1행 + 데이터 행. 행 번호는 시트 기준(헤더=1)."""

    def __init__(self, camp: Campaign, gws: Gws | None):
        self.camp = camp
        self.gws = gws
        self.csv_path = None
        self.sheet_id = None
        src = camp.source
        m = re.search(r"/spreadsheets/d/([A-Za-z0-9_-]+)", src)
        if m:
            self.sheet_id = m.group(1)
        elif src.lower().endswith(".csv"):
            p = Path(src).expanduser()
            self.csv_path = p if p.is_absolute() else camp.folder / p
        elif re.fullmatch(r"[A-Za-z0-9_-]{20,}", src):
            self.sheet_id = src
        else:
            raise CampaignError(f"source 를 해석하지 못했습니다: {src}")
        self.header: list[str] = []
        self.rows: list[list[str]] = []
        self.load()

    # 읽기
    def load(self):
        if self.csv_path:
            if not self.csv_path.exists():
                raise CampaignError(f"CSV 가 없습니다: {self.csv_path}")
            with self.csv_path.open(encoding="utf-8-sig", newline="") as f:
                table = list(csv.reader(f))
        else:
            if not self.camp.tab:
                meta = self.gws.ok(
                    ["sheets", "spreadsheets", "get", "--params",
                     json.dumps({"spreadsheetId": self.sheet_id, "fields": "sheets.properties.title"})],
                    "시트 탭 확인",
                )
                self.camp.tab = meta["sheets"][0]["properties"]["title"]
            data = self.gws.ok(["sheets", "+read", "--spreadsheet", self.sheet_id, "--range", self._q(self.camp.tab)],
                               "시트 읽기")
            table = (data or {}).get("values", [])
        if not table:
            raise CampaignError("명단이 비어 있습니다(헤더 행 없음).")
        self.header = [h.strip() for h in table[0]]
        width = len(self.header)
        self.rows = [(r + [""] * width)[:max(width, len(r))] for r in table[1:]]

    def _q(self, tab: str) -> str:
        return "'" + tab.replace("'", "''") + "'"

    def col(self, name: str) -> int | None:
        norm = _norm(name)
        for i, h in enumerate(self.header):
            if _norm(h) == norm:
                return i
        return None

    def field_col(self, field: str) -> int | None:
        if field in self.camp.columns:
            return self.col(self.camp.columns[field])
        for cand in DEFAULT_COLUMNS[field]:
            i = self.col(cand)
            if i is not None:
                return i
        return None

    def get(self, row_idx: int, col: int | None) -> str:
        if col is None:
            return ""
        r = self.rows[row_idx]
        return r[col].strip() if col < len(r) else ""

    def sheet_row(self, row_idx: int) -> int:
        return row_idx + 2

    # 쓰기
    def ensure_status_columns(self) -> list[str]:
        added = [c for c in STATUS_COLUMNS if self.col(c) is None]
        if not added:
            return []
        start = len(self.header)
        self.header += added
        for r in self.rows:
            r += [""] * (len(self.header) - len(r))
        if self.csv_path:
            self._write_csv()
        else:
            self._ensure_grid_columns(start + len(added))
            rng = f"{self._q(self.camp.tab)}!{_a1(start)}1:{_a1(start + len(added) - 1)}1"
            self._batch([{"range": rng, "values": [added]}])
        return added

    def _ensure_grid_columns(self, need: int):
        """시트 격자의 열 수가 모자라면 늘린다(CSV 를 올린 시트는 데이터 폭만큼만 열이 있다)."""
        meta = self.gws.ok(
            ["sheets", "spreadsheets", "get", "--params",
             json.dumps({"spreadsheetId": self.sheet_id, "fields": "sheets.properties(sheetId,title,gridProperties)"})],
            "시트 크기 확인",
        )
        props = next((s["properties"] for s in meta.get("sheets", []) if s["properties"].get("title") == self.camp.tab),
                     None)
        if not props:
            raise CampaignError(f"탭을 찾지 못했습니다: {self.camp.tab}")
        have = props.get("gridProperties", {}).get("columnCount", 0)
        if have >= need:
            return
        self.gws.ok(
            ["sheets", "spreadsheets", "batchUpdate", "--params", json.dumps({"spreadsheetId": self.sheet_id}),
             "--json", json.dumps({"requests": [{"appendDimension": {"sheetId": props["sheetId"], "dimension": "COLUMNS",
                                                                     "length": need - have}}]})],
            "시트 열 늘리기",
        )

    def update(self, row_idx: int, values: dict):
        """values: {열 이름: 값}. 한 행의 여러 칸을 한 번에 쓴다."""
        r = self.rows[row_idx]
        for name, val in values.items():
            c = self.col(name)
            if c is None:
                raise CampaignError(f"열이 없습니다: {name}")
            if c >= len(r):
                r += [""] * (c + 1 - len(r))
            r[c] = val
        if self.csv_path:
            self._write_csv()
            return
        data = []
        for name, val in values.items():
            c = self.col(name)
            data.append({"range": f"{self._q(self.camp.tab)}!{_a1(c)}{self.sheet_row(row_idx)}", "values": [[val]]})
        self._batch(data)

    def update_many(self, updates: list[tuple[int, dict]]):
        if not updates:
            return
        data = []
        for row_idx, values in updates:
            r = self.rows[row_idx]
            for name, val in values.items():
                c = self.col(name)
                if c >= len(r):
                    r += [""] * (c + 1 - len(r))
                r[c] = val
                data.append({"range": f"{self._q(self.camp.tab)}!{_a1(c)}{self.sheet_row(row_idx)}", "values": [[val]]})
        if self.csv_path:
            self._write_csv()
        else:
            for i in range(0, len(data), 200):
                self._batch(data[i:i + 200])

    def _batch(self, data):
        self.gws.ok(
            ["sheets", "spreadsheets", "values", "batchUpdate", "--params", json.dumps({"spreadsheetId": self.sheet_id}),
             "--json", json.dumps({"valueInputOption": "RAW", "data": data}, ensure_ascii=False)],
            "시트 쓰기",
        )

    def _write_csv(self):
        tmp = self.csv_path.with_suffix(".csv.tmp")
        with tmp.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.writer(f)
            w.writerow(self.header)
            for r in self.rows:
                w.writerow((r + [""] * len(self.header))[:len(self.header)])
        tmp.replace(self.csv_path)


def _norm(s: str) -> str:
    return re.sub(r"\s+", "", s or "").lower()


def _a1(col: int) -> str:
    s, n = "", col + 1
    while n:
        n, rem = divmod(n - 1, 26)
        s = chr(65 + rem) + s
    return s


# ── 저널(로컬 진실 원천) ───────────────────────────────────────────────
class Journal:
    def __init__(self, camp: Campaign):
        self.dir = camp.folder / STATE_DIR
        self.dir.mkdir(exist_ok=True)
        self.path = self.dir / "journal.jsonl"
        self.events = []
        if self.path.exists():
            for line in self.path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    self.events.append(json.loads(line))

    def add(self, **ev):
        ev.setdefault("ts", now_kst().isoformat(timespec="seconds"))
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
        self.events.append(ev)

    def sent(self) -> dict:
        return {e["key"]: e for e in self.events if e.get("event") == "send"}

    def drafts(self) -> dict:
        out = {}
        for e in self.events:
            if e.get("event") == "draft":
                out[e["key"]] = e
            elif e.get("event") == "draft-delete":
                out.pop(e["key"], None)
        return out


def ledger_path() -> Path:
    base = Path(os.environ.get("XDG_STATE_HOME", "").strip() or Path.home() / ".local" / "state")
    p = base / "mail-campaign"
    p.mkdir(parents=True, exist_ok=True)
    return p / "ledger.jsonl"


def ledger_add(account: str, kind: str):
    with ledger_path().open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": now_kst().isoformat(timespec="seconds"), "account": account, "kind": kind}) + "\n")


def ledger_count_24h(account: str) -> int:
    p = ledger_path()
    if not p.exists():
        return 0
    cutoff = now_kst() - dt.timedelta(hours=24)
    n = 0
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            e = json.loads(line)
            if e.get("account") == account and dt.datetime.fromisoformat(e["ts"]) >= cutoff:
                n += 1
        except Exception:
            continue
    return n


# ── 검증·렌더 ─────────────────────────────────────────────────────────
def key_for(camp: Campaign, email: str) -> str:
    return f"{camp.name}:{email.strip().lower()}"


def render(camp: Campaign, roster: Roster, row_idx: int, segment: str):
    seg = camp.segments[segment]

    def fill(t: str) -> str:
        return VAR_RE.sub(lambda m: roster.get(row_idx, roster.col(m.group(1).strip())), t)

    subject = fill(seg["subject"]).strip()
    body = fill(seg["body"])
    if camp.footer:
        body = body.rstrip() + "\n\n" + fill(camp.footer)
    if camp.kind == "광고":
        if not subject.startswith("(광고)"):
            subject = "(광고) " + subject
        body = body.rstrip() + "\n\n" + ad_footer(camp)
    if camp.html:
        body = body.replace("\n", "<br>\n") if "<" not in body else body
    return subject, body


def ad_footer(camp: Campaign) -> str:
    return (
        "──────────\n"
        f"보내는 곳: {camp.sender_name} · 연락처: {camp.sender_contact}\n"
        f"수신거부: {camp.unsubscribe} (수신거부에 드는 비용은 없습니다)"
    )


def content_hash(to: str, subject: str, body: str) -> str:
    return hashlib.sha256(f"{to}\n{subject}\n{body}".encode()).hexdigest()[:12]


def ad_scan(camp: Campaign):
    text = camp.all_template_text().lower()
    strong = [w for w in AD_STRONG if w.lower() in text]
    weak = [w for w in AD_WEAK if w.lower() in text]
    return strong, weak


def evaluate(camp: Campaign, roster: Roster, journal: Journal):
    """행마다 판정: send / hold / skip. 쓰기 없음."""
    c_email = roster.field_col("email")
    c_name = roster.field_col("name")
    c_seg = roster.field_col("segment")
    c_consent = roster.field_col("consent")
    missing = [f for f, c in (("email", c_email), ("name", c_name), ("segment", c_seg)) if c is None]
    if missing:
        raise CampaignError(
            f"필수 열을 찾지 못했습니다: {', '.join(missing)}. 헤더: {roster.header}. "
            "campaign.md 의 columns: email=…, name=…, segment=… 로 매핑하세요."
        )
    if camp.kind == "광고" and c_consent is None:
        raise CampaignError("광고 캠페인은 수신동의 열이 필수입니다(columns: consent=… 로 매핑 가능).")
    for seg in camp.segments:
        for v in camp.variables(seg):
            if roster.col(v) is None:
                raise CampaignError(f"세그먼트 '{seg}' 의 변수 {{{{{v}}}}} 에 해당하는 열이 시트에 없습니다.")

    sent = journal.sent()
    seen: dict[str, int] = {}
    results = []
    for i in range(len(roster.rows)):
        email = roster.get(i, c_email)
        name = roster.get(i, c_name)
        seg = roster.get(i, c_seg)
        status = roster.get(i, roster.col(COL_STATUS))
        row_no = roster.sheet_row(i)
        res = {"idx": i, "row": row_no, "email": email, "name": name, "segment": seg, "status": status}
        if not any(roster.get(i, c) for c in range(len(roster.header))):
            continue  # 완전히 빈 행
        if status in (ST_SKIP, ST_CHECK):
            # 사람이 정한 제외·확인 필요는 중복·보냄 판정보다 먼저(시트를 보류로 되돌리지 않는다)
            res["decision"] = "skip"
            res["why"] = status
            results.append(res)
            continue
        k = key_for(camp, email) if email else None
        low = email.lower()
        if email and low in seen:
            res["decision"] = "hold"
            res["why"] = f"중복(행 {seen[low]}과 같은 주소)"
            results.append(res)
            continue
        if email and EMAIL_RE.match(email):
            seen[low] = row_no
        if (k and k in sent) or status == ST_SENT:
            res["decision"] = "skip"
            res["why"] = "이미 보냄"
            res["journal_sent"] = sent.get(k)
            results.append(res)
            continue
        reason = None
        if not email:
            reason = "이메일 빈칸"
        elif not EMAIL_RE.match(email):
            reason = f"이메일 형식({email})"
        elif not name:
            reason = "이름 빈칸"
        elif not seg:
            reason = "세그먼트 빈칸"
        elif seg not in camp.segments:
            reason = f"문구 없는 세그먼트({seg})"
        else:
            empty = [v for v in camp.variables(seg) if not roster.get(i, roster.col(v))]
            if empty:
                reason = "빈 칸(" + ", ".join(empty) + ")"
            elif camp.kind == "광고":
                consent = roster.get(i, c_consent)
                if consent.lower() not in CONSENT_YES:
                    reason = "수신동의 없음" if not consent.startswith("거부") else "수신거부"
        if reason:
            res["decision"] = "hold"
            res["why"] = reason
        else:
            subject, body = render(camp, roster, i, seg)
            res.update(decision="send", subject=subject, body=body, key=k,
                       hash=content_hash(email, subject, body))
        results.append(res)
    return results


def sync_sheet(camp: Campaign, roster: Roster, journal: Journal, results, write_holds=True):
    """저널을 진실로 시트를 맞춘다: 보냄 복구, 보류 기록, 고쳐진 보류 해제."""
    updates = []
    for r in results:
        i = r["idx"]
        cur_reason = roster.get(i, roster.col(COL_REASON))
        if r["decision"] == "skip" and r.get("journal_sent") and r["status"] != ST_SENT:
            e = r["journal_sent"]
            updates.append((i, {COL_STATUS: ST_SENT, COL_REASON: "", COL_MSG: e.get("messageId", ""),
                                COL_THREAD: e.get("threadId", ""), COL_SENT_AT: e.get("ts", "")}))
        elif r["decision"] == "hold" and write_holds:
            if r["status"] != ST_HOLD or cur_reason != r["why"]:
                updates.append((i, {COL_STATUS: ST_HOLD, COL_REASON: r["why"]}))
        elif r["decision"] == "send" and r["status"] in (ST_HOLD, ST_ERR) and write_holds:
            updates.append((i, {COL_STATUS: ST_WAIT, COL_REASON: ""}))
    roster.update_many(updates)
    return len(updates)


# ── 승인 토큰 ─────────────────────────────────────────────────────────
def plan_items(results, limit=None):
    items = [r for r in results if r["decision"] == "send"]
    return items[:limit] if limit else items


def plan_token(camp: Campaign, items) -> str:
    h = hashlib.sha256()
    h.update(f"{camp.name}|{camp.kind}|".encode())
    for r in items:
        h.update(f"{r['row']}|{r['email'].lower()}|{r['hash']}\n".encode())
    return h.hexdigest()[:8].upper()


# ── 명령 ───────────────────────────────────────────────────────────────
def load(folder: str, need_gws=True):
    camp = Campaign(Path(folder).expanduser().resolve())
    gws = Gws() if need_gws else None
    roster = Roster(camp, gws)
    journal = Journal(camp)
    return camp, gws, roster, journal


def cmd_init(a):
    folder = Path(a.folder).expanduser()
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "campaign.md"
    if target.exists():
        raise CampaignError(f"이미 있습니다: {target} (덮어쓰지 않습니다)")
    tpl = Path(__file__).resolve().parent.parent / "assets" / "campaign.template.md"
    text = tpl.read_text(encoding="utf-8")
    if a.source:
        text = text.replace("source: <시트 URL 또는 ID, 또는 명단.csv>", f"source: {a.source}")
    target.write_text(text, encoding="utf-8")
    print(f"만들었습니다: {target}\n다음: campaign.md 의 목적·세그먼트 문구를 채운 뒤 `check`.")


def cmd_doctor(a):
    gws = Gws()
    print(f"mail-campaign {VERSION}")
    print("gws 실행기:", " ".join(gws.cmd))
    rc, data, err = gws.run(["--version"])
    if rc != 0:
        raise CampaignError("gws 를 실행하지 못했습니다: " + ((err or "").splitlines() or ["?"])[-1])
    print("gws 버전: 확인됨")
    email = gws.profile_email()
    if not email:
        raise CampaignError("보내는 계정을 확인하지 못했습니다(Google 연결 확인).")
    print("보내는 계정:", email or "(확인 실패)")
    print(f"최근 24시간 이 계정 발송(이 스킬 기록): {ledger_count_24h(email)}통")
    if a.folder:
        camp, _, roster, _ = load(a.folder)
        print("명단 열:", ", ".join(roster.header))
        print("필수 열 매핑:", {f: (roster.header[c] if c is not None else None)
                           for f in ("email", "name", "segment", "consent") for c in [roster.field_col(f)]})


def print_ad_findings(camp: Campaign):
    strong, weak = ad_scan(camp)
    blocked = False
    if camp.kind == "안내" and strong:
        if camp.override:
            print(f"⚠ 광고성 신호 {strong} — ad_check_override 로 통과: {camp.override}")
        else:
            print(f"✖ 광고성 신호: {', '.join(strong)}")
            print("  '안내' 메일에 광고 문구가 한 줄이라도 섞이면 메일 전체가 광고성 정보가 됩니다.")
            print("  그 문구를 빼거나, kind: 광고 로 바꾸세요(수신동의 열·(광고)·수신거부 안내 필요).")
            print("  거래 사실을 적은 것뿐이라면(예: '할인 적용 후 결제 금액') 사용자 확인 뒤")
            print("  ad_check_override: <사유> 를 머리말에 적습니다.")
            blocked = True
    if weak:
        print(f"△ 확인할 표현: {', '.join(weak)} — 안부·추천·뉴스레터성 문장이면 광고로 봅니다(references/korea-ad-law.md).")
    if camp.kind == "광고":
        print("광고 캠페인: 제목 앞 (광고)·발신자·수신거부 안내 자동 삽입, 수신동의 행만 발송, 21~08시 발송 차단.")
    return blocked


def summarize(results):
    send = [r for r in results if r["decision"] == "send"]
    hold = [r for r in results if r["decision"] == "hold"]
    skip = [r for r in results if r["decision"] == "skip"]
    by_seg = {}
    for r in send:
        by_seg[r["segment"]] = by_seg.get(r["segment"], 0) + 1
    print(f"보낼 대상 {len(send)}행 · 보류 {len(hold)}행 · 건너뜀 {len(skip)}행")
    if by_seg:
        print("세그먼트별:", ", ".join(f"{k} {v}" for k, v in by_seg.items()))
    for r in hold:
        print(f"  보류  행 {r['row']:>4}  {r['email'] or '-':<32} {r['why']}")
    for r in skip:
        if r["why"] != "이미 보냄":
            print(f"  건너뜀 행 {r['row']:>4}  {r['email'] or '-':<32} {r['why']}")
    return send, hold, skip


def cmd_check(a):
    camp, gws, roster, journal = load(a.folder, need_gws=not _is_csv_only(a))
    added = [] if a.no_write else roster.ensure_status_columns()
    if added:
        print("상태 열을 만들었습니다:", ", ".join(added))
    results = evaluate(camp, roster, journal)
    if not a.no_write:
        n = sync_sheet(camp, roster, journal, results)
        if n:
            print(f"시트 상태 {n}행 갱신")
    print(f"캠페인: {camp.name} ({camp.kind})")
    summarize(results)
    blocked = print_ad_findings(camp)
    return 2 if blocked else 0


def _is_csv_only(a) -> bool:
    try:
        camp = Campaign(Path(a.folder).expanduser().resolve())
        return camp.source.lower().endswith(".csv")
    except CampaignError:
        return False


def pick_row(results, row=None):
    send = [r for r in results if r["decision"] == "send"]
    if row:
        for r in results:
            if r["row"] == row:
                return r
        raise CampaignError(f"행 {row} 이 없습니다.")
    if not send:
        raise CampaignError("보낼 수 있는 행이 없습니다.")
    return send[0]


def cmd_preview(a):
    camp, gws, roster, journal = load(a.folder, need_gws=not _is_csv_only(a))
    results = evaluate(camp, roster, journal)
    r = pick_row(results, a.row)
    if r["decision"] != "send":
        print(f"행 {r['row']}: {r['decision']} — {r.get('why')}")
        return 1
    print(f"행 {r['row']} · {r['segment']} · 받는 사람 {r['email']}")
    print(f"제목: {r['subject']}")
    print("─" * 40)
    print(r["body"])
    return 0


def cmd_render(a):
    camp, gws, roster, journal = load(a.folder, need_gws=not _is_csv_only(a))
    results = evaluate(camp, roster, journal)
    out = camp.folder / STATE_DIR / "rendered.jsonl"
    send = [r for r in results if r["decision"] == "send"]
    with out.open("w", encoding="utf-8") as f:
        for r in send:
            f.write(json.dumps({k: r[k] for k in ("row", "email", "name", "segment", "subject", "body", "hash")},
                               ensure_ascii=False) + "\n")
    summarize(results)
    blocked = print_ad_findings(camp)
    seen = set()
    for r in send:
        if r["segment"] not in seen:
            seen.add(r["segment"])
            print(f"\n[{r['segment']}] 행 {r['row']} → {r['email']}\n제목: {r['subject']}\n{r['body'][:400]}")
    print(f"\n전체 렌더: {out}")
    return 2 if blocked else 0


def send_args(camp: Campaign, to: str, subject: str, body: str, draft=False):
    args = ["gmail", "+send", "--to", to, "--subject", subject, "--body", body]
    if camp.html:
        args.append("--html")
    if camp.sender_from:
        args += ["--from", camp.sender_from]
    if draft:
        args.append("--draft")
    return args


def _ids(data):
    data = data or {}
    if "message" in data:  # draft
        return data.get("id", ""), data["message"].get("id", ""), data["message"].get("threadId", "")
    return "", data.get("id", ""), data.get("threadId", "")


def cmd_draft(a):
    camp, gws, roster, journal = load(a.folder)
    roster.ensure_status_columns()
    results = evaluate(camp, roster, journal)
    sync_sheet(camp, roster, journal, results)
    if print_ad_findings(camp):
        return 2
    drafts = journal.drafts()
    items = plan_items(results, a.limit)
    made = 0
    for r in items:
        old = drafts.get(r["key"])
        if old and old.get("hash") == r["hash"] and not a.redo:
            continue
        if old:
            gws.run(["gmail", "users", "drafts", "delete", "--params", json.dumps({"userId": "me", "id": old["draftId"]})])
            journal.add(event="draft-delete", key=r["key"], draftId=old["draftId"])
        rc, data, err = gws.run(send_args(camp, r["email"], r["subject"], r["body"], draft=True))
        if rc != 0:
            print(f"  ✖ 행 {r['row']} 초안 실패: {err}")
            if is_fatal(err):
                return 3
            continue
        draft_id, msg_id, _ = _ids(data)
        journal.add(event="draft", key=r["key"], row=r["row"], email=r["email"], hash=r["hash"], draftId=draft_id)
        roster.update(r["idx"], {COL_STATUS: ST_DRAFT, COL_DRAFT: draft_id})
        made += 1
    print(f"초안 {made}통 만들었습니다(이미 있던 같은 내용 초안은 그대로 둠). Gmail 임시보관함에서 확인하세요.")
    return 0


def cmd_test(a):
    camp, gws, roster, journal = load(a.folder)
    results = evaluate(camp, roster, journal)
    if print_ad_findings(camp):
        return 2
    account = gws.profile_email()
    to = a.to or camp.test_to or account
    if not to:
        raise CampaignError("테스트 받을 주소를 알 수 없습니다(--to 또는 test_to).")
    if a.segment:
        unknown = [x for x in a.segment if x not in camp.segments]
        if unknown:
            raise CampaignError(f"campaign.md 에 없는 세그먼트: {', '.join(unknown)}")
    picks, seen = [], set()
    for r in results:
        if a.segment and r.get("segment") not in a.segment:
            continue
        if r["decision"] == "send" and r["segment"] not in seen:
            seen.add(r["segment"])
            picks.append(r)
    picks = picks[:a.count]
    if not picks:
        raise CampaignError("테스트할 행이 없습니다.")
    for r in picks:
        subject = "[테스트] " + r["subject"]
        body = f"※ 테스트 발송입니다. 실제 받는 사람: {r['email']} (행 {r['row']}, {r['segment']})\n\n" + r["body"]
        rc, data, err = gws.run(send_args(camp, to, subject, body))
        if rc != 0:
            print(f"  ✖ 테스트 실패(행 {r['row']}): {err}")
            return 3
        _, msg_id, thread_id = _ids(data)
        journal.add(event="test", key=r["key"], row=r["row"], to=to, messageId=msg_id)
        ledger_add(account, "test")
        print(f"  ✓ {r['segment']} (행 {r['row']}) → {to}  messageId={msg_id}")
    print(f"테스트 {len(picks)}통을 {to} 로 보냈습니다. 시트 상태는 바꾸지 않습니다.")
    return 0


def preflight(camp, gws, roster, journal, limit):
    results = evaluate(camp, roster, journal)
    blocked = print_ad_findings(camp)
    items = plan_items(results, limit)
    drafts = journal.drafts()
    stale = [r for r in items if r["key"] in drafts and drafts[r["key"]].get("hash") != r["hash"]]
    return results, items, blocked, stale


def cmd_plan(a):
    camp, gws, roster, journal = load(a.folder)
    roster.ensure_status_columns()
    results, items, blocked, stale = preflight(camp, gws, roster, journal, a.limit)
    sync_sheet(camp, roster, journal, results)
    print(f"캠페인: {camp.name} ({camp.kind})")
    send, hold, skip = summarize(results)
    account = gws.profile_email()
    used = ledger_count_24h(account)
    remain = max(camp.daily_cap - used, 0)
    lo, hi = camp.interval
    eta = len(items) * (lo + hi) / 2 / 60
    print(f"보내는 계정: {account} · 최근 24시간 {used}통 · 일일 상한 {camp.daily_cap} (남은 {remain})")
    print(f"이번 발송: {len(items)}통 · 간격 {lo:.0f}~{hi:.0f}초 · 예상 {eta:.1f}분")
    if len(items) > remain:
        print(f"✖ 일일 상한을 넘습니다. --limit {remain} 이하로 나눠 보내세요.")
        return 2
    if camp.kind == "광고" and is_night(now_kst()):
        print("✖ 지금은 21~08시입니다. 광고 메일은 야간 발송을 하지 않습니다.")
        return 2
    if stale:
        print(f"✖ 초안을 만든 뒤 문구가 바뀐 행이 {len(stale)}개 있습니다: "
              + ", ".join(str(r['row']) for r in stale[:10]) + " → `draft --redo` 로 초안을 다시 만드세요.")
        return 2
    if blocked:
        return 2
    if not items:
        print("보낼 행이 없습니다.")
        return 0
    token = plan_token(camp, items)
    print(f"\n승인 토큰: {token}")
    print("사용자에게 위 숫자(보낼 통수·보류 수)를 보여 주고 명시적 승인을 받은 뒤에만:")
    lim = f" --limit {a.limit}" if a.limit else ""
    print(f"  mail_campaign.py send {shlex.quote(str(camp.folder))} --confirm {token}{lim}")
    return 0


class Lock:
    def __init__(self, path: Path):
        self.path = path
        self.f = None

    def __enter__(self):
        self.f = self.path.open("w")
        if fcntl:
            try:
                fcntl.flock(self.f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                raise CampaignError("이 캠페인을 이미 다른 프로세스가 보내는 중입니다(중복 발송 방지).")
        self.f.write(str(os.getpid()))
        self.f.flush()
        return self

    def __exit__(self, *exc):
        if self.f:
            self.f.close()
        try:
            self.path.unlink()
        except OSError:
            pass


def find_in_sent(gws: Gws, to: str, subject: str):
    q = f'in:sent to:{to} subject:"{subject[:60]}" newer_than:1d'
    rc, data, err = gws.run(["gmail", "users", "messages", "list", "--params",
                             json.dumps({"userId": "me", "q": q, "maxResults": 1})])
    if rc == 0 and data and data.get("messages"):
        m = data["messages"][0]
        return m.get("id", ""), m.get("threadId", "")
    return None


def cmd_send(a):
    camp, gws, roster, journal = load(a.folder)
    roster.ensure_status_columns()
    with Lock(camp.folder / STATE_DIR / "send.lock"):
        results, items, blocked, stale = preflight(camp, gws, roster, journal, a.limit)
        sync_sheet(camp, roster, journal, results)
        if blocked or stale:
            print("✖ plan 에서 막힌 항목이 있습니다. plan 을 다시 보세요.")
            return 2
        token = plan_token(camp, items)
        print(f"=== send 시작 {now_kst().isoformat(timespec='seconds')} · 대상 {len(items)}통 · 토큰 {a.confirm} ===", flush=True)
        if a.confirm != token:
            print(f"✖ 승인 토큰이 맞지 않습니다(현재 {token}). 명단이나 문구가 바뀌었을 수 있습니다 — plan 을 다시 보여 주고 승인받으세요.")
            return 2
        account = gws.profile_email()
        remain = camp.daily_cap - ledger_count_24h(account)
        if len(items) > remain:
            print(f"✖ 일일 상한 초과(남은 {remain}통).")
            return 2
        drafts = journal.drafts()
        lo, hi = camp.interval
        if a.interval is not None:
            lo = hi = a.interval
        consecutive = 0
        done = 0
        total = len(items)
        for n, r in enumerate(items, 1):
            if camp.kind == "광고" and is_night(now_kst()):
                print("■ 21시가 되어 광고 발송을 멈춥니다. 남은 행은 내일 08시 이후 다시 plan 하세요.")
                return 4
            if r["key"] in journal.sent():
                continue
            d = drafts.get(r["key"])
            if d and d.get("hash") == r["hash"]:
                args = ["gmail", "users", "drafts", "send", "--params", json.dumps({"userId": "me"}),
                        "--json", json.dumps({"id": d["draftId"]})]
            else:
                args = send_args(camp, r["email"], r["subject"], r["body"])
            rc, data, err = gws.run(args)
            if rc == 0:
                _, msg_id, thread_id = _ids(data)
                outcome = "send"
            elif is_definite_rejection(err, data):
                outcome = "error"
            else:
                found = find_in_sent(gws, r["email"], r["subject"])
                if found:
                    msg_id, thread_id = found
                    outcome = "send"
                else:
                    outcome = "unknown"
            if outcome == "send":
                ts = now_kst().isoformat(timespec="seconds")
                journal.add(event="send", key=r["key"], row=r["row"], email=r["email"], hash=r["hash"],
                            messageId=msg_id, threadId=thread_id, ts=ts)
                ledger_add(account, "send")
                try:
                    roster.update(r["idx"], {COL_STATUS: ST_SENT, COL_REASON: "", COL_MSG: msg_id,
                                             COL_THREAD: thread_id, COL_SENT_AT: ts})
                except CampaignError as e:
                    print(f"  ⚠ 행 {r['row']} 시트 기록 실패(저널에는 기록됨, 다음 실행 때 복구): {e}")
                consecutive = 0
                done += 1
                print(f"  ✓ {n}/{total} 행 {r['row']} {r['email']}  messageId={msg_id}", flush=True)
            else:
                consecutive += 1
                status = ST_ERR if outcome == "error" else ST_CHECK
                msg = (err or "")[:180]
                journal.add(event="error", key=r["key"], row=r["row"], email=r["email"], error=msg, status=status)
                try:
                    roster.update(r["idx"], {COL_STATUS: status, COL_REASON: msg})
                except CampaignError:
                    pass
                print(f"  ✖ {n}/{total} 행 {r['row']} {r['email']} {status}: {msg}", flush=True)
                if is_fatal(err):
                    print("■ 한도·인증 오류로 즉시 멈춥니다. 원인을 해결한 뒤 plan 부터 다시 하세요.")
                    return 3
                if consecutive >= 3:
                    print("■ 연속 3건 실패로 멈춥니다.")
                    return 3
            if n < total:
                time.sleep(random.uniform(lo, hi))
        print(f"완료: {done}/{total}통 보냄.")
        return 0


def cmd_status(a):
    camp = Campaign(Path(a.folder).expanduser().resolve())
    journal = Journal(camp)
    counts = {}
    for e in journal.events:
        counts[e.get("event")] = counts.get(e.get("event"), 0) + 1
    lock = camp.folder / STATE_DIR / "send.lock"
    print(f"캠페인: {camp.name}")
    print("저널:", ", ".join(f"{k} {v}" for k, v in counts.items()) or "(비어 있음)")
    print("발송 진행 중:", "예" if lock.exists() else "아니오")
    errs = [e for e in journal.events if e.get("event") == "error"][-5:]
    for e in errs:
        print(f"  최근 오류 행 {e.get('row')} {e.get('email')}: {e.get('error')}")


def _header(msg, name):
    for h in msg.get("payload", {}).get("headers", []):
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


def cmd_replies(a):
    camp, gws, roster, journal = load(a.folder)
    roster.ensure_status_columns()
    account = gws.profile_email().lower()
    sent = journal.sent()
    out = []
    for k, e in sent.items():
        tid = e.get("threadId")
        if not tid:
            continue
        rc, data, err = gws.run(["gmail", "users", "threads", "get", "--params", json.dumps(
            {"userId": "me", "id": tid, "format": "metadata", "metadataHeaders": ["From", "Date", "Subject"]})])
        if rc != 0:
            print(f"  ⚠ 스레드 읽기 실패({e.get('email')}): {err}")
            continue
        replies = []
        for m in (data or {}).get("messages", []):
            if m.get("id") == e.get("messageId"):
                continue
            labels = set(m.get("labelIds", []))
            frm = _header(m, "From")
            if "DRAFT" in labels:
                continue
            if account and account in frm.lower() and "INBOX" not in labels:
                continue  # 내가 보낸 후속 메일
            bounce = "mailer-daemon" in frm.lower() or "postmaster" in frm.lower()
            replies.append({"messageId": m.get("id"), "from": frm, "date": _header(m, "Date"),
                            "snippet": m.get("snippet", ""), "bounce": bounce})
        if not replies:
            continue
        idx = next((i for i in range(len(roster.rows))
                    if roster.get(i, roster.field_col("email")).lower() == e["email"].lower()), None)
        current = roster.get(idx, roster.col(COL_REPLY)) if idx is not None else ""
        out.append({"row": e.get("row"), "email": e["email"], "current": current, "replies": replies})
    path = camp.folder / STATE_DIR / "replies.json"
    path.write_text(json.dumps({"categories": camp.reply_classes, "items": out}, ensure_ascii=False, indent=2),
                    encoding="utf-8")
    print(f"답장 있는 행 {len(out)}개 → {path}")
    print("분류 기준:", ", ".join(camp.reply_classes))
    for it in out:
        last = it["replies"][-1]
        tag = " [반송]" if last["bounce"] else ""
        print(f"  행 {it['row']} {it['email']}{tag}: {last['snippet'][:80]}")
    return 0


def cmd_classify(a):
    camp, gws, roster, journal = load(a.folder, need_gws=not _is_csv_only(a))
    roster.ensure_status_columns()
    data = json.loads(Path(a.file).read_text(encoding="utf-8"))
    items = data.get("items", data) if isinstance(data, dict) else data
    c_consent = roster.field_col("consent")
    updates = []
    today = now_kst().date().isoformat()
    for it in items:
        cls = (it.get("class") or "").strip()
        if not cls:
            continue
        if cls not in camp.reply_classes:
            raise CampaignError(f"분류 '{cls}' 는 reply_categories 에 없습니다: {camp.reply_classes}")
        row = int(it["row"])
        idx = row - 2
        if not 0 <= idx < len(roster.rows):
            raise CampaignError(f"행 {row} 이 없습니다.")
        vals = {COL_REPLY: cls + (f" · {it['note']}" if it.get("note") else "")}
        if cls == "수신거부" and c_consent is not None:
            vals[roster.header[c_consent]] = f"거부({today})"
        updates.append((idx, vals))
        journal.add(event="classify", row=row, cls=cls)
    roster.update_many(updates)
    print(f"답장 분류 {len(updates)}행 기록")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="mail_campaign.py", description="시트 명단 개인화 메일 발송 도우미")
    p.add_argument("--version", action="version", version=VERSION)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="캠페인 폴더와 campaign.md 만들기")
    s.add_argument("folder")
    s.add_argument("--source", help="시트 URL·ID 또는 CSV 경로")
    s.set_defaults(fn=cmd_init)

    s = sub.add_parser("doctor", help="gws 실행기·계정·열 매핑 확인")
    s.add_argument("folder", nargs="?")
    s.set_defaults(fn=cmd_doctor)

    s = sub.add_parser("check", help="열 매핑·행 검증·보류 기록·광고성 점검")
    s.add_argument("folder")
    s.add_argument("--no-write", action="store_true", help="시트에 아무것도 쓰지 않는다")
    s.set_defaults(fn=cmd_check)

    s = sub.add_parser("preview", help="한 행 렌더 미리보기")
    s.add_argument("folder")
    s.add_argument("--row", type=int, help="시트 행 번호(헤더=1)")
    s.set_defaults(fn=cmd_preview)

    s = sub.add_parser("render", help="전체 렌더(.mail-campaign/rendered.jsonl)")
    s.add_argument("folder")
    s.set_defaults(fn=cmd_render)

    s = sub.add_parser("draft", help="Gmail 임시보관함에 초안 만들기")
    s.add_argument("folder")
    s.add_argument("--limit", type=int)
    s.add_argument("--redo", action="store_true", help="기존 초안을 지우고 다시 만든다")
    s.set_defaults(fn=cmd_draft)

    s = sub.add_parser("test", help="내 주소로 세그먼트별 테스트 발송")
    s.add_argument("folder")
    s.add_argument("--to")
    s.add_argument("--count", type=int, default=3)
    s.add_argument("--segment", action="append", help="이 세그먼트만 테스트(반복 가능)")
    s.set_defaults(fn=cmd_test)

    s = sub.add_parser("plan", help="발송 계획과 승인 토큰")
    s.add_argument("folder")
    s.add_argument("--limit", type=int)
    s.set_defaults(fn=cmd_plan)

    s = sub.add_parser("send", help="승인 토큰으로 간격 발송")
    s.add_argument("folder")
    s.add_argument("--confirm", required=True)
    s.add_argument("--limit", type=int)
    s.add_argument("--interval", type=float, help="고정 간격(초). 기본은 campaign.md 의 interval")
    s.set_defaults(fn=cmd_send)

    s = sub.add_parser("status", help="저널 요약·진행 여부")
    s.add_argument("folder")
    s.set_defaults(fn=cmd_status)

    s = sub.add_parser("replies", help="보낸 스레드의 답장 수거(.mail-campaign/replies.json)")
    s.add_argument("folder")
    s.set_defaults(fn=cmd_replies)

    s = sub.add_parser("classify", help="답장 분류 JSON 을 시트에 기록")
    s.add_argument("folder")
    s.add_argument("--file", required=True)
    s.set_defaults(fn=cmd_classify)

    a = p.parse_args(argv)
    try:
        return a.fn(a) or 0
    except CampaignError as e:
        print(f"✖ {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
