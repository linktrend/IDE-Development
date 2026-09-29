#!/usr/bin/env python3
"""v3 ``main`` promotion check, published as the ``Linktrend Receipt Gate`` context.

The context name is legacy: the live ``main`` ruleset requires it. No receipt is
involved. A PR into ``main`` passes only when

  (a) its head branch matches ``promote/main/*`` in the base repository (not a fork);
  (b) some commit D among the last 200 first-parent commits of
      ``<remote>/development`` has exactly the head's tree; and
  (c) ``Verify IDE Development`` concluded success on D.

Inputs (flags override env): ``--head-sha`` / ``PR_HEAD_SHA``, ``--head-ref`` /
``PR_HEAD_REF`` (else ``GITHUB_HEAD_REF``), ``--base-ref`` / ``GITHUB_BASE_REF``,
``--repo`` / ``GITHUB_REPOSITORY``, ``--head-fork`` / ``PR_HEAD_FORK`` (``true`` fails).

Exit codes: 0 pass; 1 fail (reasons in the JSON on stdout, including tool errors).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

import git_local  # noqa: E402
import github_api  # noqa: E402
from git_local import GitError  # noqa: E402
from github_api import GitHubApiError  # noqa: E402

CONTEXT = "Linktrend Receipt Gate"
REQUIRED_CHECK = "Verify IDE Development"
PROMOTE_BRANCH_RE = re.compile(r"^promote/main/[A-Za-z0-9][A-Za-z0-9._-]*$")
SEARCH_DEPTH = 200


def tree_matches(dev_ref: str, head_tree: str, git_dir: str, depth: int) -> list[str]:
    """Development first-parent commits (newest first) whose tree equals ``head_tree``."""
    git_local.validate_ref_syntax(dev_ref)
    if isinstance(depth, bool) or not isinstance(depth, int) or depth < 1:
        raise GitError("bad_depth", "depth must be a positive integer", depth=depth)
    log = git_local.out(["log", "--first-parent", f"-n{depth}", "--format=%H %T", dev_ref], git_dir)
    return [line.split()[0] for line in log.splitlines() if line.split()[1:] == [head_tree]]


def check(
    *,
    head_sha: str,
    head_ref: str,
    base_ref: str | None,
    repo: str,
    head_fork: bool,
    git_dir: str,
    remote: str,
    depth: int,
    required_check: str,
    api: Any,
) -> dict[str, Any]:
    git_local.validate_remote_syntax(remote)
    git_local.validate_ref_syntax(head_sha)
    if head_ref:
        git_local.validate_ref_syntax(head_ref)
        git_local.require_branch(head_ref, git_dir)
    reasons: list[str] = []
    result: dict[str, Any] = {
        "context": CONTEXT,
        "headRef": head_ref,
        "headSha": head_sha,
        "headTree": None,
        "developmentSha": None,
        "searched": 0,
        "check": None,
    }
    if not PROMOTE_BRANCH_RE.match(head_ref or ""):
        reasons.append(f"head branch {head_ref!r} is not promote/main/*; only promote/main/* may merge into main")
    if base_ref and base_ref != "main":
        reasons.append(f"base {base_ref!r} is not main")
    if head_fork:
        reasons.append(f"head comes from a fork, not {repo}")

    github_api.validate_sha(head_sha)
    head_tree = git_local.tree(head_sha, git_dir)
    result["headTree"] = head_tree
    dev_ref = f"{remote}/development"
    if not git_local.rev(dev_ref, git_dir):
        raise GitError("missing_ref", f"{dev_ref} not found; fetch development with history")
    matches = tree_matches(dev_ref, head_tree, git_dir, depth)
    result["searched"] = int(git_local.out(["rev-list", "--first-parent", "--count", f"--max-count={depth}", dev_ref], git_dir))
    result["candidates"] = matches
    if not matches:
        reasons.append(
            f"no commit in the last {depth} first-parent commits of development has tree {head_tree}; "
            "main may only receive exact development content (run promote_main.py)"
        )
    else:
        # Prefer the newest green candidate; report the newest one when none is green.
        for sha in matches:
            state = github_api.check_succeeded(api, repo, sha, required_check)
            if state["ok"] or result["check"] is None:
                result["developmentSha"], result["check"] = sha, state
            if state["ok"]:
                break
        if not result["check"]["ok"]:
            reasons.append(
                f"{required_check} has not concluded success on development {result['developmentSha']} "
                f"(got {result['check']['conclusion']})"
            )
    result["reasons"] = reasons
    result["ok"] = not reasons
    return result


def _parser() -> argparse.ArgumentParser:
    env = os.environ
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--head-sha", default=env.get("PR_HEAD_SHA"))
    p.add_argument("--head-ref", default=env.get("PR_HEAD_REF") or env.get("GITHUB_HEAD_REF"))
    p.add_argument("--base-ref", default=env.get("GITHUB_BASE_REF") or None)
    p.add_argument("--repo", default=env.get("GITHUB_REPOSITORY"))
    p.add_argument("--head-fork", default=env.get("PR_HEAD_FORK", "false"), choices=("true", "false"))
    p.add_argument("--git-dir", default=".")
    p.add_argument("--remote", default="origin")
    p.add_argument("--depth", type=int, default=SEARCH_DEPTH)
    p.add_argument("--required-check", default=REQUIRED_CHECK)
    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if not (args.head_sha and args.head_ref and args.repo):
            raise GitHubApiError("missing_input", "head SHA, head ref and repo are required (flags or env)")
        github_api.validate_repo(args.repo)
        result = check(
            head_sha=args.head_sha,
            head_ref=args.head_ref,
            base_ref=args.base_ref,
            repo=args.repo,
            head_fork=args.head_fork == "true",
            git_dir=args.git_dir,
            remote=args.remote,
            depth=args.depth,
            required_check=args.required_check,
            api=github_api.from_env(),
        )
    except (GitError, GitHubApiError) as exc:
        print(json.dumps({"context": CONTEXT, **exc.as_dict(), "reasons": [str(exc)]}, indent=2))
        return 1
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
