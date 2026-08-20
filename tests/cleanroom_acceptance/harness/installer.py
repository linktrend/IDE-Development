"""CLI installer invocation helpers (subprocess only; no mutating engine imports)."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .paths import (
    INSTALLER_ENTRY,
    INSTALLER_PACKAGE_DIR,
    LANE_D_RC_CANDIDATES,
    PACKAGE_FIXTURE,
    REPO_ROOT,
)

EXIT_OK = 0
EXIT_DRIFT = 10
EXIT_CONFLICT = 11


@dataclass
class CliResult:
    returncode: int
    stdout: str
    stderr: str
    payload: dict[str, Any] | None

    @property
    def ok(self) -> bool:
        return self.returncode == EXIT_OK


def _parse_json_payload(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if not text:
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def mode_octal(path: Path) -> str:
    return f"{stat.S_IMODE(path.stat().st_mode):04o}"


def rewrite_manifest_source_hash(package: Path, entry_id: str, source: Path) -> None:
    manifest_path = package / "core" / "managed-core" / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    digest = sha256_file(source)
    found = False
    for entry in manifest.get("files") or []:
        if entry.get("id") == entry_id:
            entry["sourceHash"] = digest
            found = True
            break
    if not found:
        raise KeyError(f"manifest entry id not found: {entry_id}")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def resolve_package_source() -> tuple[Path, str]:
    """Return (package_root, provenance_note).

    Prefers a Lane D extracted RC when present; otherwise the self-contained
    clean-room fixture under ``fixtures/extracted-rc-package/``.
    """
    for candidate in LANE_D_RC_CANDIDATES:
        manifest = candidate / "core" / "managed-core" / "MANIFEST.json"
        if manifest.is_file():
            return candidate, f"lane-d-extract:{candidate.relative_to(REPO_ROOT)}"
    if (PACKAGE_FIXTURE / "core" / "managed-core" / "MANIFEST.json").is_file():
        return PACKAGE_FIXTURE, "fixture:tests/cleanroom_acceptance/fixtures/extracted-rc-package"
    raise FileNotFoundError(
        "No clean-room package found (Lane D extract or fixtures/extracted-rc-package)"
    )


def materialize_package_copy(dest: Path, *, source: Path | None = None) -> Path:
    src = source or resolve_package_source()[0]
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)
    runtime_manifest = REPO_ROOT / "core" / "github" / "managed-runtime" / "MANIFEST.json"
    runtime_sources = json.loads(runtime_manifest.read_text(encoding="utf-8")).get("files") or []
    for rel in runtime_sources:
        runtime_source = REPO_ROOT / rel
        if not runtime_source.is_file() or runtime_source.is_symlink():
            raise FileNotFoundError(f"missing physical runtime package source: {rel}")
        runtime_destination = dest / rel
        runtime_destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(runtime_source, runtime_destination)
    return dest


def materialize_isolated_rc_extract(dest: Path, *, source: Path | None = None) -> Path:
    """Copy package + installer scripts into ``dest`` (simulates extracted RC).

    After this returns, installers should be invoked from ``dest`` so the live
    IDE Development checkout is not required on PYTHONPATH or as --package.
    """
    materialize_package_copy(dest, source=source)
    scripts = dest / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    if not INSTALLER_ENTRY.is_file():
        raise FileNotFoundError(f"missing installer entrypoint: {INSTALLER_ENTRY}")
    if not INSTALLER_PACKAGE_DIR.is_dir():
        raise FileNotFoundError(f"missing installer package: {INSTALLER_PACKAGE_DIR}")
    shutil.copy2(INSTALLER_ENTRY, scripts / "ide-development.py")
    shutil.copytree(
        INSTALLER_PACKAGE_DIR,
        scripts / "ide_development",
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", ".DS_Store"),
    )
    return dest


def run_installer(
    *args: str,
    package: Path,
    target: Path,
    entrypoint: Path | None = None,
    cwd: Path | None = None,
    timeout: float = 120.0,
    env: dict[str, str] | None = None,
) -> CliResult:
    entry = entrypoint or INSTALLER_ENTRY
    cmd = [
        sys.executable,
        str(entry),
        *args,
        "--package",
        str(package),
        "--target",
        str(target),
        "--json",
    ]
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    # Prefer isolated execution: drop PYTHONPATH so checkout scripts/ is not required.
    run_env.pop("PYTHONPATH", None)
    proc = subprocess.run(
        cmd,
        cwd=str(cwd or package),
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
        env=run_env,
    )
    return CliResult(
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        payload=_parse_json_payload(proc.stdout),
    )


def managed_identity_map(repo: Path) -> dict[str, tuple[str, str]]:
    """Byte+mode fingerprint of non-git physical files (skip installed-state)."""
    out: dict[str, tuple[str, str]] = {}
    for path in sorted(repo.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        if ".git" in path.parts:
            continue
        rel = path.relative_to(repo).as_posix()
        if rel.endswith("installed-state.json"):
            continue
        out[rel] = (sha256_file(path), mode_octal(path))
    return out


def plant_interrupted_current_transaction(
    repo: Path,
    *,
    rel_path: str,
    original: bytes,
    mode: str = "0644",
) -> None:
    """Plant a live-engine interrupted current-transaction (journal + backups)."""
    scripts = str(REPO_ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    from ide_development.io_atomic import atomic_write_bytes
    from ide_development.paths import encode_backup_name
    from ide_development.transaction import backups_dir, current_tx_dir, write_journal

    dest = repo / rel_path
    dest.write_bytes(b"partial-write-interrupted\n")
    tx = current_tx_dir(repo)
    if tx.exists():
        shutil.rmtree(tx)
    tx.mkdir(parents=True)
    backups_dir(tx).mkdir(parents=True)
    backup_name = encode_backup_name(rel_path)
    atomic_write_bytes(backups_dir(tx) / backup_name, original, mode=mode)
    write_journal(
        tx,
        {
            "schemaVersion": 1,
            "transactionId": "cleanroom-interrupted",
            "command": "update",
            "packageVersion": "2.0.0",
            "phase": "apply",
            "backups": [
                {
                    "path": rel_path,
                    "existed": True,
                    "mode": mode,
                    "contentHash": "sha256:" + hashlib.sha256(original).hexdigest(),
                    "backupName": backup_name,
                }
            ],
            "applied": [rel_path],
        },
    )
