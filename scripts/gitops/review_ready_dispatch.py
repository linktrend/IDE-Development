#!/usr/bin/env python3
"""Validate workflow_dispatch inputs for App-backed Review Ready publisher.

Pure, unit-testable input validation only. Does not mint tokens, publish
statuses, read secrets, or execute untrusted branch code.

Trusted workflow: .github/workflows/linktrend-review-ready-publisher.yml
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

# Studio App-backed publisher accepts only issue/<number>-<slug> (digits).
ISSUE_BRANCH_RE = re.compile(r"^issue/([1-9][0-9]{0,8})-([a-z0-9]+(?:-[a-z0-9]+)*)$")
FULL_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")
REPO_SLUG_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")

PROTECTED_BRANCHES = frozenset({"development", "staging", "main", "HEAD"})
DEFAULT_EVIDENCE_PATH = ".linktrend/completion-evidence.json"
MAX_EVIDENCE_JSON_BYTES = 256_000


class DispatchValidationError(ValueError):
    """Fail-closed validation error with a stable machine-readable code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class ValidatedDispatch:
    branch: str
    sha: str
    issue_number: int
    issue_slug: str
    evidence_path: str
    dry_run: bool
    repository: str
    evidence_json: str  # empty when not supplied; raw JSON text when supplied


def _reject(code: str, message: str) -> None:
    raise DispatchValidationError(code, message)


def parse_dry_run(raw: Any) -> bool:
    """Parse Actions boolean / CLI dry-run values. Fail closed on ambiguity."""
    if isinstance(raw, bool):
        return raw
    if raw is None:
        return False
    text = str(raw).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off", ""}:
        return False
    _reject("dry_run_invalid", f"dry_run must be boolean-like, got {raw!r}")
    raise AssertionError("unreachable")


def validate_branch(branch: str) -> tuple[int, str]:
    if branch is None:
        _reject("branch_missing", "branch is required")
    name = str(branch).strip()
    if not name:
        _reject("branch_missing", "branch is required")
    if any(ch.isspace() for ch in name):
        _reject("branch_whitespace", "branch must not contain whitespace")
    if name.startswith("refs/") or name.startswith("origin/"):
        _reject("branch_mutable_ref", "branch must be a bare issue/<n>-<slug> name, not a ref")
    if ".." in name or name.startswith("/") or "\\" in name:
        _reject("branch_path_illegal", "branch must not look like a path")
    if name in PROTECTED_BRANCHES or name.split("/", 1)[0] in {"development", "staging", "main"}:
        _reject("branch_protected", f"protected or non-issue branch forbidden: {name}")
    m = ISSUE_BRANCH_RE.fullmatch(name)
    if not m:
        _reject(
            "branch_not_issue_slug",
            "branch must match issue/<number>-<slug> with lowercase slug segments",
        )
    issue_number = int(m.group(1))
    slug = m.group(2)
    if issue_number <= 0:
        _reject("branch_issue_number_invalid", "issue number must be positive")
    return issue_number, slug


def validate_sha(sha: str) -> str:
    if sha is None:
        _reject("sha_missing", "sha is required")
    tip = str(sha).strip()
    if not tip:
        _reject("sha_missing", "sha is required")
    if any(ch.isspace() for ch in tip):
        _reject("sha_whitespace", "sha must not contain whitespace")
    if tip.startswith("refs/") or tip in {"HEAD", "FETCH_HEAD"} or "/" in tip:
        _reject("sha_not_immutable", "sha must be an immutable 40-char commit id, not a ref")
    if len(tip) != 40 or not FULL_SHA_RE.fullmatch(tip):
        _reject("sha_not_full", "sha must be exactly 40 hexadecimal characters")
    return tip.lower()


def validate_evidence_path(path: str | None) -> str:
    raw = DEFAULT_EVIDENCE_PATH if path is None else str(path).strip()
    if not raw:
        raw = DEFAULT_EVIDENCE_PATH
    if any(ch.isspace() for ch in raw):
        _reject("evidence_path_whitespace", "evidence_path must not contain whitespace")
    if raw.startswith("/") or raw.startswith("~") or re.match(r"^[A-Za-z]:[\\/]", raw):
        _reject("evidence_path_absolute", "evidence_path must be a relative path in the tip tree")
    parts = Path(raw).parts
    if not parts or any(p in {"", ".", ".."} for p in parts):
        _reject("evidence_path_illegal", "evidence_path must not contain . or .. segments")
    if raw.endswith("/") or raw.endswith("\\"):
        _reject("evidence_path_illegal", "evidence_path must be a file path")
    return raw


