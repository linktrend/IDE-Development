"""Adversarial tests for PKT-08 manifest persistence and heartbeat recovery."""

from __future__ import annotations

import copy
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from core.execution.manifest_persistence import (
    AuthorityFailure,
    DurableManifestStore,
    MANIFEST_PERSISTENCE_FAILURE,
    ManifestPersistenceError,
    canonical_manifest_digest,
    persist_manifest,
    reconcile_manifest_heartbeat,
)


IDENTITY = {
    "repository": "linktrend/IDE-Development",
    "commit": "a" * 40,
    "tree": "b" * 40,
}


def manifest(*transitions: dict[str, object]) -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "identity": dict(IDENTITY),
        "transitions": list(transitions),
    }


class RecoveryStore(DurableManifestStore):
    def __init__(self, initial: dict[str, object] | None = None) -> None:
        self.record = None
        self.write_calls = 0
        self.read_calls = 0
        self.collide_once = False
        self.readback_failures = 0
        if initial is not None:
            persist_manifest(initial, self)

    def read(self):
        self.read_calls += 1
        if self.record is None:
            return None
        return copy.deepcopy(self.record)

    def compare_and_write(self, expected_revision, expected_digest, payload):
        self.write_calls += 1
        current = self.read()
        current_revision = 0 if current is None else current["revision"]
        current_digest = None if current is None else current["digest"]
        if self.collide_once:
            self.collide_once = False
            competing_manifest = {**(current["manifest"] if current else manifest()), "competing": True}
            self.record = {
                "revision": current_revision + 1,
                "digest": canonical_manifest_digest(competing_manifest),
                "manifest": competing_manifest,
            }
            raise ManifestPersistenceError("revision_conflict", "simulated collision")
        if current_revision != expected_revision or current_digest != expected_digest:
            raise ManifestPersistenceError("revision_conflict", "stale revision")
        next_record = {
            "revision": expected_revision + 1,
            "digest": payload["digest"],
            "manifest": copy.deepcopy(payload["manifest"]),
        }
        for key in ("updated_at", "transition_event"):
            if key in payload:
                next_record[key] = copy.deepcopy(payload[key])
        if self.readback_failures:
            self.readback_failures -= 1
            self.record = None
        else:
            self.record = next_record


class Authority:
    def __init__(self, snapshot: dict[str, object]) -> None:
        self.snapshot = snapshot
        self.calls = 0

    def read_authoritative_state(self, identity):
        self.calls += 1
        if identity != IDENTITY:
            raise AssertionError("wrong identity")
        return copy.deepcopy(self.snapshot)


