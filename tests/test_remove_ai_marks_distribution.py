from __future__ import annotations

import importlib.util
import io
import re
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = REPO_ROOT / "remove-ai-marks"
SCRIPTS_ROOT = SKILL_ROOT / "scripts"
HERMES_GUARD = Path.home() / ".hermes/hermes-agent/tools/skills_guard.py"
sys.path.insert(0, str(SCRIPTS_ROOT))

from container_meta import clean_docx, clean_pdf  # noqa: E402
from image_meta import PNG_SIG, inspect_image, inspect_jpeg, strip_jpeg, strip_png  # noqa: E402
from text_unicode import clean_text  # noqa: E402


class RemoveAiMarksDistributionTests(unittest.TestCase):
    def test_community_distribution_has_no_guard_findings(self) -> None:
        if not HERMES_GUARD.is_file():
            self.skipTest("Hermes skills guard is not installed")

        spec = importlib.util.spec_from_file_location("skills_guard", HERMES_GUARD)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        result = module.scan_skill(SKILL_ROOT, source="community")
        details = [
            f"{item.pattern_id}: {item.file}:{item.line}"
            for item in result.findings
        ]
        self.assertEqual("safe", result.verdict, "\n".join(details))
        self.assertEqual([], result.findings, "\n".join(details))

    def test_distribution_has_no_runtime_network_or_process_bootstrap(self) -> None:
        patterns = {
            "environment access": re.compile(r"os[.]environ"),
            "network client": re.compile(
                r"(?:urllib[.]request|requests[.]|httpx[.]|socket[.])"
            ),
            "process execution": re.compile(r"subprocess[.](?:run|call|Popen|check_output)[(]"),
            "repository clone": re.compile(r"git\s+clone\s+", re.IGNORECASE),
            "hardcoded IP port": re.compile(r"\d{1,3}(?:[.]\d{1,3}){3}:\d{2,5}"),
        }
        findings: list[str] = []
        for path in SKILL_ROOT.rglob("*"):
            if path.suffix.lower() not in {".md", ".py", ".sh", ".txt"}:
                continue
            text = path.read_text(encoding="utf-8")
            for label, pattern in patterns.items():
                if pattern.search(text):
                    findings.append(f"{label}: {path.relative_to(SKILL_ROOT)}")
        self.assertEqual([], findings, "\n".join(findings))

    def test_rewrite_helper_only_emits_an_offline_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "draft.md"
            source.write_text("Alpha fact 42.", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(SKILL_ROOT / "scripts/rewrite_text.py"),
                    str(source),
                    "--backend",
                    "print-prompt",
                    "--strength",
                    "paraphrase",
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
            source_after = source.read_text(encoding="utf-8")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Alpha fact 42.", result.stdout)
        self.assertIn("offline-prompt-only", result.stderr)
        self.assertEqual("Alpha fact 42.", source_after)

    def test_skill_manifest_mentions_every_runtime_module(self) -> None:
        skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        required = {
            "scripts/common.py",
            "scripts/container_meta.py",
            "scripts/image_meta.py",
            "scripts/text_unicode.py",
        }
        missing = sorted(path for path in required if path not in skill_text)
        self.assertEqual([], missing, "unpublished helper modules: " + ", ".join(missing))

    def test_truncated_png_is_rejected_without_output(self) -> None:
        data = PNG_SIG + struct.pack(">I", 100) + b"tEXt" + b"OpenAI"
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "truncated.png"
            source.write_bytes(data)
            with self.assertRaisesRegex(ValueError, "truncated PNG"):
                inspect_image(source)
            with self.assertRaisesRegex(ValueError, "truncated PNG"):
                strip_png(data)

    def test_truncated_jpeg_is_rejected_without_output(self) -> None:
        fixtures = (
            b"\xff\xd8\xff\xe1\x00\x20OpenAI",
            b"\xff\xd8\xff\xda\x00\x08abcdef",
        )
        for data in fixtures:
            with self.subTest(data=data):
                with self.assertRaisesRegex(ValueError, "truncated JPEG"):
                    inspect_jpeg(data)
                with self.assertRaisesRegex(ValueError, "truncated JPEG"):
                    strip_jpeg(data)

    def test_default_unicode_clean_preserves_joiners_and_variation_selectors(self) -> None:
        text = "family: 👨‍👩‍👧‍👦; Persian: می‌روم; plane: ✈️"
        cleaned, stats = clean_text(text)
        self.assertEqual(text, cleaned)
        self.assertEqual(0, stats["removed_count"])

    def test_pdf_with_xmp_is_inspection_only(self) -> None:
        data = b"%PDF-1.4\n<?xpacket begin='x'?><x:xmpmeta>AI</x:xmpmeta><?xpacket end='w'?>"
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.pdf"
            output = Path(tmp) / "cleaned.pdf"
            source.write_bytes(data)
            with self.assertRaisesRegex(ValueError, "inspection-only"):
                clean_pdf(source, output)
            self.assertFalse(output.exists())

    def test_docx_preserves_unrelated_custom_xml(self) -> None:
        source = io.BytesIO()
        with zipfile.ZipFile(source, "w") as archive:
            archive.writestr("[Content_Types].xml", "<Types/>")
            archive.writestr("word/document.xml", "<document>hello</document>")
            archive.writestr("customXml/item1.xml", "<root>business-data</root>")
        cleaned, actions = clean_docx(source.getvalue())
        with zipfile.ZipFile(io.BytesIO(cleaned)) as archive:
            self.assertIn("customXml/item1.xml", archive.namelist())
        self.assertNotIn("drop part customXml/item1.xml", actions)

    def test_markdown_inspect_reports_layer_a_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "sample.md"
            source.write_text("visible\u200btext", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS_ROOT / "inspect_file.py"),
                    "--json",
                    str(source),
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=10,
            )
        self.assertEqual(1, result.returncode, result.stderr)
        self.assertIn('"layer_a"', result.stdout)
        self.assertIn('"suspicious_total": 1', result.stdout)


if __name__ == "__main__":
    unittest.main()
