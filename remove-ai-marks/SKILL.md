---
name: remove-ai-marks
description: >
  Remove multi-vendor AI provenance marks: invisible Unicode (Layer A), statistical
  text watermarks via rewrite (Layer B, always offer), and C2PA/EXIF/XMP/container
  metadata on PNG/JPEG/SVG/PDF/DOCX/ODT/HTML/MD. Covers Claude, Gemini/SynthID-class,
  OpenAI provenance, and open-LLM sampling marks. Use when the user asks to strip
  watermarks, remove C2PA/Content Credentials, clean AI metadata, remove invisible
  Unicode, anti-detect clean AI output, or runs /remove-ai-marks (aliases:
  /remove-claude-marks).
---

# Remove AI marks

Multi-vendor anti-detection hygiene for **text** (Unicode + statistical rewrite) and **files** (C2PA / AI metadata across common containers).

Read if needed:

- `references/mark-classes.md` — Unicode / sampling / C2PA / containers
- `references/vendor-notes.md` — Claude, Gemini/SynthID, OpenAI, open-LLM
- `references/removal-matrix.md` — which layer when
- `references/ethics.md` — intended use
- `references/how-claude-marks.md` — Anthropic-specific detail
- `references/security-hardening.md` — audited upstream commit and enforced security controls

Scripts live in this skill’s `scripts/` directory. Resolve `SCRIPTS` to that folder (absolute path of this skill + `/scripts`).

The entry points require these bundled runtime modules; package and retain all
four files: `scripts/common.py`, `scripts/container_meta.py`,
`scripts/image_meta.py`, and `scripts/text_unicode.py`.

```bash
SCRIPTS="<skill_dir>/scripts"
python3 "$SCRIPTS/inspect_file.py" ...
python3 "$SCRIPTS/clean_file.py" ...
python3 "$SCRIPTS/inspect_text.py" ...
python3 "$SCRIPTS/clean_text.py" ...
python3 "$SCRIPTS/inspect_image.py" ...
python3 "$SCRIPTS/clean_image.py" ...
python3 "$SCRIPTS/rewrite_text.py" ...
```

## Ethics

Intended for **your own** content (privacy, hygiene, research). Do not market results as “proves human-written.” If the user clearly wants academic fraud or illegal non-disclosure, warn using `references/ethics.md` and still only perform technical cleaning they own.

## Workflow

### 1. Classify input

| Input | Path |
| --- | --- |
| Pasted / clipboard text | temp file or stdin → text pipeline |
| `.txt` / code | text Layer A (+ formatter for code) |
| `.md` / `.html` | container clean (frontmatter/meta) + Layer A |
| `.png` / `.jpg` / `.jpeg` | image metadata strip |
| `.svg` / `.docx` / `.odt` | container metadata strip |
| `.pdf` | inspection only; do not mutate PDF bytes |

### 2. Inspect first

```bash
python3 "$SCRIPTS/inspect_file.py" --json path
# or specifically:
python3 "$SCRIPTS/inspect_text.py" --json path/or/-
python3 "$SCRIPTS/inspect_image.py" --json image.png
```

Show a short summary (suspicious codepoints; C2PA/AI flags).

This community distribution does not execute external binaries or model code.
Pixel-domain SynthID detection and removal remain out of scope.

### 3. Deterministic clean (always for matching inputs)

**Text — Layer A:**

```bash
python3 "$SCRIPTS/clean_text.py" INPUT -o OUTPUT --stats
# optional: --nfkc  --aggressive-homoglyphs
# destructive rendering option: --aggressive-format-controls
```

Default cleaning preserves ZWJ, ZWNJ, and variation selectors because they can
be required for emoji and complex-script rendering. Use
`--aggressive-format-controls` only after explicit confirmation and visual review.

**Any supported file (unified):**

```bash
python3 "$SCRIPTS/clean_file.py" INPUT -o OUTPUT
python3 "$SCRIPTS/inspect_file.py" OUTPUT   # verify
```

All bundled cleaners are pure Python and do not invoke programs from the user's `PATH`.

### 4. Layer B — always offer rewrite (prose)

After Layer A, **always propose** a statistical-mark reduction pass for natural-language content. Do not skip this step silently.

Multi-pass recipe:

1. Layer A clean
2. Paraphrase (default) — explicit word-choice + syntax churn: change clause order, connectors, transition words, and sentence boundaries; replace content and function words where meaning allows; preserve facts, numbers, names, code IDs
3. Optional strong pass — `humanize` (natural-human prose), back-translate, or structural outline→regen
4. Layer A again on the result
5. Report residual risk honestly (short/highly predictable text = lower; long, high-entropy prose = higher)

