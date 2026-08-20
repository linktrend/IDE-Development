"""Semantic lifecycle validation tests. None of these tests may skip."""

from __future__ import annotations

import json
import sys
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.execution.lifecycle import (  # noqa: E402
    validate_execution_lifecycle,
    validate_plan_or_runtime,
)
from core.execution.protocol import validate_execution_manifest  # noqa: E402

COMMIT = "004bd5faa1e14ee100a018e16dcb049f0fb2d8eb"
TREE = "6c55220132cc7e9a1baef06f8c147ee9ac9431e7"


def _base() -> dict:
    path = ROOT / "core/execution/examples/execution-manifest.example.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _packet(document: dict) -> dict:
    return document["packets"][0]


def _terminal_attempt(attempt_id: str = "ATT-01") -> dict:
    return {
        "id": attempt_id,
        "authoritative": False,
        "lifecycle": "TERMINAL",
        "rawStatus": "failed",
        "endedAt": "2026-08-20T07:00:00Z",
        "result": None,
        "reason": "ordinary_source_repair",
    }


def _running_attempt(attempt_id: str = "ATT-02") -> dict:
    return {
        "id": attempt_id,
        "authoritative": True,
        "lifecycle": "RUNNING",
        "rawStatus": "running",
        "endedAt": None,
        "result": None,
        "reason": None,
    }


def _success_attempt(attempt_id: str = "ATT-03") -> dict:
    return {
        "id": attempt_id,
        "authoritative": True,
        "lifecycle": "TERMINAL",
        "rawStatus": "succeeded",
        "endedAt": "2026-08-20T08:00:00Z",
        "result": "accepted",
        "reason": None,
    }


def _completion_evidence() -> dict:
    return {
        "kind": "packet_completion",
        "commit": COMMIT,
        "tree": TREE,
        "summary": "ISS-01 protocol contracts accepted",
    }


def repaired_running_history() -> dict:
    document = _base()
    packet = _packet(document)
    packet["executionState"] = "RUNNING"
    packet["attempts"] = [_terminal_attempt("ATT-01"), _running_attempt("ATT-02")]
    packet["writeLock"] = {"active": True, "attemptId": "ATT-02"}
    packet["orchestrationLease"] = {
        "holder": "implementer-341",
        "nonce": "lease-1",
        "expiresAt": "2026-08-20T09:00:00Z",
        "packetId": "PKT-01",
        "repository": "linktrend/IDE-Development",
    }
    return document


def complete_valid() -> dict:
    document = _base()
    packet = _packet(document)
    packet["executionState"] = "COMPLETE"
    packet["acceptedCommit"] = COMMIT
    packet["acceptedTree"] = TREE
    packet["completionEvidence"] = _completion_evidence()
    packet["attempts"] = [_terminal_attempt("ATT-01"), _success_attempt("ATT-03")]
    packet["writeLock"] = {"active": False, "attemptId": "ATT-03"}
    return document


def archive_valid() -> dict:
    document = complete_valid()
    packet = _packet(document)
    packet["executionState"] = "ARCHIVE_CONFIRMED"
    packet["archiveEvidence"] = {
        "apiReadback": True,
        "readback": {"archiveId": "arc-01", "commit": COMMIT, "tree": TREE},
    }
    return document


