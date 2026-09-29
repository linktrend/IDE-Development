#!/usr/bin/env python3
"""Local git plumbing shared by the orchestrator delivery scripts.

git always runs with an allowlisted environment (never tokens or API keys) and
with repository hooks and fsmonitor disabled, as in ``scripts/dispatch/cursor002.py``.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from typing import Any, Iterator, Sequence

REMOTE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

GIT_ENV_ALLOW = (
    "PATH", "HOME", "USER", "LOGNAME", "SHELL", "LANG", "LANGUAGE", "TZ", "TMPDIR", "TERM",
    "SSH_AUTH_SOCK", "SSL_CERT_FILE", "SSL_CERT_DIR",
    "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "no_proxy", "all_proxy",
    "GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL",
    "GIT_CONFIG_GLOBAL", "GIT_CONFIG_NOSYSTEM",
)
SAFE_GIT_CONFIG = ("-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false")


class GitError(RuntimeError):
    def __init__(self, code: str, message: str, **detail: Any) -> None:
        super().__init__(message)
        self.code = code
        self.detail = detail

    def as_dict(self) -> dict[str, Any]:
        return {"ok": False, "error": self.code, "message": str(self), **self.detail}


def git_env() -> dict[str, str]:
    env = {name: os.environ[name] for name in GIT_ENV_ALLOW if name in os.environ}
    env.update({k: v for k, v in os.environ.items() if k.startswith("LC_")})
    # Deterministic, non-interactive: never prompt for credentials or open an editor.
    env.update({"GIT_TERMINAL_PROMPT": "0", "GIT_EDITOR": "true", "GIT_MERGE_AUTOEDIT": "no"})
    return env


def run(args: Sequence[str], git_dir: str, *, check: bool = True) -> subprocess.CompletedProcess[str]:
    cmd = ["git", *SAFE_GIT_CONFIG, "-C", git_dir, *args]
    proc = subprocess.run(cmd, capture_output=True, text=True, env=git_env(), check=False)
    if check and proc.returncode != 0:
        raise GitError("git_failed", f"git {' '.join(args[:2])} failed", stderr=proc.stderr[-500:])
    return proc


def out(args: Sequence[str], git_dir: str) -> str:
    return run(args, git_dir).stdout.strip()


def validate_remote_syntax(remote: str) -> None:
    """Reject option injection before any git process is started."""
    if not isinstance(remote, str) or not REMOTE_RE.match(remote):
        raise GitError("bad_remote", "remote name is not allowed", remote=remote)


def validate_ref_syntax(ref: str) -> None:
    """Reject option injection and refspec metacharacters before git runs."""
    if not isinstance(ref, str) or not ref or ref.startswith("-") or ref == "@" or "@{" in ref or ".." in ref:
        raise GitError("bad_ref", "ref is not a safe git argument", ref=ref)
    if ref.startswith("/") or ref.endswith("/") or ref.endswith(".") or "//" in ref:
        raise GitError("bad_ref", "ref is not a safe git argument", ref=ref)
    if any(ord(char) < 32 or char in " ~^:?*[\\" for char in ref):
        raise GitError("bad_ref", "ref is not a safe git argument", ref=ref)
    for part in ref.split("/"):
        if not part or part.startswith(".") or part.endswith(".lock") or part.endswith("."):
            raise GitError("bad_ref", "ref is not a safe git argument", ref=ref)


def require_remote(remote: str, git_dir: str) -> str:
    validate_remote_syntax(remote)
    names = out(["remote"], git_dir).splitlines()
    if remote not in names:
        raise GitError("unknown_remote", f"remote {remote!r} is not configured", remote=remote)
    return remote


def require_branch(name: str, git_dir: str) -> str:
    """Syntax-check, then ``git check-ref-format --branch``."""
    validate_ref_syntax(name)
    if run(["check-ref-format", "--branch", name], git_dir, check=False).returncode != 0:
        raise GitError("bad_ref", "git check-ref-format rejected the branch", ref=name)
    return name


def rev(ref: str, git_dir: str) -> str | None:
    validate_ref_syntax(ref)
    # ``rev-parse -- <rev>^{commit}`` is not accepted by git; the ref was syntax-checked.
    proc = run(["rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"], git_dir, check=False)
    return proc.stdout.strip() if proc.returncode == 0 else None


def tree(ref: str, git_dir: str) -> str:
    validate_ref_syntax(ref)
    return out(["rev-parse", "--verify", f"{ref}^{{tree}}"], git_dir)


def is_ancestor(ancestor: str, descendant: str, git_dir: str) -> bool:
    validate_ref_syntax(ancestor)
    validate_ref_syntax(descendant)
    return run(["merge-base", "--is-ancestor", "--", ancestor, descendant], git_dir, check=False).returncode == 0


def valid_branch_name(name: str, git_dir: str) -> bool:
    try:
        validate_ref_syntax(name)
    except GitError:
        return False
    return run(["check-ref-format", "--branch", name], git_dir, check=False).returncode == 0


def fetch(remote: str, branches: Sequence[str], git_dir: str) -> None:
    validate_remote_syntax(remote)
    for branch in branches:
        validate_ref_syntax(branch)
    require_remote(remote, git_dir)
    specs = [f"+refs/heads/{branch}:refs/remotes/{remote}/{branch}" for branch in branches]
    run(["fetch", "--quiet", "--no-tags", "--", remote, *specs], git_dir)


def remote_branch_exists(remote: str, branch: str, git_dir: str) -> bool:
    validate_remote_syntax(remote)
    validate_ref_syntax(branch)
    require_remote(remote, git_dir)
    return bool(out(["ls-remote", "--heads", "--", remote, f"refs/heads/{branch}"], git_dir))


def checked_out_branches(git_dir: str) -> set[str]:
    listing = out(["worktree", "list", "--porcelain"], git_dir)
    return {line.split(" ", 1)[1] for line in listing.splitlines() if line.startswith("branch ")}


def unmerged_files(worktree: str) -> list[str]:
    listing = out(["diff", "--name-only", "--diff-filter=U"], worktree)
    return sorted(line for line in listing.splitlines() if line)


def merge(worktree: str, ref: str, message: str, *, no_ff: bool) -> dict[str, Any]:
    """Merge ``ref`` into the worktree HEAD. On conflict, aborts and reports files."""
    validate_ref_syntax(ref)
    args = ["merge", "--no-edit", "-m", message]
    if no_ff:
        args.append("--no-ff")
    proc = run([*args, "--", ref], worktree, check=False)
    if proc.returncode == 0:
        return {"ok": True}
    files = unmerged_files(worktree)
    run(["merge", "--abort"], worktree, check=False)
    if not files:
        raise GitError("merge_failed", f"git merge {ref} failed", stderr=proc.stderr[-500:])
    return {"ok": False, "conflicts": files}


@contextmanager
def temp_worktree(git_dir: str, start: str) -> Iterator[str]:
    """Detached scratch worktree so the caller's checkout is never touched."""
    path = tempfile.mkdtemp(prefix="ide-orchestrator-")
    os.rmdir(path)
    validate_ref_syntax(start)
    run(["worktree", "add", "--quiet", "--detach", "--", path, start], git_dir)
    try:
        yield path
    finally:
        run(["worktree", "remove", "--force", path], git_dir, check=False)
        shutil.rmtree(path, ignore_errors=True)
        run(["worktree", "prune"], git_dir, check=False)
