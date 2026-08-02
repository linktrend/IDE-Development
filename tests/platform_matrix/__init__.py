"""Cross-platform installer matrix (Issue #67 Work Packet 1 Lane A).

Authoritative entrypoint: ``python3 scripts/run_cross_platform_matrix.py``.

This package discovers and extends ``scripts/ide_development_tests`` with
Windows-safe assertions, Unicode path coverage, and true cross-process lock
proofs that run on every supported OS (including Windows msvcrt).
"""

from __future__ import annotations

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
SUMMARIES_DIR = PACKAGE_ROOT / "summaries"
FIXTURES_DIR = PACKAGE_ROOT / "fixtures"
