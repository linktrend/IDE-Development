"""Shared paths for clean-room acceptance tests."""

from __future__ import annotations

from pathlib import Path

CLEANROOM_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = CLEANROOM_ROOT.parents[1]
FIXTURES_DIR = CLEANROOM_ROOT / "fixtures"
PACKAGE_FIXTURE = FIXTURES_DIR / "extracted-rc-package"
INSTALLER_ENTRY = REPO_ROOT / "scripts" / "ide-development.py"
INSTALLER_PACKAGE_DIR = REPO_ROOT / "scripts" / "ide_development"
# Future Lane D extract location (optional preference).
LANE_D_RC_CANDIDATES = (
    REPO_ROOT / "artifacts" / "release-candidate" / "extracted",
    REPO_ROOT / "dist" / "release-candidate" / "extracted",
    REPO_ROOT / "build" / "release-candidate" / "extracted",
)
BB_ROOT = REPO_ROOT / "tests" / "managed-core-migration-bb"
BB_LIVE_PACKAGE = BB_ROOT / "fixtures" / "live-package"
