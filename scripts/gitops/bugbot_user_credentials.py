#!/usr/bin/env python3
"""Carlos user-token credentials for two Packager operations only.

Allowed operations:
  - pr_create: Review Packager feature PR creation into development
  - bugbot_comment: exactly one `@cursor review` + SHA marker comment

Never use this token for merge, promote, repair, status/check writes, cleanup,
or branch pushes. Never print or return token material in logs/outcomes.
"""

from __future__ import annotations

import os

ALLOWED_OPERATIONS = frozenset({"pr_create", "bugbot_comment"})

# Env keys that must never silently substitute for the user token.
_FORBIDDEN_EQUALITY_KEYS = (
    "AUTOMATION_TOKEN",
    "LINKTREND_APP_TOKEN",
    "GH_TOKEN",
    "GITHUB_TOKEN",
)


class BugbotUserCredentialsError(RuntimeError):
    """User token missing or invalid for a permitted Packager operation."""


def resolve_bugbot_user_token() -> tuple[str | None, str, str]:
    """Resolve BUGBOT_USER_TOKEN without logging secret material.

    Returns:
      (token_or_none, source, status)

    source: user_secret | none | invalid
    status: configured | missing | must_not_equal_automation_or_github_token
    """
    raw = (
        os.environ.get("BUGBOT_USER_TOKEN")
        or os.environ.get("LINKTREND_BUGBOT_USER_TOKEN")
        or ""
    ).strip()
    if not raw:
        return None, "none", "missing"

    for key in _FORBIDDEN_EQUALITY_KEYS:
        other = (os.environ.get(key) or "").strip()
        if other and raw == other:
            return None, "invalid", "must_not_equal_automation_or_github_token"

    return raw, "user_secret", "configured"


def require_bugbot_user_token(operation: str) -> str:
    """Fail closed: return user token only for an allowlisted operation."""
    if operation not in ALLOWED_OPERATIONS:
        raise BugbotUserCredentialsError(
            f"operation_not_permitted_for_bugbot_user_token:{operation}"
        )
    token, source, status = resolve_bugbot_user_token()
    if not token or source != "user_secret" or status != "configured":
        raise BugbotUserCredentialsError(
            f"bugbot_user_credentials_blocked:{status}"
        )
    return token
