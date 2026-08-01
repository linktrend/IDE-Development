"""Conflict-matrix classifiers for migration black-box fixtures.

Implements the MANAGED-CORE-V2 classifications needed by WP4 fixtures without
owning the installer engine.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def sha256_prefixed(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_prefixed(path.read_bytes())


@dataclass(frozen=True)
class Classification:
    path: str
    kind: str
    detail: str = ""


def resolve_under(root: Path, rel: str) -> Path:
    candidate = (root / rel).resolve()
    root_resolved = root.resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(f"path escapes root: {rel}") from exc
    return candidate


def classify_symlink(root: Path, rel: str = ".cursor") -> Classification:
    path = root / rel
    if not path.exists() and not path.is_symlink():
        return Classification(rel, "missing", "path absent")
    if path.is_symlink():
        target = os.readlink(path)
        # Absolute or checkout-to-checkout external symlink → unsafe / migratable
        if target.startswith("/") or target.startswith("~") or ":\\" in target or ":/" in target[:3]:
            return Classification(rel, "unsafe_link", f"absolute symlink -> {target}")
        # Relative external (e.g. ../IDE Development/.cursor)
        resolved = path.resolve()
        try:
            resolved.relative_to(root.resolve())
            # Points inside repo — still a symlink, fail closed for managed install
            return Classification(rel, "unsafe_link", f"symlink inside/outside probe -> {target}")
        except ValueError:
            return Classification(rel, "unsafe_link", f"external symlink -> {target}")
    if path.is_dir():
        return Classification(rel, "physical_tree", "physical directory")
    return Classification(rel, "unknown_conflict", "unexpected .cursor type")


def classify_supersession(
    root: Path,
    *,
    path: str,
    identity: str,
    content_hash: str,
) -> Classification:
    dest = root / path
    if dest.is_symlink():
        return Classification(path, "unsafe_link", "migration target is symlink")
    if not dest.exists():
        return Classification(path, "missing", "migration target absent")
    if not dest.is_file():
        return Classification(path, "unknown_conflict", "migration target not a file")
    actual = sha256_file(dest)
    if actual == content_hash:
        return Classification(path, "supersede_exact", f"identity={identity}")
    return Classification(path, "supersede_mismatch", f"expected {content_hash}, actual {actual}")


def classify_consumer_owned(root: Path, rel: str, *, package_hash: str | None = None) -> Classification:
    dest = root / rel
    if not dest.exists():
        return Classification(rel, "missing")
    if dest.is_symlink():
        return Classification(rel, "unsafe_link")
    if not dest.is_file():
        return Classification(rel, "consumer_owned", "non-file consumer path preserved")
    actual = sha256_file(dest)
    if package_hash and actual == package_hash:
        return Classification(rel, "match")
    return Classification(rel, "consumer_owned", "preserve consumer bytes")


def classify_dirty_unrelated(root: Path, rel: str) -> Classification:
    dest = root / rel
    if not dest.exists():
        return Classification(rel, "missing")
    return Classification(rel, "unrelated_dirty", "preserve unrelated dirty path")


def mode_octal(path: Path) -> str:
    return f"{stat.S_IMODE(path.stat().st_mode):04o}"


def byte_identical(a: Path, b: Path) -> bool:
    if not a.is_file() or not b.is_file():
        return False
    return a.read_bytes() == b.read_bytes() and mode_octal(a) == mode_octal(b)


def load_scenario(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
