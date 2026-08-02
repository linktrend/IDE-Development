#!/usr/bin/env python3
"""Lane E security acceptance runner (Issue #67 Work Packet 1).

Usage:
  python3 tests/security_acceptance/run_tests.py
  python3 -m unittest discover -s tests/security_acceptance -p 'test_*.py'
"""

from __future__ import annotations

import argparse
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"

# Ensure imports: harness (local) + ide_development / gitops (scripts/)
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def _load_suite(pattern: str = "test_*.py") -> unittest.TestSuite:
    loader = unittest.TestLoader()
    return loader.discover(start_dir=str(HERE), pattern=pattern)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Lane E security acceptance runner")
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Less verbose unittest output",
    )
    parser.add_argument(
        "--json-summary",
        action="store_true",
        help="Print machine-readable summary after the run",
    )
    args = parser.parse_args(argv)

    suite = _load_suite()
    verbosity = 1 if args.quiet else 2
    result = unittest.TextTestRunner(verbosity=verbosity, buffer=True).run(suite)

    # Also note discover compatibility path for operators.
    discover_cmd = (
        f"PYTHONPATH={SCRIPTS_DIR}:{HERE} python3 -m unittest discover "
        f"-s {HERE} -p 'test_*.py'"
    )

    summary = {
        "lane": "E",
        "ok": result.wasSuccessful(),
        "testsRun": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "runner": "tests/security_acceptance/run_tests.py",
        "unittestDiscover": discover_cmd,
    }
    print(
        f"\nLane E summary: run={summary['testsRun']} "
        f"fail={summary['failures']} err={summary['errors']} "
        f"skip={summary['skipped']} ok={summary['ok']}"
    )
    if args.json_summary:
        print(json.dumps(summary, indent=2, sort_keys=True))

    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
