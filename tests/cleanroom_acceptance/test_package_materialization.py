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
    "scripts/gitops/run_delivery_profile.py",
    "core/execution/__init__.py",
    "core/execution/protocol.py",
    "core/execution/lifecycle.py",
    "core/execution/scheduler.py",
    "core/execution/verification_liveness.py",
    "core/execution/manifest_persistence.py",
    "core/execution/transactional_dispatch.py",
    "core/execution/rollout.py",
    "scripts/gitops/heartbeat_controller.py",
    "core/managed-core/content/config/manifest-persistence.json",
    "core/managed-core/schemas/manifest-persistence.schema.json",
    "core/managed-core/content/config/transactional-dispatch.json",
    "core/managed-core/schemas/transactional-dispatch.schema.json",
)

APPLICATION_RUNTIME_SOURCES = (
    "scripts/ide_development/app_canary.mjs",
    "core/managed-core/platforms/codex/adapter.mjs",
    "core/managed-core/platforms/cursor/adapter.mjs",
    "core/link-integrations/errors.mjs",
)

HEARTBEAT_CONTROLLER_SCRIPT = r"""
import copy
from datetime import datetime, timedelta, timezone

from core.execution import (
    DispatchBudget,
    DurableDispatchIntentStore,
    LeaseState,
    persist_manifest,
    run_heartbeat_controller,
)

identity = {
    "repository": "linktrend/IDE-Development",
    "commit": "a" * 40,
    "tree": "b" * 40,
}

class Store:
    def __init__(self):
        self.record = None
    def read(self):
        return copy.deepcopy(self.record)
    def compare_and_write(self, expected_revision, expected_digest, payload):
        current_revision = 0 if self.record is None else self.record["revision"]
        current_digest = None if self.record is None else self.record["digest"]
        assert (current_revision, current_digest) == (expected_revision, expected_digest)
        self.record = {
            "revision": expected_revision + 1,
            "digest": payload["digest"],
            "manifest": copy.deepcopy(payload["manifest"]),
        }

class Authority:
    def read_authoritative_state(self, observed_identity):
        assert observed_identity == identity
        return {
            "identity": dict(identity),
            "cursor": {"status": "REPAIR_REQUESTED"},
            "github": {},
            "git": {"head": identity["commit"], "tree": identity["tree"]},
        }

class FailedAuthority(Authority):
    def read_authoritative_state(self, observed_identity):
        assert observed_identity == identity
        return {
            "identity": dict(identity),
            "cursor": {"status": "queued"},
            "github": {"check": {"conclusion": "FAILURE"}},
            "git": {"head": identity["commit"], "tree": identity["tree"]},
        }

class External:
    def __init__(self):
        self.calls = 0
        self.records = {}
    def dispatch(self, request, key):
        self.calls += 1
        record = {"dispatchId": "cleanroom-dispatch-1", "idempotencyKey": key}
        self.records[key] = record
        return {"statusCode": 201, **record}
    def read_by_idempotency_key(self, key):
        return copy.deepcopy(self.records.get(key))

now = datetime(2026, 8, 21, tzinfo=timezone.utc)
manifest = {
    "schemaVersion": 1,
    "packetId": "PKT-08",
    "identity": dict(identity),
    "transitions": [],
    "orchestrationLease": {
        "holder": "stale",
        "nonce": "stale",
        "expiresAt": (now - timedelta(seconds=1)).isoformat(),
    },
    "safeAction": {
        "id": "cleanroom-action",
        "safe": True,
        "action": "run-repair",
        "payload": {"reason": "failed-check"},
    },
}
store = Store()
persist_manifest(manifest, store)
external = External()
lease = LeaseState(
    holder="executor",
    packet_id="PKT-08",
    repository=identity["repository"],
    nonce="fresh",
    expires_at=now + timedelta(minutes=5),
)
first = run_heartbeat_controller(
    store,
    Authority(),
    dispatch_store=DurableDispatchIntentStore(),
    external_dispatch=external,
    lease=lease,
    holder="executor",
    budget=DispatchBudget(30, 4),
    now=now,
    no_progress_wakes=2,
)
assert first["dispatchPerformed"] is True, first
assert first["requiredAction"]["kind"] != "DONT_NOTIFY", first
assert first["receipt"]["readback"] is True, first
second = run_heartbeat_controller(
    store,
    Authority(),
    dispatch_store=first.get("_dispatchStore", DurableDispatchIntentStore()),
    external_dispatch=external,
    lease=lease,
    holder="executor",
    budget=DispatchBudget(30, 4),
    now=now + timedelta(seconds=1),
    no_progress_wakes=2,
)
assert external.calls == 1, external.calls
assert second["requiredAction"]["kind"] == "DONT_NOTIFY", second
assert sum(
    row.get("kind") == "UTILIZATION_GAP"
    for row in store.read()["manifest"]["transitions"]
) == 1
failed_store = Store()
persist_manifest(
    {
        "schemaVersion": 1,
        "packetId": "PKT-08",
        "identity": dict(identity),
        "transitions": [],
    },
    failed_store,
)
failed = run_heartbeat_controller(failed_store, FailedAuthority())
assert failed["notify"] is True, failed
assert failed["requiredAction"]["code"] == "failed_check_repair", failed
assert failed["requiredAction"]["kind"] != "DONT_NOTIFY", failed
print("PASS")
"""


