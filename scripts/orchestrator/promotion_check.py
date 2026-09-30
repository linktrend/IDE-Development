#!/usr/bin/env python3
"""v3 ``main`` promotion check, published as ``Linktrend Main Receipt Gate``.

A candidate passes only when its tree exactly matches a recent development
first-parent merge D, D's second parent H is the exact Phase PR head, H and D
have the same tree, and ``Verify IDE Development`` succeeded on H in a same-repo
``phase/*`` pull request targeting ``development``. The workflow run id is
returned so the caller can download and verify that run's identity-bound Full
inventory; no Full suite is rerun during promotion.

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
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import git_local  # noqa: E402
import github_api  # noqa: E402
from git_local import GitError  # noqa: E402
from github_api import GitHubApiError  # noqa: E402
from scripts.gitops.repository_ci_contract import requires_cross_platform_matrix  # noqa: E402

CONTEXT = "Linktrend Main Receipt Gate"
REQUIRED_CHECK = "Verify IDE Development"
PROMOTE_BRANCH_RE = re.compile(r"^promote/main/[A-Za-z0-9][A-Za-z0-9._-]*$")
SEARCH_DEPTH = git_local.DEVELOPMENT_FIRST_PARENT_WINDOW


def tree_matches(dev_ref: str, head_tree: str, git_dir: str, depth: int) -> list[str]:
    """Development first-parent commits (newest first) whose tree equals ``head_tree``."""
    return [
        commit
        for commit, tree in git_local.first_parent_commits(dev_ref, git_dir, depth)
        if tree == head_tree
    ]


def phase_evidence_for_development(
    development_sha: str, *, git_dir: str, repo: str, required_check: str, api: Any
) -> dict[str, Any]:
    """Resolve the exact Phase head and successful Verify run for a dev merge."""
    parents = git_local.out(["show", "-s", "--format=%P", development_sha], git_dir).split()
    if len(parents) < 2:
        return {"ok": False, "reason": "development candidate is not a merge commit"}
    phase_sha = parents[1]
    development_tree = git_local.tree(development_sha, git_dir)
    phase_tree = git_local.tree(phase_sha, git_dir)
    if phase_tree != development_tree:
        return {
            "ok": False,
            "phaseSha": phase_sha,
            "reason": "development merge tree differs from the reviewed Phase head tree",
        }
    observed = github_api.head_checks(
        api,
        repo,
        phase_sha,
        require_phase_pr_on_development=True,
    )
    check = github_api.summarize_check(phase_sha, required_check, observed.get(required_check))
    matching_pulls = [
        pull
        for pull in api.pulls_for_commit(repo, phase_sha)
        if isinstance(pull, dict)
        and (pull.get("base") or {}).get("ref") == "development"
        and ((pull.get("base") or {}).get("repo") or {}).get("full_name") == repo
        and (pull.get("head") or {}).get("sha") == phase_sha
        and str((pull.get("head") or {}).get("ref") or "").startswith("phase/")
        and ((pull.get("head") or {}).get("repo") or {}).get("full_name") == repo
        and pull.get("merged_at")
        and pull.get("merge_commit_sha") == development_sha
        and isinstance(pull.get("number"), int)
    ]
    pull_numbers = sorted({int(pull["number"]) for pull in matching_pulls})
    if len(pull_numbers) != 1:
        return {
            "ok": False,
            "phaseSha": phase_sha,
            "check": check,
            "reason": "development merge is not linked to exactly one merged same-repo Phase PR with this head and merge commit",
        }
    phase_pr = pull_numbers[0]
    phase_files = api.pull_files(repo, phase_pr)
    matrix_required = requires_cross_platform_matrix(
        [str(item.get("filename") or "") for item in phase_files if isinstance(item, dict)]
    )
    matrix_names = (
        "Installer matrix (ubuntu-latest)",
        "Installer matrix (macos-latest)",
        "Installer matrix (windows-latest)",
    )
    matrix_checks = (
        {
            name: github_api.summarize_check(phase_sha, name, observed.get(name))
            for name in matrix_names
        }
        if matrix_required
        else {}
    )
    return {
        "ok": check["ok"] and all(value["ok"] for value in matrix_checks.values()),
        "phaseSha": phase_sha,
        "phasePr": phase_pr,
        "matrixRequired": matrix_required,
        "workflowRunId": check.get("workflowRunId"),
        "check": check,
        "matrixChecks": matrix_checks,
    }


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
        "phaseEvidenceOk": False,
    }
    allowed_head = head_ref in {"development"} or head_ref.startswith("phase/") or bool(PROMOTE_BRANCH_RE.match(head_ref or ""))
    if not allowed_head:
        reasons.append(f"head branch {head_ref!r} is not development, phase/*, or the controlled promote/main/* bridge")
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
            evidence = phase_evidence_for_development(
                sha, git_dir=git_dir, repo=repo, required_check=required_check, api=api
            )
            if evidence["ok"] or result["check"] is None:
                result["developmentSha"] = sha
                result["phaseSha"] = evidence.get("phaseSha")
                result["workflowRunId"] = evidence.get("workflowRunId")
                result["check"] = evidence.get("check") or {"ok": False, "reason": evidence.get("reason")}
                result["matrixChecks"] = evidence.get("matrixChecks", {})
                result["matrixRequired"] = bool(evidence.get("matrixRequired"))
                result["phasePr"] = evidence.get("phasePr")
                result["phaseEvidenceReason"] = evidence.get("reason")
                result["phaseEvidenceOk"] = bool(evidence["ok"])
            if evidence["ok"]:
                break
        if not result["phaseEvidenceOk"]:
            got = result["check"].get("conclusion")
            detail = result["check"].get("workflowReason") or result["check"].get("reason")
            failed_matrix = [
                name for name, state in result.get("matrixChecks", {}).items() if not state.get("ok")
            ]
            shown = result.get("phaseEvidenceReason") or (f"{got}: {detail}" if detail else str(got))
            if result.get("matrixRequired") and failed_matrix:
                shown += "; missing/failed Phase matrix checks: " + ", ".join(failed_matrix)
            reasons.append(
                f"{required_check} has not concluded success on the Phase head for development {result['developmentSha']} "
                f"(got {shown})"
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
    p.add_argument("--depth", type=int, default=git_local.DEVELOPMENT_FIRST_PARENT_WINDOW)
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
    if result.get("ok") and os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as output:
            output.write(f"workflow_run_id={result['workflowRunId']}\n")
            output.write(f"phase_sha={result['phaseSha']}\n")
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
