"""Shared paths for migration black-box tests."""

from __future__ import annotations

from pathlib import Path

BB_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BB_ROOT.parents[1]
MIGRATIONS_DIR = REPO_ROOT / "core" / "managed-core" / "migrations"
CATALOG_PATH = MIGRATIONS_DIR / "catalog.json"
SCHEMA_PATH = MIGRATIONS_DIR / "schema.json"
SCENARIOS_PATH = MIGRATIONS_DIR / "scenarios.json"
KNOWN_BYTES_DIR = MIGRATIONS_DIR / "known-bytes"
FIXTURES_DIR = BB_ROOT / "fixtures"

# Legacy duplicate catalog paths — must remain absent after Wave 1 integration.
LEGACY_DUPLICATE_CATALOGS = (
    REPO_ROOT / "core" / "managed-core" / "migration" / "catalog.json",
    REPO_ROOT / "core" / "managed-core" / "migration-catalog.json",
)

INSTALLER_ENTRY = REPO_ROOT / "scripts" / "ide-development.py"
# Hermetic package for live installer E2E probes (independent of dirty system MANIFEST).
LIVE_PACKAGE_DIR = FIXTURES_DIR / "live-package"
