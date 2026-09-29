#!/usr/bin/env python3
"""Create or reuse issue/<LEDGER-ID>-<slug> from origin/<base>.

The Project orchestrator assigns Ledger IDs. This script never invents one
and never creates a GitHub Issue.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# Same override cursor002 uses so repo hooks cannot run during branch setup.
SAFE_GIT_CONFIG = ("-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false")

LEDGER_ID_RE = re.compile(r"^[A-Z][A-Z0-9]{1,9}-[1-9][0-9]*$")
# lowercase [a-z0-9-], 1..48, no leading/trailing/doubled hyphen
SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9]|-[a-z0-9]){0,47}$")
REF_RE = re.compile(r"^[A-Za-z0-9._/-]+$")


def die(msg: str, code: int = 1) -> None:
    print(msg, file=sys.stderr)
    raise SystemExit(code)


def git(
    args: list[str],
    *,
    cwd: Path,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    cmd = ["git", *SAFE_GIT_CONFIG, *args]
    try:
        return subprocess.run(
            cmd,
            cwd=str(cwd),
            check=check,
            text=True,
            capture_output=True,
        )
    except FileNotFoundError as exc:
        die(f"required binary missing: {exc.filename or cmd[0]}")
    except subprocess.CalledProcessError as exc:
        err = (exc.stderr or exc.stdout or "").strip()
        die(f"git failed ({' '.join(args)}): {err or exc}")
    raise AssertionError("unreachable")


def kebab_slug(text: str, max_len: int = 48) -> str:
    slug = text.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    if len(slug) > max_len:
        slug = slug[:max_len].rstrip("-")
    return slug


def valid_slug(slug: str) -> bool:
    return bool(slug) and len(slug) <= 48 and SLUG_RE.fullmatch(slug) is not None


def repo_root(start: Path) -> Path:
    proc = git(["rev-parse", "--show-toplevel"], cwd=start, check=False)
    if proc.returncode != 0:
        die(f"not a git work tree: {start}")
    return Path((proc.stdout or "").strip()).resolve()


def remote_branch_sha(root: Path, branch: str) -> str | None:
    proc = git(["ls-remote", "--heads", "origin", branch], cwd=root, check=False)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()
        die(f"git ls-remote failed for origin/{branch}: {err or proc.returncode}")
    for line in (proc.stdout or "").splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1] == f"refs/heads/{branch}":
            return parts[0]
    return None


def local_branch_sha(root: Path, branch: str) -> str | None:
    proc = git(["rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"], cwd=root, check=False)
    if proc.returncode != 0:
        return None
    sha = (proc.stdout or "").strip()
    return sha or None


def is_ancestor(root: Path, ancestor: str, descendant: str) -> bool:
    proc = git(["merge-base", "--is-ancestor", ancestor, descendant], cwd=root, check=False)
    return proc.returncode == 0


def resolve_existing_tip(root: Path, branch: str, local: str | None, remote: str | None) -> str:
    """Pick the existing tip. Fast-forward only. Never reset away unique commits."""
    if local and remote and local != remote:
        local_behind = is_ancestor(root, local, remote)
        remote_behind = is_ancestor(root, remote, local)
        if not local_behind and not remote_behind:
            die(
                f"{branch} has diverged from origin/{branch} "
                f"(local {local}, origin {remote}). "
                "Refusing to reset because that would lose work. "
                "Ask the Project orchestrator."
            )
        if local_behind:
            return remote
        return local
    if local:
        return local
    if remote:
        return remote
    die(f"internal error: {branch} has no local or origin tip")
    raise AssertionError("unreachable")


def worktree_for_branch(root: Path, branch: str) -> str | None:
    proc = git(["worktree", "list", "--porcelain"], cwd=root, check=False)
    if proc.returncode != 0:
        return None
    current: str | None = None
    for line in (proc.stdout or "").splitlines():
        if line.startswith("worktree "):
            current = line[len("worktree ") :].strip()
        elif line == f"branch refs/heads/{branch}" and current:
            return str(Path(current).resolve())
    return None


def ensure_local_branch(root: Path, branch: str, tip: str) -> None:
    local = local_branch_sha(root, branch)
    if local is None:
        git(["branch", branch, tip], cwd=root)
        return
    if local == tip:
        return
    if is_ancestor(root, local, tip):
        git(["branch", "-f", branch, tip], cwd=root)
        return
    die(
        f"{branch} at {local} is not a fast-forward of {tip}. "
        "Refusing to reset because that would lose work. "
        "Ask the Project orchestrator."
    )


def checkout_branch(root: Path, branch: str, tip: str, *, create: bool) -> Path:
    local = local_branch_sha(root, branch)
    if create or local is None:
        git(["checkout", "-b", branch, tip], cwd=root)
        return root
    current = git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=root).stdout.strip()
    if current != branch:
        git(["checkout", branch], cwd=root)
    if local != tip and is_ancestor(root, local, tip):
        git(["merge", "--ff-only", tip], cwd=root)
    return root


def use_worktree(root: Path, branch: str, tip: str, worktree: Path, *, create: bool) -> Path:
    path = worktree.resolve()
    if path == root:
        return checkout_branch(root, branch, tip, create=create)
    existing = worktree_for_branch(root, branch)
    if path.exists():
        if existing and Path(existing).resolve() == path:
            if not create:
                local = local_branch_sha(root, branch)
                if local and local != tip and is_ancestor(root, local, tip):
                    git(["merge", "--ff-only", tip], cwd=path)
            return path
        die(f"worktree path already exists and is not {branch}: {path}")
    if existing:
        die(f"{branch} is already checked out at {existing}; refusing to move it")
    path.parent.mkdir(parents=True, exist_ok=True)
    if create:
        git(["worktree", "add", "-b", branch, str(path), tip], cwd=root)
    else:
        ensure_local_branch(root, branch, tip)
        git(["worktree", "add", str(path), branch], cwd=root)
        local = local_branch_sha(root, branch)
        if local and local != tip and is_ancestor(root, local, tip):
            git(["merge", "--ff-only", tip], cwd=path)
    return path


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "description",
        nargs="*",
        help="free-text description; used to derive the slug when --slug is omitted",
    )
    parser.add_argument("--id", default=None, help="Ledger ID from the Project orchestrator, e.g. IDE-42")
    parser.add_argument("--slug", default=None, help="branch slug [a-z0-9-], max 48 characters")
    parser.add_argument("--base", default="development", help="base branch on origin (default: development)")
    parser.add_argument("--worktree", default=None, help="create or reuse the branch in this worktree path")
    parser.add_argument("--no-push", action="store_true", help="do not push or set upstream")
    parser.add_argument("--workdir", default=".", help="git working tree to operate on")
    args = parser.parse_args(argv)

    ledger_id = (args.id or "").strip()
    if not ledger_id:
        die(
            "missing --id. Get a Ledger ID from the Project orchestrator. "
            "Workers must not invent IDs."
        )
    if LEDGER_ID_RE.fullmatch(ledger_id) is None:
        die(
            f"invalid --id {ledger_id!r}. Get a Ledger ID from the Project orchestrator "
            "(expected <PREFIX>-<n>, e.g. IDE-42). Workers must not invent IDs."
        )

    base = (args.base or "").strip()
    if REF_RE.fullmatch(base) is None or base.startswith("/") or ".." in base.split("/"):
        die(f"invalid --base {base!r}")

    explicit_slug = (args.slug or "").strip()
    description = " ".join(args.description).strip()
    if explicit_slug:
        slug = explicit_slug
    elif description:
        slug = kebab_slug(description)
    else:
        slug = ""
    if not valid_slug(slug):
        die(
            f"invalid slug {slug!r}. Use lowercase [a-z0-9-], at most 48 characters, "
            "or pass a description to derive one."
        )

    branch = f"issue/{ledger_id}-{slug}"
    start = Path(args.workdir).resolve()
    root = repo_root(start)

    git(["fetch", "origin", base], cwd=root)
    base_sha = git(["rev-parse", f"origin/{base}"], cwd=root).stdout.strip()
    if not base_sha:
        die(f"origin/{base} has no commit")

    remote_sha = remote_branch_sha(root, branch)
    if remote_sha:
        git(
            ["fetch", "origin", f"+refs/heads/{branch}:refs/remotes/origin/{branch}"],
            cwd=root,
        )
        remote_sha = local_ref_sha(root, f"refs/remotes/origin/{branch}")

    local_sha = local_branch_sha(root, branch)
    creating = local_sha is None and remote_sha is None
    if creating:
        tip = base_sha
    else:
        tip = resolve_existing_tip(root, branch, local_sha, remote_sha)

    if args.worktree:
        checkout = use_worktree(root, branch, tip, Path(args.worktree), create=creating)
    else:
        checkout = checkout_branch(root, branch, tip, create=creating)

    pushed = False
    if not args.no_push:
        git(["push", "--set-upstream", "origin", f"{branch}:{branch}"], cwd=checkout)
        pushed = True

    payload = {
        "id": ledger_id,
        "branch": branch,
        "worktree": str(checkout.resolve()),
        "base": base,
        "baseSha": base_sha,
        "pushed": pushed,
    }
    print(json.dumps(payload, sort_keys=True))
    return 0


def local_ref_sha(root: Path, ref: str) -> str | None:
    proc = git(["rev-parse", "--verify", "--quiet", ref], cwd=root, check=False)
    if proc.returncode != 0:
        return None
    sha = (proc.stdout or "").strip()
    return sha or None


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
