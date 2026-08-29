"""Focused P4 receipt transition and loop-prevention tests."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.gitops.coordinator import receipts
from scripts.gitops import delivery_controller as controller
from scripts.gitops.receipt_loop_detector import admit_receipt_maintenance_transition
from scripts.tests.test_delivery_controller import (
    _gates,
    _handoff,
    _identity as controller_identity,
    _named_checks,
    _receipt as controller_receipt,
    _repository_ci,
    _sha as controller_sha,
)


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def sha(number: int) -> str:
    return f"{number:040x}"


class P4TransitionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q")
        git(self.repo, "config", "user.email", "p4@example.com")
        git(self.repo, "config", "user.name", "P4")
        git(self.repo, "remote", "add", "origin", "https://github.com/acme/p4.git")
        (self.repo / "app.txt").write_text("same tree\n", encoding="utf-8")
        (self.repo / "deps.lock").write_text("dependency-one\n", encoding="utf-8")
        git(self.repo, "add", ".")
        git(self.repo, "commit", "-qm", "candidate")
        self.identity = receipts.compute_candidate_identity(self.repo, ["deps.lock"], "full")
        self.receipt = receipts.create_full_suite_receipt(
            {
                "candidateIdentity": self.identity.to_dict(),
                "workflowRunId": 9001,
                "workflowRunAttempt": 2,
                "runnerLabel": "ubuntu-24.04-arm",
                "startedAt": "2026-08-28T01:00:00Z",
                "completedAt": "2026-08-28T01:01:00Z",
                "conclusion": "success",
                "commandDigest": "sha256:" + "c" * 64,
                "evidenceDigests": {"evidence/full.log": "sha256:" + "e" * 64},
            }
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_same_tree_transition_is_the_only_commit_change_reuse_seam(self) -> None:
        old_commit = self.identity.head_commit
        git(self.repo, "commit", "--allow-empty", "-qm", "protected merge identity")
        new_commit = git(self.repo, "rev-parse", "HEAD")
        self.assertNotEqual(old_commit, new_commit)
        self.assertEqual(self.identity.git_tree, git(self.repo, "rev-parse", "HEAD^{tree}"))
        target = receipts.CandidateIdentity(
            self.identity.repository,
            "development",
            new_commit,
            self.identity.git_tree,
            self.identity.dependency_digest,
            self.identity.profile_digest,
            self.identity.workflow_digest,
        )
        transition = receipts.create_transition_receipt(
            self.receipt,
            target_branch="development",
            target_commit=new_commit,
            target_tree=target.git_tree,
        )
        self.assertTrue(receipts.verify_receipt(self.receipt, target, "full-gate").code == "head_mismatch")
        accepted = receipts.verify_receipt(
            self.receipt,
            target,
            "full-gate",
            transition_receipt=transition,
            workflow_run_id=9001,
            workflow_run_attempt=2,
        )
        self.assertTrue(accepted.accepted, accepted.message)
        self.assertEqual(accepted.promotion_commit, new_commit)
        self.assertEqual(transition.source_receipt_digest, self.receipt.receipt_digest)

        stale = receipts.verify_receipt(
            self.receipt,
            target,
            "full-gate",
            transition_receipt=transition,
            workflow_run_id=9002,
        )
        self.assertEqual(stale.code, "run_mismatch")

    def test_changed_tree_lock_profile_and_workflow_reject_transition_reuse(self) -> None:
        new_commit = sha(20)
        transition = receipts.create_transition_receipt(
            self.receipt,
            target_branch="development",
            target_commit=new_commit,
            target_tree=self.identity.git_tree,
        )
        for field, value, expected_code in (
            ("git_tree", sha(21), "tree_mismatch"),
            ("dependency_digest", "sha256:" + "1" * 64, "dependency_mismatch"),
            ("profile_digest", "sha256:" + "2" * 64, "profile_mismatch"),
            ("workflow_digest", "sha256:" + "3" * 64, "workflow_mismatch"),
        ):
            with self.subTest(field=field):
                values = self.identity.to_dict()
                wire_field = {
                    "git_tree": "gitTree",
                    "dependency_digest": "dependencyDigest",
                    "profile_digest": "profileDigest",
                    "workflow_digest": "workflowDigest",
                }[field]
                values[wire_field] = value
                values["headCommit"] = new_commit
                target = receipts.CandidateIdentity.from_dict(values)
                verdict = receipts.verify_receipt(
                    self.receipt,
                    target,
                    transition_receipt=transition,
                )
                self.assertEqual(verdict.code, expected_code)
        with self.assertRaises(receipts.ReceiptError) as error:
            receipts.create_transition_receipt(
                self.receipt,
                target_branch="development",
                target_commit=new_commit,
                target_tree=sha(22),
            )
        self.assertEqual(error.exception.code, "transition_tree_mismatch")

    def test_store_is_external_and_rejects_candidate_or_common_directories(self) -> None:
        store = self.root / "external-store"
        receipt_path = receipts.store_receipt(self.receipt, repo_path=self.repo, store_root=store)
        self.assertTrue(receipt_path.is_file())
        self.assertNotIn(self.repo, receipt_path.parents)
        self.assertNotIn((self.repo / ".git").resolve(), receipt_path.parents)
        transition = receipts.create_transition_receipt(
            self.receipt,
            target_branch="development",
            target_commit=sha(30),
            target_tree=self.identity.git_tree,
        )
        transition_path = receipts.store_transition_receipt(transition, repo_path=self.repo, store_root=store)
        self.assertTrue(transition_path.is_file())
        with self.assertRaises(receipts.ReceiptError) as error:
            receipts.store_receipt(self.receipt, repo_path=self.repo, store_root=self.repo / "evidence")
        self.assertEqual(error.exception.code, "receipt_store_invalid")
        common = (self.repo / git(self.repo, "rev-parse", "--git-common-dir")).resolve()
        with self.assertRaises(receipts.ReceiptError) as error:
            receipts.store_transition_receipt(transition, repo_path=self.repo, store_root=common / "evidence")
        self.assertEqual(error.exception.code, "receipt_store_invalid")

    def test_controller_issues_transition_and_promotion_reuses_full_receipt(self) -> None:
        head = controller_sha(1)
        tree = controller_sha(2)
        identity = controller_identity(head=head, tree=tree)
        receipt = controller_receipt(identity)
        handoff = _handoff(head=head, tree=tree)
        pr = {
            "number": 11,
            "isDraft": False,
            "state": "open",
            "head": "phase/next",
            "base": "development",
            "headSha": head,
            "mergeableState": "MERGEABLE",
        }
        github = controller.MemoryGitHub(repository="owner/name")
        github.prs[11] = dict(pr)
        github.refs.update({"development": controller_sha(8), "staging": controller_sha(7)})
        merged = controller.deliver_phase_to_development(
            github=github,
            repository="owner/name",
            handoff=handoff,
            pr=pr,
            live_head=head,
            live_tree=tree,
            gate_payload=_gates(head),
            named_checks=_named_checks(head),
            repository_ci=_repository_ci(head),
            receipt=receipt,
            candidate_identity=identity,
            role="operator",
        )
        self.assertEqual(merged["status"], "merged")
        transition = merged["transitionReceipt"]
        protected_head = merged["mergeCommitSha"]
        target_identity = dict(identity, sourceBranch="development", headCommit=protected_head)
        promoted = controller.promote_to_staging(
            github=github,
            repository="owner/name",
            development_sha=protected_head,
            staging_sha=controller_sha(7),
            candidate_sha=protected_head,
            candidate_tree=tree,
            receipt=receipt,
            candidate_identity=target_identity,
            release_gate={"status": "passed", "testProfile": "release"},
            transition_receipt=transition,
            role="operator",
        )
        self.assertTrue(promoted["receiptReused"])
        self.assertFalse(promoted["fullSuiteRerun"])


class P4MaintenanceLoopTests(unittest.TestCase):
    def setUp(self) -> None:
        self.identity = {
            "repository": "acme/p4",
            "sourceBranch": "phase/p4",
            "headCommit": sha(1),
            "gitTree": sha(2),
            "dependencyDigest": "sha256:" + "d" * 64,
            "profileDigest": "sha256:" + "a" * 64,
            "workflowDigest": "sha256:" + "b" * 64,
        }
        self.base = "sha256:" + "f" * 64

    def successor(self, number: int) -> dict[str, object]:
        return {
            "kind": "transition-receipt",
            "transitionType": "receipt-maintenance",
            "sourceIdentity": self.identity,
            "targetCommit": sha(number),
            "targetTree": self.identity["gitTree"],
            "maintenancePaths": ["scripts/gitops/receipt_seal.py"],
        }

    def test_one_maintenance_transition_allowed_second_is_structural_stop(self) -> None:
        first = self.successor(3)
        allowed = admit_receipt_maintenance_transition(
            self.identity,
            first,
            changed_paths=["scripts/gitops/receipt_seal.py"],
            authorized_paths=["scripts/gitops/receipt_seal.py"],
            current_protected_base=sha(9),
            expected_protected_base=sha(9),
            failure_contract_digest=self.base,
            predecessor_failure_contract_digest=self.base,
        )
        self.assertTrue(allowed.allowed, allowed.detail)
        second = self.successor(4)
        stopped = admit_receipt_maintenance_transition(
            first,
            second,
            history=[first],
            changed_paths=["scripts/gitops/receipt_seal.py"],
            authorized_paths=["scripts/gitops/receipt_seal.py"],
            current_protected_base=sha(9),
            expected_protected_base=sha(9),
            failure_contract_digest=self.base,
            predecessor_failure_contract_digest=self.base,
        )
        self.assertFalse(stopped.allowed)
        self.assertEqual(stopped.code, "receipt_loop_detected")
        self.assertEqual(stopped.successor_count, 2)

    def test_maintenance_requires_exact_scope_and_unchanged_failure_contract(self) -> None:
        successor = self.successor(3)
        out_of_scope = admit_receipt_maintenance_transition(
            self.identity,
            successor,
            changed_paths=["scripts/gitops/delivery_controller.py"],
            authorized_paths=["scripts/gitops/receipt_seal.py"],
        )
        self.assertEqual(out_of_scope.code, "maintenance_scope_invalid")
        changed_contract = admit_receipt_maintenance_transition(
            self.identity,
            successor,
            changed_paths=["scripts/gitops/receipt_seal.py"],
            authorized_paths=["scripts/gitops/receipt_seal.py"],
            failure_contract_digest=self.base,
            predecessor_failure_contract_digest="sha256:" + "0" * 64,
        )
        self.assertEqual(changed_contract.code, "failure_contract_changed")


if __name__ == "__main__":
    unittest.main()