class ManifestPersistenceTests(unittest.TestCase):
    def test_extracted_runtime_loads_config_without_checkout_imports(self) -> None:
        root = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory(prefix="pkt08-cleanroom-") as temp:
            extract = Path(temp)
            (extract / "core" / "execution").mkdir(parents=True)
            (extract / "core" / "execution" / "__init__.py").write_text("", encoding="utf-8")
            shutil.copy2(
                root / "core/execution/manifest_persistence.py",
                extract / "core/execution/manifest_persistence.py",
            )
            config = extract / "core/managed-core/content/config/manifest-persistence.json"
            config.parent.mkdir(parents=True)
            shutil.copy2(root / "core/managed-core/content/config/manifest-persistence.json", config)
            proc = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "from core.execution.manifest_persistence import load_manifest_persistence_config; "
                    "print(load_manifest_persistence_config('.')['amendment'])",
                ],
                cwd=extract,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("V25_PKT08_MANIFEST_PERSISTENCE_RECOVERY", proc.stdout)

    def test_compare_and_retry_uses_fresh_revision_after_write_collision(self) -> None:
        store = RecoveryStore()
        store.collide_once = True
        result = persist_manifest(manifest(), store, max_attempts=3)
        self.assertEqual(result["revision"], 2)
        self.assertGreaterEqual(store.write_calls, 2)
        self.assertEqual(result["digest"], store.record["digest"])

    def test_stale_revision_and_failed_readback_are_bounded(self) -> None:
        store = RecoveryStore()
        store.readback_failures = 5
        with self.assertRaisesRegex(ManifestPersistenceError, "durable_storage_exhausted"):
            persist_manifest(manifest(), store, max_attempts=2)
        self.assertEqual(store.write_calls, 2)
        self.assertGreaterEqual(store.read_calls, store.write_calls)

    def test_changed_digest_at_unchanged_revision_fails_closed_after_valid_payload_checks(self) -> None:
        store = RecoveryStore(manifest())
        assert store.record is not None
        revision = store.record["revision"]
        store.record["digest"] = "sha256:" + "c" * 64

        with self.assertRaises(ManifestPersistenceError) as context:
            persist_manifest(manifest(), store)

        self.assertEqual(context.exception.code, MANIFEST_PERSISTENCE_FAILURE)
        self.assertEqual(store.record["revision"], revision)

    def test_monotonic_cas_write_binds_advanced_timestamp_and_transition_event(self) -> None:
        store = RecoveryStore()
        first = manifest()
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

        second = manifest({"kind": "run", "id": "run-1"})
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

        self.assertEqual(result["revision"], 2)
        self.assertEqual(result["digest"], second_digest)
        self.assertEqual(result["updated_at"], second_updated_at)
        self.assertEqual(result["transition_event"]["revision"], 2)
        self.assertEqual(store.record["updated_at"], second_updated_at)
        self.assertEqual(store.record["transition_event"]["digest"], second_digest)

    def test_next_heartbeat_reconstructs_missing_transitions_without_dispatch(self) -> None:
        store = RecoveryStore(manifest({"kind": "dispatch", "id": "dispatch-1"}))
        authority = Authority(
            {
                "identity": dict(IDENTITY),
                "cursor": {"runId": "run-1", "status": "completed"},
                "github": {
                    "workflowRunId": "run-1",
                    "pr": {"number": 9, "head": IDENTITY["commit"], "merged": True},
                    "archive": {"id": "archive-1", "readback": True},
                },
                "git": {"head": IDENTITY["commit"], "tree": IDENTITY["tree"]},
            }
        )
        result = reconcile_manifest_heartbeat(store, authority, max_attempts=3)
        kinds = [row["kind"] for row in result["reconstructed"]]
        self.assertEqual(kinds, ["run", "integration", "archive"])
        self.assertFalse(result["dispatchPerformed"])
        self.assertEqual(len({row["id"] for row in result["reconstructed"]}), 3)

        repeated = reconcile_manifest_heartbeat(store, authority, max_attempts=3)
        self.assertEqual(repeated["reconstructed"], [])

    def test_heartbeat_never_claims_an_undispatched_persisted_action(self) -> None:
        store = RecoveryStore(manifest({"kind": "dispatch", "id": "dispatch-1"}))
        authority = Authority(
            {
                "identity": dict(IDENTITY),
                "cursor": {"status": "queued"},
                "github": {},
                "git": {"head": IDENTITY["commit"], "tree": IDENTITY["tree"]},
            }
        )

        result = reconcile_manifest_heartbeat(store, authority, max_attempts=3)

        self.assertEqual(result["status"], "reconciled")
        self.assertFalse(result["dispatchPerformed"])
        self.assertEqual(result["reconstructed"], [])
        self.assertEqual(store.read()["manifest"]["transitions"], [{"kind": "dispatch", "id": "dispatch-1"}])

    def test_authority_identity_mismatch_is_fail_closed_and_not_conversation_derived(self) -> None:
        store = RecoveryStore(manifest())
        authority = Authority(
            {
                "identity": {**IDENTITY, "tree": "c" * 40},
                "cursor": {"conversation": "pretend this is authority"},
                "github": {},
                "git": {},
            }
        )
        with self.assertRaisesRegex(ManifestPersistenceError, "authority_identity_mismatch"):
            reconcile_manifest_heartbeat(store, authority, max_attempts=1)

    def test_repeated_authority_failure_notifies_only_after_bound(self) -> None:
        class BrokenAuthority(Authority):
            def read_authoritative_state(self, identity):
                del identity
                raise AuthorityFailure("cursor unavailable")

        store = RecoveryStore(manifest())
        authority = BrokenAuthority({})
        first = reconcile_manifest_heartbeat(store, authority, max_attempts=2)
        self.assertFalse(first["notify"])
        second = reconcile_manifest_heartbeat(store, authority, max_attempts=2)
        self.assertTrue(second["notify"])
        self.assertEqual(second["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
