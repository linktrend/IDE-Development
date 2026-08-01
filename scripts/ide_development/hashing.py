"""Hashing helpers (sha256, content + mode identity)."""

from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def normalize_mode(mode: int | str) -> str:
    """Return a 4-digit octal mode string (e.g. '0644')."""
    if isinstance(mode, str):
        text = mode.strip().lower()
        if text.startswith("0o"):
            value = int(text, 8)
        elif text.startswith("0") and text.isdigit():
            value = int(text, 8)
        else:
            value = int(text, 8) if all(c in "01234567" for c in text) else int(text)
    else:
        value = int(mode)
    value &= 0o7777
    return f"{value:04o}"


def mode_int(mode: str | int) -> int:
    return int(normalize_mode(mode), 8)