def validate_repository(*, github_repository: str, requested_repository: str | None) -> str:
    expected = (github_repository or "").strip()
    if not expected or not REPO_SLUG_RE.fullmatch(expected):
        _reject(
            "repository_context_invalid",
            "GITHUB_REPOSITORY must be set to owner/repo for this dispatch",
        )
    if requested_repository is None:
        return expected
    requested = str(requested_repository).strip()
    if not requested:
        return expected
    if not REPO_SLUG_RE.fullmatch(requested):
        _reject("repository_format_invalid", "repository must look like owner/repo")
    if requested.lower() != expected.lower():
        _reject(
            "repository_mismatch",
            "dispatch cannot publish for another repository "
            f"(requested={requested}, context={expected})",
        )
    return expected


def validate_evidence_json(raw: str | None) -> str:
    """Optional inline evidence JSON. Empty string means 'use tip file'."""
    if raw is None:
        return ""
    text = str(raw).strip()
    if not text:
        return ""
    encoded = text.encode("utf-8")
    if len(encoded) > MAX_EVIDENCE_JSON_BYTES:
        _reject("evidence_json_too_large", "evidence_json exceeds size limit")
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as e:
        _reject("evidence_json_invalid", f"evidence_json is not valid JSON: {e}")
    if not isinstance(payload, dict):
        _reject("evidence_json_not_object", "evidence_json must be a JSON object")
    # Structural minimum only; full schema check happens in the trusted workflow
    # against the immutable SHA after tip verification.
    if "schemaVersion" not in payload or "headSha" not in payload:
        _reject(
            "evidence_json_missing_fields",
            "evidence_json must include schemaVersion and headSha",
        )
    return text


def validate_issue_number_binding(issue_number: int, explicit_issue: str | None) -> None:
    if explicit_issue is None:
        return
    text = str(explicit_issue).strip()
    if not text:
        return
    if not re.fullmatch(r"[1-9][0-9]{0,8}", text):
        _reject("issue_number_invalid", "issue_number must be a positive integer string")
    if int(text) != issue_number:
        _reject(
            "issue_branch_mismatch",
            f"issue_number {text} does not match branch issue/{issue_number}-…",
        )


def validate_dispatch_inputs(
    *,
    branch: str,
    sha: str,
    dry_run: Any = False,
    evidence_path: str | None = None,
    evidence_json: str | None = None,
    github_repository: str,
    repository: str | None = None,
    issue_number: str | None = None,
) -> ValidatedDispatch:
    """Validate and normalize all dispatch inputs. Raises DispatchValidationError."""
    issue_num, slug = validate_branch(branch)
    tip = validate_sha(sha)
    path = validate_evidence_path(evidence_path)
    dry = parse_dry_run(dry_run)
    repo = validate_repository(
        github_repository=github_repository,
        requested_repository=repository,
    )
    validate_issue_number_binding(issue_num, issue_number)
    ev_json = validate_evidence_json(evidence_json)
    return ValidatedDispatch(
        branch=f"issue/{issue_num}-{slug}",
        sha=tip,
        issue_number=issue_num,
        issue_slug=slug,
        evidence_path=path,
        dry_run=dry,
        repository=repo,
        evidence_json=ev_json,
    )


