"""Semantic lifecycle validation for execution-manifest runtime states.

Rejects inconsistent packet/attempt/evidence/lease/lock/archive records.
Does not silently normalize. Diagnostics always name packet and attempt.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from core.execution.protocol import ValidationResult, validate_execution_manifest

_SHA40 = frozenset("0123456789abcdef")

COMPLETED_STATES = frozenset({"COMPLETE", "ARCHIVE_CONFIRMED"})
RUNNING_STATE = "RUNNING"
PLAN_STATE = "PLAN"
TERMINAL_LIFECYCLE = "TERMINAL"
NONTERMINAL_LIFECYCLE = "RUNNING"
TERMINAL_RAW = frozenset({"succeeded", "failed", "cancelled", "archived"})
NONTERMINAL_RAW = frozenset({"running", "queued"})
PACKET_COMPLETION_KIND = "packet_completion"
EVENT_KIND = "event"


def _is_sha40(value: str) -> bool:
    return len(value) == 40 and all(char in _SHA40 for char in value)


@dataclass(frozen=True)
class LifecycleDiagnostic:
    packet_id: str
    attempt_id: str | None
    code: str

    def format(self) -> str:
        attempt = self.attempt_id if self.attempt_id else "-"
        return f"packet={self.packet_id} attempt={attempt}: {self.code}"


def _diag(
    packet_id: str,
    code: str,
    *,
    attempt_id: str | None = None,
) -> LifecycleDiagnostic:
    return LifecycleDiagnostic(packet_id, attempt_id, code)


def _attempts(packet: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw = packet.get("attempts")
    if raw is None:
        return []
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict)]


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_terminal_attempt(attempt: Mapping[str, Any]) -> bool:
    return (
        attempt.get("lifecycle") == TERMINAL_LIFECYCLE
        and attempt.get("rawStatus") in TERMINAL_RAW
        and _nonempty(attempt.get("endedAt"))
        and (_nonempty(attempt.get("result")) or _nonempty(attempt.get("reason")))
    )


def _is_nonterminal_attempt(attempt: Mapping[str, Any]) -> bool:
    return (
        attempt.get("lifecycle") == NONTERMINAL_LIFECYCLE
        and attempt.get("rawStatus") in NONTERMINAL_RAW
        and not _nonempty(attempt.get("endedAt"))
    )


def _lock_active(packet: Mapping[str, Any]) -> bool:
    lock = packet.get("writeLock")
    return isinstance(lock, dict) and lock.get("active") is True


def _completion_evidence_ok(packet: Mapping[str, Any], diagnostics: list[LifecycleDiagnostic]) -> None:
    packet_id = str(packet.get("id") or "-")
    evidence = packet.get("completionEvidence")
    accepted_commit = packet.get("acceptedCommit")
    accepted_tree = packet.get("acceptedTree")
    if not _is_sha40(str(accepted_commit or "")) or not _is_sha40(str(accepted_tree or "")):
        diagnostics.append(_diag(packet_id, "missing_accepted_commit_tree"))
        return
    if not isinstance(evidence, dict) or not evidence:
        diagnostics.append(_diag(packet_id, "empty_completion_evidence"))
        return
    kind = evidence.get("kind")
    if kind == EVENT_KIND:
        diagnostics.append(_diag(packet_id, "event_only_completion_evidence"))
        return
    if kind != PACKET_COMPLETION_KIND:
        diagnostics.append(_diag(packet_id, "empty_completion_evidence"))
        return
    if not _nonempty(evidence.get("summary")):
        diagnostics.append(_diag(packet_id, "empty_completion_evidence"))
        return
    if evidence.get("commit") != accepted_commit or evidence.get("tree") != accepted_tree:
        diagnostics.append(_diag(packet_id, "completion_evidence_identity_mismatch"))
        return
    if not _is_sha40(str(evidence.get("commit") or "")) or not _is_sha40(
        str(evidence.get("tree") or "")
    ):
        diagnostics.append(_diag(packet_id, "completion_evidence_identity_mismatch"))


def _archive_evidence_ok(packet: Mapping[str, Any], diagnostics: list[LifecycleDiagnostic]) -> None:
    packet_id = str(packet.get("id") or "-")
    evidence = packet.get("archiveEvidence")
    if not isinstance(evidence, dict):
        diagnostics.append(_diag(packet_id, "missing_archive_readback"))
        return
    readback = evidence.get("readback")
    if evidence.get("apiReadback") is not True or readback in (None, "", {}, []):
        diagnostics.append(_diag(packet_id, "missing_archive_readback"))


def _validate_completed_packet(
    packet: Mapping[str, Any],
    diagnostics: list[LifecycleDiagnostic],
) -> None:
    packet_id = str(packet.get("id") or "-")
    _completion_evidence_ok(packet, diagnostics)
    if packet.get("executionState") == "ARCHIVE_CONFIRMED":
        _archive_evidence_ok(packet, diagnostics)
    if _lock_active(packet):
        lock = packet.get("writeLock") if isinstance(packet.get("writeLock"), dict) else {}
        diagnostics.append(
            _diag(
                packet_id,
                "completed_packet_has_active_lock",
                attempt_id=str(lock.get("attemptId") or "-"),
            )
        )
    attempts = _attempts(packet)
    if not attempts:
        diagnostics.append(_diag(packet_id, "completed_packet_missing_terminal_attempts"))
        return
    for attempt in attempts:
        attempt_id = str(attempt.get("id") or "-")
        if _is_nonterminal_attempt(attempt) or attempt.get("lifecycle") == NONTERMINAL_LIFECYCLE:
            diagnostics.append(
                _diag(packet_id, "complete_packet_has_running_attempt", attempt_id=attempt_id)
            )
            continue
        if not _is_terminal_attempt(attempt):
            diagnostics.append(
                _diag(packet_id, "completed_attempt_not_terminal", attempt_id=attempt_id)
            )


def _validate_running_packet(
    packet: Mapping[str, Any],
    diagnostics: list[LifecycleDiagnostic],
) -> None:
    packet_id = str(packet.get("id") or "-")
    attempts = _attempts(packet)
    for attempt in attempts:
        if _is_terminal_attempt(attempt) or _is_nonterminal_attempt(attempt):
            continue
        diagnostics.append(
            _diag(
                packet_id,
                "attempt_neither_terminal_nor_nonterminal",
                attempt_id=str(attempt.get("id") or "-"),
            )
        )
    current = [
        attempt
        for attempt in attempts
        if attempt.get("authoritative") is True and _is_nonterminal_attempt(attempt)
    ]
    if len(current) != 1:
        diagnostics.append(
            _diag(
                packet_id,
                "running_packet_requires_one_authoritative_nonterminal_attempt",
                attempt_id="-",
            )
        )
        current_id = "-"
        current_attempt = None
    else:
        current_attempt = current[0]
        current_id = str(current_attempt.get("id") or "-")
    lock = packet.get("writeLock")
    expected_lock_id = current_id if current_attempt is not None else None
    if (
        not isinstance(lock, dict)
        or lock.get("active") is not True
        or (expected_lock_id is not None and lock.get("attemptId") != expected_lock_id)
        or expected_lock_id is None
    ):
        diagnostics.append(
            _diag(packet_id, "running_packet_missing_active_write_lock", attempt_id=current_id)
        )
    lease = packet.get("orchestrationLease")
    if (
        not isinstance(lease, dict)
        or not _nonempty(lease.get("holder"))
        or not _nonempty(lease.get("nonce"))
        or not _nonempty(lease.get("expiresAt"))
    ):
        diagnostics.append(
            _diag(packet_id, "running_packet_missing_orchestration_lease", attempt_id=current_id)
        )


def validate_execution_lifecycle(document: Mapping[str, Any]) -> ValidationResult:
    packets = document.get("packets")
    if not isinstance(packets, list):
        return ValidationResult(ok=False, errors=("packets_missing",))
    diagnostics: list[LifecycleDiagnostic] = []
    for packet in packets:
        if not isinstance(packet, dict):
            diagnostics.append(_diag("-", "packet_not_object"))
            continue
        packet_id = str(packet.get("id") or "-")
        state = packet.get("executionState")
        if state in (None, PLAN_STATE):
            continue
        if state == RUNNING_STATE:
            _validate_running_packet(packet, diagnostics)
            continue
        if state in COMPLETED_STATES:
            _validate_completed_packet(packet, diagnostics)
            continue
        diagnostics.append(_diag(packet_id, "unknown_execution_state"))
    if diagnostics:
        return ValidationResult(
            ok=False,
            errors=tuple(item.format() for item in diagnostics),
        )
    return ValidationResult(ok=True)


def validate_plan_or_runtime(
    document: Mapping[str, Any],
    *,
    schema: Mapping[str, Any] | None = None,
    repo_root: Path | str | None = None,
) -> ValidationResult:
    schema_result = validate_execution_manifest(
        document, schema=schema, repo_root=repo_root
    )
    if not schema_result.ok:
        return schema_result
    return validate_execution_lifecycle(document)
