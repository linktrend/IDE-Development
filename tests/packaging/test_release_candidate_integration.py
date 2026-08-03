"""Packaging integration tests for release-candidate create/verify."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ENTRYPOINT = REPO_ROOT / "scripts" / "ide-development.py"
BUILD_DIR = REPO_ROOT / "build" / "release-candidate"


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
        import os

        env = os.environ.copy()
        env["PYTHONPATH"] = str(REPO_ROOT / "scripts")
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
        self.assertEqual(self.create_payload["packageVersion"], "2.1.0")
        self.assertTrue(self.create_payload["summary"]["reproducible"])
        self.assertIsNotNone(self.create_payload.get("installVerify"))
        self.assertEqual(self.create_payload["installVerify"]["installedVersion"], "2.1.0")

    def test_archives_exist_with_checksums(self) -> None:
        self.assertTrue(BUILD_DIR.is_dir(), "build/release-candidate missing")
        tar = BUILD_DIR / "ide-development-managed-core-2.1.0.tar.gz"
        zip_path = BUILD_DIR / "ide-development-managed-core-2.1.0.zip"
        meta = BUILD_DIR / "release-candidate.json"
        sums = BUILD_DIR / "SHA256SUMS.json"
        for path in (tar, zip_path, meta, sums):
            self.assertTrue(path.is_file(), path.name)
        meta_obj = json.loads(meta.read_text(encoding="utf-8"))
        self.assertEqual(meta_obj["packageVersion"], "2.1.0")
        self.assertEqual(len(meta_obj["archives"]), 2)
        for archive in meta_obj["archives"]:
            self.assertTrue(archive["path"].startswith("build/release-candidate/"))
            self.assertTrue(archive["sha256"].startswith("sha256:"))
        # Provenance identities are repo-relative only.
        for ident in meta_obj["provenance"]["identities"]:
            self.assertFalse(ident.startswith("/"))
            self.assertNotIn(":", ident.split("/")[0])

    def test_verify_subcommand_reports_version_and_checksum(self) -> None:
        tar = BUILD_DIR / "ide-development-managed-core-2.1.0.tar.gz"
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
        import os

        env = os.environ.copy()
        env["PYTHONPATH"] = str(REPO_ROOT / "scripts")
        proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        raw = proc.stdout
        if "--- json ---" in raw:
            raw = raw.split("--- json ---", 1)[1]
        payload = json.loads(raw)
        self.assertEqual(payload["installedVersion"], "2.1.0")
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
        import os

        env = os.environ.copy()
        env["PYTHONPATH"] = str(REPO_ROOT / "scripts")
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
