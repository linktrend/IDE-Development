"""Focused tests for the OpenClaw Prime live-boundary admission path."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from gitops.secret_scan import scan_repository as packaged_scan_repository  # noqa: E402
from ide_development import engine as installer_engine  # noqa: E402
from ide_development.engine import _openclaw_admission  # noqa: E402
from ide_development.openclaw_customization_admission import (  # noqa: E402
    BOUNDARY_KIND,
    BOUNDARY_REL,
    KIND,
    SCHEMA_REL,
    OpenClawAdmissionError,
    admit_openclaw_customization,
)
from gitops.coordinator.receipts import (  # noqa: E402
    compute_candidate_identity,
    create_full_suite_receipt,
)

PRIME_COMMIT = "a" * 40
PRIME_TREE = "b" * 40
UPSTREAM_COMMIT = "c" * 40
UPSTREAM_TREE = "d" * 40
CUSTOM_PATH = "linkbots/lisa/ops/contract.md"
EXACT_PATH = "docs/agent-briefing.md"
IDE_PATH = ".ide-development/README.md"
TRANSACTION_PATH = "scripts/gitops/secret_scan.py"
FORBIDDEN_PATH = "src/gateway/server.ts"


def _boundary() -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "kind": BOUNDARY_KIND,
        "prime": {
            "repository": "linktrend/openclaw_prime",
            "ref": "main",
            "commit": PRIME_COMMIT,
            "tree": PRIME_TREE,
        },
        "upstream": {
            "repository": "openclaw/openclaw",
            "classificationPin": {
                "kind": "fork-network-merge-base-with-observed-parent-main",
                "commit": UPSTREAM_COMMIT,
                "tree": UPSTREAM_TREE,
            },
        },
        "exclusion": {
            "untouchedUpstream": {"enumerated": False, "rule": "omitted"},
            "forbiddenWholeTrees": ["src", "extensions"],
        },
        "linktrendOwned": {
            "prefixes": [
                {"path": "linkbots", "provenance": "this-manifest-namespace"},
                {"path": ".linktrend/openclaw-prime", "provenance": "this-manifest-namespace"},
            ],
            "exactPaths": [{"path": EXACT_PATH, "provenance": "this-manifest-namespace"}],
        },
        "ideManaged": {
            "separateFromLinktrendOwnedInventory": True,
            "inventoryPath": ".ide-development/installed-state.json",
            "packageName": "ide-development-managed-core",
            "packageVersion": "2.5.1",
            "destinationCount": 1,
            "prefixes": [".ide-development", "scripts/gitops"],
            "overlayOnUpstreamExactPaths": [],
            "declaredMissingLocally": [],
        },
        "ideTransactionChanged": {
            "separateFromIdeManagedInventory": True,
            "records": [{"receiptPath": "docs/receipt.json", "paths": [TRANSACTION_PATH]}],
            "paths": [TRANSACTION_PATH],
        },
        "uncertainty": [{"id": "test", "summary": "test"}],
    }


def _write_json(root: Path, rel: str, payload: Any) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


class OpenClawCustomizationAdmissionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmpdir.name)
        self.consumer = self.root / "consumer"
        self.consumer.mkdir()
        for rel in (CUSTOM_PATH, EXACT_PATH, IDE_PATH, TRANSACTION_PATH):
            path = self.consumer / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(rel + "\n", encoding="utf-8")
        _write_json(
            self.consumer,
            ".ide-development/installed-state.json",
            {"schemaVersion": 1, "packageVersion": "2.5.2", "files": {IDE_PATH: {}}},
        )
        self.boundary_path = _write_json(self.consumer, BOUNDARY_REL, _boundary())
        subprocess.run(["git", "init", "-q"], cwd=self.consumer, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=self.consumer, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=self.consumer, check=True)
        subprocess.run(["git", "remote", "add", "origin", "https://github.com/linktrend/openclaw_prime.git"], cwd=self.consumer, check=True)
        subprocess.run(["git", "add", "."], cwd=self.consumer, check=True)
        subprocess.run(["git", "commit", "-qm", "test target baseline"], cwd=self.consumer, check=True)
        self.target_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.consumer, text=True).strip()
        self.target_tree = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=self.consumer, text=True).strip()
        self.scanned: list[list[str]] = []

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def _scanner(self, result: dict[str, Any] | None = None):
        def scan(paths: list[str]) -> dict[str, Any]:
            self.scanned.append(list(paths))
            payload = copy.deepcopy(result) if result is not None else {"ok": True, "findings": []}
            payload.setdefault("candidateCommit", self.target_commit)
            payload.setdefault("candidateGitTree", self.target_tree)
            payload.setdefault("repository", "linktrend/openclaw_prime")
            payload.setdefault("scannerPolicyVersion", "secret-scan-policy/v1")
            return payload

        return scan

    def _admit(self, *, scanner=None, baseline=None, capture=None, full_run_receipt=None, package_root=None) -> dict[str, Any]:
        return admit_openclaw_customization(
            consumer_root=self.consumer,
            package_root=package_root or ROOT,
            boundary_path=self.boundary_path,
            scanner=scanner or self._scanner(),
            pre_install_baseline=baseline,
            capture_baseline=(baseline is None if capture is None else capture),
            full_run_receipt=full_run_receipt,
        )

    def _capture_baseline(self, *, scanner=None) -> dict[str, Any]:
        return self._admit(scanner=scanner)["preInstallBaseline"]

    def test_schema_is_present_and_managed(self) -> None:
        schema = json.loads((ROOT / SCHEMA_REL).read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["kind"]["const"], KIND)
        self.assertIn("prime", schema["properties"])
        self.assertIn("upstream", schema["properties"])
        self.assertIn("scope", schema["properties"])

    def test_live_boundary_kind_is_admitted_without_stale_manifest_digest(self) -> None:
        result = self._admit()
        schema = json.loads((ROOT / SCHEMA_REL).read_text(encoding="utf-8"))
        self.assertEqual(list(Draft202012Validator(schema).iter_errors(result)), [])
        self.assertEqual(result["verdict"], "admitted")
        self.assertEqual(result["prime"]["commit"], PRIME_COMMIT)
        self.assertEqual(
            result["upstream"]["classificationPin"]["tree"], UPSTREAM_TREE
        )
        self.assertEqual(result["boundary"]["kind"], BOUNDARY_KIND)

    def test_checked_paths_use_owned_and_declared_inventories_only(self) -> None:
        result = self._admit()
        checked = set(result["checkedPaths"])
        self.assertEqual(checked, {CUSTOM_PATH, EXACT_PATH, IDE_PATH, TRANSACTION_PATH, BOUNDARY_REL})
        self.assertEqual(set(self.scanned[0]), checked)
        self.assertNotIn(FORBIDDEN_PATH, checked)
        self.assertNotIn("core/unrelated-managed-destination.py", checked)

    def test_present_v252_package_destination_is_added_to_exact_scope(self) -> None:
        package = self.root / "package"
        package.mkdir()
        package_path = ".ide-development/package-changed.md"
        target_path = self.consumer / package_path
        target_path.write_text("package destination\n", encoding="utf-8")
        _write_json(package, "core/managed-core/MANIFEST.json", {
            "schemaVersion": 1,
            "packageName": "ide-development-managed-core",
            "packageVersion": "2.5.2",
            "files": [{"destination": package_path}],
        })
        result = self._admit(package_root=package)
        self.assertIn(package_path, result["checkedPaths"])
        self.assertIn(package_path, result["scope"]["ideManaged"]["packageChangedPaths"])

    def test_forged_forbidden_owned_path_is_rejected_before_scanning(self) -> None:
        forged = copy.deepcopy(_boundary())
        forged["linktrendOwned"]["exactPaths"].append(
            {"path": FORBIDDEN_PATH, "provenance": "this-manifest-namespace"}
        )
        self.boundary_path.write_text(json.dumps(forged) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(OpenClawAdmissionError, "forbidden-path"):
            self._admit()
        self.assertEqual(self.scanned, [])

    def test_forged_forbidden_transaction_path_is_rejected_before_scanning(self) -> None:
        forged = copy.deepcopy(_boundary())
        forged["ideTransactionChanged"]["paths"] = [FORBIDDEN_PATH]
        self.boundary_path.write_text(json.dumps(forged) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(OpenClawAdmissionError, "forbidden-path"):
            self._admit()
        self.assertEqual(self.scanned, [])

    def test_wrong_kind_is_not_reported_as_stale_manifest(self) -> None:
        forged = copy.deepcopy(_boundary())
        forged["kind"] = "openclaw-prime-customization-manifest"
        self.boundary_path.write_text(json.dumps(forged) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(OpenClawAdmissionError, "boundary-kind-mismatch"):
            self._admit()
        self.assertEqual(self.scanned, [])

    def test_new_finding_and_skipped_input_fail_closed(self) -> None:
        baseline = self._capture_baseline()
        for kind, expected in (("credential_finding", "new-or-changed-finding"), ("skipped_input", "new-skipped-input")):
            with self.subTest(kind=kind):
                with self.assertRaisesRegex(OpenClawAdmissionError, expected):
                    self._admit(
                        scanner=self._scanner(
                            {
                                "ok": False,
                                "findings": [
                                    {"kind": kind, "path": CUSTOM_PATH, "rule": "test.rule"}
                                ],
                            }
                        ),
                        baseline=baseline,
                    )

    def test_exact_pre_existing_finding_is_allowed_and_returned_as_object(self) -> None:
        finding = {"kind": "credential_finding", "path": CUSTOM_PATH, "rule": "test.rule"}
        baseline = self._capture_baseline(
            scanner=self._scanner({"ok": False, "findings": [finding]})
        )
        result = self._admit(
            scanner=self._scanner({"ok": False, "findings": [finding]}),
            baseline=baseline,
        )
        self.assertEqual(result["findings"][0]["kind"], finding["kind"])
        self.assertIn("contentDigest", result["findings"][0])
        self.assertEqual(result["preInstallBaseline"]["findings"][0]["kind"], finding["kind"])

    def test_missing_baseline_is_rejected_before_scanning(self) -> None:
        with self.assertRaisesRegex(OpenClawAdmissionError, "missing-baseline-identity"):
            self._admit(capture=False)

    def test_scanner_cannot_supply_its_own_baseline(self) -> None:
        with self.assertRaisesRegex(OpenClawAdmissionError, "scanner-error"):
            self._admit(scanner=self._scanner({"baselineFindings": []}))

    def test_full_receipt_is_passed_through_only_when_github_receipt_is_digest_valid(self) -> None:
        identity = compute_candidate_identity(
            self.consumer, [], "full", profile_files=[], workflow_files=[]
        )
        receipt = create_full_suite_receipt({
            "candidateIdentity": identity.to_dict(),
            "workflowRunId": 123,
            "workflowRunAttempt": 1,
            "runnerLabel": "ubuntu-24.04-arm",
            "startedAt": "2026-08-31T00:00:00Z",
            "completedAt": "2026-08-31T00:01:00Z",
            "conclusion": "success",
            "commandDigest": "sha256:" + "1" * 64,
            "evidenceDigests": {},
        }).to_dict()
        result = self._admit(full_run_receipt=receipt)
        self.assertEqual(result["fullRunReceiptIdentity"]["workflowRunId"], 123)
        self.assertEqual(result["fullRunReceiptIdentity"]["candidateIdentity"]["gitTree"], self.target_tree)

    def test_finding_outside_scope_is_rejected(self) -> None:
        with self.assertRaisesRegex(OpenClawAdmissionError, "out-of-scope-finding"):
            self._admit(scanner=self._scanner({"ok": False, "findings": [
                {"kind": "credential_finding", "path": "other.py", "rule": "x"}
            ]}))

    def test_missing_legacy_inputs_are_omitted_from_scan(self) -> None:
        missing = "core/legacy-package-path.py"
        boundary = copy.deepcopy(_boundary())
        boundary["ideManaged"]["declaredMissingLocally"] = ["core"]
        boundary["ideTransactionChanged"]["paths"].append(missing)
        self.boundary_path.write_text(json.dumps(boundary) + "\n", encoding="utf-8")
        result = self._admit()
        self.assertNotIn(missing, result["checkedPaths"])
        self.assertIn(missing, result["omittedMissingPaths"])
        self.assertIn("core", result["omittedMissingPaths"])

    def test_scanner_failure_and_timeout_fail_closed(self) -> None:
        with self.assertRaisesRegex(OpenClawAdmissionError, "scanner-error"):
            self._admit(scanner=self._scanner({"ok": False, "findings": []}))
        with self.assertRaisesRegex(OpenClawAdmissionError, "scanner-timeout"):
            self._admit(scanner=self._scanner({"ok": False, "errorType": "timeout", "findings": []}))

    def test_non_252_installed_state_is_rejected(self) -> None:
        state_path = self.consumer / ".ide-development/installed-state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["packageVersion"] = "2.5.0"
        state_path.write_text(json.dumps(state) + "\n", encoding="utf-8")
        with self.assertRaisesRegex(OpenClawAdmissionError, "ide-package-version-mismatch"):
            self._admit()

    def test_forbidden_scanner_finding_is_rejected(self) -> None:
        with self.assertRaisesRegex(OpenClawAdmissionError, "forbidden-path"):
            self._admit(
                scanner=self._scanner(
                    {"ok": False, "findings": [{"kind": "x", "path": FORBIDDEN_PATH, "rule": "x"}]}
                )
            )

    def test_official_installer_helper_calls_scoped_admission(self) -> None:
        seen: list[list[str]] = []

        class ScannerModule:
            @staticmethod
            def scan_repository(root: Path, *, paths: list[str]) -> dict[str, Any]:
                del root
                seen.append(list(paths))
                return {
                    "ok": True,
                    "findings": [],
                    "scannerPolicyVersion": "secret-scan-policy/v1",
                }

        with patch.object(installer_engine, "_load_secret_scan_module", return_value=ScannerModule):
            result = installer_engine._openclaw_admission(ROOT, self.consumer)
        self.assertEqual(result["verdict"], "admitted")
        self.assertEqual(seen, [result["checkedPaths"]])
        self.assertEqual(result["candidateIdentity"]["commit"], self.target_commit)
        self.assertEqual(result["candidateIdentity"]["tree"], self.target_tree)

    def test_real_packaged_scanner_admits_prime_shaped_consumer(self) -> None:
        captured: list[dict[str, Any]] = []

        def scanner(paths: list[str]) -> dict[str, Any]:
            result = packaged_scan_repository(self.consumer, paths=paths)
            captured.append(result)
            return result

        admitted = self._admit(scanner=scanner)
        self.assertEqual(admitted["verdict"], "admitted")
        self.assertEqual(admitted["candidateIdentity"]["commit"], self.target_commit)
        self.assertEqual(admitted["candidateIdentity"]["tree"], self.target_tree)
        self.assertEqual(admitted["baselineComparison"], "captured")
        self.assertNotIn("fullRunReceiptIdentity", admitted)
        self.assertEqual(len(captured), 1)
        scan = captured[0]
        self.assertEqual(scan["candidateCommit"], self.target_commit)
        self.assertEqual(scan["candidateGitTree"], self.target_tree)
        self.assertEqual(scan["repository"], "linktrend/openclaw_prime")
        self.assertNotIn("scanMode", scan)
        self.assertTrue(scan["ok"], scan)

    def test_official_installer_real_scanner_binds_head_identity(self) -> None:
        result = _openclaw_admission(ROOT, self.consumer)
        self.assertIsNotNone(result)
        self.assertEqual(result["verdict"], "admitted")
        self.assertEqual(result["candidateIdentity"]["commit"], self.target_commit)
        self.assertEqual(result["candidateIdentity"]["tree"], self.target_tree)
        self.assertNotIn("fullRunReceiptIdentity", result)


if __name__ == "__main__":
    unittest.main()
