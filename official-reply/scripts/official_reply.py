#!/usr/bin/env python3
"""official-reply — 받은 공문에 대한 회신 묶음(채운 붙임 양식 + 회신 공문 + 미리보기 + Gmail 회신 초안)을 만든다.

판단(요구 사항·기한 정리, 칸에 넣을 값, 회신 문장)은 에이전트가 하고,
이 스크립트는 kordoc·gws 호출 순서와 실패 판정을 고정한다. 보내기는 하지 않는다(초안까지만).
표준 라이브러리만 쓴다.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

VERSION = "1.1.0"
DOC_EXT = {".hwp", ".hwpx", ".pdf", ".docx", ".xlsx"}


class ReplyError(Exception):
    pass


# ── 실행기 ─────────────────────────────────────────────────────────────
def kordoc_cmd() -> list[str]:
    env = os.environ.get("OFFICIAL_REPLY_KORDOC", "").strip()
    if env:
        return shlex.split(env)
    if shutil.which("kordoc"):
        return ["kordoc"]
    raise ReplyError("kordoc 이 없습니다. `npm i -g kordoc` 로 설치하세요(4.24.9 이상).")


def kordoc(args, check=True, timeout=300):
    p = subprocess.run(kordoc_cmd() + args, capture_output=True, text=True, timeout=timeout)
    if check and p.returncode != 0:
        raise ReplyError(f"kordoc {args[0]} 실패(종료 코드 {p.returncode}):\n{(p.stderr or p.stdout).strip()[-1500:]}")
    return p


def bridge_python(home: Path) -> str:
    """gws_bridge.py 는 datetime.UTC 를 써서 Python 3.11 이상이 필요하다."""
    if sys.version_info >= (3, 11):
        return sys.executable
    cands = []
    for root in dict.fromkeys([home, Path.home() / ".hermes"]):
        cands += sorted(root.glob("installs/*/environments/*/venv/bin/python"), key=lambda p: p.stat().st_mtime,
                        reverse=True)
    cands += [Path(p) for n in ("python3.14", "python3.13", "python3.12", "python3.11") if (p := shutil.which(n))]
    for c in cands:
        try:
            if subprocess.run([str(c), "-c", "import sys; sys.exit(sys.version_info < (3, 11))"],
                              capture_output=True, timeout=10).returncode == 0:
                return str(c)
        except (OSError, subprocess.TimeoutExpired):
            continue
    raise ReplyError("gws_bridge.py 를 실행할 Python 3.11 이상을 찾지 못했습니다.")


def gws_cmd() -> list[str]:
    env = os.environ.get("OFFICIAL_REPLY_GWS", "").strip() or os.environ.get("MAIL_WATCH_GWS", "").strip()
    if env:
        return shlex.split(env)
    home = Path(os.environ.get("HERMES_HOME", "").strip() or Path.home() / ".hermes")
    if (home / "google_token.json").exists():
        for root in (home, Path.home() / ".hermes", Path.home() / ".hermes" / "hermes-agent"):
            bridge = root / "skills" / "productivity" / "google-workspace" / "scripts" / "gws_bridge.py"
            if bridge.exists():
                return [bridge_python(home), str(bridge)]
    if shutil.which("gws"):
        return ["gws"]
    raise ReplyError("gws CLI 를 찾지 못했습니다. `npm i -g @googleworkspace/cli` 로 설치하세요.")


def parse_json_out(text: str):
    i = text.find("{")
    if i < 0:
        return None
    try:
        return json.loads(text[i:])
    except json.JSONDecodeError:
        return None


# ── 작업 폴더 ─────────────────────────────────────────────────────────
def folders(work: Path):
    return work / "받은", work / "회신"


def manifest_path(work: Path) -> Path:
    return work / "묶음.json"


def load_manifest(work: Path) -> dict:
    p = manifest_path(work)
    if not p.exists():
        raise ReplyError(f"작업 폴더가 아닙니다(묶음.json 없음): {work}  — 먼저 init")
    return json.loads(p.read_text(encoding="utf-8"))


def save_manifest(work: Path, m: dict):
    manifest_path(work).write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")


REQUEST_TEMPLATE = """# 요청 정리

> 에이전트가 받은 공문을 읽고 채운다. 확인하지 못한 칸은 「모름」으로 두고 사용자에게 묻는다.

- 보낸 기관:
- 받은 공문 제목:
- 받은 공문 문서번호·날짜:
- 회신 기한:
- 회신 방법(전자우편·시스템 업로드·우편):
- 회신 받는 곳(주소·담당자):

