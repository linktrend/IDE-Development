"""Installer engine behavior tests."""

from __future__ import annotations

import json
import os
import shutil
import stat
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path

from ide_development.constants import (
    EXIT_CONFLICT,
    EXIT_DRIFT,
    EXIT_INVALID_PACKAGE,
    EXIT_OK,
)
from ide_development.engine import (
    _run_post_install_secret_scan,
    run_drift,
    run_install_or_update,
    run_plan,
    run_rollback,
    run_verify,
    run_version,
)
from ide_development.hashing import sha256_file
from ide_development.managed_write_guard import managed_write_lease
from ide_development.transaction import (
    current_tx_dir,
    last_tx_dir,
    write_journal,
    backups_dir,
    encode_backup_name,
)
from ide_development.io_atomic import atomic_write_bytes
from ide_development_tests import TempRepoTestCase, FIXTURE_PACKAGE


class EngineTests(TempRepoTestCase):
    def test_post_install_scoped_scan_uses_bound_evidence_and_removes_temp_file(self) -> None:
        scanner = self.target / "scripts/gitops/secret_scan.py"
        scanner.parent.mkdir(parents=True)
        scanner.write_text("# cleanroom scanner fixture\n", encoding="utf-8")
        evidence = {
            "schemaVersion": 1,
            "kind": "change-scoped-secret-scan-evidence",
            "repository": "example/consumer",
            "authoritativeRemoteRef": "origin/development",
            "baselineCommit": "a" * 40,
            "baselineTree": "b" * 40,
            "candidateCommit": "c" * 40,
            "candidateGitTree": "d" * 40,
            "scannerPolicyVersion": "secret-scan-policy/1",
            "managedPaths": ["scripts/gitops/secret_scan.py"],
            "configDigest": "sha256:" + "e" * 64,
            "findings": [
                {"kind": "approved_synthetic_fixture", "path": f"old/{i}.py", "rule": "assignment.secret"}
                for i in range(10_000)
            ],
        }
        resolution = SimpleNamespace(
            verification={
                "changeScopedSecretScan": {
                    "evidence": evidence,
                    "evidenceDigest": "sha256:" + "f" * 64,
                }
            }
        )
        seen: dict[str, object] = {}

        def fake_run(args, **kwargs):
            seen["args"] = args
            evidence_path = Path(args[args.index("--baseline-evidence") + 1])
            seen["evidence"] = json.loads(evidence_path.read_text(encoding="utf-8"))
            seen["exists_during_scan"] = evidence_path.exists()
            return SimpleNamespace(returncode=0)

        with patch("ide_development.engine.subprocess.run", side_effect=fake_run):
            result = _run_post_install_secret_scan(target_root=self.target, resolution=resolution)
        self.assertTrue(result["ok"])
        self.assertEqual(result["mode"], "change-scoped")
        self.assertEqual(len(seen["evidence"]["findings"]), 10_000)
        self.assertTrue(seen["exists_during_scan"])
        evidence_path = Path(seen["args"][seen["args"].index("--baseline-evidence") + 1])
        self.assertFalse(evidence_path.exists())

    def test_post_install_full_scan_remains_full_and_timeout_is_typed(self) -> None:
        scanner = self.target / "scripts/gitops/secret_scan.py"
        scanner.parent.mkdir(parents=True)
        scanner.write_text("# cleanroom scanner fixture\n", encoding="utf-8")

        def timeout(*_args, **_kwargs):
            import subprocess

            raise subprocess.TimeoutExpired(cmd="secret_scan", timeout=60)

        with patch("ide_development.engine.subprocess.run", side_effect=timeout):
            result = _run_post_install_secret_scan(target_root=self.target, resolution=None)
        self.assertFalse(result["ok"])
        self.assertEqual(result["mode"], "full")
        self.assertEqual(result["errorType"], "timeout")
    def test_version(self) -> None:
        result = run_version(package=self.package)
        self.assertEqual(result.exit_code, EXIT_OK)
        self.assertEqual(result.payload["packageVersion"], "2.1.0")
        self.assertEqual(result.payload["installerVersion"], "2.5.2")

    def test_marker_upsert_preserves_consumer_text(self) -> None:
        agents = self.target / "AGENTS.md"
        agents.write_text("# Consumer AGENTS\n\nKeep me.\n", encoding="utf-8")
        result = run_install_or_update(
            target=self.target,
            package=self.package,
            command="install",
            dry_run=False,
        )
        self.assertEqual(result.exit_code, EXIT_OK, result.payload)
        text = agents.read_text(encoding="utf-8")
        self.assertIn("Keep me.", text)
        self.assertIn("BEGIN LINKTREND-IDE-MANAGED", text)
        self.assertIn("Managed AGENTS block from package.", text)
        result = run_version(package=self.package)
        self.assertEqual(result.exit_code, EXIT_OK)
        self.assertEqual(result.payload["packageVersion"], "2.1.0")
        self.assertEqual(result.payload["installerVersion"], "2.5.2")

    def test_plan_and_dry_run_no_writes(self) -> None:
        before = _snapshot(self.target)
        plan = run_plan(target=self.target, package=self.package)
        self.assertEqual(plan.exit_code, EXIT_OK)
        self.assertTrue(plan.payload["dryRun"])
        self.assertGreaterEqual(plan.payload["summary"]["mutatingActionCount"], 1)

        dry = run_install_or_update(
            target=self.target,
            package=self.package,
            command="install",
            dry_run=True,
        )
        self.assertEqual(dry.exit_code, EXIT_OK)
        self.assertFalse(dry.payload.get("applied"))
        after = _snapshot(self.target)
        self.assertEqual(before, after)
        self.assertFalse((self.target / ".git" / "ide-development").exists())
        self.assertFalse((self.target / ".ide-development").exists())

    def test_install_idempotent_and_physical(self) -> None:
        first = run_install_or_update(
            target=self.target,
            package=self.package,
            command="install",
            dry_run=False,
        )
        self.assertEqual(first.exit_code, EXIT_OK, first.payload)
        snap1 = _file_identity_map(self.target)
        installed_state_before_repeat = (
            self.target / ".ide-development" / "installed-state.json"
        ).read_bytes()

        # Ensure physical files (not symlinks)
        for rel in (
            ".ide-development/CORE.txt",
            ".cursor/rules/sample-rule.mdc",
            ".ide-development/assets/file-with-spaces.txt",
            "AGENTS.md",
        ):
            path = self.target / Path(rel)
            self.assertTrue(path.is_file(), rel)
            self.assertFalse(path.is_symlink(), rel)
        agents = (self.target / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("BEGIN LINKTREND-IDE-MANAGED", agents)
        self.assertIn("Managed AGENTS block from package.", agents)

        second = run_install_or_update(
            target=self.target,
            package=self.package,
            command="install",
            dry_run=False,
        )
        self.assertEqual(second.exit_code, EXIT_OK, second.payload)
        snap2 = _file_identity_map(self.target)
        # Byte-identical content + mode for all managed destinations
        self.assertEqual(snap1, snap2)
        self.assertEqual(
            installed_state_before_repeat,
            (self.target / ".ide-development" / "installed-state.json").read_bytes(),
            "second install must not rewrite committed installed-state bytes",
        )

        update = run_install_or_update(
            target=self.target,
            package=self.package,
            command="update",
            dry_run=False,
        )
        self.assertEqual(update.exit_code, EXIT_OK, update.payload)
        snap3 = _file_identity_map(self.target)
        self.assertEqual(snap1, snap3)

        verify = run_verify(target=self.target, package=self.package)
        self.assertEqual(verify.exit_code, EXIT_OK, verify.payload)
        self.assertEqual(verify.payload["drift"], [])
        self.assertEqual(verify.payload["summary"]["driftCount"], 0)

    def test_sha256_and_read_refuse_symlink(self) -> None:
        from ide_development.io_atomic import read_file_bytes

        real = Path(self._tmp.name) / "real-target.txt"
        real.write_text("secret\n", encoding="utf-8")
        link = Path(self._tmp.name) / "link-to-real.txt"
        link.symlink_to(real)
        with self.assertRaises(OSError) as ctx:
            sha256_file(link)
        self.assertIn("symlink", str(ctx.exception).lower())
        with self.assertRaises(OSError) as ctx2:
            read_file_bytes(link)
        self.assertIn("symlink", str(ctx2.exception).lower())
        # Physical file still hashes
        self.assertTrue(sha256_file(real).startswith("sha256:"))

    def test_exclusive_lock_fail_closed(self) -> None:
        from ide_development.errors import ConflictError
        from ide_development.lock import exclusive_transaction_lock, lock_path
        from ide_development.paths import git_meta_dir

        # Lock path must live under resolved git meta, not under a gitfile path.
        expected = git_meta_dir(self.target) / "lock"
        self.assertEqual(lock_path(self.target), expected)

        with exclusive_transaction_lock(self.target) as held:
            self.assertEqual(held, expected)
            self.assertTrue(expected.is_file())
            with self.assertRaises(ConflictError) as ctx:
                with exclusive_transaction_lock(self.target):
                    pass  # pragma: no cover - must not enter
            self.assertIn("exclusive lock", str(ctx.exception).lower())

        # After release, a new acquire succeeds
        with exclusive_transaction_lock(self.target):
            pass

    def test_plan_dry_run_does_not_take_lock(self) -> None:
        from ide_development.lock import exclusive_transaction_lock, lock_path

        lock = lock_path(self.target)
        with exclusive_transaction_lock(self.target):
            # Holding the lock must not block plan / dry-run (no exclusive acquire).
            plan = run_plan(target=self.target, package=self.package)
            self.assertEqual(plan.exit_code, EXIT_OK)
            dry = run_install_or_update(
                target=self.target,
                package=self.package,
                command="install",
                dry_run=True,
            )
            self.assertEqual(dry.exit_code, EXIT_OK)
            self.assertFalse(dry.payload.get("applied"))
        # Mutating install still works after plan/dry-run under contention ended
        result = run_install_or_update(
            target=self.target,
            package=self.package,
            command="install",
            dry_run=False,
        )
        self.assertEqual(result.exit_code, EXIT_OK, result.payload)
        self.assertTrue(lock.parent.is_dir())

    def test_noop_rewrites_missing_installed_state(self) -> None:
        first = run_install_or_update(
            target=self.target,
            package=self.package,
            command="install",
            dry_run=False,
        )
        self.assertEqual(first.exit_code, EXIT_OK, first.payload)
        state = self.target / ".ide-development" / "installed-state.json"
        self.assertTrue(state.is_file())
        state.unlink()
        second = run_install_or_update(
            target=self.target,
            package=self.package,
            command="install",
            dry_run=False,
        )
        self.assertEqual(second.exit_code, EXIT_OK, second.payload)
        self.assertTrue(state.is_file(), "noop install must restore installed-state")
        update = run_install_or_update(
            target=self.target,
            package=self.package,
            command="update",
            dry_run=True,
        )
        self.assertEqual(update.exit_code, EXIT_OK, update.payload)

    def test_install_into_gitfile_worktree(self) -> None:
        import tempfile
        from ide_development.paths import git_meta_dir

        with tempfile.TemporaryDirectory() as td:
            real_git = Path(td) / "gitdir"
            real_git.mkdir()
            worktree = Path(td) / "consumer-worktree"
            worktree.mkdir()
            (worktree / ".git").write_text(f"gitdir: {real_git}\n", encoding="utf-8")
            (worktree / "README.md").write_text("# wt\n", encoding="utf-8")
            result = run_install_or_update(
                target=worktree,
                package=self.package,
                command="install",
                dry_run=False,
            )
            self.assertEqual(result.exit_code, EXIT_OK, result.payload)
            self.assertTrue((worktree / ".ide-development" / "CORE.txt").is_file())
            meta = git_meta_dir(worktree)
            self.assertTrue(meta.is_dir())
            self.assertTrue((meta / "last-transaction").is_dir())
            self.assertFalse((worktree / ".git").is_dir())

    def test_consumer_owned_preserved_and_unknown_conflict(self) -> None:
        owned = self.target / ".cursor" / "rules" / "consumer-owned.mdc"
        owned.parent.mkdir(parents=True, exist_ok=True)
        owned.write_text("# consumer owned\n", encoding="utf-8")

        # Collide with managed destination using different content
        collide = self.target / ".cursor" / "rules" / "sample-rule.mdc"
        collide.write_text("NOT THE PACKAGE\n", encoding="utf-8")

        result = run_install_or_update(
            target=self.target,
            package=self.package,
            command="install",
            dry_run=False,
        )
        self.assertEqual(result.exit_code, EXIT_CONFLICT, result.payload)
        self.assertTrue(owned.is_file())
        self.assertEqual(owned.read_text(encoding="utf-8"), "# consumer owned\n")
        self.assertEqual(collide.read_text(encoding="utf-8"), "NOT THE PACKAGE\n")

    def test_drift_detection(self) -> None:
        run_install_or_update(
            target=self.target,
            package=self.package,
            command="install",
            dry_run=False,
        )
        target_file = self.target / ".ide-development" / "CORE.txt"
        with managed_write_lease(
            target_root=self.target,
            paths=[".ide-development/CORE.txt"],
            operation="repair",
            package_version="2.1.0",
            manifest_digest=sha256_file(self.package / "core/managed-core/MANIFEST.json"),
            transaction_id="test-drift",
        ):
            target_file.write_text("drifted\n", encoding="utf-8")
        drift = run_drift(target=self.target, package=self.package)
        self.assertEqual(drift.exit_code, EXIT_DRIFT)
        kinds = {item["kind"] for item in drift.payload["drift"]}
        self.assertIn("modified", kinds)

        verify = run_verify(target=self.target, package=self.package)
        self.assertIn(verify.exit_code, {EXIT_DRIFT, EXIT_CONFLICT})

    def test_rollback_restores_bytes_and_modes(self) -> None:
        # Pre-create a file that install will replace after first adopting via matching?
        # Better: install, modify via second package update simulation by writing then rollback.
        run_install_or_update(
            target=self.target,
            package=self.package,
            command="install",
            dry_run=False,
        )
        core = self.target / ".ide-development" / "CORE.txt"
        original = core.read_bytes()
        original_mode = stat.S_IMODE(core.stat().st_mode)

        # Mutate managed file through a forced replace by temporarily matching state:
        # Direct engine update after aligning installed-state is complex; instead create
        # a second install from a mutated package copy.
        mutated_pkg = Path(self._tmp.name) / "mutated-package"
        shutil.copytree(self.package, mutated_pkg)
        mutated_core = mutated_pkg / "core/managed-core/files/CORE.txt"
        mutated_core.write_text("managed-core fixture MUTATED\n", encoding="utf-8")
        _rewrite_manifest_hash(mutated_pkg, "managed-core-readme", mutated_core)
        _rewrite_package_version(mutated_pkg, "2.1.1")

        updated = run_install_or_update(
            target=self.target,
            package=mutated_pkg,
            command="update",
            dry_run=False,
        )
        self.assertEqual(updated.exit_code, EXIT_OK, updated.payload)
        self.assertEqual(core.read_text(encoding="utf-8"), "managed-core fixture MUTATED\n")

        rolled = run_rollback(target=self.target)
        self.assertEqual(rolled.exit_code, EXIT_OK, rolled.payload)
        self.assertEqual(core.read_bytes(), original)
        self.assertEqual(stat.S_IMODE(core.stat().st_mode), original_mode)

    def test_migration_exact_remove_and_refuse_mismatch(self) -> None:
        obsolete = self.target / ".cursor" / "rules" / "obsolete-generic.mdc"
        obsolete.parent.mkdir(parents=True, exist_ok=True)
        # Exact match to catalog
        src = self.package / "core/managed-core/files/obsolete-generic.txt"
        obsolete.write_bytes(src.read_bytes())

        ok = run_install_or_update(
            target=self.target,
            package=self.package,
            command="install",
            dry_run=False,
        )
        self.assertEqual(ok.exit_code, EXIT_OK, ok.payload)
        self.assertFalse(obsolete.exists())

        # Recreate with wrong bytes → conflict
        obsolete.write_text("CHANGED\n", encoding="utf-8")
        bad = run_install_or_update(
            target=self.target,
            package=self.package,
            command="update",
            dry_run=False,
        )
        self.assertEqual(bad.exit_code, EXIT_CONFLICT, bad.payload)
        self.assertTrue(obsolete.exists())

    def test_interrupted_transaction_recovery(self) -> None:
        run_install_or_update(
            target=self.target,
            package=self.package,
            command="install",
            dry_run=False,
        )
        core = self.target / ".ide-development" / "CORE.txt"
        original = core.read_bytes()

        # Simulate interrupted apply: current-transaction with backup + partial change
        tx = current_tx_dir(self.target)
        tx.mkdir(parents=True, exist_ok=True)
        (tx / "backups").mkdir(parents=True, exist_ok=True)
        backup_name = encode_backup_name(".ide-development/CORE.txt")
        atomic_write_bytes(tx / "backups" / backup_name, original, mode="0644")
        with managed_write_lease(
            target_root=self.target,
            paths=[".ide-development/CORE.txt"],
            operation="repair",
            package_version="2.1.0",
            manifest_digest=sha256_file(self.package / "core/managed-core/MANIFEST.json"),
            transaction_id="test-interrupted-write",
        ):
            core.write_text("partial-write\n", encoding="utf-8")
        write_journal(
            tx,
            {
                "schemaVersion": 1,
                "transactionId": "test-interrupted",
                "command": "update",
                "packageVersion": "2.1.0",
                "phase": "apply",
                "backups": [
                    {
                        "path": ".ide-development/CORE.txt",
                        "existed": True,
                        "mode": "0644",
                        "contentHash": sha256_file(Path(self._tmp.name) / "unused")
                        if False
                        else None,
                        "backupName": backup_name,
                    }
                ],
                "applied": [".ide-development/CORE.txt"],
            },
        )
        # Fix contentHash in journal properly
        journal = {
            "schemaVersion": 1,
            "transactionId": "test-interrupted",
            "command": "update",
            "packageVersion": "2.1.0",
            "phase": "apply",
            "backups": [
                {
                    "path": ".ide-development/CORE.txt",
                    "existed": True,
                    "mode": "0644",
                    "contentHash": "sha256:" + ("0" * 64),
                    "backupName": backup_name,
                }
            ],
            "applied": [".ide-development/CORE.txt"],
        }
        write_journal(tx, journal)

        # Next mutating command should recover then proceed idempotently
        result = run_install_or_update(
            target=self.target,
            package=self.package,
            command="update",
            dry_run=False,
        )
        self.assertEqual(result.exit_code, EXIT_OK, result.payload)
        self.assertEqual(core.read_bytes(), original)
        self.assertFalse(current_tx_dir(self.target).exists())

    def test_refuse_system_self_install(self) -> None:
        pkg = Path(self._tmp.name) / "system-pkg"
        shutil.copytree(self.package, pkg)
        import subprocess

        subprocess.run(["git", "init"], cwd=str(pkg), check=True, capture_output=True)
        from ide_development.errors import InvalidPackageError

        with self.assertRaises(InvalidPackageError):
            run_install_or_update(
                target=pkg,
                package=pkg,
                command="install",
                dry_run=False,
            )

    def test_invalid_package_hash(self) -> None:
        bad = Path(self._tmp.name) / "bad-package"
        shutil.copytree(self.package, bad)
        manifest_path = bad / "core/managed-core/MANIFEST.json"
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        data["files"][0]["sourceHash"] = "sha256:" + ("a" * 64)
        manifest_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        from ide_development.errors import InvalidPackageError

        with self.assertRaises(InvalidPackageError):
            run_plan(target=self.target, package=bad)


def _snapshot(root: Path) -> dict[str, tuple[bytes | None, int | None, bool]]:
    out: dict[str, tuple[bytes | None, int | None, bool]] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        # skip .git objects noise except presence marker
        rel_dir = os.path.relpath(dirpath, root)
        if rel_dir == ".git" or rel_dir.startswith(".git" + os.sep):
            dirnames[:] = []
            out[".git"] = (None, None, True)
            continue
        for name in filenames:
            path = Path(dirpath) / name
            rel = path.relative_to(root).as_posix()
            if path.is_symlink():
                out[rel] = (None, None, True)
            else:
                out[rel] = (path.read_bytes(), stat.S_IMODE(path.stat().st_mode), False)
    return out


def _file_bytes_map(root: Path) -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        if rel_dir == ".git" or rel_dir.startswith(".git" + os.sep):
            dirnames[:] = []
            continue
        for name in filenames:
            path = Path(dirpath) / name
            rel = path.relative_to(root).as_posix()
            if path.is_symlink():
                continue
            out[rel] = path.read_bytes()
    return out


def _file_identity_map(root: Path) -> dict[str, tuple[bytes, int]]:
    """Map relative path -> (content bytes, mode) for physical files (excl. .git).

    Skips installed-state.json because noop apply rewrites installedAt (second
    precision) without changing managed destination bytes/modes.
    """
    out: dict[str, tuple[bytes, int]] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        if rel_dir == ".git" or rel_dir.startswith(".git" + os.sep):
            dirnames[:] = []
            continue
        for name in filenames:
            path = Path(dirpath) / name
            rel = path.relative_to(root).as_posix()
            if path.is_symlink():
                continue
            if rel == ".ide-development/installed-state.json":
                continue
            out[rel] = (path.read_bytes(), stat.S_IMODE(path.stat().st_mode))
    return out


def _rewrite_manifest_hash(package: Path, entry_id: str, source: Path) -> None:
    manifest_path = package / "core/managed-core/MANIFEST.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    digest = sha256_file(source)
    for entry in data["files"]:
        if entry["id"] == entry_id:
            entry["sourceHash"] = digest
    manifest_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _rewrite_package_version(package: Path, version: str) -> None:
    manifest_path = package / "core/managed-core/MANIFEST.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    data["packageVersion"] = version
    manifest_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    (package / "core/managed-core/VERSION").write_text(version + "\n", encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
