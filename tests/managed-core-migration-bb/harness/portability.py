"""Portability scanners: no secrets, no absolute host paths in package payloads."""

from __future__ import annotations

import re
from pathlib import Path

# Absolute local checkout / host path smells that must not appear in packaged catalog bytes.
ABSOLUTE_PATH_RE = re.compile(
    r"(?:^|[\s\"'`=])"
    r"(?:"
    r"/Users/[A-Za-z0-9._-]+/"
    r"|/home/[A-Za-z0-9._-]+/"
    r"|[A-Za-z]:\\\\(?:Users|home)\\"
    r"|\\\\[A-Za-z0-9._$-]+\\"
    r")"
)

CREDENTIAL_RES = [
    re.compile(r"(?i)api[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}"),
    re.compile(r"(?i)secret\s*[:=]\s*['\"]?[A-Za-z0-9_\-/+=]{12,}"),
    re.compile(r"(?i)token\s*[:=]\s*['\"]?[A-Za-z0-9_\-\.]{16,}"),
    re.compile(r"(?i)BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
]


def scan_text(text: str, *, rel: str) -> list[str]:
    findings: list[str] = []
    if ABSOLUTE_PATH_RE.search(text):
        findings.append(f"{rel}: absolute host/checkout path smell")
    for cre in CREDENTIAL_RES:
        if cre.search(text):
            findings.append(f"{rel}: credential/secret pattern ({cre.pattern[:40]}…)")
            break
    return findings


def scan_tree(root: Path, *, base: Path | None = None) -> list[str]:
    base = base or root
    findings: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico"}:
            continue
        rel = str(path.relative_to(base)).replace("\\", "/")
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Binary non-image: still forbid absolute UTF-8 path fragments if decodable as latin-1
            raw = path.read_bytes()
            text = raw.decode("latin-1", errors="ignore")
        findings.extend(scan_text(text, rel=rel))
    return findings
