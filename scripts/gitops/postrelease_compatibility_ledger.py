"""Fail-closed evaluation of the v2.5.2 post-release consumer compatibility ledger.

Observation helper only. It does not install consumers, publish releases, or
promote protected branches.
"""

from __future__ import annotations

from typing import Any, Mapping

RELEASED_PACKAGE_VERSION = "2.5.2"
LEDGER_KIND = "ide-development-v2.5.2-postrelease-consumer-compatibility-ledger"

FAIL_RELEASED_IDENTITY = "released_identity_mismatch"
FAIL_CONSUMER_HASH = "consumer_manifest_hash_mismatch"
FAIL_INCOMPLETE = "portfolio_observation_incomplete"


def evaluate_ref(
    released_manifest_hash: str,
    observation: Mapping[str, Any],
    *,
    promotion_ref: bool = False,
) -> str:
    """Return the required status for one consumer ref observation."""

    status = observation.get("status")
    if not isinstance(status, str) or not status:
        raise ValueError("consumer_ref_status_missing")

    if status == "observation_unavailable":
        return status

    version = observation.get("packageVersion")
    observed_hash = observation.get("manifestHash") or observation.get(
        "installedManifestSha256"
    )

    if version == RELEASED_PACKAGE_VERSION:
        if observed_hash != released_manifest_hash:
            return "mismatch"
        if promotion_ref:
            return "match"
        return "match"

    if promotion_ref:
        return "older_package"
    if version and version != RELEASED_PACKAGE_VERSION:
        return "older_package"
    return status


def evaluate_ledger(document: Mapping[str, Any]) -> tuple[str, list[str]]:
    """Return (overallVerdict, failClosedReasons) for a ledger document."""

    if document.get("kind") != LEDGER_KIND:
        raise ValueError("ledger_kind_invalid")
    if document.get("packageVersion") != RELEASED_PACKAGE_VERSION:
        raise ValueError("ledger_package_version_invalid")

    released = document.get("releasedIdentity")
    if not isinstance(released, Mapping):
        raise ValueError("released_identity_missing")

    reasons: list[str] = []
    protected_main = released.get("protectedMain")
    if not isinstance(protected_main, Mapping) or protected_main.get(
        "matchesReleasedIdentity"
    ) is not True:
        reasons.append(FAIL_RELEASED_IDENTITY)
    if released.get("sourceCommit") != (protected_main or {}).get("commit"):
        reasons.append(FAIL_RELEASED_IDENTITY)
    if released.get("sourceTree") != (protected_main or {}).get("tree"):
        reasons.append(FAIL_RELEASED_IDENTITY)

    archives = released.get("archives")
    if not isinstance(archives, list) or not archives:
        reasons.append(FAIL_RELEASED_IDENTITY)
    elif any(row.get("locallyVerified") is not True for row in archives):
        reasons.append(FAIL_RELEASED_IDENTITY)

    released_hash = released.get("manifestHash")
    if not isinstance(released_hash, str) or not released_hash.startswith("sha256:"):
        reasons.append(FAIL_RELEASED_IDENTITY)

    for consumer in document.get("consumers") or []:
        refs = consumer.get("refs") if isinstance(consumer, Mapping) else None
        if not isinstance(refs, Mapping):
            reasons.append(FAIL_INCOMPLETE)
            continue
        development = refs.get("development")
        if not isinstance(development, Mapping):
            reasons.append(FAIL_INCOMPLETE)
            continue
        expected = evaluate_ref(str(released_hash), development)
        if development.get("status") == "observation_unavailable" or expected == "observation_unavailable":
            reasons.append(FAIL_INCOMPLETE)
        if expected == "mismatch" or development.get("status") == "mismatch":
            reasons.append(FAIL_CONSUMER_HASH)
        if development.get("status") != expected and development.get("status") not in {
            "observation_unavailable",
            "mismatch",
            "match",
            "older_package",
        }:
            reasons.append(FAIL_INCOMPLETE)

    unique = []
    for reason in reasons:
        if reason not in unique:
            unique.append(reason)
    verdict = "fail_closed" if unique else "match"
    return verdict, unique
