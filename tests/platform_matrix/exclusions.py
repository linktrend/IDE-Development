"""Explicit platform exclusions for discovered installer unit tests.

Exclusions must be justified and paired with equivalent safety coverage under
``tests/platform_matrix/`` (see ``test_windows_safe_contracts.py`` and
``test_cross_process_lock_matrix.py``).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Iterable, List, Optional, Set

from .platform_assertions import can_create_symlinks, is_windows


@dataclass(frozen=True)
class Exclusion:
    """A single skip rule applied to unittest ids (``module.Class.method``)."""

    test_id_suffix: str
    reason: str
    equivalent_coverage: str
    platforms: frozenset  # e.g. frozenset({"win32"}) or frozenset({"*"})


# Symlink-creation tests in scripts/ide_development_tests — skip on Windows when
# the process cannot create file symlinks. Paired equivalents live in this package.
_SYMLINK_CREATION_EXCLUSIONS: List[Exclusion] = [
    Exclusion(
        test_id_suffix="test_sha256_and_read_refuse_symlink",
        reason="requires creating a file symlink",
        equivalent_coverage="test_windows_safe_contracts.WindowsSafeContractsTests.test_physical_install_never_symlink",
        platforms=frozenset({"win32"}),
    ),
    Exclusion(
        test_id_suffix="test_lock_refuses_symlink_lock_path",
        reason="requires creating a file symlink at the lock path",
        equivalent_coverage="test_windows_safe_contracts.WindowsSafeContractsTests.test_lock_path_physical_after_acquire",
        platforms=frozenset({"win32"}),
    ),
    Exclusion(
        test_id_suffix="test_atomic_write_refuses_symlink_dest_without_following",
        reason="requires creating a file symlink",
        equivalent_coverage="test_windows_safe_contracts.WindowsSafeContractsTests.test_atomic_write_physical_roundtrip_portable",
        platforms=frozenset({"win32"}),
    ),
    Exclusion(
        test_id_suffix="test_atomic_write_refuses_when_dest_swapped_to_symlink_before_call",
        reason="requires creating a file symlink",
        equivalent_coverage="test_windows_safe_contracts.WindowsSafeContractsTests.test_atomic_write_physical_roundtrip_portable",
        platforms=frozenset({"win32"}),
    ),
    Exclusion(
        test_id_suffix="test_simulated_symlink_swap_before_open_refuses",
        reason="requires creating a file symlink",
        equivalent_coverage="test_windows_safe_contracts.WindowsSafeContractsTests.test_path_is_symlink_false_for_physical",
        platforms=frozenset({"win32"}),
    ),
    Exclusion(
        test_id_suffix="test_detect_cursor_symlink_readlink_only",
        reason="requires creating a directory symlink for .cursor",
        equivalent_coverage="test_windows_safe_contracts.WindowsSafeContractsTests.test_physical_cursor_tree_after_install",
        platforms=frozenset({"win32"}),
    ),
    Exclusion(
        test_id_suffix="test_plan_includes_migrate_symlink",
        reason="requires creating a directory symlink for .cursor",
        equivalent_coverage="test_windows_safe_contracts.WindowsSafeContractsTests.test_physical_cursor_tree_after_install",
        platforms=frozenset({"win32"}),
    ),
    Exclusion(
        test_id_suffix="test_dry_run_writes_nothing",
        reason="requires creating a directory symlink for .cursor",
        equivalent_coverage="test_windows_safe_contracts.WindowsSafeContractsTests.test_plan_dry_run_no_writes_unicode_target",
        platforms=frozenset({"win32"}),
    ),
    Exclusion(
        test_id_suffix="test_migrate_success_outside_untouched_consumer_preserved",
        reason="requires creating a directory symlink for .cursor",
        equivalent_coverage="test_windows_safe_contracts.WindowsSafeContractsTests.test_physical_cursor_tree_after_install",
        platforms=frozenset({"win32"}),
    ),
    Exclusion(
        test_id_suffix="test_relative_symlink_migrate",
        reason="requires creating a directory symlink for .cursor",
        equivalent_coverage="test_windows_safe_contracts.WindowsSafeContractsTests.test_physical_cursor_tree_after_install",
        platforms=frozenset({"win32"}),
    ),
    Exclusion(
        test_id_suffix="test_rollback_restores_symlink",
        reason="requires creating a directory symlink for .cursor",
        equivalent_coverage="test_windows_safe_contracts.WindowsSafeContractsTests.test_rollback_restores_bytes_portable_modes",
        platforms=frozenset({"win32"}),
    ),
    Exclusion(
        test_id_suffix="test_file_symlink_elsewhere_still_fail_closed",
        reason="requires creating a file symlink",
        equivalent_coverage="test_windows_safe_contracts.WindowsSafeContractsTests.test_path_is_symlink_false_for_physical",
        platforms=frozenset({"win32"}),
    ),
]

# Existing POSIX-only skips in ide_development_tests leave Windows without a
# cross-process proof. Matrix supplies ``test_cross_process_lock_matrix`` on all
# platforms — no exclusion needed for those skipped methods (they self-skip).


def active_exclusions() -> List[Exclusion]:
    """Return exclusions that apply on the current platform."""
    out: List[Exclusion] = []
    if is_windows() and not can_create_symlinks():
        out.extend(_SYMLINK_CREATION_EXCLUSIONS)
    return out


def should_exclude(test_id: str, exclusions: Optional[Iterable[Exclusion]] = None) -> Optional[Exclusion]:
    """Return the matching Exclusion if ``test_id`` should be skipped."""
    rules = list(exclusions) if exclusions is not None else active_exclusions()
    for rule in rules:
        if sys.platform not in rule.platforms and "*" not in rule.platforms:
            continue
        if test_id.endswith(rule.test_id_suffix) or f".{rule.test_id_suffix}" in test_id:
            return rule
    return None


def exclusion_summary(exclusions: Optional[Iterable[Exclusion]] = None) -> List[dict]:
    rules = list(exclusions) if exclusions is not None else active_exclusions()
    return [
        {
            "testIdSuffix": e.test_id_suffix,
            "reason": e.reason,
            "equivalentCoverage": e.equivalent_coverage,
            "platforms": sorted(e.platforms),
        }
        for e in rules
    ]


def excluded_suffixes() -> Set[str]:
    return {e.test_id_suffix for e in active_exclusions()}
