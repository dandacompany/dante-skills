"""Shared helpers for remove-ai-marks scripts."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

# Fixed caps on attacker-influenced input sizes. This community distribution
# deliberately has no environment-configured escape hatch.
MAX_INPUT_BYTES = 256 << 20
MAX_STDIN_BYTES = 64 << 20


def eprint(*args: object) -> None:
    print(*args, file=sys.stderr)


def read_text_input(path: str | None) -> str:
    if path is None or path == "-":
        return _read_stdin_capped()
    p = Path(path)
    try:
        size = p.stat().st_size
    except OSError:
        size = 0
    if size > MAX_INPUT_BYTES:
        eprint(f"refusing input larger than {MAX_INPUT_BYTES} bytes: {path}")
        raise SystemExit(2)
    return p.read_text(encoding="utf-8", errors="surrogateescape")


def require_input_size(path: str | Path) -> None:
    """Reject files that exceed the whole-file processing budget."""
    p = Path(path)
    size = p.stat().st_size
    if size > MAX_INPUT_BYTES:
        raise ValueError(f"refusing input larger than {MAX_INPUT_BYTES} bytes: {p}")


def _read_stdin_capped() -> str:
    """Read stdin with a hard cap (uncapped stdin was a memory-DoS hole)."""
    chunks: list[str] = []
    total = 0
    while True:
        chunk = sys.stdin.read(1 << 20)
        if not chunk:
            break
        total += len(chunk)
        if total > MAX_STDIN_BYTES:
            eprint(f"refusing stdin input larger than {MAX_STDIN_BYTES} bytes")
            raise SystemExit(2)
        chunks.append(chunk)
    return "".join(chunks)


def write_text_output(text: str, path: str | None) -> None:
    if path is None or path == "-":
        sys.stdout.write(text)
        if text and not text.endswith("\n"):
            sys.stdout.write("\n")
        return
    safe_write_text(path, text)


def _default_file_mode() -> int:
    """0o666 & ~umask — the mode a plain open() would produce."""
    mask = os.umask(0)
    os.umask(mask)
    return 0o666 & ~mask


def safe_write_bytes(path: str | Path, data: bytes) -> None:
    """Atomically write bytes to *path* without following symlinks.

    Writes to a temp file in the destination directory and ``os.replace``s it
    into place. ``os.replace`` replaces a symlink rather than following it, and
    the explicit symlink check gives a clear error instead of surprising
    behavior. This defeats pre-placed symlinks (e.g. in /tmp or download dirs)
    redirecting a clean write onto an arbitrary victim file.
    """
    dest = Path(path)
    parent = dest.parent
    parent.mkdir(parents=True, exist_ok=True)
    if dest.is_symlink():
        raise OSError(f"refusing to write through symlink: {dest}")
    fd, tmp_name = tempfile.mkstemp(prefix=f".{dest.name}.", suffix=".tmp", dir=str(parent))
    try:
        # mkstemp creates 0600; restore the umask-default mode so outputs
        # keep normal permissions.
        os.fchmod(fd, _default_file_mode())
        with os.fdopen(fd, "wb") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, dest)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def safe_write_text(path: str | Path, text: str) -> None:
    safe_write_bytes(path, text.encode("utf-8", errors="surrogateescape"))


def backup_path(src: Path) -> Path:
    """Create a ``.bak`` copy of *src* via a safe write; return the backup path.

    Used by ``--in-place`` flows so the original is never partially lost: the
    original file stays untouched until the cleaned output is atomically
    renamed over it.
    """
    bak = src.with_suffix(src.suffix + ".bak")
    try:
        safe_write_bytes(bak, src.read_bytes())
    except OSError as e:
        eprint(f"cannot create backup {bak}: {e}")
        raise SystemExit(2)
    return bak


def emit_json(data: Any) -> None:
    json.dump(data, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


def cleaned_path(src: Path, suffix: str = ".cleaned") -> Path:
    """path/to/file.ext -> path/to/file.cleaned.ext"""
    return src.with_name(f"{src.stem}{suffix}{src.suffix}")
