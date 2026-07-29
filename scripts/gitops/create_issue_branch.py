#!/usr/bin/env python3
"""Create or reuse a GitHub issue and checkout issue/<n>-<slug> from origin/development.

Fail closed on auth/create/sync failure — never invent local issue IDs.
Prints machine-readable KEY=value lines: ISSUE_NUMBER, BRANCH, WORKTREE, SLUG.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path


def die(msg: str, code: int = 1) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(code)


def run(
    cmd: list[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
    capture: bool = True,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            check=check,
            text=True,
            capture_output=capture,
        )
    except FileNotFoundError as e:
        die(f"required binary missing: {e.filename or cmd[0]}")
    except subprocess.CalledProcessError as e:
        err = (e.stderr or e.stdout or "").strip()
        die(f"command failed ({' '.join(cmd)}): {err or e}")


def kebab_slug(title: str, max_len: int = 48) -> str:
    s = title.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    if not s:
        s = "work"
    if len(s) > max_len:
        s = s[:max_len].rstrip("-")
    return s or "work"


def resolve_repo(explicit: str | None, workdir: Path) -> str:
    if explicit:
        return explicit
    env = os.environ.get("GH_REPO") or os.environ.get("GITHUB_REPOSITORY")
    if env:
        return env
    try:
        out = run(
            ["gh", "repo", "view", "--json", "nameWithOwner", "--jq", ".nameWithOwner"],
            cwd=workdir,
        )
        slug = (out.stdout or "").strip()
        if slug:
            return slug
    except SystemExit:
        pass
    die("cannot resolve repository (pass --repo or set GH_REPO)")


def gh_auth_ok(repo: str) -> None:
    p = subprocess.run(
        ["gh", "auth", "status"],
        text=True,
        capture_output=True,
    )
    if p.returncode != 0:
        die("gh auth failed — refuse to invent local issue IDs", 1)
    # Touch API for the repo
    p2 = subprocess.run(
        ["gh", "api", f"repos/{repo}", "--jq", ".full_name"],
        text=True,
        capture_output=True,
    )
    if p2.returncode != 0:
        die(f"cannot access repo {repo}: {(p2.stderr or '').strip()}", 1)


def find_open_issue_by_title(repo: str, title: str) -> int | None:
    p = subprocess.run(
        [
            "gh",
            "issue",
            "list",
            "--repo",
            repo,
            "--state",
            "open",
            "--limit",
            "100",
            "--json",
            "number,title",
        ],
        text=True,
        capture_output=True,
    )
    if p.returncode != 0:
        die(f"gh issue list failed: {(p.stderr or '').strip()}")
    import json

    for row in json.loads(p.stdout or "[]"):
        if (row.get("title") or "") == title:
            return int(row["number"])
    return None


def validate_issue(repo: str, number: int) -> str:
    p = subprocess.run(
        [
            "gh",
            "issue",
            "view",
            str(number),
            "--repo",
            repo,
            "--json",
            "number,title,state",
        ],
        text=True,
        capture_output=True,
    )
    if p.returncode != 0:
        die(f"gh issue view #{number} failed: {(p.stderr or '').strip()}")
    import json

    data = json.loads(p.stdout)
    if int(data.get("number") or 0) != number:
        die(f"issue number mismatch for #{number}")
    return str(data.get("title") or f"issue-{number}")


def create_issue(repo: str, title: str) -> int:
    existing = find_open_issue_by_title(repo, title)
    if existing is not None:
        return existing
    p = subprocess.run(
        ["gh", "issue", "create", "--repo", repo, "--title", title, "--body", "Created by create_issue_branch.py"],
        text=True,
        capture_output=True,
    )
    if p.returncode != 0:
        die(f"gh issue create failed: {(p.stderr or '').strip()}")
    url = (p.stdout or "").strip()
    m = re.search(r"/issues/(\d+)", url)
    if not m:
        # Idempotent race: search again
        again = find_open_issue_by_title(repo, title)
        if again is not None:
            return again
        die(f"could not parse issue number from: {url}")
    return int(m.group(1))


def git_dirty(workdir: Path) -> bool:
    out = run(["git", "status", "--porcelain"], cwd=workdir)
    return bool((out.stdout or "").strip())


def on_development_tip(workdir: Path) -> bool:
    run(["git", "fetch", "origin", "development"], cwd=workdir)
    head = run(["git", "rev-parse", "HEAD"], cwd=workdir).stdout.strip()
    tip = run(["git", "rev-parse", "origin/development"], cwd=workdir).stdout.strip()
    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=workdir).stdout.strip()
    return branch == "development" and head == tip


def ensure_branch(
    workdir: Path,
    branch: str,
    *,
    prefer_worktree: bool,
) -> str:
    """Return worktree path (may equal workdir)."""
    run(["git", "fetch", "origin", "development"], cwd=workdir)
    # Already on branch?
    cur = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=workdir).stdout.strip()
    if cur == branch:
        return str(workdir)

    exists_local = (
        subprocess.run(
            ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"],
            cwd=str(workdir),
        ).returncode
        == 0
    )
    exists_remote = (
        subprocess.run(
            ["git", "show-ref", "--verify", "--quiet", f"refs/remotes/origin/{branch}"],
            cwd=str(workdir),
        ).returncode
        == 0
    )

    need_wt = prefer_worktree or git_dirty(workdir) or not on_development_tip(workdir)
    if need_wt:
        wt_root = workdir / ".git" / "linktrend-worktrees"
        # Prefer sibling under /tmp when .git is a file (worktree)
        git_dir = run(["git", "rev-parse", "--git-common-dir"], cwd=workdir).stdout.strip()
        common = Path(git_dir)
        if not common.is_absolute():
            common = (workdir / common).resolve()
        wt_root = common / "linktrend-worktrees"
        wt_root.mkdir(parents=True, exist_ok=True)
        wt_path = wt_root / branch.replace("/", "-")
        if wt_path.exists():
            # Already a worktree for this branch?
            return str(wt_path)
        if exists_local or exists_remote:
            ref = branch if exists_local else f"origin/{branch}"
            run(["git", "worktree", "add", str(wt_path), ref], cwd=workdir)
        else:
            run(
                ["git", "worktree", "add", "-b", branch, str(wt_path), "origin/development"],
                cwd=workdir,
            )
        return str(wt_path)

    # In-place checkout
    if exists_local:
        run(["git", "checkout", branch], cwd=workdir)
    elif exists_remote:
        run(["git", "checkout", "-b", branch, f"origin/{branch}"], cwd=workdir)
    else:
        run(["git", "checkout", "-b", branch, "origin/development"], cwd=workdir)
    return str(workdir)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("description", nargs="?", default=os.environ.get("TASK_DESCRIPTION", ""))
    ap.add_argument("--issue-number", type=int, default=None)
    ap.add_argument("--repo", default=os.environ.get("GH_REPO") or os.environ.get("GITHUB_REPOSITORY"))
    ap.add_argument("--workdir", default=os.environ.get("GITOPS_WORKDIR") or ".")
    ap.add_argument(
        "--prefer-worktree",
        action="store_true",
        default=os.environ.get("PREFER_WORKTREE", "").lower() in ("1", "true", "yes"),
    )
    args = ap.parse_args(argv)

    title = (args.description or "").strip()
    if not title and not args.issue_number:
        die("task description required (positional or TASK_DESCRIPTION)")

    workdir = Path(args.workdir).resolve()
    if not (workdir / ".git").exists() and not (workdir / ".git").is_file():
        # allow worktree
        try:
            run(["git", "rev-parse", "--show-toplevel"], cwd=workdir)
        except SystemExit:
            die(f"not a git workdir: {workdir}")

    repo = resolve_repo(args.repo, workdir)
    gh_auth_ok(repo)

    if args.issue_number:
        issue_title = validate_issue(repo, args.issue_number)
        number = args.issue_number
        if not title:
            title = issue_title
    else:
        number = create_issue(repo, title)

    slug = kebab_slug(title)
    branch = f"issue/{number}-{slug}"
    wt = ensure_branch(workdir, branch, prefer_worktree=args.prefer_worktree)

    print(f"ISSUE_NUMBER={number}")
    print(f"BRANCH={branch}")
    print(f"WORKTREE={wt}")
    print(f"SLUG={slug}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
