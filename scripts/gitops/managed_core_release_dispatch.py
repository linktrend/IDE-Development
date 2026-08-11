#!/usr/bin/env python3
"""Validate workflow_dispatch inputs for normal-token managed-core release publisher.

Pure, unit-testable input validation only. Does not mint tokens, create tags,
upload releases, read secrets, or execute untrusted source trees.

Trusted workflow: .github/workflows/linktrend-managed-core-release-publisher.yml
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from typing import Any

FULL_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")
REPO_SLUG_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+([.-][0-9A-Za-z.-]+)?$")
TAG_RE = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+([.-][0-9A-Za-z.-]+)?$")

DEFAULT_VERSION = "2.1.0"
DEFAULT_TAG = "v2.1.0"
ACTIONS = frozenset({"publish", "verify-only"})


class DispatchValidationError(ValueError):
    """Fail-closed validation error with a stable machine-readable code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True)
class ValidatedReleaseDispatch:
    source_sha: str
    version: str
    tag: str
    action: str
    dry_run: bool
    repository: str
    default_branch: str


def _reject(code: str, message: str) -> None:
    raise DispatchValidationError(code, message)


def parse_dry_run(raw: Any) -> bool:
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


def validate_source_sha(sha: str) -> str:
    if sha is None or not str(sha).strip():
        _reject("source_sha_missing", "source_sha is required")
    text = str(sha).strip().lower()
    if not FULL_SHA_RE.fullmatch(text):
        _reject("source_sha_invalid", "source_sha must be a 40-char lowercase hex SHA")
    return text


def validate_version(version: str | None) -> str:
    text = (version or DEFAULT_VERSION).strip()
    if not VERSION_RE.fullmatch(text):
        _reject("version_invalid", f"version must be semver-like, got {version!r}")
    if text != DEFAULT_VERSION:
        _reject(
            "version_not_authorized",
            f"only package version {DEFAULT_VERSION} is authorized for this publisher",
        )
    return text


def validate_tag(tag: str | None, *, version: str) -> str:
    text = (tag or f"v{version}").strip()
    if not TAG_RE.fullmatch(text):
        _reject("tag_invalid", f"tag must look like vX.Y.Z, got {tag!r}")
    expected = f"v{version}"
    if text != expected:
        _reject(
            "tag_version_mismatch",
            f"tag {text!r} must equal {expected!r} for version {version}",
        )
    return text


def validate_action(action: str | None) -> str:
    text = (action or "publish").strip().lower() or "publish"
    if text not in ACTIONS:
        _reject("action_invalid", f"action must be one of {sorted(ACTIONS)}, got {action!r}")
    return text


def validate_repository(repo: str | None) -> str:
    text = (repo or "").strip()
    if not text:
        _reject("repository_missing", "github repository slug is required")
    if not REPO_SLUG_RE.fullmatch(text):
        _reject("repository_invalid", f"repository must be owner/name, got {repo!r}")
    return text


def validate_default_branch(branch: str | None) -> str:
    text = (branch or "main").strip()
    if not text or "/" in text or text in {".", ".."}:
        _reject("default_branch_invalid", f"default_branch invalid: {branch!r}")
    if text != "main":
        _reject(
            "default_branch_not_main",
            "managed-core release publisher requires default_branch=main",
        )
    return text


def validate_dispatch_inputs(
    *,
    source_sha: str,
    version: str | None = None,
    tag: str | None = None,
    action: str | None = None,
    dry_run: Any = False,
    github_repository: str | None = None,
    default_branch: str | None = None,
) -> ValidatedReleaseDispatch:
    sha = validate_source_sha(source_sha)
    ver = validate_version(version)
    tg = validate_tag(tag, version=ver)
    act = validate_action(action)
    dry = parse_dry_run(dry_run)
    repo = validate_repository(github_repository)
    branch = validate_default_branch(default_branch)
    return ValidatedReleaseDispatch(
        source_sha=sha,
        version=ver,
        tag=tg,
        action=act,
        dry_run=dry,
        repository=repo,
        default_branch=branch,
    )


