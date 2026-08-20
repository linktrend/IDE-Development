"""Adversarial tests for exact runtime candidate-baseline identity."""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.gitops.generated_output_closure import (
    BASELINE_REF_ENV,
    BASELINE_SHA_ENV,
    ClosureError,
    candidate_diff_check,
    resolve_candidate_baseline,
)


ROOT = Path(__file__).resolve().parents[2]


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise AssertionError(result.stderr or result.stdout)
    return result.stdout.strip()


def init_repo() -> tuple[tempfile.TemporaryDirectory[str], Path, str, str]:
    tmp = tempfile.TemporaryDirectory(prefix="candidate-baseline-")
    root = Path(tmp.name) / "repo"
    root.mkdir()
    git(root, "init", "-q", "-b", "development")
    git(root, "config", "user.email", "baseline@example.invalid")
    git(root, "config", "user.name", "Baseline tests")
    git(root, "remote", "add", "origin", str(root / "origin.git"))
    (root / "README.md").write_text("# baseline\n", encoding="utf-8")
    git(root, "add", "README.md")
    git(root, "commit", "-qm", "authoritative target baseline")
    baseline = git(root, "rev-parse", "HEAD")
    git(root, "update-ref", "refs/remotes/origin/development", baseline)
    (root / "candidate.txt").write_text("candidate\n", encoding="utf-8")
    git(root, "add", "candidate.txt")
    git(root, "commit", "-qm", "candidate commit")
    candidate = git(root, "rev-parse", "HEAD")
    return tmp, root, baseline, candidate


def runtime_env(baseline: str, ref: str = "origin/development") -> dict[str, str]:
    return {
        BASELINE_SHA_ENV: baseline,
        BASELINE_REF_ENV: ref,
    }


class CandidateBaselineResolutionTests(unittest.TestCase):
    def test_branch_checkout_requires_distinct_remote_target(self) -> None:
        tmp, root, baseline, candidate = init_repo()
        self.addCleanup(tmp.cleanup)
        self.assertNotEqual(candidate, baseline)
        self.assertEqual(resolve_candidate_baseline(root, environ=runtime_env(baseline)), baseline)

    def test_candidate_equal_baseline_fails_closed(self) -> None:
        tmp, root, baseline, _ = init_repo()
        self.addCleanup(tmp.cleanup)
        git(root, "checkout", "-q", "--detach", baseline)
        with self.assertRaisesRegex(ClosureError, "candidate_baseline_equal_head"):
            resolve_candidate_baseline(root, environ=runtime_env(baseline))

    def test_detached_candidate_binds_to_named_remote_target(self) -> None:
        tmp, root, baseline, candidate = init_repo()
        self.addCleanup(tmp.cleanup)
        git(root, "checkout", "-q", "--detach", candidate)
        self.assertEqual(resolve_candidate_baseline(root, environ=runtime_env(baseline)), baseline)

    def test_detached_candidate_equal_baseline_fails_closed(self) -> None:
        tmp, root, baseline, _ = init_repo()
        self.addCleanup(tmp.cleanup)
        git(root, "checkout", "-q", "--detach", baseline)
        with self.assertRaisesRegex(ClosureError, "candidate_baseline_equal_head"):
            resolve_candidate_baseline(root, environ=runtime_env(baseline))

    def test_local_branch_ref_is_not_authoritative(self) -> None:
        tmp, root, baseline, candidate = init_repo()
        self.addCleanup(tmp.cleanup)
        git(root, "update-ref", "refs/heads/baseline-target", baseline)
        git(root, "checkout", "-q", "--detach", candidate)
        with self.assertRaisesRegex(ClosureError, "candidate_baseline_ref_invalid"):
            resolve_candidate_baseline(root, environ=runtime_env(baseline, "refs/heads/baseline-target"))

    def test_remote_target_move_is_stale(self) -> None:
        tmp, root, baseline, candidate = init_repo()
        self.addCleanup(tmp.cleanup)
        git(root, "update-ref", "refs/remotes/origin/development", candidate)
        git(root, "checkout", "-q", "--detach", candidate)
        with self.assertRaisesRegex(ClosureError, "candidate_baseline_stale"):
            resolve_candidate_baseline(root, environ=runtime_env(baseline))

    def test_omitted_and_wrong_baselines_fail_closed(self) -> None:
        tmp, root, _, _ = init_repo()
        self.addCleanup(tmp.cleanup)
        with self.assertRaisesRegex(ClosureError, "candidate_baseline_missing"):
            resolve_candidate_baseline(root, environ={})
        with self.assertRaisesRegex(ClosureError, "candidate_baseline_invalid"):
            resolve_candidate_baseline(root, environ=runtime_env("a" * 40))

    def test_detached_diff_check_rejects_trailing_whitespace(self) -> None:
        tmp, root, baseline, candidate = init_repo()
        self.addCleanup(tmp.cleanup)
        git(root, "checkout", "-q", "--detach", candidate)
        (root / "candidate.txt").write_text("candidate \n", encoding="utf-8")
        with self.assertRaisesRegex(ClosureError, "candidate_whitespace"):
            candidate_diff_check(root, environ=runtime_env(baseline))

    def test_hardcoded_baseline_patterns_are_absent_from_candidate_paths(self) -> None:
        paths = (
            ROOT / ".githooks" / "pre-push",
            ROOT / "scripts" / "gitops" / "generated_output_closure.py",
            ROOT / "scripts" / "ide_development" / "release_candidate.py",
            ROOT / ".github" / "workflows" / "ci.yml",
            ROOT / ".github" / "workflows" / "linktrend-integrator-merge.yml",
            ROOT / ".github" / "workflows" / "linktrend-review-packager.yml",
        )
        for path in paths:
            self.assertNotRegex(
                path.read_text(encoding="utf-8"),
                r"(?i)(?:baseline|target)[^\n]{0,100}[0-9a-f]{40}",
                path.as_posix(),
            )

    def test_hosted_managed_and_extracted_contexts_use_remote_target(self) -> None:
        for context in ("hosted", "managed-package", "extracted-cleanroom"):
            with self.subTest(context=context):
                tmp, root, baseline, candidate = init_repo()
                self.addCleanup(tmp.cleanup)
                git(root, "checkout", "-q", "--detach", candidate)
                environment = {**runtime_env(baseline), "CANDIDATE_CONTEXT": context}
                self.assertEqual(resolve_candidate_baseline(root, environ=environment), baseline)


if __name__ == "__main__":
    unittest.main()
