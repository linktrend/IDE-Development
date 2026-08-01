#!/usr/bin/env python3
"""Read-only external-state audit for App-backed Review Ready completion.

Reports required GitHub App / Bugbot / protection external state.
Default mode is dry-run report: emit the checklist without live calls or
mutations. Optional ``--fixture-dir`` (tests/offline) or ``--live`` (operator
read-only GitHub GETs) fill observations.

Never mutates GitHub settings, never creates credentials, and never reads or
prints secret values — secret checks are name-presence only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1

EXIT_OK = 0
EXIT_FAILED = 1
EXIT_NOT_READY = 3
EXIT_REFUSED = 5

APP_ID_VAR = "LINKTREND_GITOPS_APP_ID"
APP_PRIVATE_KEY_SECRET = "LINKTREND_GITOPS_APP_PRIVATE_KEY"
BUGBOT_USER_TOKEN_SECRET = "LINKTREND_BUGBOT_USER_TOKEN"
BUGBOT_CHECK_NAME = "Cursor Bugbot"
SOURCE_POLICY_CHECK = "Enforce allowed PR source branches"
DEVELOPMENT_RULESET = "development-autonomous-merge"
STATUS_CONTEXT = "Linktrend Review Ready"

# Env names that must never appear in report output as values.
_SECRET_ENV_NAMES = frozenset(
    {
        APP_PRIVATE_KEY_SECRET,
        BUGBOT_USER_TOKEN_SECRET,
        "LINKTREND_APP_TOKEN",
        "AUTOMATION_TOKEN",
        "BUGBOT_USER_TOKEN",
        "CURSOR_ADMIN_API_KEY",
        "GH_TOKEN",
        "GITHUB_TOKEN",
    }
)

_MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


class AuditError(Exception):
    def __init__(self, message: str, exit_code: int = EXIT_FAILED) -> None:
        super().__init__(message)
        self.exit_code = exit_code


def _check(
    *,
    check_id: str,
    category: str,
    required: bool,
    expected: str,
    observed: str,
    status: str,
    detail: str = "",
) -> dict[str, Any]:
    return {
        "id": check_id,
        "category": category,
        "required": required,
        "expected": expected,
        "observed": observed,
        "status": status,
        "detail": detail,
    }


def required_checklist() -> list[dict[str, Any]]:
    """Canonical required external-state items (contract surface)."""
    return [
        {
            "id": "github_app.app_id_variable",
            "category": "github_app",
            "required": True,
            "expected": f"{APP_ID_VAR} repository/org variable present and numeric",
        },
        {
            "id": "github_app.private_key_secret",
            "category": "github_app",
            "required": True,
            "expected": (
                f"{APP_PRIVATE_KEY_SECRET} Actions secret name present "
                "(value never read)"
            ),
        },
        {
            "id": "github_app.installation",
            "category": "github_app",
            "required": True,
            "expected": "GitHub App installation present on the repository",
        },
        {
            "id": "bugbot.user_token_secret",
            "category": "bugbot",
            "required": True,
            "expected": (
                f"{BUGBOT_USER_TOKEN_SECRET} Actions secret name present "
                "(value never read)"
            ),
        },
        {
            "id": "bugbot.manual_trigger_only",
            "category": "bugbot",
            "required": True,
            "expected": "Bugbot manualTriggerOnly=true (mention-only)",
        },
        {
            "id": "bugbot.check_name",
            "category": "bugbot",
            "required": True,
            "expected": f"Integrator/ruleset Bugbot check name is {BUGBOT_CHECK_NAME!r}",
        },
        {
            "id": "protection.development_ruleset",
            "category": "protection",
            "required": True,
            "expected": (
                f"Active ruleset {DEVELOPMENT_RULESET!r} on development requires "
                f"{BUGBOT_CHECK_NAME!r} and {SOURCE_POLICY_CHECK!r}"
            ),
        },
        {
            "id": "protection.allow_auto_merge",
            "category": "protection",
            "required": True,
            "expected": "Repository allow_auto_merge=true",
        },
        {
            "id": "completion.status_context",
            "category": "completion",
            "required": True,
            "expected": (
                f"Privileged publish context remains {STATUS_CONTEXT!r} "
                "(App-backed publisher only)"
            ),
        },
    ]


def _secret_env_leak_warnings() -> list[str]:
    """Detect secret material present in the process env without printing values."""
    warnings: list[str] = []
    for name in sorted(_SECRET_ENV_NAMES):
        raw = os.environ.get(name)
        if raw is not None and str(raw).strip():
            warnings.append(
                f"{name}=present_in_process_env (value redacted; audit must not print it)"
            )
    return warnings


class ReadOnlyGitHubClient:
    """GET-only gh api client. Mutating methods raise immediately."""

    def __init__(self, repo: str) -> None:
        self.repo = repo

    def _api_get(self, path: str) -> tuple[int, Any, str]:
        cmd = ["gh", "api", "--method", "GET", path]
        proc = subprocess.run(cmd, text=True, capture_output=True)
        err = (proc.stderr or "").strip()
        if proc.returncode != 0:
            return proc.returncode, None, err or (proc.stdout or "").strip()
        text = (proc.stdout or "").strip()
        if not text:
            return 0, None, ""
        try:
            return 0, json.loads(text), ""
        except json.JSONDecodeError:
            return 0, text, ""

    def mutate(self, method: str, *_args: Any, **_kwargs: Any) -> None:
        method_u = (method or "").upper()
        if method_u in _MUTATING_METHODS:
            raise AuditError(
                f"external_state_audit refuses mutating HTTP method {method_u}",
                EXIT_REFUSED,
            )
        raise AuditError(f"unsupported method: {method}", EXIT_REFUSED)

    def list_actions_variables(self) -> list[dict[str, Any]]:
        code, data, err = self._api_get(f"repos/{self.repo}/actions/variables")
        if code != 0:
            raise AuditError(f"list actions variables failed: {err}")
        if isinstance(data, dict):
            vars_ = data.get("variables") or []
            return list(vars_) if isinstance(vars_, list) else []
        return []

    def list_actions_secret_names(self) -> list[str]:
        """Return secret *names* only — GitHub API never returns values here."""
        code, data, err = self._api_get(f"repos/{self.repo}/actions/secrets")
        if code != 0:
            raise AuditError(f"list actions secrets failed: {err}")
        names: list[str] = []
        if isinstance(data, dict):
            for item in data.get("secrets") or []:
                if isinstance(item, dict) and item.get("name"):
                    names.append(str(item["name"]))
        return names

    def get_installation(self) -> dict[str, Any] | None:
        code, data, err = self._api_get(f"repos/{self.repo}/installation")
        if code != 0:
            low = (err or "").lower()
            if "404" in low or "not installed" in low:
                return None
            raise AuditError(f"get installation failed: {err}")
        return data if isinstance(data, dict) else None

    def list_rulesets(self) -> list[dict[str, Any]]:
        code, data, err = self._api_get(f"repos/{self.repo}/rulesets")
        if code != 0:
            raise AuditError(f"list rulesets failed: {err}")
        if isinstance(data, list):
            return data
        return []

    def get_ruleset(self, ruleset_id: int) -> dict[str, Any] | None:
        code, data, err = self._api_get(f"repos/{self.repo}/rulesets/{ruleset_id}")
        if code != 0:
            low = (err or "").lower()
            if "404" in low:
                return None
            raise AuditError(f"get ruleset {ruleset_id} failed: {err}")
        return data if isinstance(data, dict) else None

    def get_repo(self) -> dict[str, Any]:
        code, data, err = self._api_get(f"repos/{self.repo}")
        if code != 0 or not isinstance(data, dict):
            raise AuditError(f"get repo failed: {err or data}")
        return data

    def get_bugbot_repo_settings(self) -> dict[str, Any] | None:
        """Bugbot settings are not on the GitHub API; live mode leaves unchecked."""
        return None


class FixtureClient(ReadOnlyGitHubClient):
    """Offline observations from fixture state.json. Never shells out to gh."""

    def __init__(self, repo: str, fixture_dir: Path) -> None:
        super().__init__(repo)
        self.fixture_dir = fixture_dir
        path = fixture_dir / "state.json"
        if not path.is_file():
            raise AuditError(f"fixture state missing: {path}")
        self.state = json.loads(path.read_text(encoding="utf-8"))

    def list_actions_variables(self) -> list[dict[str, Any]]:
        return deepcopy(self.state.get("actions_variables") or [])

    def list_actions_secret_names(self) -> list[str]:
        # Accept either names-only list or objects with name (never values).
        raw = self.state.get("actions_secret_names")
        if raw is None:
            raw = self.state.get("actions_secrets") or []
        names: list[str] = []
        for item in raw:
            if isinstance(item, str):
                names.append(item)
            elif isinstance(item, dict) and item.get("name"):
                # Ignore any accidental "value" key — never surface it.
                names.append(str(item["name"]))
        return names

    def get_installation(self) -> dict[str, Any] | None:
        inst = self.state.get("installation")
        if inst is None:
            return None
        if inst is False:
            return None
        return deepcopy(inst) if isinstance(inst, dict) else None

    def list_rulesets(self) -> list[dict[str, Any]]:
        return deepcopy(self.state.get("rulesets") or [])

    def get_ruleset(self, ruleset_id: int) -> dict[str, Any] | None:
        details = self.state.get("ruleset_details") or {}
        detail = details.get(str(ruleset_id))
        if detail:
            return deepcopy(detail)
        for rs in self.state.get("rulesets") or []:
            if rs.get("id") == ruleset_id:
                return deepcopy(rs)
        return None

    def get_repo(self) -> dict[str, Any]:
        return deepcopy(self.state.get("repo") or {})

    def get_bugbot_repo_settings(self) -> dict[str, Any] | None:
        bugbot = self.state.get("bugbot")
        if bugbot is None:
            return None
        return deepcopy(bugbot) if isinstance(bugbot, dict) else None


class UncheckedClient(ReadOnlyGitHubClient):
    """Dry-run default: no live reads; every observation stays unchecked."""

    def list_actions_variables(self) -> list[dict[str, Any]]:
        return []

    def list_actions_secret_names(self) -> list[str]:
        return []

    def get_installation(self) -> dict[str, Any] | None:
        return None

    def list_rulesets(self) -> list[dict[str, Any]]:
        return []

    def get_ruleset(self, ruleset_id: int) -> dict[str, Any] | None:
        return None

    def get_repo(self) -> dict[str, Any]:
        return {}

    def get_bugbot_repo_settings(self) -> dict[str, Any] | None:
        return None


def _find_variable(variables: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    for item in variables:
        if isinstance(item, dict) and item.get("name") == name:
            return item
    return None


def _extract_ruleset_checks(ruleset: dict[str, Any] | None) -> list[str]:
    if not ruleset:
        return []
    out: list[str] = []
    for rule in ruleset.get("rules") or []:
        if rule.get("type") != "required_status_checks":
            continue
        params = rule.get("parameters") or {}
        for item in params.get("required_status_checks") or []:
            if isinstance(item, dict) and item.get("context"):
                out.append(str(item["context"]))
    return out


def _is_numeric_app_id(value: Any) -> bool:
    if value is None:
        return False
    text = str(value).strip()
    return bool(re.fullmatch(r"[0-9]+", text))


def evaluate(client: ReadOnlyGitHubClient, *, source: str) -> list[dict[str, Any]]:
    """Evaluate required checks against a client. UncheckedClient → all unchecked."""
    unchecked = isinstance(client, UncheckedClient)
    results: list[dict[str, Any]] = []

    # --- github_app.app_id_variable ---
    if unchecked:
        results.append(
            _check(
                check_id="github_app.app_id_variable",
                category="github_app",
                required=True,
                expected=f"{APP_ID_VAR} repository/org variable present and numeric",
                observed="unchecked",
                status="unchecked",
                detail="dry-run default: pass --live or --fixture-dir to observe",
            )
        )
    else:
        variables = client.list_actions_variables()
        var = _find_variable(variables, APP_ID_VAR)
        if var is None:
            results.append(
                _check(
                    check_id="github_app.app_id_variable",
                    category="github_app",
                    required=True,
                    expected=f"{APP_ID_VAR} repository/org variable present and numeric",
                    observed="missing",
                    status="missing",
                    detail=f"{APP_ID_VAR} not listed in Actions variables",
                )
            )
        elif not _is_numeric_app_id(var.get("value")):
            results.append(
                _check(
                    check_id="github_app.app_id_variable",
                    category="github_app",
                    required=True,
                    expected=f"{APP_ID_VAR} repository/org variable present and numeric",
                    observed="non_numeric",
                    status="drift",
                    detail=f"{APP_ID_VAR} present but value is not a numeric App ID",
                )
            )
        else:
            results.append(
                _check(
                    check_id="github_app.app_id_variable",
                    category="github_app",
                    required=True,
                    expected=f"{APP_ID_VAR} repository/org variable present and numeric",
                    observed="present_numeric",
                    status="ok",
                    detail=f"{APP_ID_VAR} present (numeric; value not echoed)",
                )
            )

    # --- github_app.private_key_secret ---
    if unchecked:
        results.append(
            _check(
                check_id="github_app.private_key_secret",
                category="github_app",
                required=True,
                expected=(
                    f"{APP_PRIVATE_KEY_SECRET} Actions secret name present "
                    "(value never read)"
                ),
                observed="unchecked",
                status="unchecked",
                detail="dry-run default: pass --live or --fixture-dir to observe",
            )
        )
    else:
        secret_names = client.list_actions_secret_names()
        if APP_PRIVATE_KEY_SECRET in secret_names:
            results.append(
                _check(
                    check_id="github_app.private_key_secret",
                    category="github_app",
                    required=True,
                    expected=(
                        f"{APP_PRIVATE_KEY_SECRET} Actions secret name present "
                        "(value never read)"
                    ),
                    observed="name_present",
                    status="ok",
                    detail="secret name listed; value not retrieved",
                )
            )
        else:
            results.append(
                _check(
                    check_id="github_app.private_key_secret",
                    category="github_app",
                    required=True,
                    expected=(
                        f"{APP_PRIVATE_KEY_SECRET} Actions secret name present "
                        "(value never read)"
                    ),
                    observed="missing",
                    status="missing",
                    detail=f"{APP_PRIVATE_KEY_SECRET} not listed among Actions secret names",
                )
            )

    # --- github_app.installation ---
    if unchecked:
        results.append(
            _check(
                check_id="github_app.installation",
                category="github_app",
                required=True,
                expected="GitHub App installation present on the repository",
                observed="unchecked",
                status="unchecked",
                detail="dry-run default: pass --live or --fixture-dir to observe",
            )
        )
    else:
        inst = client.get_installation()
        if inst:
            app_slug = ""
            app = inst.get("app_slug") or (inst.get("app") or {}).get("slug")
            if app:
                app_slug = str(app)
            results.append(
                _check(
                    check_id="github_app.installation",
                    category="github_app",
                    required=True,
                    expected="GitHub App installation present on the repository",
                    observed="installed",
                    status="ok",
                    detail=(
                        f"installation id present"
                        + (f"; app_slug={app_slug}" if app_slug else "")
                    ),
                )
            )
        else:
            results.append(
                _check(
                    check_id="github_app.installation",
                    category="github_app",
                    required=True,
                    expected="GitHub App installation present on the repository",
                    observed="missing",
                    status="missing",
                    detail="no GitHub App installation found for repository",
                )
            )

    # --- bugbot.user_token_secret ---
    if unchecked:
        results.append(
            _check(
                check_id="bugbot.user_token_secret",
                category="bugbot",
                required=True,
                expected=(
                    f"{BUGBOT_USER_TOKEN_SECRET} Actions secret name present "
                    "(value never read)"
                ),
                observed="unchecked",
                status="unchecked",
                detail="dry-run default: pass --live or --fixture-dir to observe",
            )
        )
    else:
        secret_names = client.list_actions_secret_names()
        if BUGBOT_USER_TOKEN_SECRET in secret_names:
            results.append(
                _check(
                    check_id="bugbot.user_token_secret",
                    category="bugbot",
                    required=True,
                    expected=(
                        f"{BUGBOT_USER_TOKEN_SECRET} Actions secret name present "
                        "(value never read)"
                    ),
                    observed="name_present",
                    status="ok",
                    detail="secret name listed; value not retrieved",
                )
            )
        else:
            results.append(
                _check(
                    check_id="bugbot.user_token_secret",
                    category="bugbot",
                    required=True,
                    expected=(
                        f"{BUGBOT_USER_TOKEN_SECRET} Actions secret name present "
                        "(value never read)"
                    ),
                    observed="missing",
                    status="missing",
                    detail=f"{BUGBOT_USER_TOKEN_SECRET} not listed among Actions secret names",
                )
            )

    # --- bugbot.manual_trigger_only ---
    if unchecked:
        results.append(
            _check(
                check_id="bugbot.manual_trigger_only",
                category="bugbot",
                required=True,
                expected="Bugbot manualTriggerOnly=true (mention-only)",
                observed="unchecked",
                status="unchecked",
                detail=(
                    "dry-run default / live GitHub path cannot read Cursor Bugbot "
                    "dashboard; supply fixture bugbot.manualTriggerOnly or confirm "
                    "manually per docs/contracts/BUGBOT-MENTION-ONLY.md"
                ),
            )
        )
    else:
        bugbot = client.get_bugbot_repo_settings()
        if bugbot is None:
            results.append(
                _check(
                    check_id="bugbot.manual_trigger_only",
                    category="bugbot",
                    required=True,
                    expected="Bugbot manualTriggerOnly=true (mention-only)",
                    observed="unchecked",
                    status="unchecked",
                    detail=(
                        "Bugbot settings unavailable via GitHub API; fixture or "
                        "operator confirmation required"
                    ),
                )
            )
        else:
            mto = bugbot.get("manualTriggerOnly")
            if mto is True:
                results.append(
                    _check(
                        check_id="bugbot.manual_trigger_only",
                        category="bugbot",
                        required=True,
                        expected="Bugbot manualTriggerOnly=true (mention-only)",
                        observed="true",
                        status="ok",
                        detail="manualTriggerOnly=true",
                    )
                )
            else:
                results.append(
                    _check(
                        check_id="bugbot.manual_trigger_only",
                        category="bugbot",
                        required=True,
                        expected="Bugbot manualTriggerOnly=true (mention-only)",
                        observed=str(mto).lower() if mto is not None else "missing",
                        status="drift" if mto is False else "missing",
                        detail="manualTriggerOnly must be true before consumer rollout",
                    )
                )

    # --- bugbot.check_name ---
    # Contractual constant; optional override via repo variable observation.
    if unchecked:
        results.append(
            _check(
                check_id="bugbot.check_name",
                category="bugbot",
                required=True,
                expected=f"Integrator/ruleset Bugbot check name is {BUGBOT_CHECK_NAME!r}",
                observed="unchecked",
                status="unchecked",
                detail="dry-run default: pass --live or --fixture-dir to observe",
            )
        )
    else:
        variables = client.list_actions_variables()
        override = _find_variable(variables, "LINKTREND_BUGBOT_CHECK_NAME")
        if override is None:
            results.append(
                _check(
                    check_id="bugbot.check_name",
                    category="bugbot",
                    required=True,
                    expected=f"Integrator/ruleset Bugbot check name is {BUGBOT_CHECK_NAME!r}",
                    observed="default",
                    status="ok",
                    detail=(
                        f"LINKTREND_BUGBOT_CHECK_NAME unset; default {BUGBOT_CHECK_NAME!r} applies"
                    ),
                )
            )
        else:
            value = str(override.get("value") or "").strip()
            if value == BUGBOT_CHECK_NAME:
                results.append(
                    _check(
                        check_id="bugbot.check_name",
                        category="bugbot",
                        required=True,
                        expected=f"Integrator/ruleset Bugbot check name is {BUGBOT_CHECK_NAME!r}",
                        observed=value,
                        status="ok",
                        detail="LINKTREND_BUGBOT_CHECK_NAME matches contract",
                    )
                )
            else:
                results.append(
                    _check(
                        check_id="bugbot.check_name",
                        category="bugbot",
                        required=True,
                        expected=f"Integrator/ruleset Bugbot check name is {BUGBOT_CHECK_NAME!r}",
                        observed=value or "empty",
                        status="drift",
                        detail=(
                            "LINKTREND_BUGBOT_CHECK_NAME differs from "
                            f"{BUGBOT_CHECK_NAME!r}"
                        ),
                    )
                )

    # --- protection.development_ruleset ---
    if unchecked:
        results.append(
            _check(
                check_id="protection.development_ruleset",
                category="protection",
                required=True,
                expected=(
                    f"Active ruleset {DEVELOPMENT_RULESET!r} on development requires "
                    f"{BUGBOT_CHECK_NAME!r} and {SOURCE_POLICY_CHECK!r}"
                ),
                observed="unchecked",
                status="unchecked",
                detail="dry-run default: pass --live or --fixture-dir to observe",
            )
        )
    else:
        rulesets = client.list_rulesets()
        match = next(
            (r for r in rulesets if isinstance(r, dict) and r.get("name") == DEVELOPMENT_RULESET),
            None,
        )
        if not match:
            results.append(
                _check(
                    check_id="protection.development_ruleset",
                    category="protection",
                    required=True,
                    expected=(
                        f"Active ruleset {DEVELOPMENT_RULESET!r} on development requires "
                        f"{BUGBOT_CHECK_NAME!r} and {SOURCE_POLICY_CHECK!r}"
                    ),
                    observed="missing",
                    status="missing",
                    detail=f"ruleset {DEVELOPMENT_RULESET!r} not found",
                )
            )
        else:
            detail_rs = client.get_ruleset(int(match["id"])) if match.get("id") is not None else match
            enforcement = (detail_rs or match).get("enforcement") or match.get("enforcement")
            checks = _extract_ruleset_checks(detail_rs or match)
            missing_ctx = [
                c for c in (BUGBOT_CHECK_NAME, SOURCE_POLICY_CHECK) if c not in checks
            ]
            if enforcement and enforcement != "active":
                results.append(
                    _check(
                        check_id="protection.development_ruleset",
                        category="protection",
                        required=True,
                        expected=(
                            f"Active ruleset {DEVELOPMENT_RULESET!r} on development requires "
                            f"{BUGBOT_CHECK_NAME!r} and {SOURCE_POLICY_CHECK!r}"
                        ),
                        observed=f"enforcement={enforcement}",
                        status="drift",
                        detail=f"ruleset exists but enforcement is {enforcement!r}, not active",
                    )
                )
            elif missing_ctx:
                results.append(
                    _check(
                        check_id="protection.development_ruleset",
                        category="protection",
                        required=True,
                        expected=(
                            f"Active ruleset {DEVELOPMENT_RULESET!r} on development requires "
                            f"{BUGBOT_CHECK_NAME!r} and {SOURCE_POLICY_CHECK!r}"
                        ),
                        observed="incomplete_checks",
                        status="drift",
                        detail=f"missing required contexts: {', '.join(missing_ctx)}",
                    )
                )
            else:
                results.append(
                    _check(
                        check_id="protection.development_ruleset",
                        category="protection",
                        required=True,
                        expected=(
                            f"Active ruleset {DEVELOPMENT_RULESET!r} on development requires "
                            f"{BUGBOT_CHECK_NAME!r} and {SOURCE_POLICY_CHECK!r}"
                        ),
                        observed="active_with_required_checks",
                        status="ok",
                        detail="ruleset active with Bugbot + source-policy checks",
                    )
                )

    # --- protection.allow_auto_merge ---
    if unchecked:
        results.append(
            _check(
                check_id="protection.allow_auto_merge",
                category="protection",
                required=True,
                expected="Repository allow_auto_merge=true",
                observed="unchecked",
                status="unchecked",
                detail="dry-run default: pass --live or --fixture-dir to observe",
            )
        )
    else:
        repo = client.get_repo()
        aam = repo.get("allow_auto_merge")
        if aam is True:
            results.append(
                _check(
                    check_id="protection.allow_auto_merge",
                    category="protection",
                    required=True,
                    expected="Repository allow_auto_merge=true",
                    observed="true",
                    status="ok",
                    detail="allow_auto_merge=true",
                )
            )
        elif aam is False:
            results.append(
                _check(
                    check_id="protection.allow_auto_merge",
                    category="protection",
                    required=True,
                    expected="Repository allow_auto_merge=true",
                    observed="false",
                    status="drift",
                    detail="allow_auto_merge is false",
                )
            )
        else:
            results.append(
                _check(
                    check_id="protection.allow_auto_merge",
                    category="protection",
                    required=True,
                    expected="Repository allow_auto_merge=true",
                    observed="missing",
                    status="missing",
                    detail="allow_auto_merge field unavailable in observation",
                )
            )

    # --- completion.status_context ---
    # Constant contract reminder — always ok when reporting the checklist.
    results.append(
        _check(
            check_id="completion.status_context",
            category="completion",
            required=True,
            expected=(
                f"Privileged publish context remains {STATUS_CONTEXT!r} "
                "(App-backed publisher only)"
            ),
            observed=STATUS_CONTEXT,
            status="ok",
            detail=(
                "contract constant; privileged publish must use the GitHub App "
                "from protected workflow context only"
            ),
        )
    )

    # Attach source for debugging without changing ids.
    for row in results:
        row["source"] = source
    return results


def summarize(checks: list[dict[str, Any]]) -> dict[str, Any]:
    counts = {"ok": 0, "missing": 0, "drift": 0, "unchecked": 0, "error": 0}
    for row in checks:
        status = row.get("status") or "error"
        if status not in counts:
            counts["error"] += 1
        else:
            counts[status] += 1
    required = [c for c in checks if c.get("required")]
    ready = all(c.get("status") == "ok" for c in required)
    return {
        **counts,
        "requiredTotal": len(required),
        "ready": ready,
    }


def build_report(
    *,
    repo: str,
    mode: str,
    client: ReadOnlyGitHubClient,
    source: str,
) -> dict[str, Any]:
    checks = evaluate(client, source=source)
    summary = summarize(checks)
    leak_warnings = _secret_env_leak_warnings()
    return {
        "schemaVersion": SCHEMA_VERSION,
        "mode": mode,
        "dryRun": True,
        "repo": repo,
        "mutations": [],
        "source": source,
        "statusContext": STATUS_CONTEXT,
        "checklist": required_checklist(),
        "checks": checks,
        "summary": summary,
        "warnings": leak_warnings,
        "notes": [
            "Read-only audit: mutations are always empty.",
            "Secret checks use Actions secret *names* only; values are never retrieved or printed.",
            "Default dry-run emits the required checklist with unchecked observations.",
            "Use --fixture-dir for offline tests or --live for operator read-only GitHub GETs.",
            "Agents must not create Apps, secrets, variables, Bugbot settings, or rulesets.",
        ],
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Read-only dry-run report of required external GitHub App / Bugbot / "
            "protection state for App-backed Review Ready."
        )
    )
    parser.add_argument(
        "mode",
        nargs="?",
        default="report",
        choices=("report", "verify"),
        help="report (default dry-run) or verify (non-zero when not ready)",
    )
    parser.add_argument(
        "--repo",
        default=os.environ.get("GH_REPO", "linktrend/IDE-Development"),
        help="owner/name (default: GH_REPO or linktrend/IDE-Development)",
    )
    parser.add_argument(
        "--fixture-dir",
        default=None,
        help="Offline fixture directory containing state.json (no live GitHub calls)",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Perform read-only GitHub GET observations via gh api",
    )
    parser.add_argument(
        "--json-output",
        default=None,
        help="Optional path to write the full JSON result",
    )
    return parser.parse_args(argv)


def build_client(args: argparse.Namespace) -> tuple[ReadOnlyGitHubClient, str]:
    if args.fixture_dir and args.live:
        raise AuditError("pass only one of --fixture-dir or --live", EXIT_REFUSED)
    if args.fixture_dir:
        return FixtureClient(args.repo, Path(args.fixture_dir)), "fixture"
    if args.live:
        return ReadOnlyGitHubClient(args.repo), "live"
    return UncheckedClient(args.repo), "dry-run"


def _emit(payload: dict[str, Any], path: str | None) -> None:
    # Defense in depth: never dump known secret env values into stdout/file.
    text = json.dumps(payload, indent=2)
    for name in _SECRET_ENV_NAMES:
        val = (os.environ.get(name) or "").strip()
        if val and val in text:
            raise AuditError(
                f"refusing to emit report: secret env {name} would leak into output",
                EXIT_REFUSED,
            )
    print(text)
    if path:
        Path(path).write_text(text + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        client, source = build_client(args)
        report = build_report(
            repo=args.repo,
            mode=args.mode,
            client=client,
            source=source,
        )
        _emit(report, args.json_output)
        if args.mode == "report":
            return EXIT_OK
        # verify
        if report["summary"]["ready"]:
            return EXIT_OK
        return EXIT_NOT_READY
    except AuditError as exc:
        err = {
            "schemaVersion": SCHEMA_VERSION,
            "error": str(exc),
            "exitCode": exc.exit_code,
            "mutations": [],
            "dryRun": True,
        }
        print(json.dumps(err, indent=2), file=sys.stderr)
        return exc.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
