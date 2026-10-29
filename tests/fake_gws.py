#!/usr/bin/env python3
"""mail-campaign 테스트용 가짜 gws. 호출을 FAKE_GWS_LOG 에 남기고 정해진 JSON 을 돌려준다."""
import json
import os
import sys

args = sys.argv[1:]
log = os.environ.get("FAKE_GWS_LOG")
state_path = os.environ.get("FAKE_GWS_STATE")
state = {"n": 0}
if state_path and os.path.exists(state_path):
    state = json.load(open(state_path))
state["n"] += 1
if state_path:
    json.dump(state, open(state_path, "w"))
if log:
    with open(log, "a") as f:
        f.write(json.dumps(args, ensure_ascii=False) + "\n")


def arg(name):
    return args[args.index(name) + 1] if name in args else None


def out(obj, rc=0):
    print(json.dumps(obj, ensure_ascii=False))
    sys.exit(rc)


fail_to = [x for x in os.environ.get("FAKE_GWS_FAIL_TO", "").split(",") if x]
crash_to = [x for x in os.environ.get("FAKE_GWS_CRASH_TO", "").split(",") if x]
n = state["n"]

if args[:3] == ["gmail", "users", "getProfile"]:
    out({"emailAddress": "me@example.com"})
if args[:2] == ["gmail", "+send"]:
    to = arg("--to")
    if to in fail_to:
        out({"error": {"code": 400, "message": "Invalid To header", "reason": "badRequest"}}, 1)
    if to in crash_to:
        sys.stderr.write("connection reset\n")
        sys.exit(1)
    if "--draft" in args:
        out({"id": f"d{n}", "message": {"id": f"dm{n}", "threadId": f"dt{n}"}})
    out({"id": f"m{n}", "threadId": f"t{n}", "labelIds": ["SENT"]})
if args[:4] == ["gmail", "users", "drafts", "send"]:
    body = json.loads(arg("--json"))
    out({"id": "sent-" + body["id"], "threadId": "thr-" + body["id"], "labelIds": ["SENT"]})
if args[:4] == ["gmail", "users", "drafts", "delete"]:
    out({})
if args[:4] == ["gmail", "users", "messages", "list"]:
    out({"resultSizeEstimate": 0})
if args[:4] == ["gmail", "users", "threads", "get"]:
    tid = json.loads(arg("--params"))["id"]
    msgs = [{"id": "orig", "labelIds": ["SENT"], "snippet": "원문",
             "payload": {"headers": [{"name": "From", "value": "me@example.com"}]}}]
    if not tid.endswith("x"):
        msgs.append({"id": "r" + tid, "labelIds": ["INBOX"], "snippet": "네 확인했습니다, 참석할게요",
                     "payload": {"headers": [{"name": "From", "value": "고객 <c@example.com>"},
                                             {"name": "Date", "value": "Thu, 29 Oct 2026 10:00:00 +0900"}]}})
    out({"id": tid, "messages": msgs})
out({"error": {"code": 400, "message": "fake: unknown " + " ".join(args[:4])}}, 1)
