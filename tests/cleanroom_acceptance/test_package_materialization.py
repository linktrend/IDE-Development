"""Regression tests for extracted-package script materialization."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness.installer import materialize_isolated_rc_extract, materialize_package_copy
from harness.paths import PACKAGE_FIXTURE


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_SOURCES = (
    "scripts/gitops/repository_ci_contract.py",
    "scripts/gitops/promotion_receipt_gate.py",
    "core/execution/__init__.py",
    "core/execution/protocol.py",
    "core/execution/lifecycle.py",
    "core/execution/scheduler.py",
    "core/execution/verification_liveness.py",
    "core/execution/manifest_persistence.py",
    "core/execution/transactional_dispatch.py",
    "core/managed-core/content/config/manifest-persistence.json",
    "core/managed-core/schemas/manifest-persistence.schema.json",
    "core/managed-core/content/config/transactional-dispatch.json",
    "core/managed-core/schemas/transactional-dispatch.schema.json",
)


class PackageMaterializationTests(unittest.TestCase):
    def test_runtime_manifest_declares_transactional_dispatch_dependency_closure(self) -> None:
        manifest = json.loads(
            (REPO_ROOT / "core/github/managed-runtime/MANIFEST.json").read_text(
                encoding="utf-8"
            )
        )
        sources = set(manifest["files"])
        self.assertTrue(
            {
                "core/execution/transactional_dispatch.py",
                "core/managed-core/content/config/transactional-dispatch.json",
                "core/managed-core/schemas/transactional-dispatch.schema.json",
            }.issubset(sources)
        )

    def test_package_copy_materializes_canonical_runtime_sources(self) -> None:
        with tempfile.TemporaryDirectory(prefix="package-copy-") as tmp:
            package = Path(tmp) / "package"
            materialize_package_copy(package, source=PACKAGE_FIXTURE)

            for rel in RUNTIME_SOURCES:
                self.assertTrue(
                    (package / rel).is_file(),
                    f"constructed package lost runtime source {rel}",
                )

    def test_extracted_package_preserves_runtime_contract_dependencies(self) -> None:
        with tempfile.TemporaryDirectory(prefix="package-materialization-") as tmp:
            source = Path(tmp) / "source"
            extract = Path(tmp) / "extract"
            for rel in RUNTIME_SOURCES:
                source_path = REPO_ROOT / rel
                destination = source / rel
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, destination)

            materialize_isolated_rc_extract(extract, source=source)

            for rel in RUNTIME_SOURCES:
                self.assertTrue(
                    (extract / rel).is_file(),
                    f"extracted package lost runtime source {rel}",
                )

    def test_extracted_package_imports_scheduler_liveness_and_manifest_runtime(self) -> None:
        with tempfile.TemporaryDirectory(prefix="package-execution-runtime-") as tmp:
            package = Path(tmp) / "package"
            materialize_package_copy(package, source=PACKAGE_FIXTURE)
            env = os.environ.copy()
            env.pop("PYTHONPATH", None)
            proc = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "from core.execution import manifest_persistence, scheduler, verification_liveness; "
                    "print(manifest_persistence.MAX_PERSISTENCE_ATTEMPTS, "
                    "scheduler.__name__, verification_liveness.__name__)",
                ],
                cwd=package,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("3", proc.stdout)

    def test_extracted_package_contains_revision_60_final_controls(self) -> None:
        with tempfile.TemporaryDirectory(prefix="package-final-controls-") as tmp:
            source = Path(tmp) / "source"
            extract = Path(tmp) / "extract"
            final_sources = (
                "core/execution/__init__.py",
                "core/execution/protocol.py",
                "core/execution/lifecycle.py",
                "core/execution/scheduler.py",
                "core/execution/verification_liveness.py",
                "core/execution/manifest_persistence.py",
                "core/execution/transactional_dispatch.py",
                "core/contracts/PKT08-REVISION-60-FINAL-CONTROLS.md",
                "core/managed-core/content/config/transactional-dispatch.json",
                "core/managed-core/content/doctrine/PKT08-REVISION-60-FINAL-CONTROLS.md",
                "core/managed-core/schemas/transactional-dispatch.schema.json",
            )
            for rel in final_sources:
                destination = source / rel
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(REPO_ROOT / rel, destination)

            materialize_isolated_rc_extract(extract, source=source)
            for rel in final_sources:
                self.assertTrue((extract / rel).is_file(), rel)

            env = os.environ.copy()
            env.pop("PYTHONPATH", None)
            proc = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "from core.execution import ("
                    "CONTROL_IDEMPOTENCY_KEY, load_transactional_dispatch_config); "
                    "print(CONTROL_IDEMPOTENCY_KEY); "
                    "print(load_transactional_dispatch_config('.')["
                    "'amendment'])",
                ],
                cwd=extract,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn(
                "pkt08-b44060-transactional-dispatch-and-approved-design-authority-v1",
                proc.stdout,
            )
            self.assertIn("V25_PKT08_REVISION_60_FINAL_CONTROLS", proc.stdout)

    def test_extracted_closure_requires_named_remote_target_without_origin(self) -> None:
        with tempfile.TemporaryDirectory(prefix="package-baseline-cleanroom-") as tmp:
            extract = Path(tmp) / "extract"
            materialize_isolated_rc_extract(extract, source=PACKAGE_FIXTURE)
            script = r"""
import subprocess
from pathlib import Path

from scripts.gitops.generated_output_closure import ClosureError, resolve_candidate_baseline

root = Path.cwd()
def git(*args):
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    return result.stdout.strip()

git("init", "-q", "-b", "development")
git("config", "user.email", "cleanroom@example.invalid")
git("config", "user.name", "Cleanroom")
git("add", "-A")
git("commit", "-qm", "cleanroom baseline")
baseline = git("rev-parse", "HEAD")
git("remote", "add", "fixture", str(root / "fixture.git"))
git("update-ref", "refs/remotes/fixture/development", baseline)
git("commit", "--allow-empty", "-qm", "cleanroom candidate")
assert subprocess.run(
    ["git", "rev-parse", "--verify", "origin/development^{commit}"],
    cwd=root,
    capture_output=True,
    check=False,
).returncode != 0
assert resolve_candidate_baseline(
    root,
    environ={
        "LINKTREND_TARGET_BASELINE_SHA": baseline,
        "LINKTREND_TARGET_BASELINE_REF": "fixture/development",
    },
) == baseline
try:
    resolve_candidate_baseline(root, environ={})
except ClosureError as error:
    assert error.code == "candidate_baseline_missing"
else:
    raise AssertionError("missing runtime baseline was accepted")
"""
            proc = subprocess.run(
                [sys.executable, "-c", script],
                cwd=extract,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)


if __name__ == "__main__":
    unittest.main()
