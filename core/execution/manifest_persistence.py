"""PKT-08 canonical manifest persistence and heartbeat self-recovery."""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol


MAX_PERSISTENCE_ATTEMPTS = 3
TRANSITION_KINDS = ("dispatch", "run", "integration", "archive")
CONFIG_RELATIVE_PATH = "core/managed-core/content/config/manifest-persistence.json"
SCHEMA_RELATIVE_PATH = "core/managed-core/schemas/manifest-persistence.schema.json"
MANIFEST_PERSISTENCE_FAILURE = "MANIFEST_PERSISTENCE_FAILURE"


def load_manifest_persistence_config(repo_root: Path | str) -> dict[str, Any]:
    """Load the packaged bounded recovery policy without ambient checkout state."""
    root = Path(repo_root).resolve()
    payload = json.loads((root / CONFIG_RELATIVE_PATH).read_text(encoding="utf-8"))
    if (
        payload.get("schemaVersion") != 1
        or payload.get("amendment") != "V25_PKT08_MANIFEST_PERSISTENCE_RECOVERY"
        or payload.get("maxCompareAndRetryAttempts") != MAX_PERSISTENCE_ATTEMPTS
        or payload.get("requiredAuthorities") != ["cursor", "github", "git"]
        or payload.get("conversationIsAuthority") is not False
        or payload.get("duplicateDispatch") != "suppress"
    ):
        raise ManifestPersistenceError("config_invalid", "manifest persistence policy is not the packaged contract")
    return payload


class ManifestPersistenceError(RuntimeError):
    """Bounded persistence or authority failure."""

    def __init__(self, code: str, detail: str, **diagnostics: Any) -> None:
        self.code = code
        self.detail = detail
        self.diagnostics = diagnostics
        super().__init__(f"{code}: {detail}")


class AuthorityFailure(ManifestPersistenceError):
    """Transient failure reading an external authority."""

    def __init__(self, detail: str, **diagnostics: Any) -> None:
        super().__init__("authority_unavailable", detail, **diagnostics)


class DurableManifestStore(Protocol):
    def read(self) -> Mapping[str, Any] | None:
        ...

    def compare_and_write(
        self,
        expected_revision: int,
        expected_digest: str | None,
        payload: Mapping[str, Any],
    ) -> None:
        ...


class AuthorityPort(Protocol):
    def read_authoritative_state(self, identity: Mapping[str, str]) -> Mapping[str, Any]:
        ...


@dataclass(frozen=True)
class ManifestRead:
    revision: int
    digest: str | None
    manifest: Mapping[str, Any]
    updated_at: str | int | float | None = None
    transition_event: Mapping[str, Any] | None = None