def _write_github_output(validated: ValidatedReleaseDispatch) -> None:
    path = os.environ.get("GITHUB_OUTPUT")
    if not path:
        raise DispatchValidationError(
            "github_output_missing",
            "GITHUB_OUTPUT is required when --github-output is set",
        )
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(f"source_sha={validated.source_sha}\n")
        fh.write(f"version={validated.version}\n")
        fh.write(f"tag={validated.tag}\n")
        fh.write(f"action={validated.action}\n")
        fh.write(f"dry_run={'true' if validated.dry_run else 'false'}\n")
        fh.write(f"repository={validated.repository}\n")
        fh.write(f"default_branch={validated.default_branch}\n")


def cmd_validate(args: argparse.Namespace) -> int:
    try:
        validated = validate_dispatch_inputs(
            source_sha=args.source_sha,
            version=args.version,
            tag=args.tag,
            action=args.action,
            dry_run=args.dry_run,
            github_repository=args.github_repository
            or os.environ.get("GITHUB_REPOSITORY", ""),
            default_branch=args.default_branch
            or os.environ.get("DEFAULT_BRANCH", "main"),
        )
    except DispatchValidationError as e:
        payload = {"ok": False, "error": e.code, "detail": e.message}
        print(json.dumps(payload, indent=2))
        return 78
    payload = {"ok": True, **asdict(validated)}
    print(json.dumps(payload, indent=2))
    if args.github_output:
        _write_github_output(validated)
    return 0


def _self_test() -> int:
    failures: list[str] = []

    def expect_ok(**kwargs: Any) -> ValidatedReleaseDispatch | None:
        try:
            return validate_dispatch_inputs(
                github_repository="linktrend/IDE-Development",
                default_branch="main",
                **kwargs,
            )
        except DispatchValidationError as e:
            failures.append(f"unexpected fail {e.code}: {e.message} for {kwargs!r}")
            return None

    def expect_err(code: str, **kwargs: Any) -> None:
        try:
            validate_dispatch_inputs(
                github_repository="linktrend/IDE-Development",
                default_branch="main",
                **kwargs,
            )
            failures.append(f"expected {code} for {kwargs!r}")
        except DispatchValidationError as e:
            if e.code != code:
                failures.append(f"expected {code}, got {e.code} for {kwargs!r}")

    good_sha = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    ok = expect_ok(source_sha=good_sha, version="2.1.0", tag="v2.1.0", dry_run=False)
    if ok:
        assert ok.tag == "v2.1.0"
        assert ok.dry_run is False

    expect_ok(source_sha=good_sha.upper(), action="verify-only", dry_run="true")
    expect_err("source_sha_invalid", source_sha="abc")
    expect_err("version_not_authorized", source_sha=good_sha, version="2.0.0")
    expect_err("tag_version_mismatch", source_sha=good_sha, version="2.1.0", tag="v9.9.9")
    expect_err("action_invalid", source_sha=good_sha, action="delete")
    expect_err("dry_run_invalid", source_sha=good_sha, dry_run="maybe")

    try:
        validate_dispatch_inputs(
            source_sha=good_sha,
            github_repository="linktrend/IDE-Development",
            default_branch="development",
        )
        failures.append("expected default_branch_not_main")
    except DispatchValidationError as e:
        if e.code != "default_branch_not_main":
            failures.append(f"expected default_branch_not_main, got {e.code}")

    if failures:
        print(json.dumps({"ok": False, "failures": failures}, indent=2))
        return 1
    print(json.dumps({"ok": True, "self_test": "pass"}, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    validate = sub.add_parser("validate", help="Validate dispatch inputs")
    validate.add_argument("--source-sha", required=True)
    validate.add_argument("--version", default=DEFAULT_VERSION)
    validate.add_argument("--tag", default="")
    validate.add_argument("--action", default="publish")
    validate.add_argument("--dry-run", default="false")
    validate.add_argument("--github-repository", default="")
    validate.add_argument("--default-branch", default="main")
    validate.add_argument("--github-output", action="store_true")
    validate.set_defaults(func=cmd_validate)

    st = sub.add_parser("self-test", help="Run embedded unit checks")
    st.set_defaults(func=lambda _args: _self_test())
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
