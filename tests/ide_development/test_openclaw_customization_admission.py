"""Focused tests for the OpenClaw Prime live-boundary admission path."""

from __future__ import annotations

import copy
import json
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
            {"schemaVersion": 1, "packageVersion": "2.5.1", "files": {IDE_PATH: {}}},
        )
        self.boundary_path = _write_json(self.consumer, BOUNDARY_REL, _boundary())
        self.scanned: list[list[str]] = []

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def _scanner(self, result: dict[str, Any] | None = None):
        def scan(paths: list[str]) -> dict[str, Any]:
            self.scanned.append(list(paths))
            return result or {"ok": True, "findings": []}

        return scan

    def _admit(self, *, scanner=None) -> dict[str, Any]:
        return admit_openclaw_customization(
            consumer_root=self.consumer,
            boundary_path=self.boundary_path,
            scanner=scanner or self._scanner(),
        )

    def test_schema_is_present_and_managed(self) -> None:
        schema = json.loads((ROOT / SCHEMA_REL).read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["kind"]["const"], KIND)
        self.assertIn("prime", schema["properties"])
        self.assertIn("upstream", schema["properties"])
        self.assertIn("scope", schema["properties"])

    def test_live_boundary_kind_is_admitted_without_stale_manifest_digest(self) -> None:
        result = self._admit()
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
                        )
                    )

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
            @staticmethod
            def scan_repository(root: Path, *, paths: list[str]) -> dict[str, Any]:
                del root
                seen.append(list(paths))
                return {"ok": True, "findings": []}

        with patch.object(engine, "_load_secret_scan_module", return_value=ScannerModule):
            result = engine._openclaw_admission(ROOT, self.consumer)
        self.assertEqual(result["verdict"], "admitted")
        self.assertEqual(seen, [result["checkedPaths"]])


if __name__ == "__main__":
    unittest.main()