class PackageMaterializationTests(unittest.TestCase):
    def test_managed_package_runs_dogfood_closure_and_lean_design_audit(self) -> None:
        with tempfile.TemporaryDirectory(prefix="managed-closure-audit-") as tmp:
            source = Path(tmp) / "source"
            package = Path(tmp) / "package"
            audit_sources = (
                "scripts/gitops/generated_output_closure.py",
                "scripts/gitops/coordinator/state.py",
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
                "scripts/gitops/coordinator/state.py",
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
                        "assert result['leanDesign']['mappingCount'] == 6, result; "
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

    def test_managed_and_extracted_packages_invoke_heartbeat_controller(self) -> None:
        for materializer, label in (
            (materialize_package_copy, "managed"),
            (materialize_isolated_rc_extract, "extracted"),
        ):
            with self.subTest(package=label), tempfile.TemporaryDirectory(
                prefix=f"{label}-heartbeat-controller-"
            ) as tmp:
                source = Path(tmp) / "source"
                package = Path(tmp) / label
                for rel in RUNTIME_SOURCES:
                    destination = source / rel
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(REPO_ROOT / rel, destination)
                materializer(package, source=source)
                proc = subprocess.run(
                    [sys.executable, "-c", HEARTBEAT_CONTROLLER_SCRIPT],
                    cwd=package,
                    env={key: value for key, value in os.environ.items() if key != "PYTHONPATH"},
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(proc.returncode, 0, proc.stderr)
                self.assertIn("PASS", proc.stdout)

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

    def test_extracted_package_enforces_manifest_persistence_identity_and_cas_binding(self) -> None:
        with tempfile.TemporaryDirectory(prefix="package-manifest-persistence-adversarial-") as tmp:
            source = Path(tmp) / "source"
            extract = Path(tmp) / "extract"
            for rel in RUNTIME_SOURCES:
                destination = source / rel
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(REPO_ROOT / rel, destination)

            materialize_isolated_rc_extract(extract, source=source)
            proc = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    """
import copy
from core.execution.manifest_persistence import (
    MANIFEST_PERSISTENCE_FAILURE,
    ManifestPersistenceError,
    canonical_manifest_digest,
    persist_manifest,
)

identity = {"repository": "linktrend/IDE-Development", "commit": "a" * 40, "tree": "b" * 40}

def make_manifest(*transitions):
    return {"schemaVersion": 1, "identity": identity, "transitions": list(transitions)}

class Store:
    def __init__(self):
        self.record = None
    def read(self):
        return copy.deepcopy(self.record)
    def compare_and_write(self, expected_revision, expected_digest, payload):
        current_revision = 0 if self.record is None else self.record["revision"]
        current_digest = None if self.record is None else self.record["digest"]
        if (current_revision, current_digest) != (expected_revision, expected_digest):
            raise ManifestPersistenceError("revision_conflict", "stale revision")
        self.record = {
            "revision": expected_revision + 1,
            "digest": payload["digest"],
            "manifest": copy.deepcopy(payload["manifest"]),
        }
        for key in ("updated_at", "transition_event"):
            if key in payload:
                self.record[key] = copy.deepcopy(payload[key])

store = Store()
initial = make_manifest()
persist_manifest(initial, store)
store.record["digest"] = "sha256:" + "c" * 64
try:
    persist_manifest(initial, store)
except ManifestPersistenceError as error:
    assert error.code == MANIFEST_PERSISTENCE_FAILURE
else:
    raise AssertionError("tampered canonical digest was accepted")

store = Store()
first = make_manifest()
first_updated_at = "2026-08-20T22:00:00+00:00"
first_digest = canonical_manifest_digest(first)
persist_manifest(
    first,
    store,
    updated_at=first_updated_at,
    transition_event={
        "id": "transition-1",
        "kind": "manifest_persisted",
        "revision": 1,
        "digest": first_digest,
        "updated_at": first_updated_at,
    },
)
second = make_manifest({"kind": "run", "id": "run-1"})
second_updated_at = "2026-08-20T22:00:01+00:00"
second_digest = canonical_manifest_digest(second)
result = persist_manifest(
    second,
    store,
    updated_at=second_updated_at,
    transition_event={
        "id": "transition-2",
        "kind": "manifest_persisted",
        "revision": 2,
        "digest": second_digest,
        "updated_at": second_updated_at,
    },
)
assert result["revision"] == 2
assert result["updated_at"] == second_updated_at
assert result["transition_event"]["digest"] == second_digest
print("PASS")
""",
                ],
                cwd=extract,
                env={key: value for key, value in os.environ.items() if key != "PYTHONPATH"},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("PASS", proc.stdout)

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
