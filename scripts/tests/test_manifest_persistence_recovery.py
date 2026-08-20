"""Adversarial tests for PKT-08 manifest persistence and heartbeat recovery."""

from __future__ import annotations

import copy
import unittest

from core.execution.manifest_persistence import (
    AuthorityFailure,
    DurableManifestStore,
    ManifestPersistenceError,
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
            self.record = {
                "revision": current_revision + 1,
                "digest": current_digest or "sha256:" + "0" * 64,
                "manifest": current["manifest"] if current else manifest(),
            }
            raise ManifestPersistenceError("revision_conflict", "simulated collision")
        if current_revision != expected_revision or current_digest != expected_digest:
            raise ManifestPersistenceError("revision_conflict", "stale revision")
        next_record = {
            "revision": expected_revision + 1,
            "digest": payload["digest"],
            "manifest": copy.deepcopy(payload["manifest"]),
        }
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
