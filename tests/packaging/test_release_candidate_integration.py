"""Packaging integration tests for release-candidate create/verify."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

from ide_development.constants import PACKAGE_VERSION_TARGET

REPO_ROOT = Path(__file__).resolve().parents[2]
ENTRYPOINT = REPO_ROOT / "scripts" / "ide-development.py"
BUILD_DIR = REPO_ROOT / "build" / "release-candidate"


def runtime_baseline_environment() -> dict[str, str]:
    sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        text=True,
    ).strip()
    branch = subprocess.check_output(
        ["git", "branch", "--show-current"],
        cwd=REPO_ROOT,
        text=True,
    ).strip()
    return {
        "LINKTREND_TARGET_BASELINE_SHA": sha,
        "LINKTREND_TARGET_BASELINE_REF": f"refs/heads/{branch}",
    }


class ReleaseCandidateIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        # Concurrent WP1 lanes leave the tree dirty; production still refuses without flag.
        cmd = [
            sys.executable,
            str(ENTRYPOINT),
            "release-candidate",
            "create",
            "--allow-dirty",
            "--skip-evidence",
            "--json",
        ]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(REPO_ROOT / "scripts")
        env.update(runtime_baseline_environment())
        proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, env=env)
        cls.create_proc = proc
        cls.create_payload = None
        if proc.returncode == 0:
            raw = proc.stdout
            if "--- json ---" in raw:
                raw = raw.split("--- json ---", 1)[1]
            cls.create_payload = json.loads(raw)

    def test_create_succeeded(self) -> None:
        self.assertEqual(
            self.create_proc.returncode,
            0,
            self.create_proc.stderr + self.create_proc.stdout,
        )
        self.assertIsNotNone(self.create_payload)
        assert self.create_payload is not None
        self.assertTrue(self.create_payload["ok"])
        self.assertEqual(self.create_payload["packageVersion"], PACKAGE_VERSION_TARGET)
        self.assertTrue(self.create_payload["summary"]["reproducible"])
        self.assertIsNotNone(self.create_payload.get("installVerify"))
        self.assertEqual(self.create_payload["installVerify"]["installedVersion"], PACKAGE_VERSION_TARGET)

    def test_archives_exist_with_checksums(self) -> None:
        self.assertTrue(BUILD_DIR.is_dir(), "build/release-candidate missing")
        tar = BUILD_DIR / f"ide-development-managed-core-{PACKAGE_VERSION_TARGET}.tar.gz"
        zip_path = BUILD_DIR / f"ide-development-managed-core-{PACKAGE_VERSION_TARGET}.zip"
        meta = BUILD_DIR / "release-candidate.json"
        sums = BUILD_DIR / "SHA256SUMS.json"
        for path in (tar, zip_path, meta, sums):
            self.assertTrue(path.is_file(), path.name)
        meta_obj = json.loads(meta.read_text(encoding="utf-8"))
        self.assertEqual(meta_obj["packageVersion"], PACKAGE_VERSION_TARGET)
        self.assertEqual(len(meta_obj["archives"]), 2)
        for archive in meta_obj["archives"]:
            self.assertTrue(archive["path"].startswith("build/release-candidate/"))
            self.assertTrue(archive["sha256"].startswith("sha256:"))
        # Provenance identities are repo-relative only.
        for ident in meta_obj["provenance"]["identities"]:
            self.assertFalse(ident.startswith("/"))
            self.assertNotIn(":", ident.split("/")[0])

    def test_verify_subcommand_reports_version_and_checksum(self) -> None:
        tar = BUILD_DIR / f"ide-development-managed-core-{PACKAGE_VERSION_TARGET}.tar.gz"
        if not tar.is_file():
            self.skipTest("archive missing from create")
        cmd = [
            sys.executable,
            str(ENTRYPOINT),
            "release-candidate",
            "verify",
            "--archive",
            str(tar),
            "--json",
        ]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(REPO_ROOT / "scripts")
        proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        raw = proc.stdout
        if "--- json ---" in raw:
            raw = raw.split("--- json ---", 1)[1]
        payload = json.loads(raw)
        self.assertEqual(payload["installedVersion"], PACKAGE_VERSION_TARGET)
        self.assertTrue(payload["packageChecksum"].startswith("sha256:"))

    def test_dirty_refusal_via_cli(self) -> None:
        from ide_development import release_candidate as rc

        if not rc.worktree_is_dirty():
            self.skipTest("worktree clean")
        cmd = [
            sys.executable,
            str(ENTRYPOINT),
            "release-candidate",
            "create",
            "--skip-evidence",
            "--skip-install-verify",
            "--json",
        ]
        env = os.environ.copy()
        env["PYTHONPATH"] = str(REPO_ROOT / "scripts")
        env.update(runtime_baseline_environment())
        proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, env=env)
        self.assertNotEqual(proc.returncode, 0)
        raw = proc.stdout
        if "--- json ---" in raw:
            raw = raw.split("--- json ---", 1)[1]
        payload = json.loads(raw)
        self.assertFalse(payload["ok"])
        self.assertIn("dirty", payload["error"].lower())


if __name__ == "__main__":
    unittest.main()
