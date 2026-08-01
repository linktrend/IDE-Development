"""Build disposable fixture repositories for migration black-box scenarios."""

from __future__ import annotations

import json
import os
import shutil
import stat
import tempfile
from pathlib import Path
from typing import Any

from .paths import KNOWN_BYTES_DIR, REPO_ROOT


def _write_file(path: Path, content: str | bytes, *, mode: str = "0644") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, str):
        path.write_text(content, encoding="utf-8")
    else:
        path.write_bytes(content)
    path.chmod(int(mode, 8))


def _known_bytes(name: str) -> bytes:
    return (KNOWN_BYTES_DIR / name).read_bytes()


def init_git_repo(root: Path) -> None:
    # Minimal git metadata directory (not a full git init) is insufficient for
    # installer require_git_repo; use real git when available.
    import subprocess

    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "wp4@example.test"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "WP4 Fixture"], cwd=root, check=True)
    # Initial empty commit keeps some tools happier
    readme = root / "README.md"
    if not readme.exists():
        readme.write_text("# fixture\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "fixture init"], cwd=root, check=True)


def materialize_scenario(scenario: dict[str, Any], dest: Path) -> Path:
    """Create the disposable repo described by scenario['setup'] under dest."""
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    init_git_repo(dest)

    setup = scenario.get("setup") or {}
    files = setup.get("files") or {}
    for rel, spec in files.items():
        path = dest / rel
        if isinstance(spec, str):
            _write_file(path, spec)
            continue
        kind = spec.get("kind", "text")
        mode = spec.get("mode", "0644")
        if kind == "known_bytes":
            _write_file(path, _known_bytes(spec["name"]), mode=mode)
        elif kind == "text":
            _write_file(path, spec.get("content", ""), mode=mode)
        elif kind == "bytes_hex":
            _write_file(path, bytes.fromhex(spec["hex"]), mode=mode)
        else:
            raise ValueError(f"unknown file kind: {kind}")

    symlinks = setup.get("symlinks") or {}
    for rel, target in symlinks.items():
        link = dest / rel
        link.parent.mkdir(parents=True, exist_ok=True)
        if link.exists() or link.is_symlink():
            if link.is_dir() and not link.is_symlink():
                shutil.rmtree(link)
            else:
                link.unlink()
        os.symlink(target, link)

    # Optional transaction stub for interrupted recovery fixtures
    txn = setup.get("interrupted_transaction")
    if txn:
        txn_root = dest / ".git" / "ide-development" / "transactions" / txn["id"]
        txn_root.mkdir(parents=True, exist_ok=True)
        (txn_root / "status.json").write_text(
            json.dumps(txn.get("status") or {"state": "interrupted"}, indent=2) + "\n",
            encoding="utf-8",
        )
        backup_dir = txn_root / "backup"
        backup_dir.mkdir(parents=True, exist_ok=True)
        for rel, content in (txn.get("backup_files") or {}).items():
            encoded = rel.replace("%", "%25").replace("/", "%2F")
            (backup_dir / encoded).write_text(content, encoding="utf-8")
        (txn_root / "plan.json").write_text(
            json.dumps(txn.get("plan") or {"ops": []}, indent=2) + "\n",
            encoding="utf-8",
        )

    return dest


def make_temp_repo(scenario: dict[str, Any]) -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="wp4-mig-"))
    return materialize_scenario(scenario, tmp / "repo")
