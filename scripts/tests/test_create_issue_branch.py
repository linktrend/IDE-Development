"""Temp-repo tests for Ledger-ID issue branches. No network."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.gitops import create_issue_branch

SCRIPT = Path(create_issue_branch.__file__).resolve()


def run_git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false", *args],
        cwd=str(cwd),
        check=check,
        text=True,
        capture_output=True,
    )


class CreateIssueBranchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.origin = root / "origin.git"
        self.work = root / "work"
        run_git(root, "init", "--bare", "-q", str(self.origin))
        run_git(root, "init", "-q", "-b", "development", str(self.work))
        run_git(self.work, "config", "user.email", "t@example.com")
        run_git(self.work, "config", "user.name", "t")
        run_git(self.work, "config", "commit.gpgsign", "false")
        (self.work / "README").write_text("base\n", encoding="utf-8")
        run_git(self.work, "add", "README")
        run_git(self.work, "commit", "-q", "-m", "init")
        run_git(self.work, "remote", "add", "origin", str(self.origin))
        run_git(self.work, "push", "-q", "-u", "origin", "development")
        self.base_sha = run_git(self.work, "rev-parse", "HEAD").stdout.strip()
        hooks = self.work / ".git" / "hooks"
        hooks.mkdir(exist_ok=True)
        hook = hooks / "pre-push"
        hook.write_text("#!/bin/sh\necho HOOKED\nexit 1\n", encoding="utf-8")
        hook.chmod(0o755)
        run_git(self.work, "config", "core.hooksPath", str(hooks))

    def invoke(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.pop("GIT_DIR", None)
        env.pop("GIT_WORK_TREE", None)
        return subprocess.run(
            ["python3", str(SCRIPT), "--workdir", str(self.work), *args],
            text=True,
            capture_output=True,
            env=env,
            check=False,
        )

    def test_valid_create_pushes_and_skips_hooks(self) -> None:
        proc = self.invoke("--id", "IDE-42", "--slug", "fix-login")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["id"], "IDE-42")
        self.assertEqual(payload["branch"], "issue/IDE-42-fix-login")
        self.assertEqual(payload["base"], "development")
        self.assertEqual(payload["baseSha"], self.base_sha)
        self.assertTrue(payload["pushed"])
        self.assertEqual(payload["worktree"], str(self.work.resolve()))
        remote = run_git(self.work, "ls-remote", "--heads", "origin", "issue/IDE-42-fix-login")
        self.assertIn(self.base_sha, remote.stdout)
        self.assertNotIn("HOOKED", proc.stderr)
        head = run_git(self.work, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        self.assertEqual(head, "issue/IDE-42-fix-login")

    def test_description_derives_slug(self) -> None:
        proc = self.invoke("--id", "IDE-7", "--no-push", "Fix the Login")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["branch"], "issue/IDE-7-fix-the-login")
        self.assertFalse(payload["pushed"])

    def test_reuse_does_not_reset_unique_work(self) -> None:
        first = self.invoke("--id", "IDE-42", "--slug", "fix-login", "--no-push")
        self.assertEqual(first.returncode, 0, first.stderr)
        (self.work / "README").write_text("changed\n", encoding="utf-8")
        run_git(self.work, "add", "README")
        run_git(self.work, "commit", "-q", "-m", "unique")
        unique = run_git(self.work, "rev-parse", "HEAD").stdout.strip()
        run_git(self.work, "checkout", "-q", "development")
        second = self.invoke("--id", "IDE-42", "--slug", "fix-login", "--no-push")
        self.assertEqual(second.returncode, 0, second.stderr)
        payload = json.loads(second.stdout)
        self.assertEqual(payload["branch"], "issue/IDE-42-fix-login")
        self.assertEqual(payload["baseSha"], self.base_sha)
        self.assertFalse(payload["pushed"])
        head = run_git(self.work, "rev-parse", "HEAD").stdout.strip()
        self.assertEqual(head, unique)

    def test_diverged_local_and_remote_reports_instead_of_reset(self) -> None:
        created = self.invoke("--id", "IDE-42", "--slug", "fix-login")
        self.assertEqual(created.returncode, 0, created.stderr)
        (self.work / "README").write_text("local\n", encoding="utf-8")
        run_git(self.work, "add", "README")
        run_git(self.work, "commit", "-q", "-m", "local only")
        local = run_git(self.work, "rev-parse", "HEAD").stdout.strip()
        other = Path(self.tmp.name) / "other"
        run_git(self.work, "clone", "-q", str(self.origin), str(other))
        run_git(other, "config", "user.email", "t@example.com")
        run_git(other, "config", "user.name", "t")
        run_git(other, "config", "commit.gpgsign", "false")
        run_git(other, "checkout", "-q", "issue/IDE-42-fix-login")
        (other / "README").write_text("remote\n", encoding="utf-8")
        run_git(other, "add", "README")
        run_git(other, "commit", "-q", "-m", "remote only")
        run_git(other, "push", "-q", "origin", "issue/IDE-42-fix-login")
        run_git(self.work, "checkout", "-q", "development")
        proc = self.invoke("--id", "IDE-42", "--slug", "fix-login", "--no-push")
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("lose work", proc.stderr)
        self.assertIn("Project orchestrator", proc.stderr)
        still = run_git(self.work, "rev-parse", "issue/IDE-42-fix-login").stdout.strip()
        self.assertEqual(still, local)

    def test_invalid_id_and_missing_id(self) -> None:
        missing = self.invoke("--slug", "fix-login")
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn("Project orchestrator", missing.stderr)
        self.assertNotIn("{", missing.stdout)
        for bad in ("ide-42", "IDE-0", "I-1", "IDE-042", "TOOLONGPREFIX-1"):
            proc = self.invoke("--id", bad, "--slug", "fix-login", "--no-push")
            self.assertNotEqual(proc.returncode, 0, bad)
            self.assertIn("Project orchestrator", proc.stderr)

    def test_invalid_slug(self) -> None:
        for bad in ("Fix", "has space", "-leading", "trailing-", "a--b", "a" * 49):
            proc = self.invoke("--id", "IDE-42", f"--slug={bad}", "--no-push")
            self.assertNotEqual(proc.returncode, 0, bad)
            self.assertIn("invalid slug", proc.stderr)
        remote = run_git(self.work, "ls-remote", "--heads", "origin")
        self.assertNotIn("issue/", remote.stdout)

    def test_worktree_mode_leaves_main_checkout(self) -> None:
        wt = Path(self.tmp.name) / "wt"
        proc = self.invoke("--id", "IDE-9", "--slug", "wt-mode", "--worktree", str(wt), "--no-push")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["worktree"], str(wt.resolve()))
        self.assertFalse(payload["pushed"])
        main_head = run_git(self.work, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        self.assertEqual(main_head, "development")
        wt_head = run_git(wt, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        self.assertEqual(wt_head, "issue/IDE-9-wt-mode")
        self.assertEqual(run_git(wt, "rev-parse", "HEAD").stdout.strip(), self.base_sha)

    def test_no_push_does_not_publish(self) -> None:
        proc = self.invoke("--id", "IDE-3", "--slug", "local-only", "--no-push")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertFalse(payload["pushed"])
        remote = run_git(self.work, "ls-remote", "--heads", "origin", "issue/IDE-3-local-only")
        self.assertEqual(remote.stdout.strip(), "")
        local = run_git(self.work, "rev-parse", "--verify", "refs/heads/issue/IDE-3-local-only")
        self.assertEqual(local.stdout.strip(), self.base_sha)


if __name__ == "__main__":
    unittest.main()
