from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.gitops.coordinator import receipts
from scripts.gitops.promotion_receipt_gate import (
    ReceiptError,
    bind_authenticated_transition_evidence,
    canonical_digest,
    evaluate_automatic_main,
    evaluate_development_gates,
    evaluate_main_approval,
    evaluate_release_path,
    select_promotion_candidate,
    verify_receipt_file,
)


COMMAND_DIGEST = "sha256:" + ("c" * 64)


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
        git(self.repo, "config", "user.email", "w1-p3@example.com")
        git(self.repo, "config", "user.name", "W1 P3")
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
            "schemaVersion": 2,
            "candidateIdentity": self.identity.to_dict(),
            "workflowRunId": 301,
            "workflowRunAttempt": 1,
            "runnerLabel": "ubuntu-24.04-arm",
            "startedAt": "2026-08-13T01:00:00Z",
            "completedAt": "2026-08-13T01:01:00Z",
            "conclusion": "success",
            "commandDigest": COMMAND_DIGEST,
            "evidenceDigests": {"evidence/full.log": "sha256:" + ("b" * 64)},
        }
        result.update(changes)
        return result

    def test_missing_exact_reuse_and_negative_content_matrix(self) -> None:
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
            "head_mismatch",
        )
        (self.repo / "app.txt").write_text("two\n", encoding="utf-8")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "source change")
        self.assertEqual(
            verify_receipt_file(self.receipt, repo_path=self.repo, dependencies=["deps.lock"]).code,
            "tree_mismatch",
        )
        (self.repo / "app.txt").write_text("one\n", encoding="utf-8")
        git(self.repo, "add", "app.txt")
        git(self.repo, "commit", "-qm", "restore source")
        (self.repo / "deps.lock").write_text("dep-two\n", encoding="utf-8")
        self.assertEqual(
            verify_receipt_file(self.receipt, repo_path=self.repo, dependencies=["deps.lock"]).code,
            "dependency_mismatch",
        )

        legacy = self.root / "legacy.json"
        legacy.write_text(json.dumps(self._receipt(schemaVersion=1)), encoding="utf-8")
        self.assertEqual(verify_receipt_file(legacy, identity_path=self.identity_path).code, "unsupported_version")

    def test_run_profile_command_and_workflow_context_is_required_when_supplied(self) -> None:
        self.assertEqual(
            verify_receipt_file(
                self.receipt,
                identity_path=self.identity_path,
                workflow_run_id=302,
            ).code,
            "run_mismatch",
        )
        self.assertEqual(
            verify_receipt_file(
                self.receipt,
                identity_path=self.identity_path,
                workflow_run_attempt=2,
            ).code,
            "attempt_mismatch",
        )
        self.assertEqual(
            verify_receipt_file(
                self.receipt,
                identity_path=self.identity_path,
                expected_command_digest="sha256:" + ("d" * 64),
            ).code,
            "command_mismatch",
        )
        self.assertEqual(
            verify_receipt_file(
                self.receipt,
                identity_path=self.identity_path,
                expected_workflow_digest="sha256:" + ("d" * 64),
            ).code,
            "workflow_mismatch",
        )

    def test_development_release_approval_and_lineage_are_machine_readable(self) -> None:
        head = "a" * 40
        good = {"status": "passed", "sha": head}
        decision = evaluate_development_gates(
            {"sealed": good, "fastGate": good, "fullSuite": {"status": "not-required"}},
            head,
        )
        self.assertTrue(decision.accepted)
        self.assertEqual(decision.to_dict()["status"], "PASS")
        stale = dict(good, sha="b" * 40)
        self.assertEqual(
            evaluate_development_gates({"sealed": good, "fastGate": stale, "fullSuite": good}, head).code,
            "fast_stale",
        )
        self.assertEqual(
            evaluate_release_path({"status": "passed", "testProfile": "release", "fullSuiteInvoked": True}).code,
            "full_suite_reentered",
        )

        receipt_payload = json.loads(self.receipt.read_text(encoding="utf-8"))
        source, base, pr_head = "a" * 40, "b" * 40, "c" * 40
        approval = {
            "sourceSha": source,
            "baseSha": base,
            "prHeadSha": pr_head,
            "receiptDigest": receipt_payload["receiptDigest"],
        }
        self.assertTrue(
            evaluate_main_approval(
                approval,
                source_sha=source,
                base_sha=base,
                pr_head_sha=pr_head,
                receipt=receipt_payload,
            ).accepted
        )
        self.assertEqual(
            evaluate_main_approval(
                dict(approval, receiptDigest=canonical_digest({"tampered": True})),
                source_sha=source,
                base_sha=base,
                pr_head_sha=pr_head,
                receipt=receipt_payload,
            ).code,
            "receipt_mismatch",
        )
        self.assertEqual(
            select_promotion_candidate(
                [
                    {"number": 9, "sourceSha": source, "targetSha": base, "headRefName": "promote/main/aaaaaaaaaaaa"},
                    {"number": 4, "sourceSha": source, "targetSha": base, "headRefName": "promote/main/aaaaaaaaaaaa"},
                ],
                source_sha=source,
                target_sha=base,
                branch="promote/main/aaaaaaaaaaaa",
            )["reason"],
            "duplicate_promotion_candidates",
        )

        automatic = evaluate_automatic_main(
            release={"status": "passed", "testProfile": "release", "fullSuiteInvoked": False},
            required_receipt=receipt_payload,
            candidate_identity=self.identity,
            workflow_run_id=301,
            workflow_run_attempt=1,
            runner_label="ubuntu-24.04-arm",
        )
        self.assertTrue(automatic.accepted)
        self.assertIn(self.identity.head_commit, automatic.detail)
        self.assertEqual(automatic.source_commit, self.identity.head_commit)
        self.assertEqual(automatic.promotion_commit, self.identity.head_commit)
        self.assertEqual(automatic.to_dict()["status"], "PASS")
        self.assertIn("receiptLookupKey", automatic.to_dict())

    def test_protected_merge_reuses_full_receipt_only_with_canonical_transition(self) -> None:
        old_commit = self.identity.head_commit
        git(self.repo, "commit", "--allow-empty", "-qm", "protected merge")
        new_commit = git(self.repo, "rev-parse", "HEAD")
        self.assertNotEqual(old_commit, new_commit)
        self.assertEqual(
            verify_receipt_file(self.receipt, repo_path=self.repo, dependencies=["deps.lock"]).code,
            "head_mismatch",
        )
        transition = receipts.create_transition_receipt(
            json.loads(self.receipt.read_text(encoding="utf-8")),
            target_branch="development",
            target_commit=new_commit,
            target_tree=self.identity.git_tree,
        )
        transition_path = self.root / "transition.json"
        transition_path.write_text(json.dumps(transition.to_dict()), encoding="utf-8")
        accepted = verify_receipt_file(
            self.receipt,
            repo_path=self.repo,
            dependencies=["deps.lock"],
            transition_receipt_path=transition_path,
            expected_transition_digest=transition.receipt_digest,
            source_branch="development",
            workflow_run_id=301,
            workflow_run_attempt=1,
        )
        self.assertTrue(accepted.accepted, accepted.detail)
        self.assertEqual(accepted.promotion_commit, new_commit)

        forged = dict(transition.to_dict(), receiptDigest="sha256:" + ("a" * 64))
        forged_path = self.root / "forged.json"
        forged_path.write_text(json.dumps(forged), encoding="utf-8")
        self.assertEqual(
            verify_receipt_file(
                self.receipt,
                repo_path=self.repo,
                dependencies=["deps.lock"],
                transition_receipt_path=forged_path,
                expected_transition_digest=transition.receipt_digest,
                source_branch="development",
            ).code,
            "transition_digest_mismatch",
        )
        self.assertEqual(
            verify_receipt_file(
                self.receipt,
                repo_path=self.repo,
                dependencies=["deps.lock"],
                expected_transition_digest=transition.receipt_digest,
                source_branch="development",
            ).code,
            "transition_invalid",
        )

        completed = subprocess.run(
            [
                "python3",
                str(Path(__file__).resolve().parents[1] / "gitops" / "promotion_receipt_gate.py"),
                "verify",
                "--receipt",
                str(self.receipt),
                "--repo",
                str(self.repo),
                "--dependency",
                "deps.lock",
                "--transition-receipt",
                str(transition_path),
                "--expected-transition-digest",
                transition.receipt_digest,
                "--source-branch",
                "development",
                "--workflow-run-id",
                "301",
                "--workflow-run-attempt",
                "1",
                "--gate",
                "full-gate",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        payload = json.loads(completed.stdout)
        self.assertTrue(payload["accepted"])

    def test_authenticated_transition_channel_rejects_adversarial_evidence(self) -> None:
        transition = receipts.create_transition_receipt(
            json.loads(self.receipt.read_text(encoding="utf-8")),
            target_branch="development",
            target_commit=self.identity.head_commit,
            target_tree=self.identity.git_tree,
        )
        digest = transition.receipt_digest
        ref = receipts.transition_git_ref(digest)
        good = {
            "channel": "github.git.ref",
            "repository": self.identity.repository,
            "ref": ref,
            "objectType": "blob",
            "expired": False,
            "payload": transition.to_dict(),
        }
        loaded = bind_authenticated_transition_evidence(
            good,
            expected_digest=digest,
            expected_repository=self.identity.repository,
            expected_commit=self.identity.head_commit,
            expected_target_branch="development",
        )
        self.assertEqual(loaded["receiptDigest"], digest)

        with self.assertRaises(ReceiptError) as missing:
            bind_authenticated_transition_evidence(
                {"channel": "github.git.ref", "candidates": []},
                expected_digest=digest,
                expected_repository=self.identity.repository,
            )
        self.assertEqual(missing.exception.code, "transition_invalid")

        with self.assertRaises(ReceiptError) as expired:
            bind_authenticated_transition_evidence(
                dict(good, expired=True),
                expected_digest=digest,
                expected_repository=self.identity.repository,
            )
        self.assertEqual(expired.exception.code, "transition_expired")

        with self.assertRaises(ReceiptError) as ambiguous:
            bind_authenticated_transition_evidence(
                {"channel": "github.git.ref", "candidates": [good, dict(good)]},
                expected_digest=digest,
                expected_repository=self.identity.repository,
            )
        self.assertEqual(ambiguous.exception.code, "transition_ambiguous")

        with self.assertRaises(ReceiptError) as wrong_repo:
            bind_authenticated_transition_evidence(
                dict(good, repository="evil/fork"),
                expected_digest=digest,
                expected_repository=self.identity.repository,
            )
        self.assertEqual(wrong_repo.exception.code, "transition_identity_mismatch")

        with self.assertRaises(ReceiptError) as forged:
            bind_authenticated_transition_evidence(
                dict(good, payload=dict(transition.to_dict(), targetCommit="a" * 40)),
                expected_digest=digest,
                expected_repository=self.identity.repository,
            )
        self.assertEqual(forged.exception.code, "transition_digest_mismatch")

        raced = subprocess.run(
            [
                "python3",
                str(Path(__file__).resolve().parents[1] / "gitops" / "promotion_receipt_gate.py"),
                "bind-transition",
                "--evidence",
                str(self.root / "missing.json"),
                "--expected-digest",
                digest,
                "--expected-repository",
                self.identity.repository,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertNotEqual(raced.returncode, 0)


if __name__ == "__main__":
    unittest.main()
