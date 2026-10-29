"""official-reply 테스트. 순수 함수는 항상, kordoc 이 있으면 실제 문서 경로까지."""
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


@unittest.skipUnless(shutil.which("kordoc"), "kordoc 없음")
class PatchExitTwoTest(unittest.TestCase):
    """kordoc patch 가 종료 코드 2 를 내도, 결과가 고친 원고와 같으면 통과·다르면 거부."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = Path(self.tmp.name)
        letter = {"행정기관명": "예시상사", "수신자": "협력기관장", "제목": "협력 제안", "본문": "본문 첫 문단",
                  "붙임": "제안서", "발신명의": "예시상사 대표 (인)"}
        (self.t / "s.json").write_text(json.dumps(letter, ensure_ascii=False))
        subprocess.run(["kordoc", "fill", "--template", "gian", "-j", str(self.t / "s.json"), "-o",
                        str(self.t / "견본.hwpx"), "--silent"], check=True)
        # patch 만 종료 코드 2 + SKIP 문구를 덧붙이는 래퍼(결과 파일은 진짜 kordoc 이 만든다)
        (self.t / "k.py").write_text(
            "import subprocess,sys\n"
            "p=subprocess.run(['kordoc',*sys.argv[1:]])\n"
            "if sys.argv[1]=='patch':\n"
            "    print('[kordoc] ⚠️ SKIP: 개체·구역 정의·쪽 나눔이 든 문단', file=sys.stderr); sys.exit(2)\n"
            "sys.exit(p.returncode)\n")
        self.env = dict(os.environ, OFFICIAL_REPLY_KORDOC=f"{sys.executable} {self.t / 'k.py'}")

    def tearDown(self):
        self.tmp.cleanup()

    def run_cmd(self, *args):
        p = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, env=self.env)
        return p.returncode, p.stdout + p.stderr

    def test_accept_when_identical_reject_when_not(self):
        w = self.t / "job"
        self.run_cmd("init", str(w), str(self.t / "견본.hwpx"))
        self.run_cmd("sample-md", str(w), "견본.hwpx")
        md = w / "회신" / "견본-편집.md"
        md.write_text(md.read_text(encoding="utf-8").replace("협력 제안", "서류 보완 제출"), encoding="utf-8")
        rc, out = self.run_cmd("letter", str(w), "--sample", "견본.hwpx", "--md", str(md))
        self.assertEqual(rc, 0, out)
        self.assertIn("글자까지 같음", out)
        md.write_text(md.read_text(encoding="utf-8") + "\n\n원고에만 있는 문단\n", encoding="utf-8")
        # 이번에는 patch 가 견본을 그대로 내놓고(수정 미반영) 종료 코드 2 를 내는 상황을 흉내 낸다
        (self.t / "k.py").write_text(
            "import shutil,subprocess,sys\n"
            "if sys.argv[1]=='patch':\n"
            "    shutil.copyfile(sys.argv[2], sys.argv[sys.argv.index('-o')+1]); sys.exit(2)\n"
            "sys.exit(subprocess.run(['kordoc',*sys.argv[1:]]).returncode)\n")
        rc, out = self.run_cmd("letter", str(w), "--sample", "견본.hwpx", "--md", str(md))
        self.assertEqual(rc, 1, out)
        self.assertIn("문단 수를 견본과 같게", out)
        self.assertFalse((w / "회신" / "회신공문.hwpx").exists())


@unittest.skipUnless(shutil.which("kordoc"), "kordoc 없음")
class SampleAndPreviewTest(unittest.TestCase):
    """연속 공백이 든 원고도 견본에 반영되고, PNG 렌더가 안 되는 kordoc(sharp 없음)이어도 미리보기가 나온다."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = Path(self.tmp.name)
        letter = {"행정기관명": "예시상사", "수신자": "협력기관장", "제목": "협력 제안", "본문": "본문 첫 문단",
                  "붙임": "제안서", "발신명의": "예시상사 대표", "주소": "서울 강남구 테헤란로 1"}
        (self.t / "s.json").write_text(json.dumps(letter, ensure_ascii=False))
        subprocess.run(["kordoc", "fill", "--template", "gian", "-j", str(self.t / "s.json"), "-o",
                        str(self.t / "견본.hwpx"), "--silent"], check=True)
        (self.t / "k.py").write_text(
            "import subprocess,sys\n"
            "if sys.argv[1]=='render' and 'png' in sys.argv:\n"
            "    print('PNG 래스터에는 sharp가 필요합니다 (npm install sharp)', file=sys.stderr); sys.exit(1)\n"
            "sys.exit(subprocess.run(['kordoc',*sys.argv[1:]]).returncode)\n")
        self.env = dict(os.environ, OFFICIAL_REPLY_KORDOC=f"{sys.executable} {self.t / 'k.py'}")

    def tearDown(self):
        self.tmp.cleanup()

    def run_cmd(self, *args):
        p = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, env=self.env)
        return p.returncode, p.stdout + p.stderr

    def test_double_space_and_preview_fallback(self):
        w = self.t / "job"
        self.run_cmd("init", str(w), str(self.t / "견본.hwpx"))
        self.run_cmd("sample-md", str(w), "견본.hwpx")
        md = w / "회신" / "견본-편집.md"
        text = md.read_text(encoding="utf-8")
        text = text.replace("붙임 제안서 1부. 끝.", "붙임 조사표 1부.  끝.").replace("테헤란로 1", "테헤란로  99")
        md.write_text(text, encoding="utf-8")
        rc, out = self.run_cmd("letter", str(w), "--sample", "견본.hwpx", "--md", str(md))
        self.assertEqual(rc, 0, out)
        self.assertIn("연속 공백", out)
        got = orp.read_text(w / "회신" / "회신공문.hwpx")
        self.assertIn("조사표 1부. 끝.", got)
        self.assertIn("테헤란로 99", got)
        rc, out = self.run_cmd("finish", str(w))
        self.assertEqual(rc, 0, out)
        self.assertIn("SVG 로 렌더", out)
        m = json.loads((w / "묶음.json").read_text(encoding="utf-8"))
        preview = w / "회신" / m["final"]["preview"]
        self.assertTrue(preview.exists())
        if shutil.which("qlmanage") or shutil.which("rsvg-convert"):
            self.assertEqual(preview.suffix, ".png")
        self.assertFalse(list((w / "회신").glob(".preview-square*")))

    def test_square_svg_keeps_whole_page(self):
        sq = orp.square_svg('<svg viewBox="0 0 595.28 841.88" width="595.28pt" height="841.88pt"><g/></svg>')
        self.assertIn('viewBox="-123.30 0.00 841.88 841.88"', sq)
        self.assertIn('width="841.88pt" height="841.88pt"', sq)


if __name__ == "__main__":
    unittest.main()
