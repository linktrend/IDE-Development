#!/usr/bin/env python3
"""Decide whether the orchestrator may merge a PR. Never merges.

    merge_check.py --repo owner/name --pr <n> --review-sha <sha>
                   --review-verdict APPROVE|REQUEST_CHANGES
                   [--required "Linktrend Fast Checks" ...] [--allow-skipped <check> ...]

Reads the PR and the check runs plus commit statuses of its exact head SHA from
the GitHub REST API (token from ``GH_TOKEN`` / ``GITHUB_TOKEN`` when set). OK only
when the independent review covered that exact head and approved it, every
required check's latest run succeeded (``skipped`` only where allowed), nothing on
the head failed, was cancelled or timed out, the PR is open without conflicts, and
its base is ``development`` or ``main``.

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
from github_api import FAILING_CONCLUSIONS, GitHubApiError  # noqa: E402

DEFAULT_REQUIRED = ("Linktrend Fast Checks", "Linktrend Branch Source Policy", "Verify IDE Development")
ALLOWED_BASES = ("development", "main")
VERDICTS = ("APPROVE", "REQUEST_CHANGES")


def evaluate(
    pr: Mapping[str, Any],
    checks: Mapping[str, Mapping[str, Any]],
    *,
    review_sha: str,
    review_verdict: str,
    required: Sequence[str],
    allow_skipped: Sequence[str] = (),
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
    if pr.get("mergeable") is False or pr.get("mergeable_state") == "dirty":
        reasons.append("PR has merge conflicts with its base")

    required_rows = []
    for name in required:
        check = checks.get(name)
        conclusion = check.get("conclusion") if check else None
        ok = conclusion == "success" or (conclusion == "skipped" and name in allow_skipped)
        if check is None:
            reasons.append(f"required check {name!r} has not run on {head_sha}")
        elif conclusion is None:
            reasons.append(f"required check {name!r} is still {check.get('status')}")
        elif not ok:
            reasons.append(f"required check {name!r} concluded {conclusion}")
        required_rows.append({"name": name, "status": check.get("status") if check else None,
                              "conclusion": conclusion, "ok": ok})

    failing = [
        {"name": name, "conclusion": c["conclusion"], "url": c.get("url")}
        for name, c in sorted(checks.items())
        if c.get("conclusion") in FAILING_CONCLUSIONS
    ]
    for row in failing:
        if row["name"] not in required:
            reasons.append(f"check {row['name']!r} concluded {row['conclusion']}")

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
        checks = github_api.head_checks(api, args.repo, head_sha)
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
    )
    result["repo"] = args.repo
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
