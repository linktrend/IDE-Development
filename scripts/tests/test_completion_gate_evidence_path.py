from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.gitops import completion_gate


class CompletionEvidencePathTests(unittest.TestCase):
    def _repo(self, root: Path) -> Path:
        repo = root / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q", "-b", "development"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.email", "tests@example.invalid"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "Tests"], cwd=repo, check=True)
        (repo / "README.md").write_text("fixture\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-q", "-m", "seed"], cwd=repo, check=True)
        subprocess.run(["git", "switch", "-q", "-c", "issue/1-evidence"], cwd=repo, check=True)
        return repo

    def test_default_path_is_git_common_dir_and_exact_head_bound(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = self._repo(Path(td))
            sha = completion_gate.head_sha(repo)
            path = completion_gate.default_evidence_path(repo, sha)
            self.assertTrue(str(path).startswith(str((repo / ".git").resolve())))
            self.assertFalse(str(path).startswith(str((repo / ".linktrend").resolve())))
            self.assertIn(sha[:12], path.name)

    def test_default_write_does_not_dirty_candidate_tree(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = self._repo(Path(td))
            args = argparse.Namespace(
                workdir=str(repo),
                classification="tests",
                acceptance="default evidence path remains out of tree",
                command=["0|bounded fixture"],
                docs_justification="",
                evidence_file=None,
                scoped_diff=False,
                focused_tests=False,
                independent_review=False,
                manifest_evidence=False,
                proof_class="",
            )
            self.assertEqual(completion_gate.cmd_write_evidence(args), completion_gate.EXIT_OK)
            sha = completion_gate.head_sha(repo)
            path = completion_gate.default_evidence_path(repo, sha)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["headSha"], sha)
            status = subprocess.run(
                ["git", "status", "--porcelain"], cwd=repo, text=True, capture_output=True, check=True
            )
            self.assertEqual(status.stdout, "")

    def test_linked_worktree_uses_shared_git_common_dir(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            repo = self._repo(root)
            linked = root / "linked"
            subprocess.run(
                ["git", "worktree", "add", "-q", "-b", "issue/2-linked", str(linked), "HEAD"],
                cwd=repo,
                check=True,
            )
            sha = completion_gate.head_sha(linked)
            path = completion_gate.default_evidence_path(linked, sha)
            self.assertTrue(str(path).startswith(str((repo / ".git").resolve())))
            self.assertFalse(str(path).startswith(str(linked.resolve())))


if __name__ == "__main__":
    unittest.main()
