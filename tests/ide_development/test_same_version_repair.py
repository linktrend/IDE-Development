"""Focused tests for the explicit v2.5.2 same-version repair transaction."""

from __future__ import annotations

import json
import os
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
from ide_development.managed_write_guard import is_read_only_mode  # noqa: E402
from ide_development.manifest import load_manifest  # noqa: E402
from ide_development.plan import FULL_ROOT_WORKFLOW_REL, OpKind, PlanAction  # noqa: E402
from ide_development.state import load_installed_state, prove_read_only_state  # noqa: E402
from ide_development.transaction import apply_action, rollback_last  # noqa: E402
from ide_development_tests import FIXTURE_PACKAGE, TempRepoTestCase, make_git_repo  # noqa: E402

OPENCLAW_DEST = ".ide-development/content/doctrine/OPENCLAW-CUSTOMIZATION-ADMISSION.md"
OPENCLAW_SOURCE = "core/managed-core/content/doctrine/OPENCLAW-CUSTOMIZATION-ADMISSION.md"
GITHUB_ROOT_SOURCE = "core/github/managed-workflows/linktrend-integrator-merge.yml"
COMPATIBLE_FULL_WORKFLOW = """name: Linktrend Full Suite

on:
  workflow_dispatch:
    inputs:
      dependency_digest:
        description: "exact dependency digest"
        required: false
        type: string
      target_baseline_sha:
        description: "exact baseline sha"
        required: false
        type: string
      target_baseline_ref:
        description: "exact baseline ref"
        required: false
        type: string

jobs:
  full:
    name: Linktrend Full Suite
    if: github.event.label.name == 'linktrend-full-suite'
    runs-on: ubuntu-24.04-arm
    steps:
      - run: echo compatible
"""
STALE_FULL_WORKFLOW = """name: Linktrend Full Suite

on:
  pull_request:
    branches: [development]
    types: [labeled]
  workflow_dispatch:
    inputs:
      mode:
        description: "phase for a normal sealed candidate"
        required: false
        default: "phase"
        type: string

jobs:
  full:
    name: Linktrend Full Suite
    if: github.event.label.name == 'linktrend-full-suite'
    runs-on: ubuntu-24.04-arm
    steps:
      - run: echo stale
"""


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

    def _receipt(
        self,
        old: Path,
        new: Path,
        path: str,
        *,
        operation: str = "replace",
    ) -> Path:
        old_manifest = load_manifest(old)
        new_manifest = load_manifest(new)
        old_state = load_installed_state(self.target)
        assert old_state is not None
        new_entry = next(e for e in new_manifest.active_entries() if e.destination == path)
        commit, tree = self._identity(new)
        source_file = new / new_entry.source
        row: dict[str, object] = {
            "path": path,
            "source": new_entry.source,
            "sourceDigest": new_entry.source_hash,
            "sourceBytes": source_file.stat().st_size,
        }
        if operation == "add":
            row["operation"] = "add"
        else:
            old_entry = next(
                (e for e in old_manifest.active_entries() if e.destination == path),
                None,
            )
            previous = old_state.files.get(path)
            row["installedSourceDigest"] = (
                old_entry.source_hash if old_entry is not None else "sha256:" + ("0" * 64)
            )
            row["installedDigest"] = (
                previous.content_hash if previous is not None else "sha256:" + ("0" * 64)
            )
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
                        "manifestDigest": old_state.manifest_hash
                        or sha256_file(self.target / ".ide-development/MANIFEST.json"),
                    },
                    "paths": [row],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return receipt

    def _commit_package(self, package: Path, message: str) -> None:
        subprocess.run(["git", "add", "."], cwd=package, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", message],
            cwd=package,
            check=True,
            capture_output=True,
        )

    def _add_openclaw_admission(self, package: Path) -> Path:
        source = package / OPENCLAW_SOURCE
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text("# OpenClaw Prime customization-only admission\n", encoding="utf-8")
        manifest_path = package / "core/managed-core/MANIFEST.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["files"].append(
            {
                "id": "doctrine-openclaw-customization-admission-md",
                "ownershipClass": "managed-core",
                "source": OPENCLAW_SOURCE,
                "destination": OPENCLAW_DEST,
                "mode": "0644",
                "platform": "all",
                "os": "all",
                "mergeStrategy": "replace",
                "sourceHash": sha256_file(source),
            }
        )
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        return source

    def _add_github_root_workflow(self, package: Path) -> Path:
        source = package / GITHUB_ROOT_SOURCE
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(COMPATIBLE_FULL_WORKFLOW, encoding="utf-8")
        manifest_path = package / "core/managed-core/MANIFEST.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["files"].append(
            {
                "id": "github-root-workflow-linktrend-integrator-merge-yml",
                "ownershipClass": "managed-core",
                "source": GITHUB_ROOT_SOURCE,
                "destination": FULL_ROOT_WORKFLOW_REL,
                "mode": "0644",
                "platform": "github",
                "os": "all",
                "mergeStrategy": "replace",
                "sourceHash": sha256_file(source),
            }
        )
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        return source

    def _assert_managed_read_only(self) -> None:
        state = load_installed_state(self.target)
        assert state is not None
        prove_read_only_state(self.target, state)
        for rel, file_state in state.files.items():
            path = self.target / rel
            if path.is_file() and not path.is_symlink() and file_state.mutability_policy == "read-only":
                self.assertTrue(is_read_only_mode(path.stat().st_mode), rel)

    def _git_checkout_managed(self) -> list[str]:
        state = load_installed_state(self.target)
        assert state is not None
        rels = [rel for rel, file_state in state.files.items() if (self.target / rel).is_file()]
        subprocess.run(["git", "add", "-f", "-A"], cwd=self.target, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "track installed managed files"],
            cwd=self.target,
            check=True,
            capture_output=True,
        )
        checkout = subprocess.run(
            ["git", "checkout", "--", *rels],
            cwd=self.target,
            capture_output=True,
            text=True,
        )
        self.assertEqual(checkout.returncode, 0, checkout.stderr)
        # Git records blobs as 100644; checkout restores owner-writable files.
        for rel in rels:
            path = self.target / rel
            if path.is_file() and not path.is_symlink():
                os.chmod(path, 0o644)
        writable = [
            rel
            for rel in rels
            if not is_read_only_mode((self.target / rel).stat().st_mode)
        ]
        self.assertTrue(writable, "git checkout must restore writable modes for this proof")
        return writable

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

    def test_declared_openclaw_addition_and_rollback_after_git_checkout(self) -> None:
        old = self._package("old-package")
        self.assertEqual(run_install_or_update(target=self.target, package=old, command="install").exit_code, 0)
        self._assert_managed_read_only()
        writable = self._git_checkout_managed()
        with self.assertRaisesRegex(ConflictError, "read-only after lease closure"):
            prove_read_only_state(self.target)
        self.assertTrue(any(not is_read_only_mode((self.target / rel).stat().st_mode) for rel in writable))

        new = self._package("new-package")
        self._add_openclaw_admission(new)
        self._commit_package(new, "admit openclaw customization path")
        receipt = self._receipt(old, new, OPENCLAW_DEST, operation="add")
        result = run_same_version_repair(
            target=self.target, package=new, repair_manifest=receipt, dry_run=False
        )
        self.assertEqual(result.exit_code, 0, result.payload)
        created = self.target / OPENCLAW_DEST
        self.assertEqual(
            created.read_text(encoding="utf-8"),
            "# OpenClaw Prime customization-only admission\n",
        )
        self.assertTrue(is_read_only_mode(created.stat().st_mode))
        self._assert_managed_read_only()
        applied_ops = {item["path"]: item["op"] for item in result.payload["transaction"]["applied"]}
        self.assertEqual(applied_ops[OPENCLAW_DEST], "create")

        rollback = rollback_last(self.target)
        self.assertIn(OPENCLAW_DEST, rollback["restored"])
        self.assertFalse(created.exists())
        self._assert_managed_read_only()

    def test_addition_rejects_unmanaged_and_existing_collisions(self) -> None:
        old = self._package("old-package")
        self.assertEqual(run_install_or_update(target=self.target, package=old, command="install").exit_code, 0)
        new = self._package("new-package")
        self._add_openclaw_admission(new)
        self._commit_package(new, "admit openclaw customization path")

        undeclared = self._receipt(old, new, OPENCLAW_DEST)
        with self.assertRaisesRegex(InvalidPackageError, "not an IDE-managed file"):
            run_same_version_repair(target=self.target, package=new, repair_manifest=undeclared)

        colliding = self.target / OPENCLAW_DEST
        colliding.parent.mkdir(parents=True, exist_ok=True)
        colliding.write_text("consumer collision\n", encoding="utf-8")
        receipt = self._receipt(old, new, OPENCLAW_DEST, operation="add")
        with self.assertRaisesRegex(ConflictError, "existing collision"):
            run_same_version_repair(target=self.target, package=new, repair_manifest=receipt)

        colliding.unlink()
        payload = json.loads(receipt.read_text(encoding="utf-8"))
        payload["paths"][0]["path"] = "README.md"
        payload["paths"][0]["source"] = "README.md"
        receipt.write_text(json.dumps(payload) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(InvalidPackageError, "not an IDE-managed file"):
            run_same_version_repair(target=self.target, package=new, repair_manifest=receipt)

    def _github_root_repair_packages(self) -> tuple[Path, Path]:
        old = self._package("old-package")
        self.assertEqual(run_install_or_update(target=self.target, package=old, command="install").exit_code, 0)
        new = self._package("new-package")
        self._add_github_root_workflow(new)
        self._commit_package(new, "admit github-root full trigger")
        return old, new

    def test_matching_unmanaged_non_workflow_add_still_conflicts(self) -> None:
        old = self._package("old-package")
        self.assertEqual(run_install_or_update(target=self.target, package=old, command="install").exit_code, 0)
        new = self._package("new-package")
        self._add_openclaw_admission(new)
        self._commit_package(new, "admit openclaw customization path")
        colliding = self.target / OPENCLAW_DEST
        colliding.parent.mkdir(parents=True, exist_ok=True)
        colliding.write_text("# OpenClaw Prime customization-only admission\n", encoding="utf-8")
        os.chmod(colliding, 0o444)
        receipt = self._receipt(old, new, OPENCLAW_DEST, operation="add")
        with self.assertRaisesRegex(ConflictError, "existing collision"):
            run_same_version_repair(target=self.target, package=new, repair_manifest=receipt)

    def test_unmanaged_matching_github_root_add_claims_read_only_ownership(self) -> None:
        old, new = self._github_root_repair_packages()
        live = self.target / FULL_ROOT_WORKFLOW_REL
        live.parent.mkdir(parents=True, exist_ok=True)
        live.write_text(COMPATIBLE_FULL_WORKFLOW, encoding="utf-8")
        os.chmod(live, 0o644)
        receipt = self._receipt(old, new, FULL_ROOT_WORKFLOW_REL, operation="add")
        result = run_same_version_repair(
            target=self.target, package=new, repair_manifest=receipt, dry_run=False
        )
        self.assertEqual(result.exit_code, 0, result.payload)
        self.assertEqual(live.read_text(encoding="utf-8"), COMPATIBLE_FULL_WORKFLOW)
        self.assertTrue(is_read_only_mode(live.stat().st_mode))
        state = load_installed_state(self.target)
        assert state is not None
        owned = state.files[FULL_ROOT_WORKFLOW_REL]
        self.assertEqual(owned.ownership_class, "managed-core")
        self.assertEqual(owned.id, "github-root-workflow-linktrend-integrator-merge-yml")
        applied = {item["path"]: item["op"] for item in result.payload["transaction"]["applied"]}
        self.assertEqual(applied[FULL_ROOT_WORKFLOW_REL], "create")

    def test_unmanaged_exact_github_root_add_is_noop(self) -> None:
        old, new = self._github_root_repair_packages()
        live = self.target / FULL_ROOT_WORKFLOW_REL
        live.parent.mkdir(parents=True, exist_ok=True)
        live.write_text(COMPATIBLE_FULL_WORKFLOW, encoding="utf-8")
        os.chmod(live, 0o444)
        before_mode = live.stat().st_mode & 0o7777
        receipt = self._receipt(old, new, FULL_ROOT_WORKFLOW_REL, operation="add")
        result = run_same_version_repair(
            target=self.target, package=new, repair_manifest=receipt, dry_run=False
        )
        self.assertEqual(result.exit_code, 0, result.payload)
        action = next(item for item in result.payload["actions"] if item["path"] == FULL_ROOT_WORKFLOW_REL)
        self.assertEqual(action["op"], "noop")
        self.assertEqual(live.stat().st_mode & 0o7777, before_mode)
        self.assertNotIn(
            FULL_ROOT_WORKFLOW_REL,
            {item["path"] for item in result.payload["transaction"]["applied"]},
        )
        state = load_installed_state(self.target)
        assert state is not None
        self.assertEqual(state.files[FULL_ROOT_WORKFLOW_REL].ownership_class, "managed-core")

    def test_unmanaged_stale_full_github_root_add_is_replaced(self) -> None:
        old, new = self._github_root_repair_packages()
        live = self.target / FULL_ROOT_WORKFLOW_REL
        live.parent.mkdir(parents=True, exist_ok=True)
        live.write_text(STALE_FULL_WORKFLOW, encoding="utf-8")
        os.chmod(live, 0o644)
        receipt = self._receipt(old, new, FULL_ROOT_WORKFLOW_REL, operation="add")
        result = run_same_version_repair(
            target=self.target, package=new, repair_manifest=receipt, dry_run=False
        )
        self.assertEqual(result.exit_code, 0, result.payload)
        self.assertEqual(live.read_text(encoding="utf-8"), COMPATIBLE_FULL_WORKFLOW)
        self.assertTrue(is_read_only_mode(live.stat().st_mode))
        applied = {item["path"]: item["op"] for item in result.payload["transaction"]["applied"]}
        self.assertEqual(applied[FULL_ROOT_WORKFLOW_REL], "create")

    def test_unrelated_unmanaged_github_root_add_still_conflicts(self) -> None:
        old, new = self._github_root_repair_packages()
        live = self.target / FULL_ROOT_WORKFLOW_REL
        live.parent.mkdir(parents=True, exist_ok=True)
        live.write_text("name: Consumer CI\non: push\njobs: {}\n", encoding="utf-8")
        receipt = self._receipt(old, new, FULL_ROOT_WORKFLOW_REL, operation="add")
        with self.assertRaisesRegex(ConflictError, "existing collision"):
            run_same_version_repair(target=self.target, package=new, repair_manifest=receipt)
        self.assertEqual(live.read_text(encoding="utf-8"), "name: Consumer CI\non: push\njobs: {}\n")

    def test_matching_managed_add_collision_is_noop_and_derives_missing_manifest_hash(self) -> None:
        old = self._package("old-package")
        self._add_openclaw_admission(old)
        self._commit_package(old, "admit existing managed path")
        self.assertEqual(
            run_install_or_update(target=self.target, package=old, command="install").exit_code,
            0,
        )
        created = self.target / OPENCLAW_DEST
        before_bytes = created.read_bytes()
        before_mode = created.stat().st_mode & 0o7777

        new = self._package("new-package")
        self._add_openclaw_admission(new)
        changed_source = new / "core/managed-core/files/CORE.txt"
        changed_source.write_text("same-version manifest repair\n", encoding="utf-8")
        manifest_path = new / "core/managed-core/MANIFEST.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for entry in manifest["files"]:
            if entry["id"] == "managed-core-readme":
                entry["sourceHash"] = sha256_file(changed_source)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        self._commit_package(new, "change unrelated managed source")

        state_path = self.target / ".ide-development/installed-state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        os.chmod(state_path, 0o644)
        state.pop("manifestHash")
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

        receipt = self._receipt(old, new, OPENCLAW_DEST, operation="add")
        result = run_same_version_repair(
            target=self.target, package=new, repair_manifest=receipt, dry_run=False
        )
        self.assertEqual(result.exit_code, 0, result.payload)
        action = next(item for item in result.payload["actions"] if item["path"] == OPENCLAW_DEST)
        self.assertEqual(action["op"], "noop")
        self.assertEqual(created.read_bytes(), before_bytes)
        self.assertEqual(created.stat().st_mode & 0o7777, before_mode)
        self.assertEqual(
            json.loads(state_path.read_text(encoding="utf-8"))["manifestHash"],
            sha256_file(new / "core/managed-core/MANIFEST.json"),
        )
        self.assertNotIn(
            OPENCLAW_DEST,
            {item["path"] for item in result.payload["transaction"]["applied"]},
        )

    def test_matching_bytes_with_wrong_mode_or_provenance_still_fails(self) -> None:
        old = self._package("old-package")
        self._add_openclaw_admission(old)
        self._commit_package(old, "admit existing managed path")
        self.assertEqual(
            run_install_or_update(target=self.target, package=old, command="install").exit_code,
            0,
        )
        new = self._package("new-package")
        self._add_openclaw_admission(new)
        changed_source = new / "core/managed-core/files/CORE.txt"
        changed_source.write_text("manifest identity changes\n", encoding="utf-8")
        manifest_path = new / "core/managed-core/MANIFEST.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for entry in manifest["files"]:
            if entry["id"] == "managed-core-readme":
                entry["sourceHash"] = sha256_file(changed_source)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        self._commit_package(new, "change unrelated managed source")
        receipt = self._receipt(old, new, OPENCLAW_DEST, operation="add")

        os.chmod(self.target / OPENCLAW_DEST, 0o644)
        with self.assertRaisesRegex(ConflictError, "existing collision"):
            run_same_version_repair(target=self.target, package=new, repair_manifest=receipt)

        os.chmod(self.target / OPENCLAW_DEST, 0o444)
        state_path = self.target / ".ide-development/installed-state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        os.chmod(state_path, 0o644)
        state["files"][OPENCLAW_DEST]["owner"] = "unmanaged-consumer"
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(ConflictError, "existing collision"):
            run_same_version_repair(target=self.target, package=new, repair_manifest=receipt)

    def test_missing_manifest_hash_without_exact_managed_preimage_fails(self) -> None:
        old = self._package("old-package")
        self.assertEqual(
            run_install_or_update(target=self.target, package=old, command="install").exit_code,
            0,
        )
        new = self._package("new-package")
        source = new / "core/managed-core/files/CORE.txt"
        source.write_text("manifest preimage ambiguity\n", encoding="utf-8")
        manifest_path = new / "core/managed-core/MANIFEST.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for entry in manifest["files"]:
            if entry["id"] == "managed-core-readme":
                entry["sourceHash"] = sha256_file(source)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        self._commit_package(new, "repair source")
        receipt = self._receipt(old, new, ".ide-development/CORE.txt")
        state_path = self.target / ".ide-development/installed-state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        os.chmod(state_path, 0o644)
        state.pop("manifestHash")
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(InvalidPackageError, "manifestHash is missing"):
            run_install_or_update(target=self.target, package=old, command="update")
        (self.target / ".ide-development/MANIFEST.json").unlink()
        with self.assertRaisesRegex(InvalidPackageError, "cannot be exactly derived"):
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
