#!/usr/bin/env python3
"""Package worker branches into a ``phase/<slug>`` branch for one PR into ``development``.

    package.py --name <phase-slug> --branches issue/IDE-1-a issue/IDE-2-b [--base development]
               [--fast] [--push] [--git-dir .] [--remote origin]

Fetches base and branches, creates ``phase/<slug>`` from ``<remote>/<base>`` (or
reuses it when every commit on it is reachable from the base or the listed
branches), then merges each branch with ``--no-ff`` in the given order. Merging
happens in a scratch worktree, so the caller's checkout is never touched.
Conflicts are never resolved: the merge is aborted and the script stops.

A single branch without ``--name`` needs no phase branch: the script reports
whether that branch is up to date with the base.

Exit codes: 0 ok; 1 ``--fast`` failed; 2 usage, git or refusal error; 3 merge conflict.
Output is JSON on stdout.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent))

import git_local  # noqa: E402
from git_local import GitError  # noqa: E402

EXIT_OK = 0
EXIT_FAST_FAILED = 1
EXIT_ERROR = 2
EXIT_CONFLICT = 3
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,79}$")
FAST_COMMAND = ("python3", "scripts/gitops/run_delivery_profile.py", "fast")
SECRET_ENV_RE = re.compile(r"(TOKEN|SECRET|PASSWORD|API_KEY|PRIVATE_KEY|CREDENTIAL)", re.IGNORECASE)
FAST_TAIL_LINES = 40


def fast_env() -> dict[str, str]:
    """The fast profile needs a normal environment, minus anything that looks like a secret."""
    return {k: v for k, v in os.environ.items() if not SECRET_ENV_RE.search(k)}


def run_fast(worktree: str) -> dict[str, Any]:
    proc = subprocess.run(
        list(FAST_COMMAND), cwd=worktree, capture_output=True, text=True, env=fast_env(), check=False
    )
    tail = (proc.stdout + proc.stderr).strip().splitlines()[-FAST_TAIL_LINES:]
    return {"ok": proc.returncode == 0, "exitCode": proc.returncode, "command": " ".join(FAST_COMMAND), "tail": tail}


def _refuse(code: str, message: str, **detail: Any) -> GitError:
    return GitError(code, message, **detail)


def _is_clean_merge(commit: str, git_dir: str) -> bool:
    """A two-parent merge whose tree is exactly what re-merging its parents yields.

    Such commits are earlier phase merges; a merge that carries extra edits is foreign work.
    """
    parents = git_local.out(["rev-list", "--parents", "-n", "1", commit], git_dir).split()[1:]
    if len(parents) != 2:
        return False
    proc = git_local.run(["merge-tree", "--write-tree", *parents], git_dir, check=False)
    return proc.returncode == 0 and proc.stdout.split()[:1] == [git_local.tree(commit, git_dir)]


def single_branch_report(
    *, branch: str, base: str, remote: str, git_dir: str, fast: bool
) -> tuple[int, dict[str, Any]]:
    git_local.fetch(remote, [base, branch], git_dir)
    base_sha = git_local.rev(f"{remote}/{base}", git_dir)
    branch_sha = git_local.rev(f"{remote}/{branch}", git_dir)
    if not base_sha or not branch_sha:
        raise _refuse("missing_ref", "base or branch not found on the remote", base=base, branch=branch)
    behind = int(git_local.out(["rev-list", "--count", f"{branch_sha}..{base_sha}"], git_dir))
    ahead = int(git_local.out(["rev-list", "--count", f"{base_sha}..{branch_sha}"], git_dir))
    report: dict[str, Any] = {
        "ok": True,
        "phaseBranch": None,
        "base": base,
        "baseSha": base_sha,
        "branch": branch,
        "upToDate": behind == 0,
        "behindBy": behind,
        "aheadBy": ahead,
        "merged": [],
        "headSha": branch_sha,
        "fast": None,
        "pushed": False,
    }
    if fast:
        with git_local.temp_worktree(git_dir, branch_sha) as wt:
            report["fast"] = run_fast(wt)
        if not report["fast"]["ok"]:
            report["ok"] = False
            return EXIT_FAST_FAILED, report
    return EXIT_OK, report


def package(
    *,
    name: str,
    branches: Sequence[str],
    base: str,
    remote: str,
    git_dir: str,
    fast: bool,
    push: bool,
) -> tuple[int, dict[str, Any]]:
    if not SLUG_RE.match(name):
        raise _refuse("bad_name", "--name must be a lowercase slug (a-z, 0-9, '.', '_', '-')", name=name)
    phase = f"phase/{name}"
    if len(set(branches)) != len(branches):
        raise _refuse("duplicate_branch", "each branch may be listed once", branches=list(branches))
    for branch in [base, *branches]:
        if not git_local.valid_branch_name(branch, git_dir) or branch.startswith("phase/"):
            raise _refuse("bad_branch", "not a valid source branch name", branch=branch)
    if phase in branches:
        raise _refuse("bad_branch", "the phase branch cannot be a source", branch=phase)
    if f"refs/heads/{phase}" in git_local.checked_out_branches(git_dir):
        raise _refuse("phase_checked_out", f"{phase} is checked out in a worktree; switch away first", phase=phase)

    remote_phase = git_local.remote_branch_exists(remote, phase, git_dir)
    git_local.fetch(remote, [base, *branches, *([phase] if remote_phase else [])], git_dir)
    base_sha = git_local.rev(f"{remote}/{base}", git_dir)
    if not base_sha:
        raise _refuse("missing_ref", f"{remote}/{base} not found", base=base)
    sources: list[tuple[str, str]] = []
    for branch in branches:
        sha = git_local.rev(f"{remote}/{branch}", git_dir)
        if not sha:
            raise _refuse("missing_ref", f"{remote}/{branch} not found", branch=branch)
        sources.append((branch, sha))

    start, reused = base_sha, False
    existing = git_local.rev(f"{remote}/{phase}", git_dir) if remote_phase else None
    local = git_local.rev(f"refs/heads/{phase}", git_dir)
    if existing and local and local != existing and not git_local.is_ancestor(local, existing, git_dir):
        raise _refuse("phase_diverged", f"local {phase} has commits not on {remote}/{phase}", local=local, remote=existing)
    existing = existing or local
    if existing:
        unreachable = git_local.out(["rev-list", existing, "--not", base_sha, *(sha for _, sha in sources)], git_dir)
        foreign = [c for c in unreachable.splitlines() if c and not _is_clean_merge(c, git_dir)]
        if foreign:
            raise _refuse(
                "phase_has_foreign_commits",
                f"{phase} has commits not reachable from {base} or the listed branches",
                phase=phase,
                commits=foreign[:20],
            )
        start, reused = existing, True

    report: dict[str, Any] = {
        "ok": True,
        "phaseBranch": phase,
        "reused": reused,
        "base": base,
        "baseSha": base_sha,
        "merged": [],
        "headSha": None,
        "fast": None,
        "pushed": False,
    }
    with git_local.temp_worktree(git_dir, start) as wt:
        if reused and not git_local.is_ancestor(base_sha, start, git_dir):
            result = git_local.merge(wt, base_sha, f"Merge {base} into {phase}", no_ff=True)
            if not result["ok"]:
                report.update(ok=False, conflict={"branch": base, "files": result["conflicts"]})
                return EXIT_CONFLICT, report
        for branch, sha in sources:
            already = git_local.is_ancestor(sha, "HEAD", wt)
            if not already:
                result = git_local.merge(wt, sha, f"Merge {branch} into {phase}", no_ff=True)
                if not result["ok"]:
                    report.update(ok=False, conflict={"branch": branch, "sha": sha, "files": result["conflicts"]})
                    return EXIT_CONFLICT, report
            report["merged"].append({"branch": branch, "sha": sha, "alreadyMerged": already})
        head = git_local.out(["rev-parse", "HEAD"], wt)
        report["headSha"] = head
        if fast:
            report["fast"] = run_fast(wt)

    git_local.run(["update-ref", f"refs/heads/{phase}", head], git_dir)
    if report["fast"] is not None and not report["fast"]["ok"]:
        report["ok"] = False
        return EXIT_FAST_FAILED, report
    if push:
        git_local.run(["push", "--quiet", remote, f"{head}:refs/heads/{phase}"], git_dir)
        report["pushed"] = True
    return EXIT_OK, report


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--name", help="phase slug; the branch is phase/<name> (optional for a single branch)")
    p.add_argument("--branches", nargs="+", required=True, help="worker branches, merged in this order")
    p.add_argument("--base", default="development")
    p.add_argument("--remote", default="origin")
    p.add_argument("--git-dir", default=".")
    p.add_argument("--fast", action="store_true", help="run the fast delivery profile on the result")
    p.add_argument("--push", action="store_true", help="push the phase branch (never forced)")
    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if len(args.branches) == 1 and not args.name:
            code, report = single_branch_report(
                branch=args.branches[0], base=args.base, remote=args.remote, git_dir=args.git_dir, fast=args.fast
            )
        elif not args.name:
            raise _refuse("missing_name", "--name is required when packaging more than one branch")
        else:
            code, report = package(
                name=args.name,
                branches=args.branches,
                base=args.base,
                remote=args.remote,
                git_dir=args.git_dir,
                fast=args.fast,
                push=args.push,
            )
    except GitError as exc:
        print(json.dumps(exc.as_dict(), indent=2))
        return EXIT_ERROR
    print(json.dumps(report, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
