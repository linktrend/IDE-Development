"""Disposable Git consumer repositories."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Mapping


def init_git_repo(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(
        ["git", "config", "user.email", "cleanroom@example.test"],
        cwd=root,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Cleanroom Fixture"],
        cwd=root,
        check=True,
    )
    readme = root / "README.md"
    if not readme.exists():
        readme.write_text("# cleanroom consumer\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "cleanroom init"], cwd=root, check=True)
    return root


def write_file(path: Path, content: str | bytes, *, mode: str = "0644") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, str):
        path.write_text(content, encoding="utf-8")
    else:
        path.write_bytes(content)
    path.chmod(int(mode, 8))


def make_temp_workspace(prefix: str = "cleanroom-") -> Path:
    return Path(tempfile.mkdtemp(prefix=prefix))


def make_consumer_repo(
    *,
    files: Mapping[str, str | bytes] | None = None,
    symlinks: Mapping[str, str] | None = None,
    prefix: str = "cleanroom-consumer-",
) -> Path:
    """Return path to a fresh git repo under a disposable workspace parent."""
    workspace = make_temp_workspace(prefix=prefix)
    repo = workspace / "repo"
    init_git_repo(repo)
    for rel, content in (files or {}).items():
        write_file(repo / rel, content)
    for rel, target in (symlinks or {}).items():
        link = repo / rel
        link.parent.mkdir(parents=True, exist_ok=True)
        if link.exists() or link.is_symlink():
            if link.is_dir() and not link.is_symlink():
                shutil.rmtree(link)
            else:
                link.unlink()
        os.symlink(target, link)
    return repo


def cleanup_repo(repo: Path) -> None:
    """Remove the workspace parent created by make_consumer_repo."""
    shutil.rmtree(repo.parent, ignore_errors=True)


def find_git_root(start: Path) -> Path | None:
    cur = start.resolve()
    while True:
        if (cur / ".git").exists():
            return cur
        if cur.parent == cur:
            return None
        cur = cur.parent
