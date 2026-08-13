"""W2-P2 concurrent-development synchronization and conflict probes."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.gitops.phase_integrator import PhaseLifecycleError, synchronize_phase


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)
    if result.returncode:
        raise AssertionError(result.stderr or result.stdout)
    return result.stdout.strip()


class ConcurrentFeatureTests(unittest.TestCase):
    def repo(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        git(root, "init", "-q", "-b", "development")
        git(root, "config", "user.email", "tests@example.invalid")
        git(root, "config", "user.name", "W2-P2 tests")
        (root / "shared.txt").write_text("base\n", encoding="utf-8")
        git(root, "add", "shared.txt")
        git(root, "commit", "-qm", "base")
        git(root, "checkout", "-qb", "phase/demo")
        return tmp, root

    def test_synchronization_preserves_concurrent_feature_and_phase_work(self) -> None:
        tmp, root = self.repo()
        self.addCleanup(tmp.cleanup)
        (root / "phase.txt").write_text("phase work\n", encoding="utf-8")
        git(root, "add", "phase.txt")
        git(root, "commit", "-qm", "phase work")
        git(root, "checkout", "development")
        (root / "concurrent.txt").write_text("concurrent feature\n", encoding="utf-8")
        git(root, "add", "concurrent.txt")
        git(root, "commit", "-qm", "concurrent feature")
        result = synchronize_phase(root, phase_branch="phase/demo", development_branch="development")
        self.assertEqual(result["status"], "synchronized")
        self.assertEqual(git(root, "rev-parse", "--abbrev-ref", "HEAD"), "phase/demo")
        self.assertTrue((root / "phase.txt").is_file())
        self.assertTrue((root / "concurrent.txt").is_file())
        self.assertTrue(git(root, "merge-base", "--is-ancestor", result["developmentSha"], result["phaseSha"]) == "")

    def test_conflict_blocks_without_prefer_incoming_or_ours(self) -> None:
        tmp, root = self.repo()
        self.addCleanup(tmp.cleanup)
        (root / "shared.txt").write_text("phase version\n", encoding="utf-8")
        git(root, "add", "shared.txt")
        git(root, "commit", "-qm", "phase conflicting edit")
        phase_tip = git(root, "rev-parse", "HEAD")
        git(root, "checkout", "development")
        (root / "shared.txt").write_text("concurrent version\n", encoding="utf-8")
        git(root, "add", "shared.txt")
        git(root, "commit", "-qm", "concurrent conflicting edit")
        result = synchronize_phase(root, phase_branch="phase/demo", development_branch="development")
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["detail"], "merge_conflict")
        self.assertEqual(git(root, "rev-parse", "phase/demo"), phase_tip)
        self.assertEqual(git(root, "rev-parse", "--abbrev-ref", "HEAD"), "phase/demo")
        self.assertEqual((root / "shared.txt").read_text(encoding="utf-8"), "phase version\n")
        self.assertEqual(git(root, "status", "--porcelain"), "")

    def test_worker_cannot_synchronize_phase(self) -> None:
        tmp, root = self.repo()
        self.addCleanup(tmp.cleanup)
        with self.assertRaisesRegex(PhaseLifecycleError, "non_integrator_mutation"):
            synchronize_phase(root, phase_branch="phase/demo", actor="worker")


if __name__ == "__main__":
    unittest.main()