def _write_github_output(validated: ValidatedDispatch) -> None:
    out_path = os.environ.get("GITHUB_OUTPUT")
    if not out_path:
        return
    lines = [
        f"branch={validated.branch}",
        f"sha={validated.sha}",
        f"issue_number={validated.issue_number}",
        f"issue_slug={validated.issue_slug}",
        f"evidence_path={validated.evidence_path}",
        f"dry_run={'true' if validated.dry_run else 'false'}",
        f"repository={validated.repository}",
        f"has_evidence_json={'true' if validated.evidence_json else 'false'}",
    ]
    with open(out_path, "a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
        if validated.evidence_json:
            # Multiline safe output for Actions.
            fh.write("evidence_json<<LINKTREND_EVIDENCE_EOF\n")
            fh.write(validated.evidence_json)
            if not validated.evidence_json.endswith("\n"):
                fh.write("\n")
            fh.write("LINKTREND_EVIDENCE_EOF\n")


def _resolve_evidence_json_arg(args: argparse.Namespace) -> str | None:
    env_name = (args.evidence_json_env or "").strip()
    if env_name:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", env_name):
            raise DispatchValidationError(
                "evidence_json_env_invalid",
                "evidence_json_env must be a simple environment variable name",
            )
        return os.environ.get(env_name)
    if args.evidence_json:
        return args.evidence_json
    return None


def cmd_validate(args: argparse.Namespace) -> int:
    try:
        evidence_json = _resolve_evidence_json_arg(args)
        validated = validate_dispatch_inputs(
            branch=args.branch,
            sha=args.sha,
            dry_run=args.dry_run,
            evidence_path=args.evidence_path,
            evidence_json=evidence_json,
            github_repository=args.github_repository
            or os.environ.get("GITHUB_REPOSITORY", ""),
            repository=args.repository,
            issue_number=args.issue_number,
        )
    except DispatchValidationError as e:
        payload = {"ok": False, "error": e.code, "detail": e.message}
        print(json.dumps(payload, indent=2))
        return 78
    payload = {"ok": True, **asdict(validated)}
    # Avoid dumping potentially large evidence into step summaries by default.
    if not args.include_evidence_json and "evidence_json" in payload:
        payload["evidence_json"] = bool(validated.evidence_json)
    print(json.dumps(payload, indent=2))
    if args.github_output:
        _write_github_output(validated)
    return 0


def _self_test() -> int:
    """Lightweight unit checks for CI/local proof without network."""
    failures: list[str] = []

    def expect_ok(**kwargs: Any) -> ValidatedDispatch | None:
        try:
            return validate_dispatch_inputs(
                github_repository="linktrend/IDE-Development",
                **kwargs,
            )
        except DispatchValidationError as e:
            failures.append(f"unexpected fail {e.code}: {e.message} for {kwargs!r}")
            return None

    def expect_err(code: str, **kwargs: Any) -> None:
        try:
            validate_dispatch_inputs(
                github_repository="linktrend/IDE-Development",
                **kwargs,
            )
            failures.append(f"expected {code} for {kwargs!r}")
        except DispatchValidationError as e:
            if e.code != code:
                failures.append(f"expected {code}, got {e.code} for {kwargs!r}")

    good_sha = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    ok = expect_ok(
        branch="issue/44-add-app-backed-review-ready-publisher-and-produc",
        sha=good_sha,
        dry_run="false",
    )
    if ok:
        assert ok.issue_number == 44
        assert ok.sha == good_sha
        assert ok.dry_run is False
        assert ok.repository == "linktrend/IDE-Development"

    expect_ok(
        branch="issue/44-add-app-backed-review-ready-publisher-and-produc",
        sha=good_sha.upper(),
        dry_run=True,
        evidence_json=json.dumps(
            {"schemaVersion": 1, "headSha": good_sha, "classification": "tests"}
        ),
    )

    expect_err("branch_not_issue_slug", branch="feature/44-x", sha=good_sha)
    expect_err("branch_not_issue_slug", branch="issue/44-Bad_Slug", sha=good_sha)
    expect_err("branch_protected", branch="development", sha=good_sha)
    expect_err("branch_mutable_ref", branch="refs/heads/issue/44-x", sha=good_sha)
    expect_err("sha_not_full", branch="issue/44-x", sha="abc")
    expect_err("sha_not_immutable", branch="issue/44-x", sha="HEAD")
    expect_err(
        "repository_mismatch",
        branch="issue/44-x",
        sha=good_sha,
        repository="evil/other",
    )
    expect_err(
        "issue_branch_mismatch",
        branch="issue/44-x",
        sha=good_sha,
        issue_number="99",
    )
    expect_err(
        "evidence_path_absolute",
        branch="issue/44-x",
        sha=good_sha,
        evidence_path="/tmp/evil.json",
    )
    expect_err(
        "evidence_path_illegal",
        branch="issue/44-x",
        sha=good_sha,
        evidence_path="../secrets.json",
    )
    expect_err(
        "evidence_json_not_object",
        branch="issue/44-x",
        sha=good_sha,
        evidence_json="[]",
    )
    expect_err("dry_run_invalid", branch="issue/44-x", sha=good_sha, dry_run="maybe")

    if failures:
        print(json.dumps({"ok": False, "failures": failures}, indent=2))
        return 1
    print(json.dumps({"ok": True, "tests": "review_ready_dispatch.self_test"}, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("validate", help="Validate dispatch inputs (fail closed)")
    v.add_argument("--branch", required=True)
    v.add_argument("--sha", required=True)
    v.add_argument("--dry-run", default="false")
    v.add_argument("--evidence-path", default=DEFAULT_EVIDENCE_PATH)
    v.add_argument(
        "--evidence-json",
        default="",
        help="Optional inline completion evidence JSON when tip file is unavailable",
    )
    v.add_argument(
        "--evidence-json-env",
        default="",
        help="Read evidence JSON from this environment variable name (avoids shell quoting)",
    )
    v.add_argument(
        "--github-repository",
        default="",
        help="Owning repo context (defaults to GITHUB_REPOSITORY)",
    )
    v.add_argument(
        "--repository",
        default="",
        help="Optional explicit repo; must match GITHUB_REPOSITORY when set",
    )
    v.add_argument(
        "--issue-number",
        default="",
        help="Optional explicit issue number; must match branch",
    )
    v.add_argument(
        "--github-output",
        action="store_true",
        help="Append validated fields to GITHUB_OUTPUT",
    )
    v.add_argument(
        "--include-evidence-json",
        action="store_true",
        help="Include full evidence_json in stdout JSON (default: boolean only)",
    )

    sub.add_parser("self-test", help="Run built-in unit checks")
    return ap


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.cmd == "self-test":
        return _self_test()
    if args.cmd == "validate":
        # Normalize empty optional strings to None/""
        if not args.repository:
            args.repository = None
        if not args.issue_number:
            args.issue_number = None
        return cmd_validate(args)
    print(f"unknown command {args.cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
