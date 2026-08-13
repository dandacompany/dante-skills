#!/usr/bin/env python3
"""Generate an offline Layer B rewrite prompt without sending content anywhere."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import eprint, read_text_input, write_text_output  # noqa: E402


PROMPTS = {
    "paraphrase": (
        "Rewrite the following text so that it uses substantially different wording at "
        "the token level. Change clause order, connectors, and transition words; vary "
        "sentence boundaries and length; and replace both content words and function "
        "words where meaning allows. Preserve all facts, numbers, names, and technical "
        "identifiers. Do not add or remove claims. Output only the rewritten text."
        "\n\n---\n{TEXT}"
    ),
    "humanize": (
        "Rewrite the following text so it reads as if a human wrote it from scratch. "
        "Vary sentence rhythm and length, replace formulaic AI-style transitions and "
        "filler with concrete natural phrasing, and use plain, varied wording. Preserve "
        "all facts, numbers, names, and technical identifiers. Do not add or remove "
        "claims. Output only the rewritten text.\n\n---\n{TEXT}"
    ),
    "code": (
        "Rewrite the natural-language parts of this code — comments, docstrings, and "
        "string literals — using different wording. Rename local variables, function "
        "parameters, and private helper names to semantically equivalent names. Preserve "
        "program behavior, public API names, and all values that affect output. Output "
        "only the rewritten code.\n\n---\n{TEXT}"
    ),
}


def build_prompt(strength: str, text: str, *, lang: str, original_lang: str) -> str:
    if strength in PROMPTS:
        return PROMPTS[strength].format(TEXT=text)
    if strength == "backtranslate":
        return (
            f"Translate the text to {lang}, then translate that result back to "
            f"{original_lang}. Preserve all facts, numbers, and names. "
            f"Output only the final {original_lang} text.\n\n---\n{text}"
        )
    if strength == "structural":
        return (
            "First extract a bullet outline of all claims (no full sentences). Then "
            "write a complete document from that outline in natural, varied human prose "
            "without omitting any bullet. Output only the final document.\n\n---\n"
            f"{text}"
        )
    raise ValueError(f"unknown strength: {strength}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default="-", help="Input text file, or -")
    parser.add_argument("-o", "--output", help="Prompt output path (default: stdout)")
    parser.add_argument(
        "--backend",
        choices=("print-prompt",),
        default="print-prompt",
        help="Only offline prompt generation is available in the community package",
    )
    parser.add_argument(
        "--strength",
        choices=("paraphrase", "backtranslate", "structural", "humanize", "code"),
        default="paraphrase",
    )
    parser.add_argument("--lang", default="French", help="Pivot language")
    parser.add_argument("--original-lang", default="English")
    parser.add_argument("--json-stats", action="store_true", help="Stats JSON on stderr")
    args = parser.parse_args()

    text = read_text_input(args.path)
    prompt = build_prompt(
        args.strength,
        text,
        lang=args.lang,
        original_lang=args.original_lang,
    )
    write_text_output(prompt, args.output or "-")

    info = {
        "backend": "print-prompt",
        "strength": args.strength,
        "mode": "offline-prompt-only",
        "input_chars": len(text),
        "prompt_chars": len(prompt),
    }
    if args.json_stats:
        eprint(json.dumps(info, indent=2, ensure_ascii=False))
    else:
        eprint(
            f"backend=print-prompt strength={args.strength} "
            f"mode=offline-prompt-only chars {len(text)}->{len(prompt)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