def canonical_manifest_digest(manifest: Mapping[str, Any]) -> str:
    data = json.dumps(manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _read_record(store: DurableManifestStore) -> ManifestRead | None:
    raw = store.read()
    if raw is None:
        return None
    if not isinstance(raw, Mapping) or not isinstance(raw.get("revision"), int):
        raise ManifestPersistenceError("storage_invalid", "durable manifest record is malformed")
    manifest = raw.get("manifest")
    if not isinstance(manifest, Mapping):
        raise ManifestPersistenceError("storage_invalid", "durable manifest payload is missing")
    digest = raw.get("digest")
    if digest is not None and not isinstance(digest, str):
        raise ManifestPersistenceError("storage_invalid", "durable manifest digest is malformed")
    observed = canonical_manifest_digest(manifest)
    if digest is not None and digest != observed:
        raise ManifestPersistenceError(
            MANIFEST_PERSISTENCE_FAILURE,
            "durable manifest digest does not match payload",
            expectedDigest=digest,
            observedDigest=observed,
        )
    updated_at = raw.get("updated_at")
    if updated_at is not None and (
        isinstance(updated_at, bool)
        or not isinstance(updated_at, (str, int, float))
    ):
        raise ManifestPersistenceError(
            MANIFEST_PERSISTENCE_FAILURE,
            "durable manifest updated_at is malformed",
        )
    transition_event = raw.get("transition_event")
    if transition_event is not None and not isinstance(transition_event, Mapping):
        raise ManifestPersistenceError(
            MANIFEST_PERSISTENCE_FAILURE,
            "durable manifest transition event is malformed",
        )
    if transition_event is not None:
        if (
            transition_event.get("revision") != int(raw["revision"])
            or transition_event.get("digest") != digest
            or transition_event.get("updated_at") != updated_at
        ):
            raise ManifestPersistenceError(
                MANIFEST_PERSISTENCE_FAILURE,
                "durable manifest transition event is not bound to its record",
            )
    return ManifestRead(
        int(raw["revision"]),
        digest,
        copy.deepcopy(dict(manifest)),
        updated_at,
        copy.deepcopy(dict(transition_event)) if transition_event is not None else None,
    )


def _updated_at_advanced(
    previous: str | int | float | None,
    current: str | int | float,
) -> bool:
    if previous is None:
        return True
    if type(previous) is type(current) and isinstance(current, (int, float, str)):
        return current > previous
    return False


def _validate_transition_event(
    transition_event: Mapping[str, Any],
    *,
    revision: int,
    digest: str,
    updated_at: str | int | float | None,
) -> dict[str, Any]:
    event = copy.deepcopy(dict(transition_event))
    if (
        event.get("revision") != revision
        or event.get("digest") != digest
        or event.get("updated_at") != updated_at
    ):
        raise ManifestPersistenceError(
            MANIFEST_PERSISTENCE_FAILURE,
            "manifest transition event is not bound to the CAS write",
            expectedRevision=revision,
            expectedDigest=digest,
            expectedUpdatedAt=updated_at,
        )
    return event


def persist_manifest(
    manifest: Mapping[str, Any],
    store: DurableManifestStore,
    *,
    max_attempts: int = MAX_PERSISTENCE_ATTEMPTS,
    updated_at: str | int | float | None = None,
    transition_event: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Compare-and-retry a canonical write, with a fresh read after every write."""

    if max_attempts < 1:
        raise ValueError("max_attempts must be positive")
    candidate = copy.deepcopy(dict(manifest))
    candidate_digest = canonical_manifest_digest(candidate)
    if updated_at is not None and (
        isinstance(updated_at, bool)
        or not isinstance(updated_at, (str, int, float))
    ):
        raise ManifestPersistenceError(
            MANIFEST_PERSISTENCE_FAILURE,
            "manifest updated_at is malformed",
        )
    if transition_event is not None and not isinstance(transition_event, Mapping):
        raise ManifestPersistenceError(
            MANIFEST_PERSISTENCE_FAILURE,
            "manifest transition event is malformed",
        )
    metadata_requested = updated_at is not None or transition_event is not None
    last_error: ManifestPersistenceError | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            current = _read_record(store)
            if (
                current is not None
                and current.digest == candidate_digest
                and current.manifest == candidate
                and not metadata_requested
            ):
                return {
                    "revision": current.revision,
                    "digest": current.digest,
                    "manifest": copy.deepcopy(dict(current.manifest)),
                    "attempts": attempt,
                }
            expected_revision = current.revision if current is not None else 0
            expected_digest = current.digest if current is not None else None
            next_revision = expected_revision + 1
            if (
                updated_at is not None
                and current is not None
                and not _updated_at_advanced(current.updated_at, updated_at)
            ):
                raise ManifestPersistenceError(
                    MANIFEST_PERSISTENCE_FAILURE,
                    "manifest updated_at did not advance monotonically",
                    previousUpdatedAt=current.updated_at,
                    observedUpdatedAt=updated_at,
                )
            event = (
                _validate_transition_event(
                    transition_event,
                    revision=next_revision,
                    digest=candidate_digest,
                    updated_at=updated_at,
                )
                if transition_event is not None
                else None
            )
            payload = {
                "digest": candidate_digest,
                "manifest": candidate,
            }
            if updated_at is not None:
                payload["updated_at"] = updated_at
            if event is not None:
                payload["transition_event"] = event
            store.compare_and_write(expected_revision, expected_digest, payload)
            readback = _read_record(store)
            if (
                readback is not None
                and readback.revision == next_revision
                and readback.digest == candidate_digest
                and readback.manifest == candidate
                and (updated_at is None or readback.updated_at == updated_at)
                and (event is None or readback.transition_event == event)
            ):
                result = {
                    "revision": readback.revision,
                    "digest": readback.digest,
                    "manifest": copy.deepcopy(dict(readback.manifest)),
                    "attempts": attempt,
                }
                if readback.updated_at is not None:
                    result["updated_at"] = readback.updated_at
                if readback.transition_event is not None:
                    result["transition_event"] = copy.deepcopy(
                        dict(readback.transition_event)
                    )
                return result
            last_error = ManifestPersistenceError(
                "readback_mismatch",
                "fresh manifest readback did not match the write",
                expectedRevision=expected_revision + 1,
                observedRevision=readback.revision if readback else None,
                expectedDigest=candidate_digest,
                observedDigest=readback.digest if readback else None,
            )
        except ManifestPersistenceError as exc:
            last_error = exc
            if exc.code not in {"revision_conflict", "readback_mismatch", "storage_unavailable"}:
                raise
    raise ManifestPersistenceError(
        "durable_storage_exhausted",
        "bounded canonical manifest persistence attempts exhausted",
        attempts=max_attempts,
        lastCode=last_error.code if last_error else "unknown",
        lastDetail=last_error.detail if last_error else "unknown",
    )


def _transition_id(kind: str, identity: Mapping[str, str], authority: Mapping[str, Any]) -> str:
    payload = {"kind": kind, "identity": dict(identity), "authority": authority}
    data = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "recovered-" + hashlib.sha256(data).hexdigest()[:24]


def _identity_matches(expected: Mapping[str, str], observed: Mapping[str, Any]) -> bool:
    return all(observed.get(key) == value for key, value in expected.items())


def _authoritative_transitions(
    identity: Mapping[str, str],
    snapshot: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if not _identity_matches(identity, snapshot.get("identity") or {}):
        raise ManifestPersistenceError(
            "authority_identity_mismatch",
            "Cursor/GitHub/Git authority does not bind to the canonical identity",
            expectedIdentity=dict(identity),
            observedIdentity=dict(snapshot.get("identity") or {}),
        )
    cursor = snapshot.get("cursor")
    github = snapshot.get("github")
    git = snapshot.get("git")
    if not all(isinstance(value, Mapping) for value in (cursor, github, git)):
        raise AuthorityFailure("authority_incomplete", "Cursor, GitHub, and Git identities are all required")
    transitions: list[dict[str, Any]] = []
    dispatch_id = cursor.get("dispatchId") or github.get("dispatchId")
    if dispatch_id:
        transitions.append({"kind": "dispatch", "authorityId": str(dispatch_id)})
    run_id = cursor.get("runId") or github.get("workflowRunId")
    if run_id and str(cursor.get("status") or github.get("status") or "").lower() in {
        "queued",
        "running",
        "completed",
        "success",
        "failure",
    }:
        transitions.append({"kind": "run", "authorityId": str(run_id)})
    pr = github.get("pr")
    if (
        isinstance(pr, Mapping)
        and pr.get("merged") is True
        and pr.get("head") == identity.get("commit")
        and git.get("head") == identity.get("commit")
        and git.get("tree") == identity.get("tree")
    ):
        transitions.append({"kind": "integration", "authorityId": str(pr.get("number") or "")})
    archive = github.get("archive")
    if isinstance(archive, Mapping) and archive.get("readback") is True and archive.get("id"):
        transitions.append({"kind": "archive", "authorityId": str(archive["id"])})
    return transitions


def _failure_manifest(current: Mapping[str, Any], *, count: int, code: str) -> dict[str, Any]:
    updated = copy.deepcopy(dict(current))
    updated["authorityFailures"] = count
    updated["lastAuthorityFailure"] = code
    return updated


def reconcile_manifest_heartbeat(
    store: DurableManifestStore,
    authority: AuthorityPort,
    *,
    max_attempts: int = MAX_PERSISTENCE_ATTEMPTS,
) -> dict[str, Any]:
    """Recover only identity-bound transitions observed from external authorities."""

    current_record = _read_record(store)
    if current_record is None:
        raise ManifestPersistenceError("manifest_missing", "canonical manifest is missing")
    current = dict(current_record.manifest)
    identity = current.get("identity")
    if not isinstance(identity, Mapping) or not all(
        isinstance(identity.get(key), str) and identity.get(key)
        for key in ("repository", "commit", "tree")
    ):
        raise ManifestPersistenceError("manifest_identity_missing", "canonical manifest identity is incomplete")

    try:
        snapshot = authority.read_authoritative_state(dict(identity))
        transitions = _authoritative_transitions(dict(identity), snapshot)
    except AuthorityFailure as exc:
        failures = int(current.get("authorityFailures") or 0) + 1
        notify = failures >= max_attempts
        updated = _failure_manifest(current, count=failures, code=exc.code)
        try:
            persist_manifest(updated, store, max_attempts=max_attempts)
        except ManifestPersistenceError:
            pass
        return {
            "status": "blocked" if notify else "retry",
            "notify": notify,
            "reconstructed": [],
            "dispatchPerformed": False,
            "failureCode": exc.code,
        }
    except ManifestPersistenceError:
        raise

    existing = current.get("transitions")
    if not isinstance(existing, list):
        raise ManifestPersistenceError("manifest_transitions_invalid", "canonical transitions must be an array")
    existing_ids = {
        str(item.get("id"))
        for item in existing
        if isinstance(item, Mapping) and item.get("id")
    }
    recovered: list[dict[str, Any]] = []
    for transition in transitions:
        event_id = _transition_id(str(transition["kind"]), dict(identity), transition)
        if event_id in existing_ids:
            continue
        recovered.append({
            "id": event_id,
            "kind": transition["kind"],
            "authorityId": transition["authorityId"],
            "identity": dict(identity),
            "reconstructedOnHeartbeat": True,
        })
        existing_ids.add(event_id)
    updated = copy.deepcopy(current)
    updated["transitions"] = existing + recovered
    updated.pop("authorityFailures", None)
    updated.pop("lastAuthorityFailure", None)
    persisted = persist_manifest(updated, store, max_attempts=max_attempts)
    return {
        "status": "reconciled",
        "notify": False,
        "reconstructed": recovered,
        "dispatchPerformed": False,
        "revision": persisted["revision"],
        "digest": persisted["digest"],
    }
