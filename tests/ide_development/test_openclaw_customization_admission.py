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

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from ide_development.openclaw_customization_admission import (  # noqa: E402
    BASELINE_KIND,
    BOUNDARY_KIND,
    BOUNDARY_REL,
    KIND,
    SCHEMA_REL,
    OpenClawAdmissionError,
    admit_openclaw_customization,
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
        subprocess.run(
            ["git", "config", "user.email", "test@example.invalid"],
            cwd=self.consumer,
            check=True,
        )
        subprocess.run(["git", "add", "."], cwd=self.consumer, check=True)
        subprocess.run(
            ["git", "commit", "-qm", "test target baseline"],
            cwd=self.consumer,
            check=True,
        )
        self.target_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD^{commit}"], cwd=self.consumer, text=True
        ).strip()
        self.target_tree = subprocess.check_output(
            ["git", "rev-parse", "HEAD^{tree}"], cwd=self.consumer, text=True
        ).strip()
        self.scanned: list[list[str]] = []

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def _scanner(self, result: dict[str, Any] | None = None):
        def scan(paths: list[str]) -> dict[str, Any]:
            self.scanned.append(list(paths))
            payload = dict(result or {"ok": True, "findings": []})
            payload.setdefault("candidateCommit", self.target_commit)
            payload.setdefault("candidateGitTree", self.target_tree)
            payload.setdefault("repository", "linktrend/openclaw_prime")
            payload.setdefault("scannerPolicyVersion", "secret-scan-policy/v1")
            return payload

        return scan

    def _admit(self, *, scanner=None, baseline=None, capture=None) -> dict[str, Any]:
        return admit_openclaw_customization(
            consumer_root=self.consumer,
            boundary_path=self.boundary_path,
            scanner=scanner or self._scanner(),
            pre_install_baseline=baseline,
            capture_baseline=baseline is None if capture is None else capture,
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
        self.assertEqual(result["verdict"], "admitted")
        self.assertEqual(result["baselineComparison"], "captured")
        self.assertEqual(result["preInstallBaseline"]["kind"], BASELINE_KIND)
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
        self.assertEqual(result["baselineComparison"], "compared")
        self.assertEqual(result["findings"][0]["kind"], finding["kind"])
        self.assertIn("contentDigest", result["findings"][0])

    def test_pre_existing_skipped_binary_is_allowed_only_when_bytes_are_unchanged(self) -> None:
        finding = {"kind": "skipped_input", "path": CUSTOM_PATH, "rule": "input.binary"}
        baseline = self._capture_baseline(scanner=self._scanner({"ok": False, "findings": [finding]}))
        result = self._admit(
            scanner=self._scanner({"ok": False, "findings": [finding]}),
            baseline=baseline,
        )
        self.assertEqual(result["findings"][0]["kind"], "skipped_input")

        (self.consumer / CUSTOM_PATH).write_text("changed\n", encoding="utf-8")
        with self.assertRaisesRegex(OpenClawAdmissionError, "new-skipped-input"):
            self._admit(
                scanner=self._scanner({"ok": False, "findings": [finding]}),
                baseline=baseline,
            )

    def test_missing_baseline_identity_is_rejected(self) -> None:
        baseline = self._capture_baseline()
        del baseline["identity"]["tree"]
        with self.assertRaisesRegex(OpenClawAdmissionError, "missing-baseline-identity"):
            self._admit(baseline=baseline, capture=False)

    def test_shape_valid_tampered_baseline_identity_is_rejected(self) -> None:
        baseline = self._capture_baseline()
        baseline["identity"]["commit"] = "f" * 40
        with self.assertRaisesRegex(OpenClawAdmissionError, "baseline-identity-mismatch"):
            self._admit(baseline=baseline)

    def test_shape_valid_changed_scanner_identity_is_rejected(self) -> None:
        baseline = self._capture_baseline()
        with self.assertRaisesRegex(OpenClawAdmissionError, "scanner-identity-mismatch"):
            self._admit(
                baseline=baseline,
                scanner=self._scanner(
                    {
                        "ok": True,
                        "findings": [],
                        "candidateCommit": "f" * 40,
                        "candidateGitTree": "e" * 40,
                    }
                ),
            )

    def test_missing_baseline_is_rejected_before_scanning(self) -> None:
        with self.assertRaisesRegex(OpenClawAdmissionError, "missing-baseline-identity"):
            self._admit(capture=False)

    def test_scanner_cannot_supply_its_own_baseline(self) -> None:
        with self.assertRaisesRegex(OpenClawAdmissionError, "scanner-error"):
            self._admit(scanner=self._scanner({"baselineFindings": []}))

    def test_finding_outside_scope_is_rejected(self) -> None:
        with self.assertRaisesRegex(OpenClawAdmissionError, "out-of-scope-finding"):
            self._admit(
                scanner=self._scanner(
                    {
                        "ok": False,
                        "findings": [
                            {
                                "kind": "skipped_input",
                                "path": "test/upstream.bin",
                                "rule": "input.binary",
                            }
                        ],
                    }
                )
            )

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
        from ide_development import engine

        seen: list[list[str]] = []

        class ScannerModule:
            candidate_commit = self.target_commit
            candidate_tree = self.target_tree

            @classmethod
            def scan_repository(cls, root: Path, *, paths: list[str]) -> dict[str, Any]:
                del root
                seen.append(list(paths))
                return {
                    "ok": True,
                    "findings": [],
                    "candidateCommit": cls.candidate_commit,
                    "candidateGitTree": cls.candidate_tree,
                    "repository": "linktrend/openclaw_prime",
                    "scannerPolicyVersion": "secret-scan-policy/v1",
                }

        with patch.object(engine, "_load_secret_scan_module", return_value=ScannerModule):
            result = engine._openclaw_admission(ROOT, self.consumer)
        self.assertEqual(result["verdict"], "admitted")
        self.assertEqual(seen, [result["checkedPaths"]])


if __name__ == "__main__":
    unittest.main()
