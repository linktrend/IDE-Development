#!/usr/bin/env python3
"""Prepare a ``promote/main/<short-sha>`` branch that promotes ``development`` to ``main``.

    promote_main.py [--sha <development sha>] [--push] [--repo owner/name] [--git-dir .]

The SHA (default: ``<remote>/development`` head) must be on ``development`` and
``Verify IDE Development`` must have concluded success on it. The branch starts
at that SHA and gets a normal merge of ``<remote>/main`` (no strategy options), so
the PR into ``main`` is conflict-free. Its tree must equal the development SHA's
tree: if it does not, ``main`` carries changes that are missing from
``development`` and those must reach ``development`` first.

The orchestrator opens the PR from the printed ``prTitle`` / ``prBody`` and merges it
with a merge commit (never squash or rebase).

Exit codes: 0 ready; 1 development SHA is not green; 2 usage, git or API error;
3 ``main`` has changes missing from ``development``. Output is JSON on stdout.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

import git_local  # noqa: E402
import github_api  # noqa: E402
from git_local import GitError  # noqa: E402
from github_api import GitHubApiError  # noqa: E402

EXIT_OK = 0
EXIT_NOT_GREEN = 1
EXIT_ERROR = 2
EXIT_MAIN_AHEAD = 3
REQUIRED_CHECK = "Verify IDE Development"
DEVELOPMENT = "development"
MAIN = "main"
BRANCH_PREFIX = "promote/main/"
SHORT_LEN = 12
MAIN_AHEAD_HELP = (
    "main has changes that are missing from development; land them on development first "
    "(PR into development), then promote again"
)


def pr_text(*, short: str, sha: str, tree: str, main_sha: str, check: dict[str, Any]) -> tuple[str, str]:
    title = f"Promote development {short} to main"
    body = "\n".join(
        [
            f"Promotes `development` at `{sha}` to `main`.",
            "",
            f"- Development SHA: `{sha}`",
            f"- Tree: `{tree}` (identical to the development SHA)",
            f"- Merged `main` at: `{main_sha}`",
            f"- `{check['name']}` on the development SHA: {check['conclusion']}"
            + (f" ({check['url']})" if check.get("url") else ""),
            "",
            "Merge with a merge commit (not squash or rebase). `Linktrend Receipt Gate` re-checks the tree and CI.",
        ]
    )
    return title, body


def promote(
    *, sha: str | None, repo: str | None, remote: str, git_dir: str, push: bool, required_check: str, api: Any
) -> tuple[int, dict[str, Any]]:
    git_local.fetch(remote, [DEVELOPMENT, MAIN], git_dir)
    dev_head = git_local.rev(f"{remote}/{DEVELOPMENT}", git_dir)
    main_sha = git_local.rev(f"{remote}/{MAIN}", git_dir)
    if not dev_head or not main_sha:
        raise GitError("missing_ref", f"{remote}/{DEVELOPMENT} and {remote}/{MAIN} must exist")
    dev_sha = git_local.rev(sha, git_dir) if sha else dev_head
    if not dev_sha:
        raise GitError("missing_ref", f"commit {sha} not found", sha=sha)
    if not git_local.is_ancestor(dev_sha, dev_head, git_dir):
        raise GitError("not_on_development", f"{dev_sha} is not on {remote}/{DEVELOPMENT}", sha=dev_sha)
    if not repo:
        repo = github_api.repo_from_remote_url(git_local.out(["remote", "get-url", remote], git_dir))
        if not repo:
            raise GitError("unknown_repo", "cannot derive owner/name from the remote URL; pass --repo")

    short = dev_sha[:SHORT_LEN]
    branch = BRANCH_PREFIX + short
    dev_tree = git_local.tree(dev_sha, git_dir)
    report: dict[str, Any] = {
        "ok": False,
        "promoteBranch": branch,
        "developmentSha": dev_sha,
        "tree": dev_tree,
        "mainSha": main_sha,
        "headSha": None,
        "pushed": False,
        "mergeMethod": "merge",
    }

    check = github_api.check_succeeded(api, repo, dev_sha, required_check)
    report["check"] = check
    if not check["ok"]:
        report["reason"] = f"{required_check} has not concluded success on {dev_sha} (got {check['conclusion']})"
        return EXIT_NOT_GREEN, report

    if f"refs/heads/{branch}" in git_local.checked_out_branches(git_dir):
        raise GitError("promote_checked_out", f"{branch} is checked out in a worktree; switch away first")

    with git_local.temp_worktree(git_dir, dev_sha) as wt:
        if not git_local.is_ancestor(main_sha, dev_sha, git_dir):
            result = git_local.merge(wt, main_sha, f"Merge {MAIN} into {branch}", no_ff=False)
            if not result["ok"]:
                report.update(conflicts=result["conflicts"], reason=MAIN_AHEAD_HELP)
                return EXIT_MAIN_AHEAD, report
        head = git_local.out(["rev-parse", "HEAD"], wt)

    if git_local.tree(head, git_dir) != dev_tree:
        changed = git_local.out(["diff", "--name-only", dev_sha, head], git_dir).splitlines()
        report.update(headSha=head, changedFiles=changed, reason=MAIN_AHEAD_HELP)
        return EXIT_MAIN_AHEAD, report

    if git_local.remote_branch_exists(remote, branch, git_dir):
        git_local.fetch(remote, [branch], git_dir)
        existing = git_local.rev(f"{remote}/{branch}", git_dir) or ""
        reusable = (
            git_local.tree(existing, git_dir) == dev_tree
            and git_local.is_ancestor(dev_sha, existing, git_dir)
            and git_local.is_ancestor(main_sha, existing, git_dir)
        )
        if not reusable:
            raise GitError(
                "promote_branch_stale",
                f"{remote}/{branch} exists but does not promote {dev_sha} over current {MAIN}; delete it first",
                existing=existing,
            )
        head, report["reused"] = existing, True

    git_local.run(["update-ref", f"refs/heads/{branch}", head], git_dir)
    if push and not report.get("reused"):
        git_local.run(["push", "--quiet", remote, f"{head}:refs/heads/{branch}"], git_dir)
        report["pushed"] = True
    title, body = pr_text(short=short, sha=dev_sha, tree=dev_tree, main_sha=main_sha, check=check)
    report.update(ok=True, headSha=head, prTitle=title, prBody=body, prBase=MAIN)
    return EXIT_OK, report


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--sha", help=f"development commit to promote (default: <remote>/{DEVELOPMENT} head)")
    p.add_argument("--repo", help="owner/name for the CI lookup (default: from the remote URL)")
    p.add_argument("--remote", default="origin")
    p.add_argument("--git-dir", default=".")
    p.add_argument("--required-check", default=REQUIRED_CHECK)
    p.add_argument("--push", action="store_true", help="push the promote branch (never forced)")
    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.repo:
            github_api.validate_repo(args.repo)
        code, report = promote(
            sha=args.sha,
            repo=args.repo,
            remote=args.remote,
            git_dir=args.git_dir,
            push=args.push,
            required_check=args.required_check,
            api=github_api.from_env(),
        )
    except (GitError, GitHubApiError) as exc:
        print(json.dumps(exc.as_dict(), indent=2))
        return EXIT_ERROR
    print(json.dumps(report, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
