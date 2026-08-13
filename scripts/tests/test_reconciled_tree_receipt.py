from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.gitops.verify_reconciled_tree import main, state_digest
from scripts.gitops.verify_reconciled_fast_dispatch import main as fast_dispatch_main


class ReconciledTreeReceiptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "repo"
        self.root.mkdir()
        subprocess.run(["git", "-C", str(self.root), "init", "-q"], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "-C", str(self.root), "config", "user.name", "test"], check=True)
        state = {"packageVersion": "2.3.7", "installedAt": "now", "files": {"x": {"contentHash": "sha256:a"}}}
        (self.root / ".ide-development").mkdir()
        (self.root / ".ide-development" / "installed-state.json").write_text(json.dumps(state))
        (self.root / "managed.txt").write_text("exact")
        subprocess.run(["git", "-C", str(self.root), "add", "."], check=True)
        subprocess.run(["git", "-C", str(self.root), "commit", "-qm", "exact"], check=True)
        subprocess.run(["git", "-C", str(self.root), "branch", "-M", "development"], check=True)
        self.commit = subprocess.check_output(["git", "-C", str(self.root), "rev-parse", "HEAD"], text=True).strip()
        self.tree = subprocess.check_output(["git", "-C", str(self.root), "rev-parse", "HEAD^{tree}"], text=True).strip()
        self.state = state
        self.checks = Path(self.tmp.name) / "checks.json"
        self.checks.write_text(json.dumps({"fast": "success", "ci": "success", "security": "success"}))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def args(self) -> list[str]:
        return ["--repo", str(self.root), "--expected-commit", self.commit, "--expected-tree", self.tree,
                "--package-version", "2.3.7", "--installed-state-digest", state_digest(self.state),
                "--checks-json", str(self.checks), "--staging-tree", self.tree, "--main-tree", self.tree]

    def test_exact_tree_is_non_promotable_canary(self) -> None:
        self.assertEqual(main(self.args()), 0)

    def test_rejects_wrong_identity_and_stale_checks(self) -> None:
        for index, replacement in ((3, "f" * 40), (5, "e" * 40), (7, "2.3.8"), (9, "sha256:" + "0" * 64), (13, "0" * 40)):
            args = self.args(); args[index] = replacement
            with self.assertRaises(SystemExit): main(args)
        self.checks.write_text(json.dumps({"fast": "success", "ci": "failure", "security": "success"}))
        with self.assertRaises(SystemExit): main(self.args())

    def test_rejects_changed_managed_file(self) -> None:
        (self.root / "managed.txt").write_text("tampered")
        with self.assertRaises(SystemExit) as error:
            main(self.args())
        self.assertEqual(str(error.exception), "reconciled_canary_managed_drift")

    def test_reconciled_fast_dispatch_binds_only_exact_development_identity(self) -> None:
        args = [
            "--repo", str(self.root), "--expected-repository", "linktrend/example",
            "--actual-repository", "linktrend/example", "--ref", "development",
            "--expected-commit", self.commit, "--expected-tree", self.tree,
            "--package-version", "2.3.7", "--installed-state-digest", state_digest(self.state),
        ]
        self.assertEqual(fast_dispatch_main(args), 0)
        for index, replacement in ((5, "main"), (7, "f" * 40), (9, "e" * 40), (11, "2.3.8"), (13, "sha256:" + "0" * 64)):
            bad = list(args); bad[index] = replacement
            with self.assertRaises(SystemExit):
                fast_dispatch_main(bad)