## 요구 사항

1.

## 채울 붙임 양식

| 파일 | 칸 수 | 모르는 칸 |
|---|---|---|

## 회신에 붙일 것

1.
"""


def cmd_init(a):
    work = Path(a.work).expanduser().resolve()
    recv, out = folders(work)
    recv.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)
    sources = [Path(f).expanduser() for f in a.files]
    meta = {}
    if a.from_mail_watch:
        d = Path(a.from_mail_watch).expanduser()
        sources += [p for p in sorted(d.iterdir()) if p.suffix.lower() in DOC_EXT]
        mj = d / "message.json"
        if mj.exists():
            meta = json.loads(mj.read_text(encoding="utf-8"))
    if not sources:
        raise ReplyError("받은 공문 파일이 없습니다(파일 경로 또는 --from-mail-watch).")
    docs = []
    for src in sources:
        if not src.exists():
            raise ReplyError(f"파일이 없습니다: {src}")
        dst = recv / src.name
        if src.resolve() != dst.resolve():
            shutil.copyfile(src, dst)
        md = recv / (src.stem + ".md")
        p = kordoc([str(dst), "-o", str(md)], check=False)
        docs.append({"file": dst.name, "markdown": md.name if md.exists() else None,
                     "read_ok": p.returncode == 0 and md.exists()})
    if not (work / "요청정리.md").exists():
        (work / "요청정리.md").write_text(REQUEST_TEMPLATE, encoding="utf-8")
    m = {"version": VERSION, "mail": meta, "received": docs, "forms": {}, "letter": None, "final": None}
    save_manifest(work, m)
    print(f"작업 폴더: {work}")
    for d in docs:
        state = "읽음" if d["read_ok"] else "읽기 실패"
        print(f"  {d['file']} → {d['markdown'] or '-'} ({state})")
    if meta:
        print(f"원래 메일: {meta.get('from')} · {meta.get('subject')} · id {meta.get('id')}")
    print("다음: 받은/*.md 를 읽고 요청정리.md 를 채운 뒤, 붙임 양식마다 `fields`.")
    return 0


def resolve_in(work: Path, name: str) -> Path:
    p = Path(name).expanduser()
    if p.exists():
        return p.resolve()
    for base in folders(work):
        if (base / name).exists():
            return (base / name).resolve()
    raise ReplyError(f"파일을 찾지 못했습니다: {name}")


def cmd_fields(a):
    work = Path(a.work).expanduser().resolve()
    m = load_manifest(work)
    form = resolve_in(work, a.form)
    p = kordoc(["fill", str(form), "--dry-run", "--silent"])
    data = parse_json_out(p.stdout) or {}
    fields = data.get("fields", [])
    _, out = folders(work)
    (out / f"{form.stem}.fields.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    labels = [f["label"] for f in fields]
    dup = sorted({x for x in labels if labels.count(x) > 1})
    empty = [f["label"] for f in fields if not str(f.get("value", "")).strip()]
    m["forms"][form.name] = {"fields": len(fields), "empty": empty, "duplicate_labels": dup}
    save_manifest(work, m)
    print(f"{form.name}: 칸 {len(fields)}개 · 빈칸 {len(empty)}개")
    for f in fields:
        v = str(f.get("value", "")).strip()
        print(f"  [{f.get('row')},{f.get('col')}] {f['label']}: {v or '(빈칸)'}")
    if dup:
        print(f"⚠ 같은 라벨이 여러 칸에 있습니다: {', '.join(dup)} — 값 JSON 에서 배열로 칸마다 따로 준다.")
    return 0


def cmd_fill(a):
    work = Path(a.work).expanduser().resolve()
    m = load_manifest(work)
    form = resolve_in(work, a.form)
    values = json.loads(Path(a.json).read_text(encoding="utf-8"))
    blanks = [k for k, v in values.items() if isinstance(v, str) and v.strip() in ("", "모름", "?")]
    if blanks:
        raise ReplyError("값이 비었거나 「모름」인 칸이 있습니다: " + ", ".join(blanks)
                         + " — 채우지 말고 사용자에게 한 번에 물은 뒤 다시 하세요.")
    dry = parse_json_out(kordoc(["fill", str(form), "-j", a.json, "--dry-run", "--silent"]).stdout) or {}
    if dry.get("unmatched"):
        raise ReplyError(f"양식에 없는 키: {dry['unmatched']} — fields 출력의 라벨 그대로 쓰세요.")
    _, out = folders(work)
    target = out / f"{form.stem}-작성{form.suffix if form.suffix == '.hwpx' else '.hwpx'}"
    kordoc(["fill", str(form), "-j", a.json, "--require-unique", "-o", str(target), "--silent"])
    after = parse_json_out(kordoc(["fill", str(target), "--dry-run", "--silent"]).stdout) or {}
    still = [f["label"] for f in after.get("fields", []) if not str(f.get("value", "")).strip()]
    m["forms"].setdefault(form.name, {})["filled"] = target.name
    m["forms"][form.name]["still_empty"] = still
    save_manifest(work, m)
    print(f"채움: {target}")
    if still:
        print(f"남은 빈칸 {len(still)}개: {', '.join(still)} — 일부러 비우는 칸인지 사용자에게 확인하세요.")
    return 0


def attach_value(items: list[dict]) -> str:
    """일반기안문(gian) 서식은 붙임 칸 뒤에 「 1부. 끝.」을 고정 글자로 붙인다(kordoc 4.24.x).
    그래서 마지막 항목은 부수 없이 넣어야 한다. 부수가 1인 항목을 마지막으로 보낸다."""
    if not items:
        raise ReplyError("붙임 목록이 비었습니다. 붙임이 없으면 일반기안문 대신 견본(patch) 경로를 쓰세요.")
    norm = [{"이름": str(i["이름"]).strip(), "부수": int(i.get("부수", 1))} for i in items]
    ones = [i for i in norm if i["부수"] == 1]
    if not ones:
        raise ReplyError("부수가 1인 붙임이 하나도 없습니다. 일반기안문 서식은 마지막 붙임을 「1부」로 고정하므로 "
                         "견본(patch) 경로를 쓰거나 한글에서 붙임 줄을 고치세요.")
    last = ones[-1]
    order = [i for i in norm if i is not last] + [last]
    if len(order) == 1:
        return last["이름"]
    lines = [f"{n}. {i['이름']} {i['부수']}부." for n, i in enumerate(order[:-1], 1)]
    lines.append(f"{len(order)}. {last['이름']}")
    return "\n".join(lines)


def norm_lines(text: str) -> list[str]:
    return [re.sub(r"\s+", " ", l).strip() for l in text.splitlines() if l.strip()]


def linebreak_paragraphs(hwpx: Path) -> int:
    """본문에 강제 줄바꿈(<hp:lineBreak/>)이 든 문단 수. kordoc patch 는 이런 문단을 고치지 못한다."""
    import zipfile
    n = 0
    with zipfile.ZipFile(hwpx) as z:
        for name in z.namelist():
            if re.fullmatch(r"Contents/section\d+\.xml", name):
                xml = z.read(name).decode("utf-8", "replace")
                n += sum(1 for p in re.findall(r"<hp:p\b.*?</hp:p>", xml, re.S) if "<hp:lineBreak/>" in p)
    return n


def read_text(path: Path) -> str:
    return kordoc([str(path)], check=True).stdout


def check_end_mark(text: str):
    line = next((l for l in text.splitlines() if l.startswith("붙임")), None)
    if line is None:
        return
    block = text[text.find(line):].split("\n\n")[0]
    if re.search(r"\d+부\.\s+1부\.", block):
        raise ReplyError(f"붙임 줄에 부수가 겹쳤습니다: {block!r}")
    if not block.rstrip().endswith("끝."):
        raise ReplyError(f"붙임 줄이 「끝.」으로 끝나지 않습니다: {block!r}")


def cmd_letter(a):
    work = Path(a.work).expanduser().resolve()
    m = load_manifest(work)
    _, out = folders(work)
    target = out / "회신공문.hwpx"
    if a.sample:
        if not a.md:
            raise ReplyError("--sample 경로는 --md(견본을 읽어 고친 마크다운)가 필요합니다. 먼저 `sample-md`.")
        sample = resolve_in(work, a.sample)
        p = kordoc(["patch", str(sample), a.md, "-o", str(target)], check=False)
        msg = (p.stderr or "") + (p.stdout or "")
        skips = [l for l in msg.splitlines() if "SKIP" in l or "잔차" in l]
        if p.returncode not in (0, 2):
            raise ReplyError(f"kordoc patch 실패:\n{msg.strip()[-1200:]}")
        if p.returncode == 2 or skips:
            # kordoc 의 「완전 일치」 문구를 믿지 않고, 결과를 다시 읽어 고친 원고와 직접 대조한다.
            got = kordoc([str(target), "--keep-layout-tables"], check=False).stdout if target.exists() else ""
            want = Path(a.md).read_text(encoding="utf-8")
            if not target.exists() or norm_lines(got) != norm_lines(want):
                target.unlink(missing_ok=True)
                raise ReplyError("견본에 반영하지 못한 수정이 있어 회신 공문을 만들지 않았습니다(kordoc patch 종료 코드 "
                                 f"{p.returncode}):\n" + "\n".join(skips)
                                 + "\n본문 문단 수를 견본과 같게 맞추거나(항목을 합치거나 나눠서), 강제 줄바꿈이 든 견본이면 "
                                 "`sample-split` 으로 문단을 나눈 뒤 다시 하세요. 안 되면 일반기안문 경로(--json)를 쓰세요.")
            print("⚠ kordoc 이 일부 문단을 건너뛰었다고 보고했지만, 결과를 다시 읽어 고친 원고와 글자까지 같음을 확인했습니다:")
            for l in skips:
                print("   " + l.strip())
        mode = "patch"
    else:
        spec = json.loads(Path(a.json).read_text(encoding="utf-8"))
        items = spec.pop("붙임목록", None)
        if items is not None:
            spec["붙임"] = attach_value(items)
        missing = [k for k in ("수신자", "제목", "본문", "발신명의") if not str(spec.get(k, "")).strip()]
        if missing:
            raise ReplyError(f"일반기안문 필수 칸이 비었습니다: {', '.join(missing)}")
        tmp = out / ".letter-fields.json"
        tmp.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
        kordoc(["fill", "--template", "gian", "-j", str(tmp), "-o", str(target), "--silent"])
        tmp.unlink(missing_ok=True)
        mode = "gian"
    check_end_mark(read_text(target))
    m["letter"] = {"file": target.name, "mode": mode}
    m["final"] = None
    save_manifest(work, m)
    print(f"회신 공문: {target} ({'견본 서식' if mode == 'patch' else '일반기안문 서식'})")
    return 0


def cmd_sample_md(a):
    work = Path(a.work).expanduser().resolve()
    load_manifest(work)
    sample = resolve_in(work, a.sample)
    _, out = folders(work)
    md = out / "견본-편집.md"
    if sample.suffix.lower() == ".hwpx":
        n = linebreak_paragraphs(sample)
        if n:
            print(f"⚠ 견본에 강제 줄바꿈이 든 문단이 {n}개 있습니다. kordoc patch 는 이런 문단을 고치지 못합니다"
                  f"(일반기안문 서식으로 만든 견본에 흔함). 먼저 `sample-split {a.work} {sample.name}` 으로 문단을 나누세요.")
    kordoc([str(sample), "--keep-layout-tables", "-o", str(md)])
    print(f"견본을 마크다운으로 읽었습니다: {md}\n문단 수는 견본과 같게 두고 글자만 고친 뒤 "
          f"`letter --sample {sample.name} --md {md}`.")
    return 0


def cmd_sample_split(a):
    """견본의 강제 줄바꿈 문단을 줄마다 보통 문단으로 나눈 사본을 만든다(원본은 그대로)."""
    import zipfile
    work = Path(a.work).expanduser().resolve()
    load_manifest(work)
    sample = resolve_in(work, a.sample)
    _, out = folders(work)
    dst = out / f"{sample.stem}-문단나눔.hwpx"
    total = 0

    def split(m):
        nonlocal total
        para = m.group(0)
        if "<hp:lineBreak/>" not in para or para.count("<hp:t>") != 1:
            return para
        head = re.match(r"(<hp:p\b[^>]*>)", para).group(1)
        run = re.search(r'<hp:run charPrIDRef="(\d+)">', para)
        text = re.search(r"<hp:t>(.*?)</hp:t>", para, re.S).group(1)
        if not run:
            return para
        lines = text.split("<hp:lineBreak/>")
        total += len(lines) - 1
        pid = re.search(r'id="(\d+)"', head)
        out_paras = []
        for i, ln in enumerate(lines):
            h = head if not pid else head.replace(f'id="{pid.group(1)}"', f'id="{int(pid.group(1)) * 100 + i}"', 1)
            out_paras.append(f'{h}<hp:run charPrIDRef="{run.group(1)}"><hp:t>{ln}</hp:t></hp:run></hp:p>')
        return "".join(out_paras)

    with zipfile.ZipFile(sample) as zin, zipfile.ZipFile(dst, "w") as zout:
        for it in zin.infolist():
            data = zin.read(it.filename)
            if re.fullmatch(r"Contents/section\d+\.xml", it.filename):
                data = re.sub(r"<hp:p\b.*?</hp:p>", split, data.decode("utf-8"), flags=re.S).encode("utf-8")
            zout.writestr(it, data, compress_type=zipfile.ZIP_STORED if it.filename == "mimetype" else zipfile.ZIP_DEFLATED)
    v = kordoc(["validate", str(dst)], check=False)
    if v.returncode != 0:
        dst.unlink(missing_ok=True)
        raise ReplyError("문단을 나눈 견본이 구조 검증을 통과하지 못했습니다. 한글에서 견본 본문을 줄마다 Enter 로 나눠 저장하세요.")
    left = linebreak_paragraphs(dst)
    print(f"문단 나눔: 줄바꿈 {total}개 → 새 문단. 결과: {dst}" + (f" (아직 남은 줄바꿈 문단 {left}개)" if left else ""))
    print(f"다음: `sample-md {a.work} {dst.name}`")
    return 0


def cmd_finish(a):
    """검수(lint --gate) → 구조 검증(validate) → 직인(seal, 선택) → 미리보기(render png). 하나라도 실패하면 멈춘다."""
    work = Path(a.work).expanduser().resolve()
    m = load_manifest(work)
    if not m.get("letter"):
        raise ReplyError("회신 공문이 아직 없습니다(letter 먼저).")
    _, out = folders(work)
    letter = out / m["letter"]["file"]
    report = {}
    lint = kordoc(["lint", str(letter), "--gate"], check=False)
    report["lint"] = (lint.stderr + lint.stdout).strip().splitlines()[-6:]
    if lint.returncode != 0:
        print("\n".join(report["lint"]))
        raise ReplyError("표기법·구성 검수(lint --gate)를 통과하지 못했습니다. 지적을 고친 뒤 letter 부터 다시.")
    files = [letter]
    for info in m.get("forms", {}).values():
        if info.get("filled"):
            files.append(out / info["filled"])
    for f in files:
        v = kordoc(["validate", str(f)], check=False)
        if v.returncode != 0:
            raise ReplyError(f"구조 검증 실패: {f.name}\n{(v.stderr + v.stdout).strip()[-800:]}")
    report["validate"] = [f.name for f in files]
    final = letter
    if a.seal:
        anchor = a.anchor or "(인)"
        sealed = out / "회신공문-직인.hwpx"
        mode = a.seal_mode or ("overlap" if anchor == "(인)" else "right")
        kordoc(["seal", str(letter), "--image", str(Path(a.seal).expanduser()), "--anchor", anchor, "--mode", mode,
                "--size-mm", str(a.seal_size), "-o", str(sealed), "--silent"])
        v = kordoc(["validate", str(sealed)], check=False)
        if v.returncode != 0:
            raise ReplyError("직인을 넣은 뒤 구조 검증에 실패했습니다.")
        final = sealed
    png = out / "회신공문-미리보기.png"
    kordoc(["render", str(final), "--format", "png", "-o", str(png)])
    m["final"] = {"letter": final.name, "preview": png.name,
                  "attachments": [f.name for f in files[1:]], "report": report}
    save_manifest(work, m)
    print("검수 통과 · 구조 검증 통과" + (" · 직인" if a.seal else ""))
    print(f"최종 회신 공문: {final}")
    print(f"미리보기: {png}  ← 사용자에게 보여 주고 확인받는다")
    for f in files[1:]:
        print(f"붙임: {f}")
    return 0


def cmd_draft(a):
    """Gmail 회신 초안(보내지 않음). 받은 메일 스레드에 답장 초안 + 회신 공문·채운 양식 첨부."""
    work = Path(a.work).expanduser().resolve()
    m = load_manifest(work)
    if not m.get("final"):
        raise ReplyError("finish 를 먼저 통과해야 합니다.")
    mid = a.message_id or (m.get("mail") or {}).get("id")
    if not mid:
        raise ReplyError("답장할 메일 id 가 없습니다(--message-id).")
    _, out = folders(work)
    body = Path(a.body_file).read_text(encoding="utf-8") if a.body_file else a.body
    if not body or not body.strip():
        raise ReplyError("메일 본문이 비었습니다(--body 또는 --body-file).")
    attach = [out / m["final"]["letter"]] + [out / f for f in m["final"]["attachments"]]
    args = ["gmail", "+reply", "--message-id", mid, "--body", body, "--draft"]
    for f in attach:
        args += ["-a", f.name]  # gws 는 현재 폴더 밖의 첨부를 거부한다 → 회신 폴더에서 실행
    p = subprocess.run(gws_cmd() + args, capture_output=True, text=True, timeout=180, cwd=out)
    data = parse_json_out(p.stdout) or {}
    if p.returncode != 0 or "error" in data:
        raise ReplyError(f"회신 초안 만들기 실패: {(p.stderr or p.stdout).strip()[-600:]}")
    m["draft"] = {"draftId": data.get("id", ""), "threadId": (data.get("message") or {}).get("threadId", ""),
                  "attachments": [f.name for f in attach]}
    save_manifest(work, m)
    print(f"Gmail 회신 초안을 만들었습니다(보내지 않음). draftId={m['draft']['draftId']}")
    print("첨부: " + ", ".join(f.name for f in attach))
    print("보내기는 사용자가 Gmail 임시보관함에서 직접 한다.")
    return 0


def cmd_status(a):
    work = Path(a.work).expanduser().resolve()
    print(json.dumps(load_manifest(work), ensure_ascii=False, indent=2))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(prog="official_reply.py", description="공문 회신 묶음 만들기(보내지 않음)")
    p.add_argument("--version", action="version", version=VERSION)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init", help="작업 폴더 만들기 + 받은 문서 읽기")
    s.add_argument("work")
    s.add_argument("files", nargs="*")
    s.add_argument("--from-mail-watch", help="mail-watch fetch 폴더(첨부 + message.json)")
    s.set_defaults(fn=cmd_init)

    s = sub.add_parser("fields", help="붙임 양식 칸 목록(fill --dry-run)")
    s.add_argument("work")
    s.add_argument("form")
    s.set_defaults(fn=cmd_fields)

    s = sub.add_parser("fill", help="붙임 양식 채우기(--require-unique)")
    s.add_argument("work")
    s.add_argument("form")
    s.add_argument("--json", required=True)
    s.set_defaults(fn=cmd_fill)

    s = sub.add_parser("sample-md", help="회사 공문 견본을 고칠 마크다운으로 읽기")
    s.add_argument("work")
    s.add_argument("sample")
    s.set_defaults(fn=cmd_sample_md)

    s = sub.add_parser("sample-split", help="견본의 강제 줄바꿈 문단을 보통 문단으로 나눈 사본 만들기")
    s.add_argument("work")
    s.add_argument("sample")
    s.set_defaults(fn=cmd_sample_split)

    s = sub.add_parser("letter", help="회신 공문 만들기(일반기안문 --json 또는 견본 --sample --md)")
    s.add_argument("work")
    s.add_argument("--json", help="일반기안문 칸 JSON(붙임목록 포함 가능)")
    s.add_argument("--sample", help="회사 공문 견본 HWPX")
    s.add_argument("--md", help="견본을 읽어 고친 마크다운")
    s.set_defaults(fn=cmd_letter)

    s = sub.add_parser("finish", help="검수 → 구조 검증 → 직인 → 미리보기")
    s.add_argument("work")
    s.add_argument("--seal", help="직인 이미지(투명 PNG)")
    s.add_argument("--anchor", help="직인 위치 문구(기본 '(인)', 없으면 발신명의 문구)")
    s.add_argument("--seal-mode", choices=["overlap", "right", "auto"])
    s.add_argument("--seal-size", type=float, default=15.0, help="직인 한 변 크기(mm). 기본 15")
    s.set_defaults(fn=cmd_finish)

    s = sub.add_parser("draft", help="Gmail 회신 초안(보내지 않음)")
    s.add_argument("work")
    s.add_argument("--message-id")
    s.add_argument("--body")
    s.add_argument("--body-file")
    s.set_defaults(fn=cmd_draft)

    s = sub.add_parser("status", help="묶음.json 보기")
    s.add_argument("work")
    s.set_defaults(fn=cmd_status)

    a = p.parse_args(argv)
    if a.cmd == "letter" and not (a.json or a.sample):
        p.error("letter 는 --json 또는 --sample 중 하나가 필요합니다.")
    try:
        return a.fn(a) or 0
    except ReplyError as e:
        print(f"✖ {e}", file=sys.stderr)
        return 1
    except subprocess.TimeoutExpired as e:
        print(f"✖ 시간 초과: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
