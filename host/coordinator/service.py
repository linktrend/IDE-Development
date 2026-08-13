"""Scoped versioned installation helpers for the macOS launchd service.

The helpers do not call launchctl.  Installation is a filesystem transaction;
service activation remains an explicit operator action outside this packet.
"""

from __future__ import annotations

import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional


SERVICE_LABEL = "ai.linktrend.ide-coordinator"
VERSION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
PACKAGE_FILES = (
    "host/coordinator/__init__.py",
    "host/coordinator/__main__.py",
    "host/coordinator/cleanup.py",
    "host/coordinator/cli.py",
    "host/coordinator/daemon.py",
    "host/coordinator/executor.py",
    "host/coordinator/github_client.py",
    "host/coordinator/multihost.py",
    "host/coordinator/queue.py",
    "host/coordinator/resources.py",
    "host/coordinator/service.py",
    "host/coordinator/workers.py",
    "scripts/gitops/coordinator/config.py",
    "scripts/gitops/coordinator/receipts.py",
    "scripts/gitops/coordinator/state.py",
)


@dataclass(frozen=True)
class InstallPlan:
    version: str
    install_root: str
    version_path: str
    plist_path: str
    files: tuple[str, ...]
    dry_run: bool


def _safe_version(version: str) -> str:
    if not isinstance(version, str) or not VERSION_RE.fullmatch(version):
        raise ValueError("version is not a safe semantic/versioned directory name")
    return version


def _scoped_root(path: str | Path) -> Path:
    root = Path(path).expanduser()
    if root.is_symlink() or not root.is_absolute() or root in {Path("/"), Path.home()}:
        raise ValueError("installation root must be an explicit non-home absolute path")
    return root


def render_plist(*, install_root: str | Path, database: str | Path, python: str = "/usr/bin/python3", template: Optional[str | Path] = None) -> str:
    root = _scoped_root(install_root)
    db = Path(database).expanduser()
    if not db.is_absolute():
        raise ValueError("database path must be absolute")
    if template is None:
        template = Path(__file__).resolve().parents[1] / "macos" / "ai.linktrend.ide-coordinator.plist.template"
    text = Path(template).read_text(encoding="utf-8")
    substitutions = {
        "{{SERVICE_LABEL}}": SERVICE_LABEL,
        "{{PYTHON}}": python,
        "{{INSTALL_ROOT}}": str(root / "current"),
        "{{DATABASE}}": str(db),
    }
    for marker, value in substitutions.items():
        text = text.replace(marker, value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
    if "TOKEN" in text.upper() or "SECRET" in text.upper():
        raise ValueError("launchd plist template contains a secret-like field")
    return text


def _atomic_symlink(target: str, link: Path) -> None:
    link.parent.mkdir(parents=True, exist_ok=True)
    temporary = link.parent / ("." + link.name + ".tmp-" + next(tempfile._get_candidate_names()))
    try:
        os.symlink(target, temporary)
        os.replace(temporary, link)
    finally:
        if temporary.is_symlink() or temporary.exists():
            temporary.unlink(missing_ok=True)


def _remove_link(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()


def plan_install(source_root: str | Path, install_root: str | Path, version: str, plist_path: str | Path, *, dry_run: bool = False) -> InstallPlan:
    version = _safe_version(version)
    source = Path(source_root).expanduser().resolve()
    root = _scoped_root(install_root)
    files: list[str] = []
    for relative in PACKAGE_FILES:
        path = source / relative
        if not path.is_file() or path.is_symlink():
            raise ValueError("installation source file is missing or symlinked: " + relative)
        files.append(relative)
    return InstallPlan(version, str(root), str(root / version), str(Path(plist_path).expanduser()), tuple(files), dry_run)


def install_version(source_root: str | Path, install_root: str | Path, version: str, plist_path: str | Path, *, database: str | Path, dry_run: bool = False) -> InstallPlan:
    plan = plan_install(source_root, install_root, version, plist_path, dry_run=dry_run)
    if dry_run:
        return plan
    source = Path(source_root).expanduser().resolve()
    root = Path(plan.install_root)
    root.mkdir(parents=True, exist_ok=True)
    if (root / plan.version).exists() and not (root / plan.version).is_dir():
        raise ValueError("version path is not a directory")
    stage = Path(tempfile.mkdtemp(prefix=".coordinator-stage-", dir=str(root)))
    try:
        for relative in plan.files:
            destination = stage / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source / relative, destination)
        version_path = root / plan.version
        if version_path.exists():
            shutil.rmtree(version_path)
        os.replace(stage, version_path)
        current = root / "current"
        previous = root / "previous"
        if current.is_symlink():
            _remove_link(previous)
            os.replace(current, previous)
        _atomic_symlink(plan.version, current)
        plist = Path(plan.plist_path)
        plist.parent.mkdir(parents=True, exist_ok=True)
        content = render_plist(install_root=root, database=database)
        temporary = plist.parent / ("." + plist.name + ".tmp-" + next(tempfile._get_candidate_names()))
        temporary.write_text(content, encoding="utf-8")
        os.replace(temporary, plist)
    finally:
        if stage.exists():
            shutil.rmtree(stage)
    return plan


def rollback(install_root: str | Path, *, dry_run: bool = False) -> dict[str, Any]:
    root = _scoped_root(install_root)
    current = root / "current"
    previous = root / "previous"
    if not current.is_symlink() or not previous.is_symlink():
        raise ValueError("rollback requires current and previous versions")
    result = {"current": os.readlink(current), "previous": os.readlink(previous), "dryRun": dry_run}
    if dry_run:
        return result
    current_target = os.readlink(current)
    previous_target = os.readlink(previous)
    _remove_link(current)
    _remove_link(previous)
    _atomic_symlink(previous_target, current)
    _atomic_symlink(current_target, previous)
    return result


def uninstall(install_root: str | Path, plist_path: str | Path, *, dry_run: bool = False) -> dict[str, Any]:
    root = _scoped_root(install_root)
    plist = Path(plist_path).expanduser()
    if not plist.is_absolute():
        raise ValueError("plist path must be absolute")
    if not str(plist).endswith(SERVICE_LABEL + ".plist"):
        raise ValueError("plist path is outside the coordinator service scope")
    result = {"installRoot": str(root), "plist": str(plist), "dryRun": dry_run}
    if dry_run:
        return result
    if root.exists():
        shutil.rmtree(root)
    if plist.exists() or plist.is_symlink():
        plist.unlink()
    return result


__all__ = ["InstallPlan", "SERVICE_LABEL", "install_version", "plan_install", "render_plist", "rollback", "uninstall"]
