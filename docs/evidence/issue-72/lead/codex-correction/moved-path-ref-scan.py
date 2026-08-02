#!/usr/bin/env python3
"""Issue #72 moved-path reference scan.

Distinguishes valid archive-pointer / historical citations from broken active
dependencies on relocated paths.

Exit 0 when all moved destinations exist, remaining old paths are pointer stubs
(when retained), and active surfaces have no hard dependency on moved content.
Exit 1 with a classified report otherwise.

Usage (from repo root):
  python3 docs/evidence/issue-72/lead/codex-correction/moved-path-ref-scan.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
MOVE_MAP = ROOT / "docs/evidence/issue-72/lane-b/move-map.json"

# Paths excluded from "active dependency" scanning (history / this issue evidence).
EXCLUDE_PREFIXES = (
    "docs/archive/",
    "docs/evidence/issue-72/",
    "docs/adoption-backups/",
    "docs/workspace-reports/",
)

TEXT_SUFFIXES = {
    ".md",
    ".mdc",
    ".sh",
    ".py",
    ".yml",
    ".yaml",
    ".json",
    ".toml",
    ".txt",
    ".rs",
    ".ts",
    ".js",
}

# Line-level markers that classify a citation as intentional pointer/history.
# Prefer relocate-specific language; do not treat bare path segment "archive" alone
# as sufficient (that would mask unmarked deps that merely mention docs/archive/).
VALID_MARKERS = re.compile(
    r"(?i)("
    r"\brelocated\b|\bpointer stub\b|\bpointer\b|\bstub\b|\bhistorical\b|"
    r"\bcanonical copy\b|\bok if (previously )?absent\b|not present \(ok|"
    r"docs/archive/"
    r")"
)

# Hard-require patterns in scripts/tests (broken if matched against a moved path).
HARD_REQUIRE = re.compile(
    r"(?:"
    r"\[\s*-\w*\s+[\"']?(?P<path1>[^\"'\]]+)[\"']?\s*\]"
    r"|require\([\"'](?P<path2>[^\"']+)[\"']\)"
    r"|open\([\"'](?P<path3>[^\"']+)[\"']"
    r")"
)

POINTER_MARKERS = re.compile(r"(?i)\b(relocated|canonical|archive)\b")

# Extra needles beyond move-map (Claude tree removed from active root).
EXTRA_NEEDLES = [
    {
        "needle": "claude/CLAUDE.md",
        "kind": "removed_active_path",
        "destination": "docs/archive/platform-entrypoints/claude/CLAUDE.md",
    }
]


def is_excluded(rel: str) -> bool:
    return any(rel == p.rstrip("/") or rel.startswith(p) for p in EXCLUDE_PREFIXES)


def iter_text_files():
    skip_dirs = {".git", "node_modules", "__pycache__", ".venv", "dist", "build"}
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        try:
            rel_path = path.relative_to(ROOT)
        except ValueError:
            continue
        rel = rel_path.as_posix()
        # Only skip VCS/vendor dirs under the repo root (not parent path segments
        # such as `.git/linktrend-worktrees/...` in worktree absolute paths).
        if any(part in skip_dirs for part in rel_path.parts):
            continue
        if is_excluded(rel):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES and path.name not in {
            "Dockerfile",
            "Makefile",
        }:
            continue
        yield rel, path


def is_pointer_stub(path: Path) -> bool:
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8", errors="ignore")
    if len(text) > 1200:
        return False
    return bool(POINTER_MARKERS.search(text))


def classify_line(line: str) -> str:
    if VALID_MARKERS.search(line):
        return "valid_archive_pointer_or_historical"
    return "broken_active_dependency"


def main() -> int:
    data = json.loads(MOVE_MAP.read_text(encoding="utf-8"))
    moves = list(data["moves"])
    failures: list[str] = []
    notes: list[str] = []

    # 1) Destination existence + retained old-path must be pointer stub / README pointer.
    for move in moves:
        src = move["from"]
        dst = move["to"]
        dst_path = ROOT / dst
        if move.get("type") == "directory":
            if not dst_path.is_dir():
                failures.append(f"MISSING_DEST_DIR {dst}")
            readme = ROOT / src / "README.md"
            if (ROOT / src).exists():
                if readme.is_file() and is_pointer_stub(readme):
                    notes.append(f"POINTER_OK {src}/README.md -> {dst}")
                elif (ROOT / src).is_file() and is_pointer_stub(ROOT / src):
                    notes.append(f"POINTER_OK {src} -> {dst}")
                else:
                    # Directory move left a pointer README only (expected).
                    if not readme.is_file():
                        failures.append(
                            f"OLD_PATH_NOT_POINTER {src} (expected README pointer)"
                        )
                    elif not is_pointer_stub(readme):
                        failures.append(f"OLD_PATH_NOT_POINTER {src}/README.md")
                    else:
                        notes.append(f"POINTER_OK {src}/README.md -> {dst}")
        else:
            if not dst_path.is_file():
                failures.append(f"MISSING_DEST_FILE {dst}")
            src_path = ROOT / src
            if src_path.exists():
                if is_pointer_stub(src_path):
                    notes.append(f"POINTER_OK {src} -> {dst}")
                else:
                    failures.append(
                        f"OLD_PATH_NOT_POINTER {src} (retained but not a relocate stub)"
                    )

    # 2) Scan active surfaces for needles; classify each hit line.
    needles: list[tuple[str, str]] = []
    for move in moves:
        needles.append((move["from"], move["to"]))
        # Also scan basename-ish evidence path used historically.
        if move["from"].endswith("/"):
            continue
    for extra in EXTRA_NEEDLES:
        needles.append((extra["needle"], extra["destination"]))

    # Prefer longer needles first to avoid partial confusion in reporting.
    needles.sort(key=lambda x: len(x[0]), reverse=True)

    valid_hits = 0
    for rel, path in iter_text_files():
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for lineno, line in enumerate(lines, 1):
            for needle, dest in needles:
                if needle not in line:
                    continue
                # Self-path on the stub file is always valid.
                if rel == needle or rel == f"{needle.rstrip('/')}/README.md":
                    valid_hits += 1
                    notes.append(f"VALID_SELF_STUB {rel}:{lineno}")
                    continue
                kind = classify_line(line)
                if kind.startswith("valid"):
                    valid_hits += 1
                    notes.append(f"VALID {rel}:{lineno} needle={needle}")
                else:
                    # Hard-require in scripts/tests is always broken.
                    if rel.startswith(("scripts/", "tests/", "core/")) and HARD_REQUIRE.search(
                        line
                    ):
                        failures.append(
                            f"BROKEN_HARD_REQUIRE {rel}:{lineno} needle={needle} :: {line.strip()}"
                        )
                    elif kind == "broken_active_dependency":
                        failures.append(
                            f"BROKEN_ACTIVE_REF {rel}:{lineno} needle={needle} :: {line.strip()}"
                        )

    print("moved-path-ref-scan")
    print(f"move_map={MOVE_MAP.relative_to(ROOT)}")
    print(f"valid_hits={valid_hits}")
    print(f"notes={len(notes)}")
    for n in notes:
        print(f"  NOTE {n}")
    print(f"failures={len(failures)}")
    for f in failures:
        print(f"  FAIL {f}")

    if failures:
        print("RESULT=FAIL")
        return 1
    print("RESULT=PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
