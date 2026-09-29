#!/usr/bin/env python3
"""Decide whether the orchestrator may merge a PR. Never merges.

    merge_check.py --repo owner/name --pr <n> --review-sha <sha>
                   --review-verdict APPROVE|REQUEST_CHANGES
                   [--required "Linktrend Fast Checks" ...] [--allow-skipped <check> ...]

Reads the PR and the check runs plus commit statuses of its exact head SHA from
the GitHub REST API (token from ``GH_TOKEN`` / ``GITHUB_TOKEN`` when set). OK only
when the independent review covered that exact head and approved it, every
required check's latest allowlisted check run succeeded (``skipped`` only where
allowed; default app ``github-actions``; commit statuses never count as success),
nothing accepted on the head failed, was cancelled or timed out, a failing commit
status is absent, the PR is open without conflicts, and its base is ``development``
or ``main``. Each evidence check run must resolve to its expected Actions
workflow file on this repository at that SHA. ``workflowFilesChanged`` lists
``.github/workflows/*`` paths the PR itself changes (a warning for review; a PR
can edit the workflow that produced the check).

Exit codes: 0 mergeable; 1 not mergeable (see ``reasons``); 2 usage or API error.
Output is JSON on stdout.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

import github_api  # noqa: E402
from github_api import DEFAULT_ALLOWED_APPS, EXPECTED_WORKFLOWS, FAILING_CONCLUSIONS, GitHubApiError  # noqa: E402

DEFAULT_REQUIRED = ("Linktrend Fast Checks", "Linktrend Branch Source Policy", "Verify IDE Development")
ALLOWED_BASES = ("development", "main")
VERDICTS = ("APPROVE", "REQUEST_CHANGES")


def _mergeability_reasons(
    pr: Mapping[str, Any],
    required_rows: Sequence[Mapping[str, Any]],
    checks: Mapping[str, Mapping[str, Any]],
    *,
    required: Sequence[str],
    allow_skipped: Sequence[str],
    allow_nonrequired_pending: Sequence[str],
) -> list[str]:
    """Fail closed unless GitHub has computed a clean merge.

    ``unstable`` is accepted only when every required check is green and every
    non-green check is a non-required pending check named in
    ``allow_nonrequired_pending``.
    """
    mergeable = pr.get("mergeable")
    state = pr.get("mergeable_state")
    if mergeable is None or state in (None, "unknown"):
        return ["mergeability not yet computed; retry"]
    if state == "dirty":
        return ["PR has merge conflicts with its base"]
    if state == "blocked":
        return ["PR mergeable_state is blocked"]
    if mergeable is not True:
        return [f"PR is not mergeable (mergeable={mergeable!r}, mergeable_state={state!r})"]
    if state == "clean":
        return []
    if state == "unstable" and _unstable_allowed(
        required_rows, checks, required=required, allow_skipped=allow_skipped,
        allow_nonrequired_pending=allow_nonrequired_pending,
    ):
        return []
    if state == "unstable":
        return [
            "mergeable_state is unstable; required checks must be green and only listed "
            "non-required pending checks may be non-green (--allow-nonrequired-pending)"
        ]
    return [f"mergeable_state {state!r} is not clean"]


def _unstable_allowed(
    required_rows: Sequence[Mapping[str, Any]],
    checks: Mapping[str, Mapping[str, Any]],
    *,
    required: Sequence[str],
    allow_skipped: Sequence[str],
    allow_nonrequired_pending: Sequence[str],
) -> bool:
    if not required_rows or not all(row.get("ok") for row in required_rows):
        return False
    allowed = set(allow_nonrequired_pending)
    required_names = set(required)
    nongreen: list[str] = []
    for name, check in checks.items():
        if not check.get("countsAsCheck"):
            continue
        conclusion = check.get("conclusion")
        if conclusion == "success":
            continue
        if conclusion == "skipped" and name in allow_skipped and name in required_names:
            continue
        nongreen.append(name)
    if not nongreen:
        return False
    return all(name not in required_names and name in allowed and checks[name].get("conclusion") is None for name in nongreen)


def _required_gap(name: str, check: Mapping[str, Any] | None, head_sha: str, allowed_apps: Sequence[str]) -> str:
    foreign = (check or {}).get("foreignApps") or []
    if foreign and not (check or {}).get("countsAsCheck"):
        return (
            f"required check {name!r} is not a check run from an allowed app {list(allowed_apps)} "
            f"(saw {list(foreign)})"
        )
    if check and check.get("workflowOk") is False:
        detail = check.get("workflowReason") or (
            f"is not from workflow {EXPECTED_WORKFLOWS.get(name, 'the expected workflow file')}"
        )
        return f"required check {name!r}: {detail}"
    return f"required check {name!r} has not run on {head_sha}"


def evaluate(
    pr: Mapping[str, Any],
    checks: Mapping[str, Mapping[str, Any]],
    *,
    review_sha: str,
    review_verdict: str,
    required: Sequence[str],
    allow_skipped: Sequence[str] = (),
    allowed_apps: Sequence[str] = DEFAULT_ALLOWED_APPS,
    allow_nonrequired_pending: Sequence[str] = (),
    workflow_files_changed: Sequence[str] = (),
) -> dict[str, Any]:
    head_sha = str((pr.get("head") or {}).get("sha") or "")
    base = str((pr.get("base") or {}).get("ref") or "")
    reasons: list[str] = []

    if pr.get("state") != "open" or pr.get("merged"):
        reasons.append(f"PR is not open (state={pr.get('state')}, merged={bool(pr.get('merged'))})")
    if head_sha != review_sha:
        reasons.append(f"head SHA {head_sha} does not equal reviewed SHA {review_sha}; review the new head")
    if review_verdict != "APPROVE":
        reasons.append(f"review verdict is {review_verdict}, not APPROVE")
    if base not in ALLOWED_BASES:
        reasons.append(f"base {base!r} is not one of {list(ALLOWED_BASES)}")

    required_rows = []
    for name in required:
        check = checks.get(name)
        counts = bool(check and check.get("countsAsCheck"))
        conclusion = check.get("conclusion") if counts else None
        ok = conclusion == "success" or (conclusion == "skipped" and name in allow_skipped and counts)
        if not counts:
            reasons.append(_required_gap(name, check, head_sha, allowed_apps))
        elif conclusion is None:
            reasons.append(f"required check {name!r} is still {check.get('status')}")
        elif not ok:
            reasons.append(f"required check {name!r} concluded {conclusion}")
        required_rows.append({"name": name, "status": check.get("status") if check else None,
                              "conclusion": conclusion, "app": check.get("app") if check else None, "ok": ok})

    failing = [
        {"name": name, "conclusion": c["conclusion"], "url": c.get("url")}
        for name, c in sorted(checks.items())
        if c.get("countsAsCheck") and c.get("conclusion") in FAILING_CONCLUSIONS
    ]
    for row in failing:
        if row["name"] not in required:
            reasons.append(f"check {row['name']!r} concluded {row['conclusion']}")
    for name, c in sorted(checks.items()):
        report = c.get("statusReport") or {}
        if report.get("conclusion") in FAILING_CONCLUSIONS:
            reasons.append(f"commit status {name!r} concluded {report['conclusion']}")

    reasons.extend(
        _mergeability_reasons(
            pr,
            required_rows,
            checks,
            required=required,
            allow_skipped=allow_skipped,
            allow_nonrequired_pending=allow_nonrequired_pending,
        )
    )

    return {
        "ok": not reasons,
        "pr": pr.get("number"),
        "headSha": head_sha,
        "reviewSha": review_sha,
        "reviewVerdict": review_verdict,
        "base": base,
        "headRef": (pr.get("head") or {}).get("ref"),
        "mergeable": pr.get("mergeable"),
        "mergeableState": pr.get("mergeable_state"),
        "required": required_rows,
        "failing": failing,
        "workflowFilesChanged": list(workflow_files_changed),
        "reasons": reasons,
    }


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--repo", required=True, help="owner/name")
    p.add_argument("--pr", required=True, type=int)
    p.add_argument("--review-sha", required=True, help="exact head SHA the independent review covered")
    p.add_argument("--review-verdict", required=True, choices=VERDICTS)
    p.add_argument("--required", action="append", help=f"required check (repeatable; default {list(DEFAULT_REQUIRED)})")
    p.add_argument("--allow-skipped", action="append", default=[], help="required check that may conclude skipped")
    p.add_argument(
        "--check-app",
        action="append",
        help="app.slug allowed to satisfy a required check (repeatable; default github-actions)",
    )
    p.add_argument(
        "--allow-nonrequired-pending",
        action="append",
        default=[],
        help="non-required pending check that may leave mergeable_state unstable",
    )
    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    required = args.required or list(DEFAULT_REQUIRED)
    try:
        github_api.validate_repo(args.repo)
        github_api.validate_sha(args.review_sha)
        api = github_api.from_env()
        pr = api.pull(args.repo, args.pr)
        head_sha = github_api.validate_sha(str((pr.get("head") or {}).get("sha") or ""))
        allowed_apps = tuple(args.check_app) if args.check_app else DEFAULT_ALLOWED_APPS
        checks = github_api.head_checks(api, args.repo, head_sha, allowed_apps=allowed_apps)
        changed = github_api.workflow_files_changed(api.pull_files(args.repo, args.pr))
    except GitHubApiError as exc:
        print(json.dumps(exc.as_dict(), indent=2))
        return 2
    result = evaluate(
        pr,
        checks,
        review_sha=args.review_sha,
        review_verdict=args.review_verdict,
        required=required,
        allow_skipped=args.allow_skipped,
        allowed_apps=allowed_apps,
        allow_nonrequired_pending=args.allow_nonrequired_pending,
        workflow_files_changed=changed,
    )
    result["repo"] = args.repo
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
