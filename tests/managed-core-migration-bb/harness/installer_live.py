"""Live installer end-to-end probes for migration black-box scenarios.

Invokes ``scripts/ide-development.py`` against disposable fixture repos and a
hermetic package root. Does not modify the installer engine.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .fixture_builder import make_temp_repo
from .paths import FIXTURES_DIR, INSTALLER_ENTRY, LIVE_PACKAGE_DIR, REPO_ROOT


# Stable exit codes from docs/contracts/MANAGED-CORE-V2.md / installer constants.
EXIT_OK = 0
EXIT_CONFLICT = 11
EXIT_INVALID_PACKAGE = 12


@dataclass
class CliResult:
    returncode: int
    stdout: str
    stderr: str
    payload: dict[str, Any] | None

    @property
    def ok(self) -> bool:
        return self.returncode == EXIT_OK


def resolve_live_package() -> Path:
    """Hermetic package used for live probes (not the dirty system MANIFEST)."""
    if (LIVE_PACKAGE_DIR / "core" / "managed-core" / "MANIFEST.json").is_file():
        return LIVE_PACKAGE_DIR
    fallback = (
        REPO_ROOT
        / "scripts"
        / "ide_development_tests"
        / "fixtures"
        / "package_v2"
    )
    if (fallback / "core" / "managed-core" / "MANIFEST.json").is_file():
        return fallback
    raise FileNotFoundError(
        "No hermetic live package found under "
        f"{LIVE_PACKAGE_DIR} or {fallback}"
    )


def _parse_json_payload(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if not text:
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def run_installer(
    *args: str,
    package: Path,
    target: Path,
    timeout: float = 120.0,
) -> CliResult:
    """Invoke the real CLI entrypoint; never imports mutating engine APIs."""
    cmd = [
        sys.executable,
        str(INSTALLER_ENTRY),
        *args,
        "--package",
        str(package),
        "--target",
        str(target),
        "--json",
    ]
    proc = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )
    return CliResult(
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
        payload=_parse_json_payload(proc.stdout),
    )


def _sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _mode_octal(path: Path) -> str:
    return f"{stat.S_IMODE(path.stat().st_mode):04o}"


def managed_identity_map(repo: Path) -> dict[str, tuple[str, str]]:
    """Byte+mode fingerprint of non-git, non-state managed destinations."""
    out: dict[str, tuple[str, str]] = {}
    for path in sorted(repo.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        if ".git" in path.parts:
            continue
        rel = path.relative_to(repo).as_posix()
        if rel.endswith("installed-state.json"):
            continue
        out[rel] = (_sha256_file(path), _mode_octal(path))
    return out


def _rewrite_manifest_source_hash(package: Path, entry_id: str, source: Path) -> None:
    manifest_path = package / "core" / "managed-core" / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    digest = "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest()
    found = False
    for entry in manifest.get("files") or []:
        if entry.get("id") == entry_id:
            entry["sourceHash"] = digest
            found = True
            break
    if not found:
        raise KeyError(f"manifest entry id not found: {entry_id}")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def _ensure_scripts_importable() -> None:
    scripts = str(REPO_ROOT / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)


def _cleanup_temp_repo(repo: Path) -> None:
    """Remove make_temp_repo workspace (parent of ``repo``)."""
    shutil.rmtree(repo.parent, ignore_errors=True)


def _plant_interrupted_current_transaction(
    repo: Path,
    *,
    rel_path: str,
    original: bytes,
    mode: str = "0644",
) -> None:
    """Plant a live-engine interrupted current-transaction (journal + backups)."""
    _ensure_scripts_importable()
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
            "transactionId": "bb-live-interrupted",
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


def prove_external_cursor_symlink(scenario: dict[str, Any]) -> list[str]:
    """Fail-closed on external .cursor symlink; never write outside consumer."""
    errors: list[str] = []
    src = resolve_live_package()
    tmp = Path(tempfile.mkdtemp(prefix="wp4-live-01-"))
    try:
        package = tmp / "package"
        shutil.copytree(src, package)
        outside = tmp / "outside-cursor"
        outside.mkdir()
        secret = outside / "secret.txt"
        secret.write_text("OUTSIDE_MUST_STAY\n", encoding="utf-8")
        before = secret.read_bytes()
        outside_listing = {p.name for p in outside.iterdir()}

        repo = make_temp_repo(scenario)
        # Re-point .cursor at a real outside directory under our hermetic tmp.
        link = repo / ".cursor"
        if link.exists() or link.is_symlink():
            link.unlink()
        os.symlink(str(outside), link)

        result = run_installer("install", package=package, target=repo)
        # Fail-closed (conflict / escape / invalid) — never success while symlink remains.
        if result.returncode == EXIT_OK:
            if (repo / ".cursor").is_symlink():
                errors.append("install succeeded while .cursor remained an external symlink")
            # Replace path: success only if physical managed tree replaced the link.
            elif not (repo / ".cursor").is_dir():
                errors.append("install succeeded but .cursor is not a physical directory")
        elif result.returncode not in {EXIT_CONFLICT, EXIT_INVALID_PACKAGE, 1}:
            errors.append(
                f"unexpected install exit={result.returncode} "
                f"stdout={result.stdout[:300]} stderr={result.stderr[:200]}"
            )

        if secret.read_bytes() != before:
            errors.append("outside symlink target bytes were modified")
        if {p.name for p in outside.iterdir()} != outside_listing:
            errors.append("outside symlink target gained or lost children")
        # Never materialize managed paths under the outside tree.
        if (outside / "rules").exists() or (outside / "sample-rule.mdc").exists():
            errors.append("installer followed .cursor symlink and wrote outside consumer")
    finally:
        if "repo" in locals():
            _cleanup_temp_repo(repo)
        shutil.rmtree(tmp, ignore_errors=True)
    return errors


def prove_interrupted_transaction_recovery(scenario: dict[str, Any]) -> list[str]:
    """Interrupted current-transaction is restored by the next mutating CLI call."""
    del scenario  # scenario stub layout differs; live plants engine journal format
    errors: list[str] = []
    src = resolve_live_package()
    tmp = Path(tempfile.mkdtemp(prefix="wp4-live-07-"))
    try:
        package = tmp / "package"
        shutil.copytree(src, package)
        # Empty consumer (install first), then interrupt.
        empty = {
            "id": "07-live",
            "setup": {"files": {}},
        }
        repo = make_temp_repo(empty)
        installed = run_installer("install", package=package, target=repo)
        if not installed.ok:
            return [
                f"pre-install failed exit={installed.returncode} "
                f"{installed.stdout[:400]}{installed.stderr[:200]}"
            ]

        rel = ".ide-development/CORE.txt"
        core = repo / rel
        original = core.read_bytes()
        original_mode = _mode_octal(core)
        _plant_interrupted_current_transaction(repo, rel_path=rel, original=original)

        if core.read_text(encoding="utf-8") == original.decode("utf-8"):
            errors.append("interrupt plant did not change destination bytes")

        recovered = run_installer("update", package=package, target=repo)
        if not recovered.ok:
            errors.append(
                f"update/recovery exit={recovered.returncode} "
                f"{recovered.stdout[:400]}{recovered.stderr[:200]}"
            )
        if core.read_bytes() != original:
            errors.append("recovery did not restore pre-interrupt bytes")
        if _mode_octal(core) != original_mode:
            errors.append("recovery did not restore pre-interrupt mode")

        _ensure_scripts_importable()
        from ide_development.transaction import current_tx_dir

        if current_tx_dir(repo).exists():
            errors.append("current-transaction still present after recovery")
    finally:
        if "repo" in locals():
            _cleanup_temp_repo(repo)
        shutil.rmtree(tmp, ignore_errors=True)
    return errors


def prove_byte_exact_rollback(scenario: dict[str, Any]) -> list[str]:
    """Completed transaction rollback restores exact pre-change bytes and modes."""
    del scenario
    errors: list[str] = []
    src = resolve_live_package()
    tmp = Path(tempfile.mkdtemp(prefix="wp4-live-08-"))
    try:
        package = tmp / "package"
        shutil.copytree(src, package)
        empty = {"id": "08-live", "setup": {"files": {}}}
        repo = make_temp_repo(empty)
        installed = run_installer("install", package=package, target=repo)
        if not installed.ok:
            return [
                f"pre-install failed exit={installed.returncode} "
                f"{installed.stdout[:400]}{installed.stderr[:200]}"
            ]

        core = repo / ".ide-development" / "CORE.txt"
        original = core.read_bytes()
        original_mode = _mode_octal(core)

        mutated = tmp / "mutated-package"
        shutil.copytree(package, mutated)
        mutated_core = mutated / "core" / "managed-core" / "files" / "CORE.txt"
        mutated_core.write_text("BEFORE_BYTES_v1_MUTATED_FOR_ROLLBACK\n", encoding="utf-8")
        _rewrite_manifest_source_hash(mutated, "managed-core-readme", mutated_core)

        updated = run_installer("update", package=mutated, target=repo)
        if not updated.ok:
            return [
                f"mutating update failed exit={updated.returncode} "
                f"{updated.stdout[:400]}{updated.stderr[:200]}"
            ]
        if core.read_bytes() == original:
            errors.append("update did not change CORE.txt (nothing to rollback)")

        rolled = run_installer("rollback", package=package, target=repo)
        if not rolled.ok:
            errors.append(
                f"rollback exit={rolled.returncode} "
                f"{rolled.stdout[:400]}{rolled.stderr[:200]}"
            )
        if core.read_bytes() != original:
            errors.append("rollback bytes mismatch")
        if _mode_octal(core) != original_mode:
            errors.append(f"rollback mode mismatch got={_mode_octal(core)} want={original_mode}")
    finally:
        if "repo" in locals():
            _cleanup_temp_repo(repo)
        shutil.rmtree(tmp, ignore_errors=True)
    return errors


def prove_idempotent_repeat(scenario: dict[str, Any]) -> list[str]:
    """Repeat install/update leaves managed destinations byte-identical."""
    del scenario
    errors: list[str] = []
    src = resolve_live_package()
    tmp = Path(tempfile.mkdtemp(prefix="wp4-live-09-"))
    try:
        package = tmp / "package"
        shutil.copytree(src, package)
        empty = {"id": "09-live", "setup": {"files": {}}}
        repo = make_temp_repo(empty)

        first = run_installer("install", package=package, target=repo)
        if not first.ok:
            return [
                f"first install failed exit={first.returncode} "
                f"{first.stdout[:400]}{first.stderr[:200]}"
            ]
        snap1 = managed_identity_map(repo)

        second = run_installer("install", package=package, target=repo)
        if not second.ok:
            errors.append(
                f"second install failed exit={second.returncode} "
                f"{second.stdout[:400]}{second.stderr[:200]}"
            )
        snap2 = managed_identity_map(repo)
        if snap1 != snap2:
            errors.append("second install changed managed destination bytes/modes")

        updated = run_installer("update", package=package, target=repo)
        if not updated.ok:
            errors.append(
                f"noop update failed exit={updated.returncode} "
                f"{updated.stdout[:400]}{updated.stderr[:200]}"
            )
        snap3 = managed_identity_map(repo)
        if snap1 != snap3:
            errors.append("noop update changed managed destination bytes/modes")

        # Physical (non-symlink) managed destinations
        for rel in (
            ".ide-development/CORE.txt",
            ".cursor/rules/sample-rule.mdc",
        ):
            path = repo / rel
            if not path.is_file() or path.is_symlink():
                errors.append(f"managed destination not physical file: {rel}")
    finally:
        if "repo" in locals():
            _cleanup_temp_repo(repo)
        shutil.rmtree(tmp, ignore_errors=True)
    return errors


LIVE_PROOFS: dict[str, Any] = {
    "01-external-cursor-symlink": prove_external_cursor_symlink,
    "07-interrupted-transaction": prove_interrupted_transaction_recovery,
    "08-byte-exact-rollback": prove_byte_exact_rollback,
    "09-idempotent-repeat": prove_idempotent_repeat,
}


def run_live_proofs(
    *,
    scenarios: list[dict[str, Any]] | None = None,
) -> list[tuple[str, list[str]]]:
    """Return list of (proof_name, errors). Empty errors means pass."""
    results: list[tuple[str, list[str]]] = []
    if scenarios is None:
        for fixture_id, prover in LIVE_PROOFS.items():
            scenario_path = FIXTURES_DIR / fixture_id / "scenario.json"
            scenario = json.loads(scenario_path.read_text(encoding="utf-8"))
            results.append((f"live:{fixture_id}", prover(scenario)))
        return results

    for scenario in scenarios:
        sid = scenario["id"]
        prover = LIVE_PROOFS.get(sid)
        if prover is None:
            continue
        results.append((f"live:{sid}", prover(scenario)))
    return results
