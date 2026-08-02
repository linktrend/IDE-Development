#!/usr/bin/env python3
"""Authoritative cross-platform installer matrix entrypoint (Issue #67 Lane A).

Runs on macOS, Ubuntu Linux, and Windows:

    python3 scripts/run_cross_platform_matrix.py

Discovers ``scripts/ide_development_tests`` plus ``tests/platform_matrix``
supplements, applies explicit Windows symlink-privilege exclusions (paired with
equivalent safety tests), and writes machine-readable JSON under
``tests/platform_matrix/summaries/``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TESTS_DIR = REPO_ROOT / "tests"
SCRIPTS_DIR = REPO_ROOT / "scripts"

for path in (str(SCRIPTS_DIR), str(TESTS_DIR)):
    if path not in sys.path:
        sys.path.insert(0, path)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run the IDE Development cross-platform installer matrix.",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Less verbose unittest output",
    )
    parser.add_argument(
        "--no-json",
        action="store_true",
        help="Do not write JSON summary artifacts",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=None,
        help="Optional explicit summary JSON path",
    )
    parser.add_argument(
        "--matrix-only",
        action="store_true",
        help="Run only tests/platform_matrix (skip scripts/ide_development_tests)",
    )
    parser.add_argument(
        "--existing-only",
        action="store_true",
        help="Run only scripts/ide_development_tests (skip matrix supplements)",
    )
    args = parser.parse_args(argv)

    from platform_matrix.runner import run_matrix

    summary = run_matrix(
        verbosity=1 if args.quiet else 2,
        include_existing=not args.matrix_only,
        include_matrix=not args.existing_only,
        write_json=not args.no_json,
        summary_path=args.summary,
        argv=[sys.executable, str(Path(__file__).resolve()), *(argv or sys.argv[1:])],
    )
    return int(summary.exitCode)


if __name__ == "__main__":
    raise SystemExit(main())