class SemanticLifecycleTests(unittest.TestCase):
    def test_plan_example_is_schema_and_semantically_valid(self) -> None:
        document = _base()
        schema = validate_execution_manifest(document, repo_root=ROOT)
        semantic = validate_execution_lifecycle(document)
        combined = validate_plan_or_runtime(document, repo_root=ROOT)
        self.assertTrue(schema.ok)
        self.assertTrue(semantic.ok)
        self.assertTrue(combined.ok)
        self.assertFalse(combined.skipped)

    def test_repaired_terminal_history_running_packet_is_valid(self) -> None:
        document = repaired_running_history()
        result = validate_plan_or_runtime(document, repo_root=ROOT)
        self.assertTrue(result.ok, result.errors)
        example = json.loads(
            (ROOT / "core/execution/examples/execution-runtime-repaired-terminal.example.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertTrue(validate_plan_or_runtime(example, repo_root=ROOT).ok)

    def test_complete_and_archive_confirmed_bind_identity_and_evidence(self) -> None:
        complete = validate_plan_or_runtime(complete_valid(), repo_root=ROOT)
        archive = validate_plan_or_runtime(archive_valid(), repo_root=ROOT)
        self.assertTrue(complete.ok, complete.errors)
        self.assertTrue(archive.ok, archive.errors)

    def test_complete_plus_running_attempt_is_rejected_with_packet_attempt(self) -> None:
        document = complete_valid()
        _packet(document)["attempts"].append(_running_attempt("ATT-99"))
        result = validate_plan_or_runtime(document, repo_root=ROOT)
        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "packet=PKT-01 attempt=ATT-99: complete_packet_has_running_attempt" in err
                for err in result.errors
            ),
            result.errors,
        )

    def test_complete_empty_completion_evidence_is_rejected(self) -> None:
        document = complete_valid()
        _packet(document)["completionEvidence"] = {}
        result = validate_plan_or_runtime(document, repo_root=ROOT)
        self.assertFalse(result.ok)
        self.assertTrue(
            any("packet=PKT-01 attempt=-: empty_completion_evidence" in err for err in result.errors),
            result.errors,
        )

    def test_event_only_completion_evidence_is_rejected(self) -> None:
        document = complete_valid()
        _packet(document)["completionEvidence"] = {
            "kind": "event",
            "commit": COMMIT,
            "tree": TREE,
            "summary": "log-only",
        }
        result = validate_plan_or_runtime(document, repo_root=ROOT)
        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "packet=PKT-01 attempt=-: event_only_completion_evidence" in err
                for err in result.errors
            ),
            result.errors,
        )

    def test_archive_confirmed_without_readback_is_rejected(self) -> None:
        document = archive_valid()
        _packet(document)["archiveEvidence"] = {"apiReadback": False, "readback": {}}
        result = validate_plan_or_runtime(document, repo_root=ROOT)
        self.assertFalse(result.ok)
        self.assertTrue(
            any("packet=PKT-01 attempt=-: missing_archive_readback" in err for err in result.errors),
            result.errors,
        )

    def test_running_without_attempt_lock_lease_is_rejected(self) -> None:
        document = _base()
        _packet(document)["executionState"] = "RUNNING"
        result = validate_plan_or_runtime(document, repo_root=ROOT)
        self.assertFalse(result.ok)
        joined = " ".join(result.errors)
        self.assertIn("packet=PKT-01 attempt=-: running_packet_requires_one_authoritative_nonterminal_attempt", joined)
        self.assertIn("packet=PKT-01 attempt=-: running_packet_missing_active_write_lock", joined)
        self.assertIn("packet=PKT-01 attempt=-: running_packet_missing_orchestration_lease", joined)

    def test_completed_packet_cannot_retain_active_lock(self) -> None:
        document = complete_valid()
        _packet(document)["writeLock"] = {"active": True, "attemptId": "ATT-03"}
        result = validate_plan_or_runtime(document, repo_root=ROOT)
        self.assertFalse(result.ok)
        self.assertTrue(
            any(
                "packet=PKT-01 attempt=ATT-03: completed_packet_has_active_lock" in err
                for err in result.errors
            ),
            result.errors,
        )

    def test_does_not_silently_normalize_complete_plus_running(self) -> None:
        document = complete_valid()
        _packet(document)["attempts"].append(_running_attempt("ATT-99"))
        before = deepcopy(document)
        result = validate_plan_or_runtime(document, repo_root=ROOT)
        self.assertFalse(result.ok)
        self.assertEqual(document, before)
        self.assertEqual(_packet(document)["attempts"][-1]["lifecycle"], "RUNNING")


if __name__ == "__main__":
    unittest.main()
