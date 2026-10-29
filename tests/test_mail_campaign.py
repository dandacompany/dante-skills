"""mail-campaign 스크립트 오프라인 테스트(가짜 gws + CSV 명단)."""
import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "mail-campaign" / "scripts" / "mail_campaign.py"
FAKE = Path(__file__).resolve().parent / "fake_gws.py"

CAMPAIGN = """---
name: 테스트 캠페인
source: roster.csv
kind: {kind}
columns: email=이메일, name=이름, segment=세그먼트
reply_categories: 확인, 일정 조율, 문의, 기타
interval: 0
daily_cap: {cap}
sender_name: 운영팀
sender_contact: 02-000-0000
unsubscribe: '수신거부'라고 답장
---

## 세그먼트: 확정

제목: {{{{이름}}}}님, {{{{회차}}}} 확정 안내
본문:
{{{{이름}}}}님, {{{{회차}}}} 참가가 확정되었습니다.{extra}

## 세그먼트: 대기

제목: {{{{이름}}}}님, 대기 안내
본문:
{{{{이름}}}}님, 대기로 등록되었습니다.

## 꼬리말

운영팀 드림
"""

ROWS = [
    ["이메일", "이름", "세그먼트", "회차", "수신동의"],
    ["a@example.com", "가나", "확정", "1회차", "Y"],
    ["b@example.com", "다라", "대기", "1회차", "Y"],
    ["bad-email", "마바", "확정", "1회차", "Y"],
    ["c@example.com", "", "확정", "1회차", "Y"],
    ["a@example.com", "가나2", "확정", "1회차", "Y"],
    ["d@example.com", "사아", "VIP", "1회차", "Y"],
    ["e@example.com", "자차", "확정", "", "Y"],
    ["f@example.com", "카타", "확정", "2회차", ""],
]


class MailCampaignTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name) / "camp"
        self.dir.mkdir()
        self.log = Path(self.tmp.name) / "gws.log"
        self.env = dict(os.environ)
        self.env.update({
            "MAIL_CAMPAIGN_GWS": f"{sys.executable} {FAKE}",
            "FAKE_GWS_LOG": str(self.log),
            "FAKE_GWS_STATE": str(Path(self.tmp.name) / "state.json"),
            "XDG_STATE_HOME": str(Path(self.tmp.name) / "xdg"),
            "MAIL_CAMPAIGN_NOW": "2026-10-29T10:00:00",
        })
        self.write(kind="안내")

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, kind="안내", extra="", cap=400, rows=ROWS):
        (self.dir / "campaign.md").write_text(CAMPAIGN.format(kind=kind, extra=extra, cap=cap), encoding="utf-8")
        with (self.dir / "roster.csv").open("w", encoding="utf-8-sig", newline="") as f:
            csv.writer(f).writerows(rows)

    def run_cmd(self, *args, env=None):
        p = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True,
                           env=env or self.env)
        return p.returncode, p.stdout + p.stderr

    def sheet(self):
        with (self.dir / "roster.csv").open(encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))

    def calls(self):
        if not self.log.exists():
            return []
        return [json.loads(l) for l in self.log.read_text().splitlines()]

    def token(self, *extra):
        rc, out = self.run_cmd("plan", str(self.dir), *extra)
        self.assertEqual(rc, 0, out)
        return out.split("승인 토큰: ")[1].split()[0]

    def test_check_holds_and_status_columns(self):
        rc, out = self.run_cmd("check", str(self.dir))
        self.assertEqual(rc, 0, out)
        rows = self.sheet()
        self.assertIn("발송 상태", rows[0])
        reasons = {r["이메일"] + "|" + r["이름"]: (r["발송 상태"], r["보류 사유"]) for r in rows}
        self.assertEqual(reasons["bad-email|마바"], ("보류", "이메일 형식(bad-email)"))
        self.assertEqual(reasons["c@example.com|"], ("보류", "이름 빈칸"))
        self.assertEqual(reasons["a@example.com|가나2"][1], "중복(행 2과 같은 주소)")
        self.assertEqual(reasons["d@example.com|사아"][1], "문구 없는 세그먼트(VIP)")
        self.assertEqual(reasons["e@example.com|자차"][1], "빈 칸(회차)")
        self.assertEqual(reasons["a@example.com|가나"][0], "")
        self.assertIn("보낼 대상 3행", out)
        self.assertEqual(self.calls(), [], "CSV check 는 gws 를 부르지 않는다")

    def test_other_segment_variables_do_not_hold(self):
        # '대기' 세그먼트는 {{회차}} 를 쓰지 않으므로 회차가 비어도 보류가 아니다
        rows = [ROWS[0], ["w@example.com", "대기자", "대기", "", "Y"], ["x@example.com", "확정자", "확정", "", "Y"]]
        self.write(rows=rows)
        rc, out = self.run_cmd("check", str(self.dir))
        st = {r["이메일"]: (r["발송 상태"], r["보류 사유"]) for r in self.sheet()}
        self.assertEqual(st["w@example.com"], ("", ""))
        self.assertEqual(st["x@example.com"], ("보류", "빈 칸(회차)"))

    def test_explicit_skip_wins_over_duplicate(self):
        self.run_cmd("check", str(self.dir))
        rows = self.sheet()
        header = list(rows[0].keys())
        for r in rows:
            if r["이름"] == "가나2":
                r["발송 상태"] = "제외"
                r["보류 사유"] = ""
        with (self.dir / "roster.csv").open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=header)
            w.writeheader()
            w.writerows(rows)
        rc, out = self.run_cmd("check", str(self.dir))
        dup = [r for r in self.sheet() if r["이름"] == "가나2"][0]
        self.assertEqual((dup["발송 상태"], dup["보류 사유"]), ("제외", ""))
        self.assertIn("제외", out)

    def test_test_send_single_segment(self):
        rc, out = self.run_cmd("test", str(self.dir), "--segment", "대기")
        self.assertEqual(rc, 0, out)
        sends = [c for c in self.calls() if c[:2] == ["gmail", "+send"]]
        self.assertEqual(len(sends), 1)
        self.assertIn("대기", sends[0][sends[0].index("--subject") + 1])
        rc, out = self.run_cmd("test", str(self.dir), "--segment", "없는것")
        self.assertEqual(rc, 1)

    def test_ad_signal_blocks_transactional(self):
        self.write(kind="안내", extra="\n지금 10% 할인 쿠폰도 드려요.")
        rc, out = self.run_cmd("check", str(self.dir))
        self.assertEqual(rc, 2)
        self.assertIn("광고성 신호", out)
        rc, out = self.run_cmd("plan", str(self.dir))
        self.assertEqual(rc, 2)
        self.assertNotIn("승인 토큰", out)

    def test_ad_campaign_prefix_footer_consent_and_night(self):
        self.write(kind="광고", extra="\n지금 10% 할인 쿠폰도 드려요.")
        rc, out = self.run_cmd("preview", str(self.dir))
        self.assertEqual(rc, 0, out)
        self.assertIn("제목: (광고) 가나님", out)
        self.assertIn("수신거부: '수신거부'라고 답장", out)
        self.run_cmd("check", str(self.dir))
        f = [r for r in self.sheet() if r["이메일"] == "f@example.com"][0]
        self.assertEqual(f["보류 사유"], "수신동의 없음")
        night = dict(self.env, MAIL_CAMPAIGN_NOW="2026-10-29T21:30:00")
        rc, out = self.run_cmd("plan", str(self.dir), env=night)
        self.assertEqual(rc, 2)
        self.assertIn("21~08시", out)

    def test_send_requires_token_and_is_idempotent(self):
        rc, out = self.run_cmd("send", str(self.dir), "--confirm", "WRONG")
        self.assertEqual(rc, 2)
        self.assertFalse([c for c in self.calls() if c[:2] == ["gmail", "+send"]])
        tok = self.token()
        rc, out = self.run_cmd("send", str(self.dir), "--confirm", tok)
        self.assertEqual(rc, 0, out)
        sends = [c for c in self.calls() if c[:2] == ["gmail", "+send"]]
        self.assertEqual(len(sends), 3)
        sent = [r for r in self.sheet() if r["발송 상태"] == "보냄"]
        self.assertEqual(len(sent), 3)
        self.assertTrue(all(r["messageId"] and r["threadId"] and r["발송 시각"] for r in sent))
        # 재실행: 보낼 것이 없다
        rc, out = self.run_cmd("plan", str(self.dir))
        self.assertIn("보낼 행이 없습니다", out)

    def test_journal_repairs_sheet_after_lost_write(self):
        tok = self.token()
        self.run_cmd("send", str(self.dir), "--confirm", tok)
        # 시트 기록이 날아간 상황을 흉내: 상태 칸을 지운다
        rows = self.sheet()
        header = list(rows[0].keys())
        for r in rows:
            r["발송 상태"] = ""
            r["messageId"] = ""
        with (self.dir / "roster.csv").open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=header)
            w.writeheader()
            w.writerows(rows)
        before = len([c for c in self.calls() if c[:2] == ["gmail", "+send"]])
        rc, out = self.run_cmd("plan", str(self.dir))
        self.assertIn("보낼 행이 없습니다", out)
        self.assertEqual(len([r for r in self.sheet() if r["발송 상태"] == "보냄"]), 3)
        self.assertEqual(before, len([c for c in self.calls() if c[:2] == ["gmail", "+send"]]))

    def test_token_invalidated_by_copy_change(self):
        tok = self.token()
        self.write(kind="안내", extra="\n장소가 바뀌었습니다.")
        rc, out = self.run_cmd("send", str(self.dir), "--confirm", tok)
        self.assertEqual(rc, 2)
        self.assertIn("승인 토큰이 맞지 않습니다", out)

    def test_limit_and_daily_cap(self):
        self.write(cap=2)
        rc, out = self.run_cmd("plan", str(self.dir))
        self.assertEqual(rc, 2)
        self.assertIn("일일 상한", out)
        tok = self.token("--limit", "2")
        rc, out = self.run_cmd("send", str(self.dir), "--confirm", tok, "--limit", "2")
        self.assertEqual(rc, 0, out)
        self.assertEqual(len([r for r in self.sheet() if r["발송 상태"] == "보냄"]), 2)

    def test_definite_error_vs_ambiguous(self):
        env = dict(self.env, FAKE_GWS_FAIL_TO="a@example.com", FAKE_GWS_CRASH_TO="b@example.com")
        rc, out = self.run_cmd("plan", str(self.dir), env=env)
        tok = out.split("승인 토큰: ")[1].split()[0]
        rc, out = self.run_cmd("send", str(self.dir), "--confirm", tok, env=env)
        st = {r["이메일"]: r["발송 상태"] for r in self.sheet() if r["이름"] in ("가나", "다라", "카타")}
        self.assertEqual(st["a@example.com"], "오류")
        self.assertEqual(st["b@example.com"], "확인 필요")
        self.assertEqual(st["f@example.com"], "보냄")
        # 확인 필요 행은 자동 재시도하지 않는다
        rc, out = self.run_cmd("plan", str(self.dir))
        self.assertIn("보낼 대상 1행", out)  # 오류 행만 다시 대상

    def test_three_consecutive_failures_stop(self):
        rows = [ROWS[0]] + [[f"x{i}@example.com", f"n{i}", "확정", "1회차", "Y"] for i in range(5)]
        self.write(rows=rows)
        env = dict(self.env, FAKE_GWS_FAIL_TO=",".join(f"x{i}@example.com" for i in range(5)))
        rc, out = self.run_cmd("plan", str(self.dir), env=env)
        tok = out.split("승인 토큰: ")[1].split()[0]
        rc, out = self.run_cmd("send", str(self.dir), "--confirm", tok, env=env)
        self.assertEqual(rc, 3)
        self.assertIn("연속 3건", out)
        self.assertEqual(len([c for c in self.calls() if c[:2] == ["gmail", "+send"]]), 3)

    def test_draft_then_send_uses_draft_and_detects_stale(self):
        rc, out = self.run_cmd("draft", str(self.dir))
        self.assertEqual(rc, 0, out)
        self.assertEqual(len([r for r in self.sheet() if r["발송 상태"] == "초안"]), 3)
        rc, out = self.run_cmd("draft", str(self.dir))
        self.assertIn("초안 0통", out)
        self.write(kind="안내", extra="\n시간이 바뀌었습니다.")
        rc, out = self.run_cmd("plan", str(self.dir))
        self.assertEqual(rc, 2)
        self.assertIn("draft --redo", out)
        self.run_cmd("draft", str(self.dir), "--redo")
        tok = self.token()
        rc, out = self.run_cmd("send", str(self.dir), "--confirm", tok)
        self.assertEqual(rc, 0, out)
        self.assertEqual(len([c for c in self.calls() if c[:4] == ["gmail", "users", "drafts", "send"]]), 3)

    def test_test_send_goes_to_me_one_per_segment(self):
        rc, out = self.run_cmd("test", str(self.dir))
        self.assertEqual(rc, 0, out)
        sends = [c for c in self.calls() if c[:2] == ["gmail", "+send"]]
        self.assertEqual(len(sends), 2)  # 세그먼트 2개
        self.assertTrue(all(c[c.index("--to") + 1] == "me@example.com" for c in sends))
        self.assertTrue(all(c[c.index("--subject") + 1].startswith("[테스트] ") for c in sends))
        self.assertFalse([r for r in self.sheet() if r.get("발송 상태") == "보냄"])

    def test_replies_and_classify(self):
        tok = self.token()
        self.run_cmd("send", str(self.dir), "--confirm", tok)
        rc, out = self.run_cmd("replies", str(self.dir))
        self.assertEqual(rc, 0, out)
        data = json.loads((self.dir / ".mail-campaign" / "replies.json").read_text())
        self.assertTrue(data["items"])
        self.assertTrue(all(r["messageId"] != "orig" for it in data["items"] for r in it["replies"]))
        first = data["items"][0]
        cls = Path(self.tmp.name) / "cls.json"
        cls.write_text(json.dumps([{"row": first["row"], "class": "확인"},
                                   {"row": 3, "class": "수신거부"}], ensure_ascii=False))
        rc, out = self.run_cmd("classify", str(self.dir), "--file", str(cls))
        self.assertEqual(rc, 0, out)
        rows = self.sheet()
        self.assertEqual(rows[first["row"] - 2]["답장 분류"], "확인")
        self.assertTrue(rows[1]["수신동의"].startswith("거부("))
        bad = Path(self.tmp.name) / "bad.json"
        bad.write_text(json.dumps([{"row": 2, "class": "아무거나"}], ensure_ascii=False))
        rc, out = self.run_cmd("classify", str(self.dir), "--file", str(bad))
        self.assertEqual(rc, 1)


