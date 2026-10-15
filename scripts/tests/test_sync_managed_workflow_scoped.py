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
PUBLISH_SOURCE = ROOT / "core" / "github" / "managed-workflows" / "repository-overlays" / "linktrend-LiNKpublish" / "Full.yml"
PUBLISH_PREIMAGE = ROOT / "scripts" / "tests" / "fixtures" / "bugbot-a40" / "publish-full-preimage.yml"
PUBLISH_SOURCE_SHA = "7bb95f1c82f5777572590150f936791002d13fb70bb64252e30fadcc3a4d8d23"
PUBLISH_TARGET_SHA = "5eb82e65c68ae825015beedaeeb1ee7e49ec34677514e55c58ed97ca3b1cb525"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def original_workflow() -> bytes:
    return subprocess.run(
        ["git", "show", "f4236d6fb72089c9b51c94497b1810d06ac86dcd:core/github/managed-workflows/linktrend-integrator-merge.yml"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
    ).stdout


def without_bugbot_job(data: bytes) -> bytes:
    start_marker = b"  bugbot:\n"
    next_marker = b"  reconciled-canary:\n"
    if data.count(start_marker) != 1 or data.count(next_marker) != 1:
        raise AssertionError("Publish Full fixture must contain one bounded Bugbot job")
    start = data.index(start_marker)
    end = data.index(next_marker, start)
    block = data[start:end]
    if block.count(b"\n") != 26 or b"@cursor review" not in block:
        raise AssertionError("Publish Bugbot block changed; do not regenerate the overlay blindly")
    return data[:start] + data[end:]


class ScopedWorkflowSyncTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.old_bytes = original_workflow()
        cls.new_bytes = SOURCE.read_bytes()
        if sha256(cls.old_bytes) != OLD_SHA or sha256(cls.new_bytes) != SOURCE_SHA:
            raise AssertionError("frozen source preimages changed; refresh this test from an approved candidate")
        cls.publish_preimage = PUBLISH_PREIMAGE.read_bytes()
        cls.publish_overlay = PUBLISH_SOURCE.read_bytes()
        if sha256(cls.publish_preimage) != PUBLISH_TARGET_SHA:
            raise AssertionError("frozen LiNKpublish preimage changed; refresh from a separately approved source")
        if sha256(cls.publish_overlay) != PUBLISH_SOURCE_SHA:
            raise AssertionError("fixed LiNKpublish overlay SHA-256 changed")
        if without_bugbot_job(cls.publish_preimage) != cls.publish_overlay:
            raise AssertionError("LiNKpublish overlay must equal its exact root preimage minus only the Bugbot job")

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

    def run_publish_sync(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                "bash", str(SCRIPT), str(self.target),
                "--only-workflow", "linktrend-integrator-merge.yml",
                "--source-variant", "linktrend-publish",
                "--expected-source-sha256", PUBLISH_SOURCE_SHA,
                "--expected-target-sha256", PUBLISH_TARGET_SHA,
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

    def test_publish_overlay_is_exact_bugbot_only_removal_and_applies_only_target(self) -> None:
        self.dest.write_bytes(self.publish_preimage)
        os.chmod(self.dest, 0o640)
        other = {p.relative_to(self.target): p.read_bytes() for p in self.target.rglob("*")
                 if p.is_file() and p != self.dest}
        target_stat = self.dest.stat()
        entries = sorted(str(p.relative_to(self.target)) for p in self.target.rglob("*"))
        dry_run = self.run_publish_sync("--dry-run")
        self.assertEqual(dry_run.returncode, 0, dry_run.stdout)
        self.assertIn("from linktrend-publish", dry_run.stdout)
        self.assertEqual(self.dest.read_bytes(), self.publish_preimage)
        self.assertEqual(self.dest.stat().st_mtime_ns, target_stat.st_mtime_ns)
        self.assertEqual(self.dest.stat().st_mode & 0o777, 0o640)
        self.assertEqual(sorted(str(p.relative_to(self.target)) for p in self.target.rglob("*")), entries)
        self.assertEqual({p.relative_to(self.target): p.read_bytes() for p in self.target.rglob("*")
                          if p.is_file() and p != self.dest}, other)
        result = self.run_publish_sync()
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(self.dest.read_bytes(), self.publish_overlay)
        self.assertEqual(self.dest.stat().st_mode & 0o777, 0o640)
        self.assertEqual({p.relative_to(self.target): p.read_bytes() for p in self.target.rglob("*")
                          if p.is_file() and p != self.dest}, other)
        for preserved in (b"Install hash-locked release-control Python dependencies",
                          b"require_exact_ci_success.py", b"promotion-recovery:",
                          b"name: Linktrend Full Suite"):
            self.assertIn(preserved, self.dest.read_bytes())
        self.assertNotIn(b"@cursor review", self.dest.read_bytes())

    def test_publish_variant_rejects_wrong_selector_or_workflow_path(self) -> None:
        for args, expected_message in (
            (("--source-variant", "publish"), "unsupported --source-variant"),
            (("--only-workflow", "ci.yml"), "unsupported --only-workflow"),
        ):
            result = subprocess.run(
                ["bash", str(SCRIPT), str(self.target), "--only-workflow", "linktrend-integrator-merge.yml",
                 "--source-variant", "linktrend-publish", "--expected-source-sha256", PUBLISH_SOURCE_SHA,
                 "--expected-target-sha256", PUBLISH_TARGET_SHA, *args],
                cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(expected_message, result.stdout)
            self.assertEqual(self.dest.read_bytes(), self.old_bytes)

    def test_publish_variant_preimage_and_generic_source_mismatch_fail_closed(self) -> None:
        self.dest.write_bytes(self.publish_preimage)
        before = self.dest.read_bytes()
        wrong_overlay = self.run_publish_sync("--expected-source-sha256", "0" * 64)
        self.assertNotEqual(wrong_overlay.returncode, 0)
        self.assertIn("source SHA-256 must match the reviewed fixed overlay", wrong_overlay.stdout)
        wrong_publish_target = subprocess.run(
            ["bash", str(SCRIPT), str(self.target), "--only-workflow", "linktrend-integrator-merge.yml",
             "--source-variant", "linktrend-publish", "--expected-source-sha256", PUBLISH_SOURCE_SHA,
             "--expected-target-sha256", "0" * 64],
            cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        self.assertNotEqual(wrong_publish_target.returncode, 0)
        self.assertIn("target SHA-256 must match the reviewed Publish Full preimage", wrong_publish_target.stdout)
        generic = subprocess.run(
            ["bash", str(SCRIPT), str(self.target), "--only-workflow", "linktrend-integrator-merge.yml",
             "--expected-source-sha256", SOURCE_SHA, "--expected-target-sha256", OLD_SHA],
            cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        self.assertNotEqual(generic.returncode, 0)
        self.assertIn("target SHA-256 mismatch", generic.stdout)
        generic_publish_preimage = subprocess.run(
            ["bash", str(SCRIPT), str(self.target), "--only-workflow", "linktrend-integrator-merge.yml",
             "--expected-source-sha256", SOURCE_SHA, "--expected-target-sha256", PUBLISH_TARGET_SHA],
            cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        )
        self.assertNotEqual(generic_publish_preimage.returncode, 0)
        self.assertIn("requires --source-variant linktrend-publish", generic_publish_preimage.stdout)
        self.assertEqual(self.dest.read_bytes(), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
