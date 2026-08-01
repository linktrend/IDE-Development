"""Shared constants for the IDE Development installer."""

from __future__ import annotations

from pathlib import PurePosixPath

# Exit codes (stable contract — docs/contracts/MANAGED-CORE-V2.md)
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_DRIFT = 10
EXIT_CONFLICT = 11
EXIT_INVALID_PACKAGE = 12
EXIT_ROLLBACK_FAILURE = 13

SCHEMA_VERSION = 1
INSTALLER_VERSION = "2.0.0"
PACKAGE_NAME = "ide-development-managed-core"

# Committed managed-core root inside a consumer repository
MANAGED_CORE_DIR = ".ide-development"
INSTALLED_STATE_REL = PurePosixPath(".ide-development/installed-state.json")

# Package-relative defaults (WP1 layout)
DEFAULT_MANIFEST_REL = PurePosixPath("core/managed-core/MANIFEST.json")
# Canonical Wave 1 path only — do not reintroduce duplicate catalogs.
DEFAULT_MIGRATION_CATALOG_REL = PurePosixPath("core/managed-core/migrations/catalog.json")
DEFAULT_MIGRATION_CATALOG_RELS = (DEFAULT_MIGRATION_CATALOG_REL,)
DEFAULT_PACKAGE_VERSION_REL = PurePosixPath("core/managed-core/VERSION")
DEFAULT_PACKAGE_VERSION_FALLBACK_REL = PurePosixPath("VERSION")

# Git-local metadata (not committed)
GIT_META_DIR = PurePosixPath(".git/ide-development")
TX_CURRENT_REL = GIT_META_DIR / "current-transaction"
TX_LAST_REL = GIT_META_DIR / "last-transaction"
LOCK_REL = GIT_META_DIR / "lock"

DEFAULT_MARKER_BEGIN = "<!-- BEGIN LINKTREND-IDE-MANAGED -->"
DEFAULT_MARKER_END = "<!-- END LINKTREND-IDE-MANAGED -->"

OWNERSHIP_CLASSES = frozenset(
    {
        "managed",
        "managed-core",
        "managed-entrypoint",
        "managed-marker",
        "optional",
        "consumer-preserve",
        "external-state",
    }
)
MERGE_STRATEGIES = frozenset(
    {
        "replace",
        "create-only",
        "remove-if-matches",
        "marker-upsert",
        "external-plan-only",
    }
)
# Discovery/runtime adapter scope (not an OS filter)
PLATFORMS = frozenset({"all", "cursor", "codex", "github", "none"})
# Host OS applicability
OS_FILTERS = frozenset({"all", "posix", "windows", "darwin", "linux"})
