"""official-reply 2.x 테스트. 순수 함수는 항상, rhwp 와 실습 파일이 있으면 실제 문서 흐름까지.

실습 파일 폴더는 OFFICIAL_REPLY_FIXTURES 로 준다(공문 .hwp·양식 .hwpx·견본 .hwpx·직인 .png).
"""
import importlib.util
import json
import os
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
FIX = Path(os.environ.get("OFFICIAL_REPLY_FIXTURES", "/nonexistent"))


class PureTest(unittest.TestCase):
    def test_attach_fixed_tail_drops_last_count(self):
        self.assertEqual(orp.attach_value([{"이름": "조사표"}], "  1부.  끝."), "조사표")
        v = orp.attach_value([{"이름": "조사표", "부수": 1}, {"이름": "사본", "부수": 2}], "  1부.  끝.")
        self.assertEqual(v, "1. 사본  2부.\n2. 조사표")
        with self.assertRaises(orp.ReplyError):
            orp.attach_value([{"이름": "사본", "부수": 2}], "  1부.  끝.")

    def test_attach_free_tail_writes_counts_and_end(self):
        self.assertEqual(orp.attach_value([{"이름": "사본", "부수": 2}], ""), "사본  2부.  끝.")
        self.assertEqual(orp.attach_value([{"이름": "가"}, {"이름": "나"}], "  끝."), "1. 가  1부.\n2. 나  1부.")

    def test_end_mark(self):
        orp.check_end_mark("붙임  조사표  1부.  끝.")
        with self.assertRaises(orp.ReplyError):
            orp.check_end_mark("붙임  조사표  2부.  1부.  끝.")
        with self.assertRaises(orp.ReplyError):
            orp.check_end_mark("붙임  조사표  1부.")

    def test_style_warnings(self):
        w = orp.style_warnings("시행 2026.10.30 오후 2시, 2026년 11월 6일")
        self.assertEqual(len(w), 3)
        self.assertEqual(orp.style_warnings("2026. 10. 30. 14:00"), [])

    def test_paragraph_parsing_skips_field_instructions(self):
        xml = ('<hs:sec x="1"><hp:p id="0"><hp:run><hp:t>제목 </hp:t><hp:ctrl><hp:fieldBegin name="제목">'
               '<hp:parameters><hp:stringParam>Clickhere</hp:stringParam></hp:parameters></hp:fieldBegin></hp:ctrl>'
               '<hp:t>보완 제출</hp:t></hp:run></hp:p><hp:p id="1"><hp:run><hp:t>1. 가&amp;나</hp:t></hp:run></hp:p></hs:sec>')
        paras = orp.top_paragraphs(xml)
        self.assertEqual([orp.para_text(p) for p in paras], ["제목 보완 제출", "1. 가&나"])

    def test_body_region(self):
        paras = [{"index": 0, "text": "제목  x", "fields": ["제목"]}, {"index": 1, "text": "", "fields": []},
                 {"index": 2, "text": "1. 가", "fields": []}, {"index": 3, "text": "2. 나", "fields": []},
                 {"index": 4, "text": "붙임  y  1부.  끝.", "fields": ["붙임"]}]
        self.assertEqual([p["index"] for p in orp.body_region(paras)], [2, 3])


@unittest.skipUnless(shutil.which("rhwp") and (FIX / "회사공문_견본.hwpx").exists(), "rhwp 또는 실습 파일 없음")
class RhwpFlowTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def run_cmd(self, *args):
        p = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True)
        return p.returncode, p.stdout + p.stderr

    def test_full_flow(self):
        w = self.t / "job"
        rc, out = self.run_cmd("init", w, FIX / "공문_서류보완요청.hwp", FIX / "붙임_보완서류양식.hwpx")
        self.assertEqual(rc, 0, out)
        rc, out = self.run_cmd("fields", w, "붙임_보완서류양식.hwpx")
        self.assertEqual(rc, 0, out)
        values = json.loads((w / "회신" / "붙임_보완서류양식.값.json").read_text(encoding="utf-8"))
        self.assertEqual(len(values), 12)
        values = {k: "모름" for k in values}
        (self.t / "v.json").write_text(json.dumps(values, ensure_ascii=False), encoding="utf-8")
        self.assertEqual(self.run_cmd("fill", w, "붙임_보완서류양식.hwpx", "--json", self.t / "v.json")[0], 1)
        values = {k: f"값{i}" for i, k in enumerate(values)}
        (self.t / "v.json").write_text(json.dumps(values, ensure_ascii=False), encoding="utf-8")
        rc, out = self.run_cmd("fill", w, "붙임_보완서류양식.hwpx", "--json", self.t / "v.json")
        self.assertEqual(rc, 0, out)
        self.assertTrue((w / "회신" / "붙임_보완서류양식-작성.hwp").exists())

        body = ["1. 관련: 시험 공문(2026. 10. 30.)", "2. 붙임과 같이 제출합니다."]
        letter = {"fields": {"수신자": "시험기관장", "제목": "보완 제출", "시행일": "2026. 10. 31."},
                  "본문": body, "붙임목록": [{"이름": "보완서류 양식", "부수": 1}]}
        (self.t / "l.json").write_text(json.dumps(letter, ensure_ascii=False), encoding="utf-8")
        rc, out = self.run_cmd("letter", w, "--sample", FIX / "회사공문_견본.hwpx", "--json", self.t / "l.json")
        self.assertEqual(rc, 0, out)
        target = w / "회신" / "회신공문.hwp"
        got = [p["text"] for p in orp.body_region(orp.read_paragraphs(target))]
        self.assertEqual(got, body)
        fields = {f["name"]: f["value"] for f in orp.doc_fields(target)}
        self.assertEqual(fields["경유"], " ")  # 빈 누름틀 안내문 대신 공백
        self.assertIn("시행번호", out)  # 견본 값이 남은 칸 경고

        rc, out = self.run_cmd("finish", w, "--seal", FIX / "직인_실습용.png")
        self.assertEqual(rc, 0, out)
        m = json.loads((w / "묶음.json").read_text(encoding="utf-8"))
        self.assertEqual(m["final"]["letter"], "회신공문-직인.hwp")
        self.assertTrue((w / "회신" / m["final"]["preview"][0]).exists())
        self.assertEqual(m["final"]["attachments"], ["붙임_보완서류양식-작성.hwp"])
        self.assertGreater(m["final"]["sanitized"]["회신공문-직인.hwp"], 0)

    def test_unknown_field_refused(self):
        w = self.t / "job"
        self.run_cmd("init", w, FIX / "공문_서류보완요청.hwp")
        (self.t / "l.json").write_text(json.dumps({"fields": {"없는칸": "x"}}, ensure_ascii=False), encoding="utf-8")
        rc, out = self.run_cmd("letter", w, "--sample", FIX / "회사공문_견본.hwpx", "--json", self.t / "l.json")
        self.assertEqual(rc, 1, out)
        self.assertIn("없는칸", out)


if __name__ == "__main__":
    unittest.main()
