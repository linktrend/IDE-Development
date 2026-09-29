#!/usr/bin/env python3
"""Token-independent GitHub auth for Issue checkpoints and the orchestrator.

Issue checkpoints never require ``AUTOMATION_TOKEN`` or any GitHub API token.
Live orchestrator PR/merge operations need a normal GitHub API token
(``GH_TOKEN`` then ``GITHUB_TOKEN``). The retired ``AUTOMATION_TOKEN`` is not a
credential and cannot satisfy checkpoint acceptance or bypass substantive proof.
"""

from __future__ import annotations

import os
from typing import Mapping

try:
    from core.execution.protocol import WAIVED_LEGACY_GATE
except ModuleNotFoundError:  # pragma: no cover - script-style execution
    from execution.protocol import WAIVED_LEGACY_GATE  # type: ignore

PHASE_API_TOKEN_ENVS = ("GH_TOKEN", "GITHUB_TOKEN")
LEGACY_PUBLISHER_TOKEN_ENV = "AUTOMATION_TOKEN"
LEGACY_PUBLISHER_SOURCE_ENV = "AUTOMATION_TOKEN_SOURCE"


class GitHubAuthError(ValueError):
    """Fail-closed GitHub credential rejection."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail or code
        super().__init__(self.code if not detail else f"{self.code}: {self.detail}")

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "detail": self.detail}


def _nonempty(source: Mapping[str, str], key: str) -> str:
    return str(source.get(key) or "").strip()


def checkpoint_requires_token() -> bool:
    """v2.5 Issue checkpoints are token-independent."""

    return False


def checkpoint_requires_automation_token() -> bool:
    return False


def resolve_phase_api_token(
    environ: Mapping[str, str] | None = None,
) -> tuple[str, str]:
    """Resolve a GitHub API token for live Phase PR/merge operations.

    Does not require ``AUTOMATION_TOKEN`` or ``AUTOMATION_TOKEN_SOURCE``.
    Legacy publisher tokens are never treated as canonical credentials.
    """

    env = environ if environ is not None else os.environ
    for key in PHASE_API_TOKEN_ENVS:
        token = _nonempty(env, key)
        if token:
            return token, key
    auto = _nonempty(env, LEGACY_PUBLISHER_TOKEN_ENV)
    if auto:
        raise GitHubAuthError(
            "legacy_publisher_token_not_canonical",
            "AUTOMATION_TOKEN is a waived legacy publisher token, not a Phase API credential",
        )
    raise GitHubAuthError(
        "missing_github_credentials",
        "live Phase GitHub operations require GH_TOKEN or GITHUB_TOKEN",
    )


def classify_legacy_publisher_token(
    environ: Mapping[str, str] | None = None,
) -> dict[str, object]:
    """Classify retired publisher-token presence. Never PASS; never a failure."""

    env = environ if environ is not None else os.environ
    present = bool(_nonempty(env, LEGACY_PUBLISHER_TOKEN_ENV))
    return {
        "tokenPresent": present,
        "tokenSource": _nonempty(env, LEGACY_PUBLISHER_SOURCE_ENV),
        "state": "success" if present else "missing",
        "classification": WAIVED_LEGACY_GATE,
        "isPass": False,
        "isImplementationFailure": False,
        "canonicalForV25": "none",
        "reason": "legacy_publisher_waived",
    }


def issue_checkpoint_auth_decision(
    environ: Mapping[str, str] | None = None,
) -> dict[str, object]:
    """Auth view for Issue checkpoint acceptance: tokens are nonrequirements."""

    legacy = classify_legacy_publisher_token(environ)
    return {
        "acceptWithoutToken": True,
        "acceptWithoutIssuePr": True,
        "acceptWithoutHostedCompletionStatus": True,
        "automationTokenRequired": False,
        "legacyPublisher": legacy,
        "legacyClassification": WAIVED_LEGACY_GATE,
        "pass": False,
    }
