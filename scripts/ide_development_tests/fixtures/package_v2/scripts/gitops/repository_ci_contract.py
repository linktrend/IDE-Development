#!/usr/bin/env python3
"""Disposable package_v2 stand-in for scripts/gitops/repository_ci_contract.py.

The engine loads this path from the package root before plan/install/verify.
Real packaged releases ship the full WP-U07 module (and its gitops deps). The
disposable fixture only needs the installer audit entrypoint, self-contained so
matrix/CLI subprocesses do not require the factory ``scripts`` package on
``sys.path``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def installer_audit_repository_ci_triggers(
    target_root: Path,
    *,
    mutate: bool = False,
    rollout_scope: bool = False,
) -> dict[str, Any]:
    """Report-only audit stub matching the installer-facing return shape."""
    del target_root, mutate  # fixture packages do not rewrite consumer workflows
    return {
        "ok": True,
        "conflicts": [],
        "scanned": 0,
        "mayModify": False,
        "detail": "fixture_report_only_without_rollout_scope",
        "rolloutScope": bool(rollout_scope),
        "mutated": False,
    }
