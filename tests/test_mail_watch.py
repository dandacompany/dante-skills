"""mail-watch 오프라인 테스트(가짜 gws)."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "mail-watch" / "scripts" / "mail_watch.py"

FAKE = r'''
import json, os, sys
args = sys.argv[1:]
box = json.load(open(os.environ["FAKE_BOX"]))
if os.environ.get("FAKE_FAIL"):
    print(json.dumps({"error": {"code": 401, "message": "auth"}})); sys.exit(1)
p = json.loads(args[args.index("--params") + 1]) if "--params" in args else {}
if args[:4] == ["gmail", "users", "messages", "list"]:
    print(json.dumps({"messages": [{"id": m["id"], "threadId": m["id"]} for m in box]})); sys.exit(0)
if args[:4] == ["gmail", "users", "messages", "get"]:
    m = next(x for x in box if x["id"] == p["id"])
    parts = [{"filename": f, "mimeType": "application/octet-stream", "body": {"attachmentId": "a-" + f, "size": 3}}
             for f in m["files"]]
    print(json.dumps({"id": m["id"], "threadId": m["id"], "snippet": "본문",
                      "payload": {"headers": [{"name": "From", "value": "x@example.org"},
                                              {"name": "Subject", "value": m["id"]}], "parts": parts}}))
    sys.exit(0)
print(json.dumps({"error": {"code": 400, "message": "unknown"}})); sys.exit(1)
'''


class MailWatchTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        t = Path(self.tmp.name)
        (t / "fake.py").write_text(FAKE)
        self.box = t / "box.json"
        self.set_box([{"id": "old", "files": ["a.hwpx"]}])
        self.env = dict(os.environ, MAIL_WATCH_GWS=f"{sys.executable} {t / 'fake.py'}", FAKE_BOX=str(self.box),
                        MAIL_WATCH_HOME=str(t / "home"), HERMES_HOME=str(t / "hermes"))

    def tearDown(self):
        self.tmp.cleanup()

    def set_box(self, items):
        self.box.write_text(json.dumps(items))

    def run_cmd(self, *args, env=None):
        p = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, env=env or self.env)
        return p.returncode, p.stdout + p.stderr

    def last(self, out):
        return json.loads(out.strip().splitlines()[-1])

    def test_baseline_wake_ack_and_extension_filter(self):
        rc, out = self.run_cmd("init", "w", "--query", "in:inbox", "--attach-ext", "hwp,hwpx")
        self.assertEqual(rc, 0, out)
        self.assertFalse(self.last(self.run_cmd("check", "w")[1])["wakeAgent"])  # 기존 메일은 본 것으로
        self.set_box([{"id": "old", "files": ["a.hwpx"]}, {"id": "new", "files": ["b.HWPX"]},
                      {"id": "pdf", "files": ["c.pdf"]}])
        res = self.last(self.run_cmd("check", "w")[1])
        self.assertTrue(res["wakeAgent"])
        self.assertEqual([m["id"] for m in res["context"]["messages"]], ["new"])
        self.run_cmd("ack", "w", "new")
        self.assertFalse(self.last(self.run_cmd("check", "w")[1])["wakeAgent"])

    def test_unacked_rewake_then_give_up(self):
        self.run_cmd("init", "w", "--query", "in:inbox", "--max-wakes", "2")
        self.set_box([{"id": "old", "files": []}, {"id": "n1", "files": []}])
        r1 = self.last(self.run_cmd("check", "w")[1])
        r2 = self.last(self.run_cmd("check", "w")[1])
        rc, out = self.run_cmd("check", "w")
        self.assertEqual(r1["context"]["messages"][0]["wake"], 1)
        self.assertEqual(r2["context"]["messages"][0]["wake"], 2)
        self.assertFalse(self.last(out)["wakeAgent"])
        self.assertIn("넘긴 메일 1통", out)

    def test_errors_wake_once_at_three(self):
        self.run_cmd("init", "w", "--query", "in:inbox")
        env = dict(self.env, FAKE_FAIL="1")
        wakes = [self.last(self.run_cmd("check", "w", env=env)[1])["wakeAgent"] for _ in range(4)]
        self.assertEqual(wakes, [False, False, True, False])

    def test_profile_scopes_state_and_wrapper(self):
        env = dict(self.env)
        env.pop("MAIL_WATCH_HOME")
        self.run_cmd("--profile", "bot-a", "init", "w", "--query", "in:inbox", env=env)
        rc, out = self.run_cmd("--profile", "bot-a", "install", "w", env=env)
        self.assertEqual(rc, 0, out)
        prof = Path(self.env["HERMES_HOME"]) / "profiles" / "bot-a"
        self.assertTrue((prof / "mail-watch" / "w" / "watch.json").exists())
        self.assertTrue((prof / "scripts" / "mail-watch-w.py").exists())
        self.assertIn("hermes -p bot-a cron create", out)

    def test_missing_watch_is_silent(self):
        rc, out = self.run_cmd("check", "nope")
        self.assertEqual(rc, 0)
        self.assertFalse(self.last(out)["wakeAgent"])

    def test_install_writes_wrapper_under_hermes_scripts(self):
        self.run_cmd("init", "w", "--query", "in:inbox")
        rc, out = self.run_cmd("install", "w", "--skill", "official-reply")
        self.assertEqual(rc, 0, out)
        wrapper = Path(self.env["HERMES_HOME"]) / "scripts" / "mail-watch-w.py"
        self.assertTrue(wrapper.exists())
        self.assertIn("--script mail-watch-w.py --skill official-reply", out)
        p = subprocess.run([sys.executable, str(wrapper)], capture_output=True, text=True, env=self.env)
        self.assertFalse(self.last(p.stdout)["wakeAgent"])


if __name__ == "__main__":
    unittest.main()
