"""Focused tests for the v2.5.2 post-release consumer compatibility ledger."""

from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.gitops.postrelease_compatibility_ledger import (
    FAIL_CONSUMER_HASH,
    FAIL_INCOMPLETE,
    evaluate_ledger,
    evaluate_ref,
)


ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = ROOT / "docs" / "evidence" / "v2.5.2-postrelease-compatibility"
LEDGER_PATH = EVIDENCE_DIR / "consumer-compatibility-ledger.json"
SCHEMA_PATH = EVIDENCE_DIR / "consumer-compatibility-ledger.schema.json"
RELEASED_HASH = "sha256:a40ef247933c1f3d8efb43f951ee5443a32c3c121e139d0c91d82ad8cd54c384"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class PostreleaseCompatibilityLedgerTests(unittest.TestCase):
    def test_recorded_ledger_matches_schema_and_fail_closed_evaluation(self) -> None:
        document = load_json(LEDGER_PATH)
        schema = load_json(SCHEMA_PATH)
        Draft202012Validator(schema).validate(document)
        verdict, reasons = evaluate_ledger(document)
        self.assertEqual(document["overallVerdict"], "fail_closed")
        self.assertEqual(verdict, "fail_closed")
        self.assertEqual(reasons, document["failClosedReasons"])
        self.assertIn(FAIL_CONSUMER_HASH, reasons)
        self.assertIn(FAIL_INCOMPLETE, reasons)
        released = document["releasedIdentity"]
        self.assertEqual(released["sourceCommit"], "5a64f7f03d3463804b424cc59c4ee048473d9a51")
        self.assertEqual(released["sourceTree"], "d2188157f2c32f5ba9c0cf6a5a60c7553cdce58a")
        self.assertEqual(released["manifestHash"], RELEASED_HASH)
        self.assertTrue(released["protectedMain"]["matchesReleasedIdentity"])
        sites = next(
            row for row in document["consumers"] if row["repository"] == "linktrend/LiNKsites"
        )
        self.assertEqual(sites["refs"]["development"]["status"], "mismatch")
        self.assertNotEqual(sites["refs"]["development"]["manifestHash"], RELEASED_HASH)

    def test_same_version_text_with_foreign_hash_is_mismatch(self) -> None:
        status = evaluate_ref(
            RELEASED_HASH,
            {
                "status": "match",
                "packageVersion": "2.5.2",
                "manifestHash": "sha256:b18da538fec322fc49989288d6aedeea92dd4e477ef1e65f222b9d44cbe54c61",
            },
        )
        self.assertEqual(status, "mismatch")

    def test_matching_development_receipt_is_match(self) -> None:
        status = evaluate_ref(
            RELEASED_HASH,
            {
                "status": "match",
                "packageVersion": "2.5.2",
                "manifestHash": RELEASED_HASH,
            },
        )
        self.assertEqual(status, "match")

    def test_all_matching_readable_portfolio_would_pass(self) -> None:
        document = load_json(LEDGER_PATH)
        patched = deepcopy(document)
        for consumer in patched["consumers"]:
            consumer["refs"]["development"] = {
                "status": "match",
                "commit": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
                "tree": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
                "packageVersion": "2.5.2",
                "manifestHash": RELEASED_HASH,
                "installedManifestSha256": RELEASED_HASH,
            }
        patched["overallVerdict"] = "match"
        patched["failClosedReasons"] = []
        verdict, reasons = evaluate_ledger(patched)
        self.assertEqual(verdict, "match")
        self.assertEqual(reasons, [])


if __name__ == "__main__":
    unittest.main()
