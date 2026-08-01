"""Catalog validation helpers (stdlib only)."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
REL_PATH_RE = re.compile(
    r"^(?!/|\\)(?!.*\.\.(?:/|\\|$))(?!.*:)[A-Za-z0-9._@+, \-]+(?:/[A-Za-z0-9._@+, \-]+)*$"
)


def sha256_prefixed(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_catalog(catalog: dict[str, Any], *, repo_root: Path) -> list[str]:
    errors: list[str] = []
    if catalog.get("schemaVersion") != 1:
        errors.append("schemaVersion must be 1")
    entries = catalog.get("entries")
    if not isinstance(entries, list):
        errors.append("entries must be an array")
        return errors

    seen_ids: set[str] = set()
    for index, row in enumerate(entries):
        label = f"entries[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{label} must be an object")
            continue
        for key in ("identity", "path", "contentHash", "action"):
            if key not in row or not isinstance(row[key], str) or not row[key].strip():
                errors.append(f"{label}.{key} missing or empty")
        if row.get("action") != "remove":
            errors.append(f"{label}.action must be 'remove'")
        path = row.get("path", "")
        if isinstance(path, str) and not REL_PATH_RE.match(path):
            errors.append(f"{label}.path is not a safe repo-relative path: {path!r}")
        digest = row.get("contentHash", "")
        if isinstance(digest, str) and not SHA256_RE.match(digest):
            errors.append(f"{label}.contentHash invalid: {digest!r}")
        identity = row.get("identity", "")
        if identity in seen_ids:
            errors.append(f"duplicate identity: {identity}")
        seen_ids.add(identity)

        known = row.get("knownBytes")
        if known:
            if not isinstance(known, str) or not REL_PATH_RE.match(known):
                errors.append(f"{label}.knownBytes invalid path: {known!r}")
            else:
                known_path = repo_root / known
                if not known_path.is_file():
                    errors.append(f"{label}.knownBytes missing file: {known}")
                else:
                    actual = sha256_prefixed(known_path.read_bytes())
                    if actual != digest:
                        errors.append(
                            f"{label}.contentHash does not match knownBytes "
                            f"(expected {digest}, actual {actual})"
                        )
    return errors
