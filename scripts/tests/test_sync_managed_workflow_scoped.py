#!/usr/bin/env python3
"""Disposable tests for the guarded single-workflow materializer."""

from __future__ import annotations

import hashlib
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "sync-managed-workflows.sh"
SOURCE = ROOT / "core" / "github" / "managed-workflows" / "linktrend-integrator-merge.yml"
SOURCE_SHA = "1b2cd6fc2fc234391b716224d946d50fabc9fae0e3020a41b3bc00a6b032c0a1"
OLD_SHA = "f33260afcc8adf30c151838c58a558d6e400b1c4776ce77e5e04b73013d52448"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def original_workflow() -> bytes:
    return subprocess.run(
        ["git", "show", "HEAD:core/github/managed-workflows/linktrend-integrator-merge.yml"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
    ).stdout


class ScopedWorkflowSyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.old_bytes = original_workflow()
        cls.new_bytes = SOURCE.read_bytes()
        if sha256(cls.old_bytes) != OLD_SHA or sha256(cls.new_bytes) != SOURCE_SHA:
            raise AssertionError("frozen source preimages changed; refresh this test from an approved candidate")

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="scoped-workflow-sync-")
        self.addCleanup(self.temp.cleanup)
        self.target = Path(self.temp.name) / "consumer"
        self.workflow_dir = self.target / ".github" / "workflows"
        self.workflow_dir.mkdir(parents=True)
        self.dest = self.workflow_dir / "linktrend-integrator-merge.yml"
        self.dest.write_bytes(self.old_bytes)
        os.chmod(self.dest, 0o640)
        (self.target / ".github" / "linktrend-delivery-mode.json").write_text('{"untouched":true}\n')
        (self.workflow_dir / "custom-publish.yml").write_text("consumer-owned\n")
        (self.target / ".git").mkdir()
        (self.target / ".git" / "index-sentinel").write_bytes(b"git metadata sentinel")

    def run_sync(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "bash", str(SCRIPT), str(self.target),
                "--only-workflow", "linktrend-integrator-merge.yml",
                "--expected-source-sha256", SOURCE_SHA,
                "--expected-target-sha256", OLD_SHA,
                *extra,
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

    def test_updates_only_guarded_workflow_and_preserves_mode(self) -> None:
        before_other = {
            path.relative_to(self.target): path.read_bytes()
            for path in self.target.rglob("*")
            if path.is_file() and path != self.dest
        }
        result = self.run_sync()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(self.dest.read_bytes(), self.new_bytes)
        self.assertEqual(self.dest.stat().st_mode & 0o777, 0o640)
        after_other = {
            path.relative_to(self.target): path.read_bytes()
            for path in self.target.rglob("*")
            if path.is_file() and path != self.dest
        }
        self.assertEqual(after_other, before_other)
        self.assertEqual(sorted(path.name for path in self.workflow_dir.iterdir()), [
            "custom-publish.yml", "linktrend-integrator-merge.yml"
        ])

    def test_dry_run_is_project_and_git_metadata_read_only(self) -> None:
        dest_stat = self.dest.stat()
        entries_before = sorted(str(path.relative_to(self.target)) for path in self.target.rglob("*"))
        git_before = (self.target / ".git" / "index-sentinel").read_bytes()
        result = self.run_sync("--dry-run")
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("DRY-RUN: would update only", result.stdout)
        self.assertEqual(self.dest.read_bytes(), self.old_bytes)
        self.assertEqual(self.dest.stat().st_mtime_ns, dest_stat.st_mtime_ns)
        self.assertEqual(self.dest.stat().st_mode & 0o777, 0o640)
        self.assertEqual(sorted(str(path.relative_to(self.target)) for path in self.target.rglob("*")), entries_before)
        self.assertEqual((self.target / ".git" / "index-sentinel").read_bytes(), git_before)

    def test_wrong_source_or_target_preimage_fails_without_writing(self) -> None:
        before = self.dest.read_bytes()
        wrong_source = self.run_sync("--expected-source-sha256", "0" * 64)
        self.assertNotEqual(wrong_source.returncode, 0)
        self.assertIn("source SHA-256 mismatch", wrong_source.stdout)
        wrong_target = subprocess.run(
            ["bash", str(SCRIPT), str(self.target), "--only-workflow", "linktrend-integrator-merge.yml",
             "--expected-source-sha256", SOURCE_SHA, "--expected-target-sha256", "0" * 64],
            cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        self.assertNotEqual(wrong_target.returncode, 0)
        self.assertIn("target SHA-256 mismatch", wrong_target.stdout)
        self.assertEqual(self.dest.read_bytes(), before)

    def test_missing_destination_is_rejected_without_creation(self) -> None:
        self.dest.unlink()
        result = self.run_sync()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("destination must be an existing regular non-symlink file", result.stdout)
        self.assertFalse(self.dest.exists())

    def test_unsupported_workflow_is_rejected(self) -> None:
        result = subprocess.run(
            ["bash", str(SCRIPT), str(self.target), "--only-workflow", "custom-publish.yml",
             "--expected-source-sha256", SOURCE_SHA, "--expected-target-sha256", OLD_SHA],
            cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsupported --only-workflow", result.stdout)
        self.assertEqual(self.dest.read_bytes(), self.old_bytes)

    def test_symlink_destination_and_parent_are_rejected(self) -> None:
        self.dest.unlink()
        outside = self.target / "outside.yml"
        outside.write_bytes(self.old_bytes)
        self.dest.symlink_to(outside)
        linked_dest = self.run_sync()
        self.assertNotEqual(linked_dest.returncode, 0)
        self.assertIn("non-symlink", linked_dest.stdout)
        self.dest.unlink()
        self.dest.write_bytes(self.old_bytes)

        workflows = self.workflow_dir
        real_workflows = self.target / ".github" / "workflows-real"
        workflows.rename(real_workflows)
        workflows.symlink_to(real_workflows, target_is_directory=True)
        linked_parent = self.run_sync()
        self.assertNotEqual(linked_parent.returncode, 0)
        self.assertIn("destination parents", linked_parent.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
