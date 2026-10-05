"""Fail-closed tests for protected preimage state reconciliation."""

from __future__ import annotations

import json
import hashlib
import shutil
import subprocess
from pathlib import Path

from ide_development.engine import run_install_or_update, run_protected_preimage_adoption, run_rollback
from ide_development.errors import InvalidPackageError
from ide_development.hashing import sha256_file
from ide_development.managed_write_guard import managed_write_lease
from ide_development.state import load_installed_state
from ide_development_tests import TempRepoTestCase


class ProtectedPreimageAdoptionTests(TempRepoTestCase):
    rel = ".ide-development/CORE.txt"
    unrelated_rel = ".ide-development/assets/file-with-spaces.txt"

    def _git(self, *args: str) -> str:
        result = subprocess.run(
            ["git", *args], cwd=self.target, text=True, capture_output=True, check=True
        )
        return result.stdout.strip()

    def _prepare_protected_preimage(self) -> tuple[Path, dict[str, object], bytes, str, str]:
        package = Path(self._tmp.name) / "package-2.5.2"
        shutil.copytree(self.package, package)
        for version_path in (package / "VERSION", package / "core/managed-core/VERSION"):
            version_path.write_text("2.5.2\n", encoding="utf-8")
        manifest_path = package / "core/managed-core/MANIFEST.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["packageVersion"] = "2.5.2"
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        self.package = package
        installed = run_install_or_update(
            target=self.target, package=package, command="install", dry_run=False
        )
        self.assertEqual(installed.exit_code, 0, installed.payload)
        path = self.target / self.rel
        before = path.read_bytes()
        state = load_installed_state(self.target)
        assert state is not None
        previous = state.files[self.rel]
        unrelated = self.target / self.unrelated_rel
        unrelated_before = state.files[self.unrelated_rel].content_hash
        with managed_write_lease(
            target_root=self.target,
            paths=[self.unrelated_rel],
            operation="repair",
            package_version=state.package_version,
            manifest_digest=state.manifest_hash or "sha256:" + ("0" * 64),
            transaction_id="protected-preimage-unrelated-drift",
        ):
            unrelated.write_bytes(unrelated.read_bytes() + b"\npre-existing drift\n")
        self._git("add", "-A")
        self._git("commit", "-m", "installed baseline")
        with managed_write_lease(
            target_root=self.target,
            paths=[self.rel],
            operation="repair",
            package_version=state.package_version,
            manifest_digest=state.manifest_hash or "sha256:" + ("0" * 64),
            transaction_id="protected-preimage-test",
        ):
            path.write_bytes(before + b"\nprotected-preimage\n")
        self._git("add", self.rel)
        self._git("commit", "-m", "protected preimage")
        commit = self._git("rev-parse", "HEAD")
        self._git("update-ref", "refs/remotes/origin/development", commit)
        remote = Path(self._tmp.name) / "origin.git"
        subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
        subprocess.run(
            [
                "git",
                "-C",
                str(self.target),
                "push",
                str(remote),
                f"{commit}:refs/heads/development",
            ],
            check=True,
            capture_output=True,
        )
        ancestor = self._git("rev-list", "--parents", "-n", "1", commit).split()[1]
        tree = self._git("rev-parse", "HEAD^{tree}")
        blob = self._git("hash-object", "--no-filters", "--", self.rel)
        receipt = Path(self._tmp.name) / "protected-preimage.json"
        payload: dict[str, object] = {
            "schemaVersion": 1,
            "kind": "ide-managed-protected-preimage-adoption",
            "targetWorktree": str(self.target),
            "packageVersion": "2.5.2",
            "installedManifestDigest": state.manifest_hash,
            "protected": {
                "repository": str(remote),
                "baseRef": "origin/development",
                "baseCommit": commit,
                "commit": commit,
                "tree": tree,
                "ancestor": ancestor,
            },
            "paths": [
                {
                    "path": self.rel,
                    "installedSourceDigest": previous.source_hash,
                    "priorInstalledDigest": previous.content_hash,
                    "currentDigest": sha256_file(path),
                    "gitBlob": blob,
                }
            ],
        }
        self._git("remote", "add", "origin", str(remote))
        # The remote is added after the commit so this helper can also prove
        # that a receipt cannot silently select another repository.
        receipt.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return receipt, payload, before, commit, unrelated_before

    def test_adoption_updates_only_installed_state_and_is_rollbackable(self) -> None:
        receipt, _payload, before, _commit, unrelated_before = self._prepare_protected_preimage()
        path = self.target / self.rel
        current = path.read_bytes()
        result = run_protected_preimage_adoption(
            target=self.target,
            package=self.package,
            adoption_manifest=receipt,
            dry_run=False,
        )
        self.assertEqual(result.exit_code, 0, result.payload)
        self.assertEqual(path.read_bytes(), current)
        state = load_installed_state(self.target)
        assert state is not None
        self.assertEqual(state.files[self.rel].content_hash, sha256_file(path))
        self.assertEqual(state.files[self.unrelated_rel].content_hash, unrelated_before)
        self.assertTrue((self.target / ".git/ide-development/last-transaction/journal.json").is_file())
        rolled = run_rollback(target=self.target)
        self.assertEqual(rolled.exit_code, 0, rolled.payload)
        restored = load_installed_state(self.target)
        assert restored is not None
        self.assertEqual(
            restored.files[self.rel].content_hash,
            "sha256:" + hashlib.sha256(before).hexdigest(),
        )
        self.assertEqual((self.target / self.rel).read_bytes(), current)
        self.assertEqual(restored.files[self.rel].content_hash, restored.files[self.rel].source_hash)
        self.assertNotEqual(before, current)

    def test_uncommitted_byte_change_is_rejected(self) -> None:
        receipt, _payload, _before, _commit, _unrelated_before = self._prepare_protected_preimage()
        path = self.target / self.rel
        with managed_write_lease(
            target_root=self.target,
            paths=[self.rel],
            operation="repair",
            package_version="2.5.2",
            manifest_digest=sha256_file(self.target / ".ide-development/MANIFEST.json"),
            transaction_id="protected-preimage-adversarial",
        ):
            path.write_bytes(path.read_bytes() + b"tampered")
        with self.assertRaisesRegex(InvalidPackageError, "current bytes are stale|blob identity is stale"):
            run_protected_preimage_adoption(
                target=self.target,
                package=self.package,
                adoption_manifest=receipt,
                dry_run=True,
            )

    def test_repository_mismatch_is_rejected(self) -> None:
        receipt, payload, _before, _commit, _unrelated_before = self._prepare_protected_preimage()
        payload["protected"]["repository"] = "https://github.com/other/repository"
        receipt.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(InvalidPackageError, "repository does not match origin"):
            run_protected_preimage_adoption(
                target=self.target,
                package=self.package,
                adoption_manifest=receipt,
                dry_run=True,
            )

    def test_head_base_ref_is_rejected(self) -> None:
        receipt, payload, _before, _commit, _unrelated_before = self._prepare_protected_preimage()
        payload["protected"]["baseRef"] = "HEAD"
        receipt.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(InvalidPackageError, "authoritative origin/development"):
            run_protected_preimage_adoption(
                target=self.target,
                package=self.package,
                adoption_manifest=receipt,
                dry_run=True,
            )

    def test_local_tracking_ref_spoof_is_rejected(self) -> None:
        receipt, payload, _before, commit, _unrelated_before = self._prepare_protected_preimage()
        self._git("commit", "--allow-empty", "-m", "local spoof")
        spoof = self._git("rev-parse", "HEAD")
        self._git("update-ref", "refs/remotes/origin/development", spoof)
        payload["protected"]["baseCommit"] = spoof
        payload["protected"]["commit"] = commit
        payload["protected"]["tree"] = self._git("rev-parse", f"{commit}^{{tree}}")
        payload["protected"]["ancestor"] = self._git("rev-list", "--parents", "-n", "1", commit).split()[1]
        receipt.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(InvalidPackageError, "remote protected base identity is stale"):
            run_protected_preimage_adoption(
                target=self.target,
                package=self.package,
                adoption_manifest=receipt,
                dry_run=True,
            )
