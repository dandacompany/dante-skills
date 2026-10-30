#!/usr/bin/env python3
"""rhwp 저장소의 Claude 스킬 본문을 받아 이 통합 스킬의 references/ 로 다시 만든다.

사용: build_references.py [커밋 SHA]   (생략하면 main 의 최신 커밋)

상류 스킬은 rhwp 저장소 안에서 쓰도록 쓰였다(cargo 빌드, 상대 링크). 여기서는
설치된 `rhwp` 바이너리를 쓰고, 상대 링크는 그 커밋에 고정한 GitHub 주소로 바꾼다.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

REPO = "edwardkim/rhwp"
# 상류 스킬 이름 → 참조 파일 이름
SKILLS = {
    "rhwp-doc-triage": "doc-triage",
    "rhwp-explore": "explore",
    "rhwp-cli": "cli",
    "rhwp-form-fill": "form-fill",
    "rhwp-table-exchange": "table-exchange",
    "rhwp-safe-edit": "safe-edit",
    "rhwp-security-sweep": "security-sweep",
    "rhwp-bulk-pipeline": "bulk-pipeline",
    "rhwp-mcp-session": "mcp-session",
    "rhwp-recipes": "recipes",
}
OUT = Path(__file__).resolve().parent.parent / "references"
REPO_ROOT_REL = "/".join([".."] * 3) + "/"


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "rhwp-skill-builder"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def latest_sha() -> str:
    return json.loads(fetch(f"https://api.github.com/repos/{REPO}/commits/main"))["sha"]


def drop_sections(body: str, heading: re.Pattern) -> str:
    out, skip = [], False
    for line in body.splitlines():
        if line.startswith("## "):
            skip = bool(heading.match(line[3:]))
        if not skip:
            out.append(line)
    return "\n".join(out)


def convert(skill: str, text: str, sha: str) -> str:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    front, body = (m.group(1), text[m.end():]) if m else ("", text)
    desc = re.search(r"^description:\s*(.*)$", front, re.M)
    blob = f"https://github.com/{REPO}/blob/{sha}"
    here = f"{blob}/.claude/skills/{skill}"

    # 빌드 안내는 SKILL.md 의 설치 절이 대신한다
    body = drop_sections(body, re.compile(r"바이너리"))
    lines = []
    for line in body.splitlines():
        if re.match(r"^\s*cargo build", line) or "Docker 는 WASM 전용" in line:
            continue
        lines.append(line)
    body = "\n".join(lines)
    body = body.replace("./target/release/rhwp", "rhwp")
    body = body.replace("cargo run --quiet --bin rhwp --", "rhwp")

    # 상대 링크 → 커밋 고정 GitHub 링크, 형제 스킬 링크 → 이 폴더의 참조 파일
    def link(mm: re.Match) -> str:
        target = mm.group(1)
        if target.startswith(("http://", "https://", "#")):
            return mm.group(0)
        sib = re.match(r"\.\./(rhwp-[\w-]+)/SKILL\.md(#.*)?$", target)
        if sib and sib.group(1) in SKILLS:
            return f"]({SKILLS[sib.group(1)]}.md{sib.group(2) or ''})"
        if target.startswith(REPO_ROOT_REL):  # 스킬 폴더에서 저장소 루트까지 세 단계 위
            return f"]({blob}/{target[len(REPO_ROOT_REL):]})"
        if target.startswith("../"):
            return f"]({blob}/.claude/skills/{target[3:]})"
        return f"]({here}/{target.lstrip('./')})"

    body = re.sub(r"\]\(([^)\s]+)\)", link, body)

    # 본문에 나오는 형제 스킬 이름에 참조 파일을 붙인다 (링크·경로 안은 제외)
    def sibling(mm: re.Match) -> str:
        name = mm.group(2)
        return f"{mm.group(1)}{name}` → [{SKILLS[name]}.md]({SKILLS[name]}.md)"

    names = "|".join(re.escape(k) for k in SKILLS if k != skill)
    body = re.sub(rf"(`)({names})`(?! →)", sibling, body)

    head = [
        f"<!-- 자동 생성: scripts/build_references.py · 원본 {here}/SKILL.md · MIT (c) Edward Kim. 직접 고치지 않는다. -->",
        "",
        f"> **상류 스킬 `{skill}`** — {desc.group(1).strip() if desc else ''}",
        ">",
        f"> 본문의 `references/`·`examples/`·`fixtures/`·`NN_*.md` 는 상류 저장소 경로다: <{here.replace('/blob/', '/tree/')}>",
        "",
        "",
    ]
    return "\n".join(head) + body.strip() + "\n"


def main() -> None:
    sha = sys.argv[1] if len(sys.argv) > 1 else latest_sha()
    OUT.mkdir(exist_ok=True)
    for skill, name in SKILLS.items():
        raw = fetch(f"https://raw.githubusercontent.com/{REPO}/{sha}/.claude/skills/{skill}/SKILL.md")
        (OUT / f"{name}.md").write_text(convert(skill, raw, sha), encoding="utf-8")
        print(f"{name}.md  ← {skill}")
    (OUT / "UPSTREAM").write_text(f"{REPO}@{sha}\n", encoding="utf-8")
    print(f"upstream {REPO}@{sha}")


if __name__ == "__main__":
    main()
