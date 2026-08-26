"""v2.5 lean Issue checkpoint acceptance and proof-class boundaries."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.execution.protocol import WAIVED_LEGACY_GATE
from scripts.gitops.issue_checkpoint import (
    IssueCheckpointError,
    bind_issue_completion,
    hosted_validation_record,
    parse_immutable_evidence_payload,
)


COMMIT = "a" * 40
TREE = "b" * 40


def lean_payload(**overrides):
    payload = {
        "schemaVersion": 1,
        "kind": "v25-issue-checkpoint",
        "amendment": "V25_BOOTSTRAP_LEAN",
        "headSha": COMMIT,
        "gitTree": TREE,
        "pushed": True,
        "scopedDiff": True,
        "focusedTests": {"passed": True},
        "independentTerraVerification": True,
        "manifestEvidence": True,
        "proofClass": "local",
        "classification": "tests",
        "acceptance": "PKT-05 lean checkpoint",
        "commands": [{"cmd": "python3 -m unittest", "exitCode": 0}],
    }
    payload.update(overrides)
    return payload


class IssueCheckpointTests(unittest.TestCase):
    def test_workflow_style_import_uses_installed_protocol_without_core(self) -> None:
        with tempfile.TemporaryDirectory(prefix="issue-checkpoint-managed-") as raw:
            root = Path(raw)
            (root / "scripts/gitops").mkdir(parents=True)
            (root / ".ide-development/execution").mkdir(parents=True)
            shutil.copy2(
                ROOT / "scripts/gitops/issue_checkpoint.py",
                root / "scripts/gitops/issue_checkpoint.py",
            )
            shutil.copy2(
                ROOT / "scripts/gitops/github_auth.py",
                root / "scripts/gitops/github_auth.py",
            )
            shutil.copy2(
                ROOT / "core/execution/protocol.py",
                root / ".ide-development/execution/protocol.py",
            )
            code = (
                "import sys; sys.path.insert(0, 'scripts/gitops'); "
                "import issue_checkpoint as checkpoint; "
                "assert checkpoint.AMENDMENT_ID == 'V25_BOOTSTRAP_LEAN'; "
                "assert checkpoint.evaluate_issue_checkpoint is not None"
            )
            env = os.environ.copy()
            env.pop("PYTHONPATH", None)
            result = subprocess.run(
                [sys.executable, "-c", code],
                cwd=root,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_lean_evidence_accepts_without_review_ready_or_token(self) -> None:
        ok, detail, meta = bind_issue_completion(
            sha=COMMIT,
            tree=TREE,
            evidence=lean_payload(),
            review_ready_state="missing",
            automation_token_present=False,
        )
        self.assertTrue(ok)
        self.assertEqual(detail, "v25_bootstrap_lean_issue_checkpoint")
        self.assertFalse(meta["requiresReviewReady"] if "requiresReviewReady" in meta else False)
        self.assertEqual(meta["legacyClassification"], WAIVED_LEGACY_GATE)
        self.assertFalse(meta["legacyPublisher"]["isPass"])

    def test_review_ready_status_alone_is_waived_not_accepted(self) -> None:
        ok, detail, meta = bind_issue_completion(
            sha=COMMIT,
            tree=TREE,
            evidence=None,
            review_ready_state="success",
        )
        self.assertFalse(ok)
        self.assertEqual(detail, "evidence_missing")
        self.assertEqual(meta["legacyClassification"], WAIVED_LEGACY_GATE)
        self.assertFalse(meta["legacyPublisher"]["isPass"])

    def test_legacy_success_status_cannot_bypass_missing_scoped_diff(self) -> None:
        ok, detail, meta = bind_issue_completion(
            sha=COMMIT,
            tree=TREE,
            evidence=lean_payload(scopedDiff=False),
            review_ready_state="success",
            automation_token_present=True,
        )
        self.assertFalse(ok)
        self.assertEqual(detail, "scoped_diff_required")
        self.assertFalse(meta["legacyPublisher"]["isPass"])
        self.assertEqual(meta["legacyClassification"], WAIVED_LEGACY_GATE)

    def test_explicit_payload_is_immutable_and_sha_bound(self) -> None:
        raw = json.dumps(lean_payload())
        parsed = parse_immutable_evidence_payload(raw)
        self.assertEqual(parsed["headSha"], COMMIT)
        ok, _detail, _meta = bind_issue_completion(
            sha="c" * 40,
            tree=TREE,
            evidence=parsed,
        )
        self.assertFalse(ok)

    def test_local_proof_cannot_be_represented_as_hosted(self) -> None:
        with self.assertRaises(IssueCheckpointError) as raised:
            hosted_validation_record(
                sha=COMMIT,
                tree=TREE,
                payload=lean_payload(proofClass="local"),
                proof_class="hosted",
            )
        self.assertEqual(raised.exception.code, "local_proof_cannot_be_hosted")
        hosted = hosted_validation_record(
            sha=COMMIT,
            tree=TREE,
            payload=lean_payload(proofClass="hosted"),
            proof_class="hosted",
        )
        self.assertTrue(hosted["ok"])
        self.assertEqual(hosted["payloadOrigin"], "out_of_tree")
        self.assertTrue(hosted["hostedValidation"])
        self.assertFalse(hosted["productionProof"] or hosted["proofClass"] == "local")

    def test_unknown_kind_is_rejected_and_cannot_pass_via_legacy_status(self) -> None:
        ok, detail, meta = bind_issue_completion(
            sha=COMMIT,
            tree=TREE,
            evidence=lean_payload(kind="review-ready-status", scopedDiff=False),
            review_ready_state="success",
        )
        self.assertFalse(ok)
        self.assertEqual(detail, "scoped_diff_required")
        ok, detail, meta = bind_issue_completion(
            sha=COMMIT,
            tree=TREE,
            evidence={"schemaVersion": 1, "kind": "publisher-status", "headSha": COMMIT},
            review_ready_state="success",
        )
        self.assertFalse(ok)
        self.assertEqual(detail, "evidence_kind_unsupported")
        self.assertFalse(meta["legacyPublisher"]["isPass"])
