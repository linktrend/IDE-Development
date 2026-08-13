from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.gitops.coordinator import receipts
from scripts.gitops.promotion_receipt_gate import (
    canonical_digest,
    evaluate_automatic_main,
    evaluate_development_gates,
    evaluate_main_approval,
    evaluate_release_path,
    select_promotion_candidate,
    verify_receipt_file,
)


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True, check=True)
    return result.stdout.strip()


class PromotionReceiptGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.email", "w2-p3@example.com")
        git(self.repo, "config", "user.name", "W2 P3")
        git(self.repo, "remote", "add", "origin", "https://github.com/acme/promotion.git")
        (self.repo / "app.txt").write_text("one\n", encoding="utf-8")
        (self.repo / "deps.lock").write_text("dep-one\n", encoding="utf-8")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "initial")
        self.identity = receipts.compute_candidate_identity(self.repo, ["deps.lock"], "full")
        self.identity_path = self.root / "identity.json"
        self.identity_path.write_text(json.dumps(self.identity.to_dict()), encoding="utf-8")
        self.receipt = self.root / "full-receipt.json"
        receipts.write_receipt(self._receipt(), self.receipt)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _receipt(self, **changes: object) -> dict[str, object]:
        result: dict[str, object] = {
            "schemaVersion": 1,
            "status": "passed",
            "repository": self.identity.repository,
            "gate": "full-gate",
            "sourceSha": self.identity.source_sha,
            "testedCheckoutSha": self.identity.source_sha,
            "gitTreeSha": self.identity.git_tree_sha,
            "dependencyDigests": self.identity.dependency_digests,
            "testProfile": "full",
            "attempt": 1,
            "coordinatorVersion": "1.0.0",
            "startedAt": "2026-08-13T01:00:00Z",
            "completedAt": "2026-08-13T01:01:00Z",
            "evidenceDigests": {"evidence/full.log": "sha256:" + "b" * 64},
            "github": {"pullRequest": None, "runUrl": None},
        }
        result.update(changes)
        return result

    def test_missing_wrong_failed_and_exact_receipt(self) -> None:
        self.assertEqual(
            verify_receipt_file(self.root / "missing.json", repo_path=self.repo, dependencies=["deps.lock"]).code,
            "invalid_receipt",
        )
        self.assertEqual(
            verify_receipt_file(self.receipt, repo_path=self.repo, dependencies=["deps.lock"]).code,
            "accepted",
        )
        git(self.repo, "commit", "--allow-empty", "-qm", "different commit same content")
        self.assertEqual(
            verify_receipt_file(self.receipt, repo_path=self.repo, dependencies=["deps.lock"]).code,
            "accepted",
        )
        (self.repo / "app.txt").write_text("two\n", encoding="utf-8")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "one byte source change")
        self.assertEqual(
            verify_receipt_file(self.receipt, repo_path=self.repo, dependencies=["deps.lock"]).code,
            "tree_mismatch",
        )
        (self.repo / "app.txt").write_text("one\n", encoding="utf-8")
        git(self.repo, "add", "app.txt")
        git(self.repo, "commit", "-qm", "restore source content")
        (self.repo / "deps.lock").write_text("dep-two\n", encoding="utf-8")
        self.assertEqual(
            verify_receipt_file(self.receipt, repo_path=self.repo, dependencies=["deps.lock"]).code,
            "dependency_mismatch",
        )
        failed = self.root / "failed.json"
        receipts.write_receipt(self._receipt(status="failed"), failed) if False else failed.write_text(
            json.dumps(self._receipt(status="failed")), encoding="utf-8"
        )
        self.assertEqual(
            verify_receipt_file(failed, identity_path=self.identity_path).code,
            "receipt_not_passed",
        )

    def test_development_exact_gates_and_stale_negative(self) -> None:
        head = "a" * 40
        good = {"status": "passed", "sha": head}
        self.assertTrue(
            evaluate_development_gates(
                {"sealed": good, "fastGate": good, "bugbot": good, "fullSuite": {"status": "not-required"}},
                head,
            ).accepted
        )
        stale = dict(good, sha="b" * 40)
        self.assertEqual(
            evaluate_development_gates(
                {"sealed": good, "fastGate": stale, "bugbot": good, "fullSuite": good}, head
            ).code,
            "fast_stale",
        )

    def test_duplicate_approval_release_and_automatic_main(self) -> None:
        source, base, pr_head = "a" * 40, "b" * 40, "c" * 40
        receipt_payload = json.loads(self.receipt.read_text(encoding="utf-8"))
        approval = {
            "sourceSha": source,
            "baseSha": base,
            "prHeadSha": pr_head,
            "receiptDigest": canonical_digest(receipt_payload),
        }
        self.assertTrue(
            evaluate_main_approval(
                approval, source_sha=source, base_sha=base, pr_head_sha=pr_head, receipt=receipt_payload
            ).accepted
        )
        self.assertEqual(
            evaluate_main_approval(
                dict(approval, prHeadSha="d" * 40), source_sha=source, base_sha=base,
                pr_head_sha=pr_head, receipt=receipt_payload
            ).code,
            "stale_prHeadSha",
        )
        duplicate = select_promotion_candidate(
            [
                {"number": 9, "sourceSha": source, "targetSha": base, "headRefName": "promote/main/aaaaaaaaaaaa"},
                {"number": 4, "sourceSha": source, "targetSha": base, "headRefName": "promote/main/aaaaaaaaaaaa"},
            ], source_sha=source, target_sha=base, branch="promote/main/aaaaaaaaaaaa"
        )
        self.assertEqual(duplicate["reason"], "duplicate_promotion_candidates")
        self.assertEqual(evaluate_release_path({"status": "passed", "testProfile": "release", "fullSuiteInvoked": True}).code, "full_suite_reentered")
        self.assertTrue(
            evaluate_automatic_main(
                release={"status": "passed", "testProfile": "release", "fullSuiteInvoked": False},
                required_receipt=receipt_payload,
                candidate_identity=self.identity,
            ).accepted
        )


if __name__ == "__main__":
    unittest.main()
