"""Adversarial tests for runtime-supplied exact candidate baselines."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.gitops.generated_output_closure import (
    BASELINE_REF_ENV,
    BASELINE_SHA_ENV,
    ClosureError,
    resolve_candidate_baseline,
)


ROOT = Path(__file__).resolve().parents[2]
SHA40 = re.compile(r"[0-9a-f]{40}")


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


def init_repo() -> tuple[tempfile.TemporaryDirectory[str], Path, str]:
    tmp = tempfile.TemporaryDirectory(prefix="candidate-baseline-")
    root = Path(tmp.name) / "repo"
    root.mkdir()
    git(root, "init", "-q", "-b", "development")
    git(root, "config", "user.email", "baseline@example.invalid")
    git(root, "config", "user.name", "Baseline tests")
    (root / "README.md").write_text("# candidate\n", encoding="utf-8")
    git(root, "add", "README.md")
    git(root, "commit", "-qm", "authoritative baseline")
    baseline = git(root, "rev-parse", "HEAD")
    return tmp, root, baseline


def runtime_env(baseline: str, ref: str = "refs/heads/development") -> dict[str, str]:
    return {
        BASELINE_SHA_ENV: baseline,
        BASELINE_REF_ENV: ref,
    }


class CandidateBaselineResolutionTests(unittest.TestCase):
    def test_local_runtime_resolution_requires_exact_authoritative_target(self) -> None:
        tmp, root, baseline = init_repo()
        self.addCleanup(tmp.cleanup)
        self.assertEqual(
            resolve_candidate_baseline(root, environ=runtime_env(baseline)),
            baseline,
        )

    def test_omitted_baseline_fails_closed(self) -> None:
        tmp, root, _ = init_repo()
        self.addCleanup(tmp.cleanup)
        with self.assertRaisesRegex(ClosureError, "candidate_baseline_missing"):
            resolve_candidate_baseline(root, environ={})

    def test_pre_push_fails_closed_without_runtime_baseline(self) -> None:
        tmp, root, _ = init_repo()
        self.addCleanup(tmp.cleanup)
        hook = root / ".githooks" / "pre-push"
        hook.parent.mkdir()
        shutil.copy2(ROOT / ".githooks/pre-push", hook)
        runtime = root / "scripts/gitops/generated_output_closure.py"
        runtime.parent.mkdir(parents=True)
        shutil.copy2(ROOT / "scripts/gitops/generated_output_closure.py", runtime)
        environment = os.environ.copy()
        environment.pop(BASELINE_SHA_ENV, None)
        environment.pop(BASELINE_REF_ENV, None)
        proc = subprocess.run(
            [str(hook)],
            cwd=root,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("candidate_baseline_missing", proc.stderr + proc.stdout)

    def test_release_candidate_fails_closed_without_runtime_baseline(self) -> None:
        environment = os.environ.copy()
        environment["PYTHONPATH"] = str(ROOT / "scripts")
        environment.pop(BASELINE_SHA_ENV, None)
        environment.pop(BASELINE_REF_ENV, None)
        proc = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/ide-development.py"),
                "release-candidate",
                "create",
                "--allow-dirty",
                "--skip-evidence",
                "--skip-install-verify",
                "--json",
            ],
            cwd=ROOT,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("candidate_baseline_missing", proc.stderr + proc.stdout)

    def test_wrong_baseline_fails_closed(self) -> None:
        tmp, root, baseline = init_repo()
        self.addCleanup(tmp.cleanup)
        with self.assertRaisesRegex(ClosureError, "candidate_baseline_invalid"):
            resolve_candidate_baseline(root, environ=runtime_env("a" * 40))
        with self.assertRaisesRegex(ClosureError, "candidate_baseline_missing"):
            resolve_candidate_baseline(root, environ=runtime_env(baseline, ""))

    def test_stale_baseline_fails_when_authoritative_ref_moves(self) -> None:
        tmp, root, baseline = init_repo()
        self.addCleanup(tmp.cleanup)
        git(root, "update-ref", "refs/heads/development", baseline)
        (root / "README.md").write_text("# moved target\n", encoding="utf-8")
        git(root, "add", "README.md")
        git(root, "commit", "-qm", "move authoritative target")
        with self.assertRaisesRegex(ClosureError, "candidate_baseline_stale"):
            resolve_candidate_baseline(root, environ=runtime_env(baseline))

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
            text = path.read_text(encoding="utf-8")
            self.assertNotRegex(
                text,
                r"(?i)(?:baseline|target)[^\\n]{0,100}[0-9a-f]{40}",
                path.as_posix(),
            )

    def test_hosted_managed_and_extracted_runtime_contexts_use_same_authority(self) -> None:
        for context in ("hosted", "managed-package", "extracted-cleanroom"):
            with self.subTest(context=context):
                tmp, root, baseline = init_repo()
                self.addCleanup(tmp.cleanup)
                self.assertEqual(
                    resolve_candidate_baseline(
                        root,
                        environ={**runtime_env(baseline), "CANDIDATE_CONTEXT": context},
                    ),
                    baseline,
                )

    def test_extracted_runtime_rejects_missing_authority_without_checkout_fallback(self) -> None:
        tmp, root, _ = init_repo()
        self.addCleanup(tmp.cleanup)
        runtime = root / "scripts" / "gitops" / "generated_output_closure.py"
        runtime.parent.mkdir(parents=True)
        shutil.copy2(ROOT / "scripts/gitops/generated_output_closure.py", runtime)
        probe = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "from pathlib import Path\n"
                    "from scripts.gitops.generated_output_closure import "
                    "resolve_candidate_baseline\n"
                    "resolve_candidate_baseline(Path.cwd(), environ={})\n"
                ),
            ],
            cwd=root,
            env={**os.environ, "PYTHONPATH": str(root / "scripts")},
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(probe.returncode, 0)
        self.assertIn("candidate_baseline_missing", probe.stderr + probe.stdout)


if __name__ == "__main__":
    unittest.main()
