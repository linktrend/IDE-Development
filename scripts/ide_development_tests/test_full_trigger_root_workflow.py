"""Installer ownership of the live Full trigger root workflow."""

from __future__ import annotations

import json
import os
import shutil
import stat
import unittest
from pathlib import Path

from ide_development.constants import EXIT_CONFLICT, EXIT_OK
from ide_development.engine import run_install_or_update
from ide_development.hashing import sha256_file
from ide_development.managed_write_guard import is_read_only_mode
from ide_development.plan import (
    FULL_ROOT_WORKFLOW_REL,
    REQUIRED_FULL_DISPATCH_INPUTS,
    is_stale_full_root_workflow,
    required_full_dispatch_inputs_present,
)
from ide_development.state import load_installed_state
from ide_development_tests import TempRepoTestCase

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_WORKFLOW = (
    REPO_ROOT / "core" / "github" / "managed-workflows" / "linktrend-integrator-merge.yml"
)
STALE_WORKFLOW = """name: Linktrend Full Suite

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
      pr_number:
        description: "Existing same-repository Phase PR number"
        required: false
        type: string
      expected_head:
        description: "Exact 40-character Phase PR head"
        required: false
        type: string

jobs:
  full:
    name: Linktrend Full Suite
    if: github.event.label.name == 'linktrend-full-suite'
    runs-on: ubuntu-24.04-arm
    steps:
      - run: echo stale
"""


class FullTriggerContractTests(unittest.TestCase):
    def test_managed_source_declares_required_dispatch_inputs(self) -> None:
        text = SOURCE_WORKFLOW.read_text(encoding="utf-8")
        self.assertTrue(required_full_dispatch_inputs_present(text), text)
        self.assertFalse(is_stale_full_root_workflow(text))

    def test_linksites_shape_is_classified_stale(self) -> None:
        self.assertTrue(is_stale_full_root_workflow(STALE_WORKFLOW))
        for name in REQUIRED_FULL_DISPATCH_INPUTS:
            self.assertNotIn(f"      {name}:", STALE_WORKFLOW)


class FullTriggerRootWorkflowInstallTests(TempRepoTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.package = Path(self._tmp.name) / "package"
        self._materialize_package()

    def _materialize_package(self) -> None:
        source_rel = "core/github/managed-workflows/linktrend-integrator-merge.yml"
        dest = self.package / source_rel
        dest.parent.mkdir(parents=True)
        shutil.copyfile(SOURCE_WORKFLOW, dest)
        digest = sha256_file(dest)
        (self.package / "VERSION").write_text("2.5.2\n", encoding="utf-8")
        managed = self.package / "core" / "managed-core"
        managed.mkdir(parents=True)
        (managed / "VERSION").write_text("2.5.2\n", encoding="utf-8")
        (managed / "migrations").mkdir(parents=True)
        (managed / "migrations" / "catalog.json").write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "catalogId": "ide-development-managed-core-migrations",
                    "packageVersion": "2.5.2",
                    "entries": [],
                }
            )
            + "\n",
            encoding="utf-8",
        )
        manifest = {
            "schemaVersion": 1,
            "packageName": "ide-development-managed-core",
            "packageVersion": "2.5.2",
            "files": [
                {
                    "id": "workflow-linktrend-integrator-merge-yml",
                    "ownershipClass": "managed-core",
                    "source": source_rel,
                    "sourceHash": digest,
                    "destination": ".ide-development/workflows/linktrend-integrator-merge.yml",
                    "mode": "0644",
                    "platform": "github",
                    "os": "all",
                    "mergeStrategy": "replace",
                },
                {
                    "id": "github-root-workflow-linktrend-integrator-merge-yml",
                    "ownershipClass": "managed-core",
                    "source": source_rel,
                    "sourceHash": digest,
                    "destination": FULL_ROOT_WORKFLOW_REL,
                    "mode": "0644",
                    "platform": "github",
                    "os": "all",
                    "mergeStrategy": "replace",
                },
            ],
        }
        (managed / "MANIFEST.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
        ci_contract = (
            self.package / "scripts" / "gitops" / "repository_ci_contract.py"
        )
        ci_contract.parent.mkdir(parents=True)
        shutil.copyfile(
            Path(__file__).resolve().parent
            / "fixtures"
            / "package_v2"
            / "scripts"
            / "gitops"
            / "repository_ci_contract.py",
            ci_contract,
        )

    def test_install_creates_read_only_compatible_root_workflow(self) -> None:
        result = run_install_or_update(
            target=self.target, package=self.package, command="install", dry_run=False
        )
        self.assertEqual(result.exit_code, EXIT_OK, result.payload)
        live = self.target / FULL_ROOT_WORKFLOW_REL
        packaged = self.target / ".ide-development/workflows/linktrend-integrator-merge.yml"
        self.assertTrue(live.is_file())
        self.assertTrue(packaged.is_file())
        text = live.read_text(encoding="utf-8")
        self.assertTrue(required_full_dispatch_inputs_present(text), text)
        self.assertTrue(is_read_only_mode(stat.S_IMODE(live.stat().st_mode)))
        state = load_installed_state(self.target)
        assert state is not None
        owned = state.files[FULL_ROOT_WORKFLOW_REL]
        self.assertEqual(owned.ownership_class, "managed-core")
        self.assertEqual(owned.mutability_policy, "read-only")

    def test_update_adopts_stale_unmanaged_root_workflow(self) -> None:
        first = run_install_or_update(
            target=self.target, package=self.package, command="install", dry_run=False
        )
        self.assertEqual(first.exit_code, EXIT_OK, first.payload)
        live = self.target / FULL_ROOT_WORKFLOW_REL
        os.chmod(live, 0o644)
        live.write_text(STALE_WORKFLOW, encoding="utf-8")
        os.chmod(live, 0o644)
        (self.target / ".ide-development" / "installed-state.json").unlink()
        result = run_install_or_update(
            target=self.target, package=self.package, command="install", dry_run=False
        )
        self.assertEqual(result.exit_code, EXIT_OK, result.payload)
        text = live.read_text(encoding="utf-8")
        self.assertTrue(required_full_dispatch_inputs_present(text), text)
        self.assertTrue(is_read_only_mode(stat.S_IMODE(live.stat().st_mode)))
        actions = {row["path"]: row for row in result.payload.get("actions", [])}
        self.assertEqual(actions[FULL_ROOT_WORKFLOW_REL]["op"], "replace")
        self.assertEqual(actions[FULL_ROOT_WORKFLOW_REL]["classification"], "obsolete_residue")

    def test_unrelated_unmanaged_workflow_still_conflicts(self) -> None:
        live = self.target / FULL_ROOT_WORKFLOW_REL
        live.parent.mkdir(parents=True)
        live.write_text("name: Consumer CI\non: push\njobs: {}\n", encoding="utf-8")
        result = run_install_or_update(
            target=self.target, package=self.package, command="install", dry_run=False
        )
        self.assertEqual(result.exit_code, EXIT_CONFLICT, result.payload)
        kinds = {item["path"]: item["kind"] for item in result.payload.get("conflicts", [])}
        self.assertEqual(kinds.get(FULL_ROOT_WORKFLOW_REL), "unknown_content")
        self.assertEqual(
            live.read_text(encoding="utf-8"), "name: Consumer CI\non: push\njobs: {}\n"
        )


if __name__ == "__main__":
    unittest.main()
