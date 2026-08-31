"""Focused tests for the explicit v2.5.2 same-version repair transaction."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from ide_development.engine import run_install_or_update, run_same_version_repair  # noqa: E402
from ide_development.errors import ConflictError, InvalidPackageError  # noqa: E402
from ide_development.hashing import sha256_file  # noqa: E402
from ide_development.manifest import load_manifest  # noqa: E402
from ide_development.plan import OpKind, PlanAction  # noqa: E402
from ide_development.state import load_installed_state  # noqa: E402
from ide_development.transaction import apply_action  # noqa: E402
from ide_development_tests import FIXTURE_PACKAGE, TempRepoTestCase, make_git_repo  # noqa: E402


class SameVersionRepairTests(TempRepoTestCase):
    def _package(self, name: str) -> Path:
        package = Path(self._tmp.name) / name
        shutil.copytree(FIXTURE_PACKAGE, package)
        (package / "VERSION").write_text("2.5.2\n", encoding="utf-8")
        (package / "core/managed-core/VERSION").write_text("2.5.2\n", encoding="utf-8")
        manifest_path = package / "core/managed-core/MANIFEST.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["packageVersion"] = "2.5.2"
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        make_git_repo(package)
        subprocess.run(["git", "add", "."], cwd=package, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "package 2.5.2"],
            cwd=package,
            check=True,
            capture_output=True,
        )
        return package

    @staticmethod
    def _identity(package: Path) -> tuple[str, str]:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=package, text=True
        ).strip()
        tree = subprocess.check_output(
            ["git", "rev-parse", "HEAD^{tree}"], cwd=package, text=True
        ).strip()
        return commit, tree

    def _receipt(self, old: Path, new: Path, path: str) -> Path:
        old_manifest = load_manifest(old)
        new_manifest = load_manifest(new)
        old_state = load_installed_state(self.target)
        assert old_state is not None
        old_entry = next(e for e in old_manifest.active_entries() if e.destination == path)
        new_entry = next(e for e in new_manifest.active_entries() if e.destination == path)
        commit, tree = self._identity(new)
        source_file = new / new_entry.source
        receipt = Path(self._tmp.name) / "repair.json"
        receipt.write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "kind": "ide-managed-same-version-repair",
                    "targetWorktree": str(self.target.resolve()),
                    "packageVersion": "2.5.2",
                    "source": {
                        "repository": "linktrend/IDE-Development",
                        "ref": "issue/458-test-source",
                        "commit": commit,
                        "tree": tree,
                        "manifestDigest": sha256_file(new_manifest.path),
                    },
                    "installed": {
                        "packageVersion": "2.5.2",
                        "manifestDigest": old_state.manifest_hash,
                    },
                    "paths": [
                        {
                            "path": path,
                            "source": new_entry.source,
                            "installedSourceDigest": old_entry.source_hash,
                            "installedDigest": old_state.files[path].content_hash,
                            "sourceDigest": new_entry.source_hash,
                            "sourceBytes": source_file.stat().st_size,
                        }
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return receipt

    def test_exact_source_repair_replaces_only_receipted_managed_file(self) -> None:
        old = self._package("old-package")
        self.assertEqual(run_install_or_update(target=self.target, package=old, command="install").exit_code, 0)

        new = self._package("new-package")
        source = new / "core/managed-core/files/CORE.txt"
        source.write_text("repaired source bytes\n", encoding="utf-8")
        manifest_path = new / "core/managed-core/MANIFEST.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for entry in manifest["files"]:
            if entry["id"] == "managed-core-readme":
                entry["sourceHash"] = sha256_file(source)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=new, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "source repair"], cwd=new, check=True, capture_output=True)

        receipt = self._receipt(old, new, ".ide-development/CORE.txt")
        result = run_same_version_repair(
            target=self.target, package=new, repair_manifest=receipt, dry_run=False
        )
        self.assertEqual(result.exit_code, 0, result.payload)
        self.assertEqual(
            (self.target / ".ide-development/CORE.txt").read_text(encoding="utf-8"),
            "repaired source bytes\n",
        )
        self.assertEqual(result.payload["sourceIdentity"]["tree"], self._identity(new)[1])
        self.assertEqual(result.payload["transaction"]["packageVersion"], "2.5.2")

    def test_repair_rejects_stale_source_and_unmanaged_paths(self) -> None:
        old = self._package("old-package")
        self.assertEqual(run_install_or_update(target=self.target, package=old, command="install").exit_code, 0)
        new = self._package("new-package")
        source = new / "core/managed-core/files/CORE.txt"
        source.write_text("repaired source bytes\n", encoding="utf-8")
        manifest_path = new / "core/managed-core/MANIFEST.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for entry in manifest["files"]:
            if entry["id"] == "managed-core-readme":
                entry["sourceHash"] = sha256_file(source)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=new, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "source repair"], cwd=new, check=True, capture_output=True)
        receipt = self._receipt(old, new, ".ide-development/CORE.txt")
        payload = json.loads(receipt.read_text(encoding="utf-8"))
        payload["source"]["tree"] = "0" * 40
        receipt.write_text(json.dumps(payload) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(InvalidPackageError, "source identity is stale"):
            run_same_version_repair(target=self.target, package=new, repair_manifest=receipt)

        payload["source"]["tree"] = self._identity(new)[1]
        payload["paths"][0]["path"] = "README.md"
        receipt.write_text(json.dumps(payload) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(InvalidPackageError, "not an IDE-managed file"):
            run_same_version_repair(target=self.target, package=new, repair_manifest=receipt)

    def test_managed_write_without_lease_fails_closed(self) -> None:
        package = self._package("package")
        manifest = load_manifest(package)
        entry = next(e for e in manifest.active_entries() if e.destination == ".ide-development/CORE.txt")
        with self.assertRaises(ConflictError):
            apply_action(
                target_root=self.target,
                package_root=package,
                action=PlanAction(op=OpKind.REPLACE, path=entry.destination, entry_id=entry.id),
                entries={entry.destination: entry},
                lease=None,
            )


if __name__ == "__main__":
    unittest.main()
