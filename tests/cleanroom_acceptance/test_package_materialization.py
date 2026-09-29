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
    "scripts/gitops/run_delivery_profile.py",
    "core/execution/__init__.py",
    "core/execution/protocol.py",
    "core/execution/lifecycle.py",
    "core/execution/scheduler.py",
    "core/execution/verification_liveness.py",
    "core/execution/transactional_dispatch.py",
    "core/execution/rollout.py",
    "core/managed-core/content/config/transactional-dispatch.json",
    "core/managed-core/schemas/transactional-dispatch.schema.json",
)

APPLICATION_RUNTIME_SOURCES = (
    "scripts/ide_development/app_canary.mjs",
    "core/managed-core/platforms/codex/adapter.mjs",
    "core/managed-core/platforms/cursor/adapter.mjs",
    "core/link-integrations/errors.mjs",
)

class PackageMaterializationTests(unittest.TestCase):
    def test_managed_package_runs_dogfood_closure_and_lean_design_audit(self) -> None:
        with tempfile.TemporaryDirectory(prefix="managed-closure-audit-") as tmp:
            source = Path(tmp) / "source"
            package = Path(tmp) / "package"
            audit_sources = (
                "scripts/gitops/generated_output_closure.py",
                "scripts/ide-development.py",
                "scripts/ide_development/build_manifest.py",
                "core/execution/scheduler.py",
                "core/execution/verification_liveness.py",
                "core/managed-core/config/generated-output-closure.json",
            )
            for rel in audit_sources:
                destination = source / rel
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(REPO_ROOT / rel, destination)

            materialize_package_copy(package, source=source)
            proc = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    (
                        "from scripts.gitops.generated_output_closure import "
                        "audit_dogfood_improvement_closure; "
                        "import json; "
                        "print(json.dumps(audit_dogfood_improvement_closure('.')))"
                    ),
                ],
                cwd=package,
                env={key: value for key, value in os.environ.items() if key != "PYTHONPATH"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            result = json.loads(proc.stdout)
            self.assertEqual(result["status"], "audited")

    def test_managed_package_requires_named_remote_baseline(self) -> None:
        with tempfile.TemporaryDirectory(prefix="managed-baseline-audit-") as tmp:
            package = Path(tmp) / "package"
            materialize_package_copy(package, source=PACKAGE_FIXTURE)
            for rel in (
                "core/managed-core/content/config/continuous-utilization.json",
                "core/managed-core/schemas/continuous-utilization.schema.json",
            ):
                destination = package / rel
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(REPO_ROOT / rel, destination)
            proc = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    """
import subprocess
from pathlib import Path
from scripts.gitops.generated_output_closure import (
    ClosureError,
    resolve_candidate_baseline,
)

root = Path.cwd()
def git(*args):
    result = subprocess.run(
        ["git", *args], cwd=root, text=True, capture_output=True, check=False
    )
    assert result.returncode == 0, result.stderr or result.stdout
    return result.stdout.strip()

git("init", "-q", "-b", "development")
git("config", "user.email", "managed@example.invalid")
git("config", "user.name", "Managed")
(root / "baseline.txt").write_text("baseline\\n", encoding="utf-8")
git("add", "baseline.txt")
git("commit", "-qm", "managed baseline")
baseline = git("rev-parse", "HEAD")
git("remote", "add", "fixture", str(root / "fixture.git"))
git("update-ref", "refs/remotes/fixture/development", baseline)
git("commit", "--allow-empty", "-qm", "managed candidate")
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
""",
                ],
                cwd=package,
                env={key: value for key, value in os.environ.items() if key != "PYTHONPATH"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_extracted_package_runs_dogfood_closure_and_lean_design_audit(self) -> None:
        with tempfile.TemporaryDirectory(prefix="package-closure-audit-") as tmp:
            source = Path(tmp) / "source"
            extract = Path(tmp) / "extract"
            audit_sources = (
                "scripts/gitops/generated_output_closure.py",
                "scripts/ide-development.py",
                "core/execution/scheduler.py",
                "core/execution/verification_liveness.py",
                "core/managed-core/config/generated-output-closure.json",
            )
            for rel in audit_sources:
                destination = source / rel
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(REPO_ROOT / rel, destination)

            materialize_isolated_rc_extract(extract, source=source)
            proc = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    (
                        "from scripts.gitops.generated_output_closure import "
                        "audit_dogfood_improvement_closure; "
                        "result = audit_dogfood_improvement_closure('.'); "
                        "assert result['status'] == 'audited', result; "
                        "assert result['leanDesign']['mappingCount'] == 4, result; "
                        "print('PASS')"
                    ),
                ],
                cwd=extract,
                env={key: value for key, value in os.environ.items() if key != "PYTHONPATH"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("PASS", proc.stdout)

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

    def test_managed_package_runs_heartbeat_progress_contract(self) -> None:
        with tempfile.TemporaryDirectory(prefix="managed-heartbeat-contract-") as tmp:
            package = Path(tmp) / "package"
            materialize_package_copy(package, source=PACKAGE_FIXTURE)
            for rel in (
                "core/managed-core/content/config/continuous-utilization.json",
                "core/managed-core/schemas/continuous-utilization.schema.json",
            ):
                destination = package / rel
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(REPO_ROOT / rel, destination)
            proc = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    """
from datetime import datetime, timedelta, timezone
from core.execution.scheduler import (
    COMPLETE_SNAPSHOT,
    ContinuousUtilizationScheduler,
    WorkItem,
)

now = datetime(2026, 8, 20, tzinfo=timezone.utc)
scheduler = ContinuousUtilizationScheduler.from_repo(".", snapshot=None, now=now)
scheduler.submit(WorkItem("heartbeat-action", "hosted"))
scheduler.tick(now + timedelta(minutes=20))
assert scheduler.admitted_ids() == ()
scheduler.set_snapshot(COMPLETE_SNAPSHOT, recompute=False)
assert scheduler.repair_utilization_gap()
assert scheduler.admitted_ids() == ("heartbeat-action",)
""",
                ],
                cwd=package,
                env={key: value for key, value in os.environ.items() if key != "PYTHONPATH"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_managed_and_extracted_packages_plan_generic_canary_rollout(self) -> None:
        script = r'''
from core.execution.rollout import RolloutConfig, plan_rollout
config = RolloutConfig.from_mapping({
    "canaryTargets": ["alpha"],
    "downstreamTargets": ["beta", "gamma"],
    "maxParallel": 2,
})
first = plan_rollout(
    config,
    [{"name": "alpha", "status": "PENDING"}, {"name": "beta", "status": "PENDING"}, {"name": "gamma", "status": "PENDING"}],
    package_digest="sha256:" + "a" * 64,
    environment_digest="sha256:" + "b" * 64,
)
assert [row["target"] for row in first["actions"] if row["mutating"]] == ["alpha"]
receipt = {"status": "PASSED", "packageDigest": "sha256:" + "a" * 64, "environmentDigest": "sha256:" + "b" * 64, "afterTree": "2" * 40}
second = plan_rollout(
    config,
    [{"name": "alpha", "status": "VERIFIED", "afterTree": "2" * 40, "receipt": receipt}, {"name": "beta", "status": "PENDING"}, {"name": "gamma", "status": "PENDING"}],
    package_digest="sha256:" + "a" * 64,
    environment_digest="sha256:" + "b" * 64,
)
assert [row["target"] for row in second["actions"] if row["kind"] == "UPDATE"] == ["beta", "gamma"]
print("PASS")
'''
        for materializer, label in (
            (materialize_package_copy, "managed"),
            (materialize_isolated_rc_extract, "extracted"),
        ):
            with self.subTest(package=label), tempfile.TemporaryDirectory(
                prefix=f"{label}-rollout-controller-"
            ) as tmp:
                source = Path(tmp) / "source"
                package = Path(tmp) / label
                for rel in RUNTIME_SOURCES:
                    destination = source / rel
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(REPO_ROOT / rel, destination)
                materializer(package, source=source)
                proc = subprocess.run(
                    [sys.executable, "-c", script],
                    cwd=package,
                    env={key: value for key, value in os.environ.items() if key != "PYTHONPATH"},
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertIn("PASS", proc.stdout)

    def test_managed_and_extracted_packages_run_application_canary(self) -> None:
        for materializer, label in (
            (materialize_package_copy, "managed"),
            (materialize_isolated_rc_extract, "extracted"),
        ):
            with self.subTest(package=label), tempfile.TemporaryDirectory(
                prefix=f"{label}-application-canary-"
            ) as tmp:
                source = Path(tmp) / "source"
                package = Path(tmp) / label
                for rel in APPLICATION_RUNTIME_SOURCES:
                    destination = source / rel
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(REPO_ROOT / rel, destination)
                materializer(package, source=source)
                proc = subprocess.run(
                    ["node", "scripts/ide_development/app_canary.mjs", "--json"],
                    cwd=package,
                    env={key: value for key, value in os.environ.items() if key != "PYTHONPATH"},
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(proc.returncode, 0, proc.stderr)
                result = json.loads(proc.stdout)
                self.assertTrue(result["ok"])
                self.assertEqual(result["applications"], ["codex", "cursor"])

    def test_managed_and_extracted_packages_ignore_git_objects_in_dependency_digest(self) -> None:
        script = """
import fnmatch
import os
from pathlib import Path
from scripts.gitops import run_delivery_profile as runner

root = Path(".")
(root / ".git" / "objects" / "aa").mkdir(parents=True)
(root / ".git" / "objects" / "aa" / "missing.lock").write_text("control", encoding="utf-8")
(root / "requirements.txt").write_text("jsonschema\\n", encoding="utf-8")
digest = runner._digest_files(root, ("**/*lock*", "**/requirements*.txt"))
expected_rows = []
for directory, directory_names, file_names in os.walk(root, followlinks=False):
    directory_names[:] = [name for name in directory_names if name != ".git"]
    for name in file_names:
        if fnmatch.fnmatch(name, "*lock*") or fnmatch.fnmatch(name, "requirements*.txt"):
            path = Path(directory) / name
            expected_rows.append({
                "path": path.relative_to(root).as_posix(),
                "digest": runner.digest_bytes(path.read_bytes()),
            })
expected = runner.digest_json(sorted(expected_rows, key=lambda row: row["path"]))
assert digest == expected, digest
assert ".git/" not in digest
print("PASS")
"""
        for materializer, label in (
            (materialize_package_copy, "managed"),
            (materialize_isolated_rc_extract, "extracted"),
        ):
            with self.subTest(package=label), tempfile.TemporaryDirectory(
                prefix=f"{label}-dependency-digest-"
            ) as tmp:
                source = Path(tmp) / "source"
                package = Path(tmp) / label
                source_path = source / "scripts/gitops/run_delivery_profile.py"
                source_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(REPO_ROOT / "scripts/gitops/run_delivery_profile.py", source_path)
                materializer(package, source=source)
                proc = subprocess.run(
                    [sys.executable, "-c", script],
                    cwd=package,
                    env={key: value for key, value in os.environ.items() if key != "PYTHONPATH"},
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertIn("PASS", proc.stdout)

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

    def test_extracted_package_imports_scheduler_and_liveness_runtime(self) -> None:
        with tempfile.TemporaryDirectory(prefix="package-execution-runtime-") as tmp:
            package = Path(tmp) / "package"
            materialize_package_copy(package, source=PACKAGE_FIXTURE)
            env = os.environ.copy()
            env.pop("PYTHONPATH", None)
            proc = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "from core.execution import scheduler, verification_liveness; "
                    "print(scheduler.__name__, verification_liveness.__name__)",
                ],
                cwd=package,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("core.execution.scheduler", proc.stdout)

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
