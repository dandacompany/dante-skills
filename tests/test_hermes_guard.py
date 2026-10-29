"""Hermes 스킬 보안 검사(skills_guard)를 community 기준으로 돌린다. Hermes 가 없는 장비에서는 건너뛴다.

허브 설치는 community 출처라 caution 판정 하나만 나와도 막힌다(mail-watch 1.0.0 이 그렇게 막혔다).
"""
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGENT = Path.home() / ".hermes" / "hermes-agent"
PYTHONS = sorted((Path.home() / ".hermes").glob("installs/*/environments/*/venv/bin/python"),
                 key=lambda p: p.stat().st_mtime, reverse=True)
SKILLS = ["mail-campaign", "mail-watch", "official-reply"]

CHECK = """
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from tools.skills_guard import scan_skill, should_allow_install
r = scan_skill(Path(sys.argv[2]), source="community")
ok, msg = should_allow_install(r)
print(msg)
sys.exit(0 if ok else 1)
"""


@unittest.skipUnless(AGENT.exists() and PYTHONS, "Hermes 없음")
class HermesGuardTest(unittest.TestCase):
    def test_community_install_allowed(self):
        for name in SKILLS:
            with self.subTest(skill=name):
                p = subprocess.run([str(PYTHONS[0]), "-I", "-c", CHECK, str(AGENT), str(ROOT / name)],
                                   capture_output=True, text=True, timeout=120)
                self.assertEqual(p.returncode, 0, p.stdout + p.stderr)


if __name__ == "__main__":
    unittest.main()