class ProfileBinGwsTest(MailCampaignTest):
    """gws 가 Hermes 프로필 bin 에만 있고 PATH 가 최소일 때도 브리지 경로로 doctor·send 가 돈다."""

    def setUp(self):
        super().setUp()
        home = Path(self.tmp.name) / "hermes"
        (home / "bin").mkdir(parents=True)
        scripts = home / "skills" / "productivity" / "google-workspace" / "scripts"
        scripts.mkdir(parents=True)
        (home / "google_token.json").write_text("{}")
        gws = home / "bin" / "gws"
        gws.write_text(f"#!{sys.executable}\n" + FAKE.read_text())
        gws.chmod(0o755)
        # 실제 gws_bridge.py 처럼 PATH 에서만 gws 를 찾는다
        (scripts / "gws_bridge.py").write_text(
            "import subprocess, sys\nsys.exit(subprocess.run(['gws'] + sys.argv[1:]).returncode)\n")
        self.env.pop("MAIL_CAMPAIGN_GWS")
        # 이 장비의 다른 gws 를 찾지 않도록 HOME 을 비운다. Python 3.11+ 은 실제 Hermes venv 를 빌린다.
        fake_home = Path(self.tmp.name) / "home"
        (fake_home / ".hermes").mkdir(parents=True)
        real = Path.home() / ".hermes" / "installs"
        if real.exists():
            (fake_home / ".hermes" / "installs").symlink_to(real)
        self.env.update(HERMES_HOME=str(home), PATH="/usr/bin:/bin", HOME=str(fake_home))
        self.env.pop("GOOGLE_APPLICATION_CREDENTIALS", None)

    def test_doctor_and_send_with_minimal_path(self):
        rc, out = self.run_cmd("doctor")
        self.assertEqual(rc, 0, out)
        self.assertIn("/usr/bin/env PATH=", out)
        self.assertIn("me@example.com", out)
        tok = self.token()
        rc, out = self.run_cmd("send", str(self.dir), "--confirm", tok)
        self.assertEqual(rc, 0, out)
        self.assertIn("=== send 시작", out)
        self.assertEqual(len([r for r in self.sheet() if r["발송 상태"] == "보냄"]), 3)

    def test_doctor_fails_without_gws(self):
        (Path(self.env["HERMES_HOME"]) / "bin" / "gws").unlink()
        rc, out = self.run_cmd("doctor")
        self.assertNotEqual(rc, 0, out)
        self.assertIn("gws CLI 를 찾지 못했습니다", out)


if __name__ == "__main__":
    unittest.main()
