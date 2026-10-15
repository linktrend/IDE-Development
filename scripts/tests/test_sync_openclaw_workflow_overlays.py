#!/usr/bin/env python3
"""Exercise the fixed OpenClaw overlay/deletion guards on disposable payloads."""
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/sync-managed-workflows.sh"
FIXTURES = ROOT / "scripts/tests/fixtures/bugbot-a40/openclaw"
OVERLAYS = ROOT / "core/github/managed-workflows/repository-overlays/linktrend-openclaw_prime"
ROWS = {
    "linktrend-integrator-merge.yml": ("Full.yml", "47b8a9b911da549e55c7edea80d45755bc34b757972627155c65fb9568e3e8c7", "f8fe760a115424d27984c042112390c52993971dcb675b8d2b307115093c7a37"),
    "linktrend-repair-observer.yml": ("RepairObserver.yml", "76d604485c21f16c2e96d387c53ea7f1f01e35b82bf363369eff553bdcbaee35", "c82a719f88f913cdb4184199d53c82c2849b8d926e110497447a965ad0ae06fa"),
    "linktrend-review-gate.yml": ("ReviewGate.removed", "5afc95e4c8ea08acfed9374968a9d8832f00c4db7b4ccd9e91f4e37f14eb1f4b", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
}


def snapshot(root):
    return {str(p.relative_to(root)): (p.read_bytes(), p.stat().st_mode & 0o777, p.stat().st_mtime_ns)
            for p in root.rglob("*") if p.is_file()}


class OpenClawOverlayTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="openclaw-scoped-overlay-")
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.workflows = self.root / ".github/workflows"
        self.workflows.mkdir(parents=True)
        for name, (overlay, before, after) in ROWS.items():
            payload = (FIXTURES / name).read_bytes()
            self.assertEqual(hashlib.sha256(payload).hexdigest(), before)
            self.assertEqual(hashlib.sha256((OVERLAYS / overlay).read_bytes()).hexdigest(), after)
            (self.workflows / name).write_bytes(payload)
            os.chmod(self.workflows / name, 0o640)
        (self.root / ".git").mkdir()
        (self.root / ".git/sentinel").write_bytes(b"untouched Git metadata")
        (self.workflows / "ci.yml").write_bytes(b"consumer-owned CI\n")
        (self.root / ".github/linktrend-delivery-mode.json").write_bytes(b"unparsed-owned-config\n")

    def invoke(self, name, *extra):
        _, before, after = ROWS[name]
        return subprocess.run(["bash", str(SCRIPT), str(self.root), "--source-variant", "linktrend-openclaw",
                               "--only-workflow", name, "--expected-source-sha256", after,
                               "--expected-target-sha256", before, *extra], text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    def test_each_dry_run_preserves_all_bytes_modes_mtimes_and_metadata(self):
        for name in ROWS:
            before = snapshot(self.root)
            result = self.invoke(name, "--dry-run")
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("DRY-RUN:", result.stdout)
            self.assertEqual(snapshot(self.root), before)

    def test_each_apply_changes_only_named_workflow_and_preserves_other_metadata(self):
        for name, (overlay, _, _) in ROWS.items():
            before = snapshot(self.root)
            result = self.invoke(name)
            self.assertEqual(result.returncode, 0, result.stdout)
            dest = self.workflows / name
            if name == "linktrend-review-gate.yml":
                self.assertFalse(dest.exists())
            else:
                self.assertEqual(dest.read_bytes(), (OVERLAYS / overlay).read_bytes())
                self.assertEqual(dest.stat().st_mode & 0o777, 0o640)
            ignored = ".github/workflows/" + name
            self.assertEqual({k: v for k, v in snapshot(self.root).items() if k != ignored},
                             {k: v for k, v in before.items() if k != ignored})
        full = (self.workflows / "linktrend-integrator-merge.yml").read_bytes()
        self.assertNotIn(b"@cursor review", full)
        self.assertIn(b"retention-days: 30", full)
        self.assertIn(b"  reconciled-canary:", full)
        observer = (self.workflows / "linktrend-repair-observer.yml").read_bytes()
        self.assertIn(b"  workflow_run:", observer)
        self.assertIn(b"Branch Source Policy", observer)
        self.assertNotIn(b"check_run", observer)

    def test_wrong_fixed_digests_and_actual_preimage_fail_without_writes(self):
        for name in ROWS:
            for option in ("--expected-source-sha256", "--expected-target-sha256"):
                before = snapshot(self.root)
                result = self.invoke(name, option, "0" * 64)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(snapshot(self.root), before)
            dest = self.workflows / name
            dest.write_bytes(dest.read_bytes() + b"changed\n")
            before = snapshot(self.root)
            result = self.invoke(name)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("target SHA-256 mismatch", result.stdout)
            self.assertEqual(snapshot(self.root), before)

    def test_wrong_selector_or_generic_openclaw_template_cannot_apply(self):
        before = snapshot(self.root)
        result = self.invoke("linktrend-integrator-merge.yml", "--only-workflow", "ci.yml")
        self.assertNotEqual(result.returncode, 0)
        result = self.invoke("linktrend-integrator-merge.yml", "--source-variant", "")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(snapshot(self.root), before)

    def test_deletion_cannot_follow_symlink_or_remove_missing_file(self):
        name = "linktrend-review-gate.yml"
        dest = self.workflows / name
        outside = self.root / "outside.yml"
        outside.write_bytes(dest.read_bytes())
        dest.unlink()
        dest.symlink_to(outside)
        result = self.invoke(name)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(outside.read_bytes(), (FIXTURES / name).read_bytes())
        dest.unlink()
        result = self.invoke(name)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(dest.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
