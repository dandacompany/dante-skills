"""official-reply 테스트. 순수 함수는 항상, kordoc 이 있으면 실제 문서 경로까지."""
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "official-reply" / "scripts" / "official_reply.py"
spec = importlib.util.spec_from_file_location("official_reply", SCRIPT)
orp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(orp)


class AttachValueTest(unittest.TestCase):
    def test_single_drops_count(self):
        self.assertEqual(orp.attach_value([{"이름": "조사표", "부수": 1}]), "조사표")

    def test_one_count_item_goes_last(self):
        v = orp.attach_value([{"이름": "조사표", "부수": 1}, {"이름": "사본", "부수": 2}])
        self.assertEqual(v, "1. 사본 2부.\n2. 조사표")

    def test_no_single_count_refuses(self):
        with self.assertRaises(orp.ReplyError):
            orp.attach_value([{"이름": "사본", "부수": 2}])

    def test_end_mark_checks(self):
        orp.check_end_mark("붙임 조사표 1부. 끝.\n\n회사 대표")
        with self.assertRaises(orp.ReplyError):
            orp.check_end_mark("붙임 조사표 2부. 1부. 끝.")
        with self.assertRaises(orp.ReplyError):
            orp.check_end_mark("붙임 조사표 1부.\n\n끝.")


@unittest.skipUnless(shutil.which("kordoc"), "kordoc 없음")
class KordocFlowTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = Path(self.tmp.name)
        (self.t / "양식.md").write_text("# 조사표\n\n| 항목 | 내용 |\n|---|---|\n| 상호 |  |\n| 대표자 |  |\n",
                                       encoding="utf-8")
        subprocess.run(["kordoc", "generate", str(self.t / "양식.md"), "-o", str(self.t / "양식.hwpx"),
                        "--preset", "보고서"], capture_output=True, check=True)

    def tearDown(self):
        self.tmp.cleanup()

    def run_cmd(self, *args):
        p = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)
        return p.returncode, p.stdout + p.stderr

    def test_fill_letter_finish(self):
        w = self.t / "job"
        self.assertEqual(self.run_cmd("init", str(w), str(self.t / "양식.hwpx"))[0], 0)
        (self.t / "v.json").write_text(json.dumps({"상호": "예시상사", "대표자": "모름"}, ensure_ascii=False))
        self.assertEqual(self.run_cmd("fill", str(w), "양식.hwpx", "--json", str(self.t / "v.json"))[0], 1)
        (self.t / "v.json").write_text(json.dumps({"상호": "예시상사", "대표자": "홍길동"}, ensure_ascii=False))
        rc, out = self.run_cmd("fill", str(w), "양식.hwpx", "--json", str(self.t / "v.json"))
        self.assertEqual(rc, 0, out)
        letter = {"행정기관명": "예시상사", "수신자": "협력기관장", "제목": "자료 제출",
                  "본문": "1. 관련: 자료 제출 요청(2026. 10. 29.)\n2. 붙임과 같이 제출합니다.",
                  "붙임목록": [{"이름": "조사표", "부수": 1}, {"이름": "사본", "부수": 2}],
                  "발신명의": "예시상사 대표", "시행일": "2026. 11. 2."}
        (self.t / "l.json").write_text(json.dumps(letter, ensure_ascii=False))
        rc, out = self.run_cmd("letter", str(w), "--json", str(self.t / "l.json"))
        self.assertEqual(rc, 0, out)
        rc, out = self.run_cmd("finish", str(w))
        self.assertEqual(rc, 0, out)
        m = json.loads((w / "묶음.json").read_text(encoding="utf-8"))
        self.assertTrue((w / "회신" / m["final"]["preview"]).exists())
        self.assertEqual(m["final"]["attachments"], ["양식-작성.hwpx"])


if __name__ == "__main__":
    unittest.main()