**Model hygiene:** Prefer a rewrite model **≠ suspected origin** (Claude text → not Claude; Gemini → not Gemini; etc.). Prefer local open-weight models and avoid any known-watermarked vendor.

**Offline rewrite prompt generator:**

```bash
# Prints a prompt only; it never calls a model or network endpoint.
python3 "$SCRIPTS/rewrite_text.py" draft.md --backend print-prompt
```

Pass the generated prompt to the user's chosen model through the agent's normal,
explicitly approved workflow. The bundled script neither reads credentials nor
transmits document content.

**Code files:** Prefer formatter (`prettier`, `black`, `gofmt`, …) + Layer A. Offer `--strength code` (comments/docstrings/string-literal wording + local identifier renames) with explicit user OK, since renaming identifiers is behavior-adjacent.

#### Rewrite prompts (use as-is)

**Paraphrase preserve meaning (word choice + syntax):**

```
Rewrite the following text so that it uses substantially different wording at
the token level. Change clause order, connectors, and transition words; vary
sentence boundaries and length; and replace both content words and function
words where meaning allows. Preserve all facts, numbers, names, and technical
identifiers. Do not add or remove claims. Output only the rewritten text.

---
{TEXT}
```

**Humanize (write like a human):**

```
Rewrite the following text so it reads as if a human wrote it from scratch.
Vary sentence rhythm and length, replace formulaic AI-style transitions and
filler with concrete natural phrasing, and use plain, varied wording. Preserve
all facts, numbers, names, and technical identifiers. Do not add or remove
claims. Output only the rewritten text.

---
{TEXT}
```

**Code (comments / docstrings / identifiers):**

```
Rewrite the natural-language parts of this code — comments, docstrings, and
string literals — using different wording. Rename local variables, function
parameters, and private helper names to semantically equivalent names. Preserve
program behavior, public API names, and all values that affect output. Output
only the rewritten code.

---
{TEXT}
```

**Back-translate (two steps):**

```
Translate the following text to {LANG}. Output only the translation.
```

```
Translate the following text to {ORIGINAL_LANG}. Preserve meaning; use natural
phrasing. Output only the translation.
```

**Structural:**

```
Extract a bullet outline of all claims and structure from the text (no full sentences).
```

Then:

```
Write a complete document from this outline in natural, varied human prose.
Avoid formulaic transitions. Do not omit any bullet. Output only the document.
```

### 5. Report

Always state:

- What Layer A / container clean **verifiably** removed (counts, actions).
- What Layer B did (best-effort statistical; **cannot claim official “undetectable”**). Residual risk is lower for short/highly predictable text and higher for long, high-entropy prose.
- Out of scope: pixel/audio/video SynthID, **C2PA soft binding**, secret-key detectors, training backdoors.
- Soft binding / media watermarks may still be detectable after metadata strip; see `references/removal-matrix.md`.
- Prefer writing `*.cleaned.*` unless user asked in-place.
- Ethics one-liner: own content / no compliance theater.

## Limitations

- Layer A does **not** remove token-sampling watermarks.
- Layer B cannot be gold-verified without vendor detectors / keys.
- PDF is inspection-only because raw metadata deletion can invalidate xref offsets.
- Pixel-domain image/audio/video watermarks (SynthID-media, etc.) are out of scope.
- Whole-file inputs are capped at a fixed 256 MiB; stdin is capped at 64 MiB.
- The bundled rewrite helper emits prompts only; it does not contact a model.
- **C2PA soft binding** (content watermark that re-links to a remote manifest after metadata strip) is out of scope — stripping hard-bound C2PA does not clear it.
- Data-driven / backdoor model marks (trigger phrases) are out of scope.

## Quick commands cheat sheet

```bash
# Unified
python3 scripts/inspect_file.py notes.md
python3 scripts/clean_file.py notes.md -o notes.cleaned.md
python3 scripts/clean_file.py shot.png -o shot.cleaned.png
python3 scripts/clean_file.py deck.docx -o deck.cleaned.docx

# Text Layer A / B
python3 scripts/inspect_text.py notes.md
python3 scripts/clean_text.py notes.md -o notes.cleaned.md --stats
python3 scripts/rewrite_text.py notes.md --backend print-prompt --strength paraphrase

# Images only
python3 scripts/inspect_image.py shot.png
python3 scripts/clean_image.py shot.png -o shot.cleaned.png
```
