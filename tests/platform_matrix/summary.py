"""Machine-readable summary helpers for the cross-platform matrix."""

from __future__ import annotations

import json
import platform
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import SUMMARIES_DIR


SCHEMA_VERSION = 1


@dataclass
class TestCaseRecord:
    id: str
    outcome: str  # pass | fail | error | skip
    elapsedSec: float = 0.0
    message: str = ""
    exclusionReason: str = ""
    equivalentCoverage: str = ""


@dataclass
class MatrixSummary:
    schemaVersion: int = SCHEMA_VERSION
    generatedAt: str = ""
    platform: Dict[str, str] = field(default_factory=dict)
    command: List[str] = field(default_factory=list)
    exitCode: int = 1
    counts: Dict[str, int] = field(default_factory=dict)
    suites: List[str] = field(default_factory=list)
    exclusions: List[Dict[str, Any]] = field(default_factory=list)
    coverageAreas: Dict[str, List[str]] = field(default_factory=dict)
    tests: List[Dict[str, Any]] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schemaVersion": self.schemaVersion,
            "generatedAt": self.generatedAt,
            "platform": self.platform,
            "command": self.command,
            "exitCode": self.exitCode,
            "counts": self.counts,
            "suites": self.suites,
            "exclusions": self.exclusions,
            "coverageAreas": self.coverageAreas,
            "tests": self.tests,
            "notes": self.notes,
        }


def host_platform_info() -> Dict[str, str]:
    return {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "sysPlatform": sys.platform,
    }


def default_coverage_areas() -> Dict[str, List[str]]:
    """Map required Lane A areas to representative test id suffixes."""
    return {
        "install": [
            "test_install_idempotent_and_physical",
            "test_cli_install_and_verify",
            "test_physical_install_never_symlink",
        ],
        "update": [
            "test_install_idempotent_and_physical",
            "test_noop_rewrites_missing_installed_state",
        ],
        "plan_dry_run": [
            "test_plan_and_dry_run_no_writes",
            "test_cli_install_dry_run",
            "test_plan_dry_run_no_writes_unicode_target",
        ],
        "drift": ["test_drift_detection"],
        "verify": ["test_cli_install_and_verify", "test_install_idempotent_and_physical"],
        "version": ["test_version", "test_cli_version_json"],
        "rollback": [
            "test_rollback_restores_bytes_and_modes",
            "test_rollback_restores_bytes_portable_modes",
        ],
        "transaction_locking": [
            "test_exclusive_lock_fail_closed",
            "test_plan_dry_run_does_not_take_lock",
        ],
        "modes_permissions": [
            "test_mode_normalize",
            "test_rollback_restores_bytes_portable_modes",
            "test_install_modes_portable",
        ],
        "paths_spaces_unicode": [
            "test_spaces_and_join",
            "test_unicode_target_install_verify",
            "test_unicode_and_spaces_join",
        ],
        "git_worktree_metadata": [
            "test_resolve_git_dir_worktree_gitfile",
            "test_install_into_gitfile_worktree",
            "test_worktree_gitfile_meta_under_real_gitdir",
        ],
        "physical_file_guarantees": [
            "test_install_idempotent_and_physical",
            "test_physical_install_never_symlink",
            "test_atomic_write_physical_roundtrip_portable",
        ],
        "cross_process_contention": [
            "test_cross_process_exclusive_lock_all_platforms",
            "test_cross_process_exclusive_lock_fail_closed",
        ],
    }


def ensure_summaries_dir() -> Path:
    SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)
    return SUMMARIES_DIR


def summary_path_for_run(*, stamp: Optional[str] = None) -> Path:
    ensure_summaries_dir()
    if stamp is None:
        stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    safe_plat = sys.platform.replace("\\", "_")
    return SUMMARIES_DIR / f"matrix-{safe_plat}-{stamp}.json"


def write_summary(summary: MatrixSummary, path: Optional[Path] = None) -> Path:
    out = path or summary_path_for_run()
    ensure_summaries_dir()
    payload = summary.to_dict()
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    out.write_text(text, encoding="utf-8")
    # Also refresh a stable "latest" pointer for the evidence bundle.
    latest = SUMMARIES_DIR / f"matrix-{sys.platform}-latest.json"
    latest.write_text(text, encoding="utf-8")
    return out
