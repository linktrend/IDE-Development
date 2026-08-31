"""Focused fail-closed tests for generated-only exact-head evidence-rebind."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.gitops.coordinator import receipts
from scripts.gitops.evidence_rebind import (
    admit_evidence_rebind,
    create_evidence_rebind_receipt,
    issue_evidence_rebind_receipt,
    verify_evidence_rebind_receipt,
)
from scripts.gitops.independent_review_convergence import (
    ConvergenceError,
    ingest_delta_review,
    record_focused_changed_path_checks,
    rebind_full_evidence,
    record_full_evidence,
)
from scripts.gitops.receipt_seal import phase_merge_eligibility_with_receipt
from scripts.tests.test_independent_review_convergence import (
    HEAD_A,
    HEAD_B,
    TREE_A,
    TREE_B,
    apply_repair,
    consolidate_repair_batch,
    finding,
    open_default,
    review,
)


UNDERLYING = "sha256:" + "1" * 64
DEP = "sha256:" + "d" * 64
PROFILE = "sha256:" + "a" * 64
WORKFLOW = "sha256:" + "b" * 64
GENERATED = ".github/linktrend-secret-scan-fixtures.json"


def sha(number: int) -> str:
    return f"{number:040x}"


def full_receipt(*, head: str, tree: str) -> dict[str, object]:
    return receipts.create_full_suite_receipt(
        {
            "candidateIdentity": {
                "repository": "acme/ide",
                "sourceBranch": "phase/next",
                "headCommit": head,
                "gitTree": tree,
                "dependencyDigest": DEP,
                "profileDigest": PROFILE,
                "workflowDigest": WORKFLOW,
            },
            "workflowRunId": 44,
            "workflowRunAttempt": 1,
            "runnerLabel": "ubuntu-24.04-arm",
            "startedAt": "2026-08-31T01:00:00Z",
            "completedAt": "2026-08-31T01:01:00Z",
            "conclusion": "success",
            "commandDigest": "sha256:" + "c" * 64,
            "evidenceDigests": {"evidence/full.log": "sha256:" + "e" * 64},
        }
    ).to_dict()


def review_payload(head: str, tree: str, paths: list[str] | None = None) -> dict[str, object]:
    return {
        "valid": True,
        "headSha": head,
        "gitTree": tree,
        "paths": paths or [GENERATED],
    }


def checks(head: str) -> dict[str, object]:
    return {
        "fast": {"conclusion": "success", "headCommit": head},
        "secret-scan": {"conclusion": "success", "headCommit": head},
    }


def scanner(head: str) -> dict[str, object]:
    return {"conclusion": "success", "headCommit": head}


def issue_from_kwargs(kwargs: dict[str, object]) -> dict[str, object]:
    return issue_evidence_rebind_receipt(
        kwargs["source_full_receipt"],
        exact_head_commit=kwargs["exact_head_commit"],
        exact_head_tree=kwargs["exact_head_tree"],
        changed_paths=kwargs["changed_paths"],
        generated_paths=kwargs["generated_paths"],
        owned_paths=kwargs.get("owned_paths") or (),
        underlying_source_digest_source=kwargs["underlying_source_digest_source"],
        underlying_source_digest_head=kwargs["underlying_source_digest_head"],
        dependency_digest_source=kwargs["dependency_digest_source"],
        dependency_digest_head=kwargs["dependency_digest_head"],
        profile_digest_source=kwargs["profile_digest_source"],
        profile_digest_head=kwargs["profile_digest_head"],
        workflow_digest_source=kwargs["workflow_digest_source"],
        workflow_digest_head=kwargs["workflow_digest_head"],
        delta_review=kwargs["delta_review"],
        narrow_hosted_checks=kwargs["narrow_hosted_checks"],
        scanner=kwargs["scanner"],
        history=kwargs.get("history") or (),
    )


def admit_kwargs(**overrides: object) -> dict[str, object]:
    source = sha(1)
    head = sha(2)
    source_tree = sha(3)
    head_tree = sha(4)
    payload = {
        "source_commit": source,
        "source_tree": source_tree,
        "exact_head_commit": head,
        "exact_head_tree": head_tree,
        "changed_paths": [GENERATED],
        "generated_paths": [GENERATED],
        "owned_paths": ["src/app.py"],
        "underlying_source_digest_source": UNDERLYING,
        "underlying_source_digest_head": UNDERLYING,
        "dependency_digest_source": DEP,
        "dependency_digest_head": DEP,
        "profile_digest_source": PROFILE,
        "profile_digest_head": PROFILE,
        "workflow_digest_source": WORKFLOW,
        "workflow_digest_head": WORKFLOW,
        "delta_review": review_payload(head, head_tree),
        "narrow_hosted_checks": checks(head),
        "scanner": scanner(head),
        "source_full_receipt": full_receipt(head=source, tree=source_tree),
        "history": (),
    }
    payload.update(overrides)
    return payload


class EvidenceRebindAdmissionTests(unittest.TestCase):
    def test_generated_only_delta_is_admitted_once(self) -> None:
        decision = admit_evidence_rebind(**admit_kwargs())
        self.assertTrue(decision.allowed, decision.detail)
        self.assertEqual(decision.code, "evidence_rebind_allowed")
        self.assertEqual(decision.changed_paths, (GENERATED,))

    def test_product_source_or_dependency_or_owned_path_fail_closed(self) -> None:
        cases = (
            ("product_source_changed", {"underlying_source_digest_head": "sha256:" + "2" * 64}),
            ("dependency_changed", {"dependency_digest_head": "sha256:" + "9" * 64}),
            ("owned_path_changed", {"changed_paths": [GENERATED], "owned_paths": [GENERATED]}),
            ("non_generated_file", {"changed_paths": ["src/app.py"]}),
        )
        for code, overrides in cases:
            with self.subTest(code=code):
                decision = admit_evidence_rebind(**admit_kwargs(**overrides))
                self.assertFalse(decision.allowed)
                self.assertEqual(decision.code, code)

    def test_missing_review_stale_identity_and_scanner_fail_closed(self) -> None:
        missing_review = admit_evidence_rebind(**admit_kwargs(delta_review={"valid": False}))
        self.assertEqual(missing_review.code, "delta_review_missing")
        stale = admit_evidence_rebind(**admit_kwargs(source_commit=sha(9)))
        self.assertEqual(stale.code, "stale_identity")
        scan = admit_evidence_rebind(**admit_kwargs(scanner={"conclusion": "failure", "headCommit": sha(2)}))
        self.assertEqual(scan.code, "scanner_failure")
        narrow = admit_evidence_rebind(**admit_kwargs(narrow_hosted_checks={"fast": "success"}))
        self.assertEqual(narrow.code, "narrow_checks_failed")

    def test_second_rebind_for_same_underlying_source_is_a_loop(self) -> None:
        first = issue_from_kwargs(admit_kwargs())
        stopped = admit_evidence_rebind(**admit_kwargs(history=[first]))
        self.assertFalse(stopped.allowed)
        self.assertEqual(stopped.code, "receipt_loop_detected")


class EvidenceRebindReceiptTests(unittest.TestCase):
    def test_signed_receipt_reuses_full_without_tree_equality(self) -> None:
        kwargs = admit_kwargs()
        source_receipt = kwargs["source_full_receipt"]
        signed = issue_from_kwargs(kwargs)
        self.assertEqual(signed["kind"], "evidence-rebind-receipt")
        self.assertEqual(signed["authenticatedBy"], "delivery-controller")
        self.assertNotEqual(signed["sourceTree"], signed["exactHeadTree"])
        target = dict(source_receipt["candidateIdentity"])
        target["headCommit"] = signed["exactHeadCommit"]
        target["gitTree"] = signed["exactHeadTree"]
        mismatch = receipts.verify_receipt(source_receipt, target, "full-gate")
        self.assertEqual(mismatch.code, "tree_mismatch")
        reused = receipts.verify_receipt(
            source_receipt,
            target,
            "full-gate",
            evidence_rebind_receipt=signed,
            workflow_head_commit=signed["exactHeadCommit"],
        )
        self.assertTrue(reused.accepted, reused.message)
        self.assertEqual(reused.source_commit, signed["sourceCommit"])
        self.assertEqual(reused.promotion_commit, signed["exactHeadCommit"])
        both = receipts.verify_receipt(
            source_receipt,
            target,
            "full-gate",
            transition_receipt={"kind": "transition-receipt"},
            evidence_rebind_receipt=signed,
        )
        self.assertEqual(both.code, "transition_invalid")

    def test_tampered_digest_and_non_generated_receipt_reject(self) -> None:
        kwargs = admit_kwargs()
        source_receipt = kwargs["source_full_receipt"]
        signed = create_evidence_rebind_receipt(
            source_receipt,
            exact_head_commit=kwargs["exact_head_commit"],
            exact_head_tree=kwargs["exact_head_tree"],
            underlying_source_digest=UNDERLYING,
            changed_paths=[GENERATED],
            generated_paths=[GENERATED],
            delta_review=kwargs["delta_review"],
            narrow_hosted_checks=kwargs["narrow_hosted_checks"],
            scanner=kwargs["scanner"],
        )
        forged = dict(signed)
        forged["changedPaths"] = ["src/app.py"]
        target = dict(source_receipt["candidateIdentity"])
        target["headCommit"] = signed["exactHeadCommit"]
        target["gitTree"] = signed["exactHeadTree"]
        digest = verify_evidence_rebind_receipt(forged, source_receipt, target)
        self.assertFalse(digest.allowed)
        self.assertEqual(digest.code, "stale_identity")

    def test_phase_merge_accepts_rebind_and_rejects_wrong_head_without_it(self) -> None:
        kwargs = admit_kwargs()
        source_receipt = kwargs["source_full_receipt"]
        signed = issue_from_kwargs(kwargs)
        head = signed["exactHeadCommit"]
        tree = signed["exactHeadTree"]
        record = {
            "sealed": True,
            "sealedSha": head,
            "headSha": head,
            "candidateIdentity": {"sourceSha": head, "gitTreeSha": tree},
            "fast": {"status": "passed", "sha": head},
            "bugbot": {"status": "passed", "sha": head},
            "full": {"status": "passed", "sha": head},
        }
        blocked = phase_merge_eligibility_with_receipt(
            record, live_head_sha=head, retained_receipt=source_receipt, expected_tree=tree
        )
        self.assertFalse(blocked.eligible)
        self.assertIn("retained_receipt_wrong_head", blocked.detail)
        ok = phase_merge_eligibility_with_receipt(
            record,
            live_head_sha=head,
            retained_receipt=source_receipt,
            expected_tree=tree,
            evidence_rebind_receipt=signed,
        )
        self.assertTrue(ok.eligible, ok.detail)

    def test_schema_is_additional_properties_false(self) -> None:
        schema = json.loads(
            (Path(__file__).resolve().parents[2] / "core/managed-core/schemas/evidence-rebind-receipt.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["kind"]["const"], "evidence-rebind-receipt")
        index = (Path(__file__).resolve().parents[2] / "core/managed-core/INDEX.yaml").read_text(encoding="utf-8")
        self.assertIn("schemas/evidence-rebind-receipt.schema.json", index)


class EvidenceRebindConvergenceTests(unittest.TestCase):
    def test_generated_delta_reuses_full_without_a_second_full_run(self) -> None:
        session, entries, _clock = open_default(require_full_before_review=True)
        review(session, entries, [finding("fixture", paths=[GENERATED])])
        record_full_evidence(session, head_sha=HEAD_A)
        source_receipt = full_receipt(head=HEAD_A, tree=TREE_A)
        self.assertEqual(len(session.full_runs), 1)
        consolidate_repair_batch(session, entries)
        apply_repair(session, entries, new_head=HEAD_B, new_tree=TREE_B, touched_paths=[GENERATED])
        self.assertFalse(session.full_evidence["valid"])
        record_focused_changed_path_checks(
            session,
            head_sha=HEAD_B,
            git_tree=TREE_B,
            changed_paths=[GENERATED],
            results=[{"path": GENERATED, "status": "success"}],
        )
        ingest_delta_review(
            session,
            entries,
            {"headSha": HEAD_B, "gitTree": TREE_B, "findings": [], "changedPaths": [GENERATED]},
            actor=session.reviewer_actor,
            role="reviewer",
            changed_paths=[GENERATED],
            accepted_unchanged_evidence={
                "valid": True,
                "sourceHeadSha": HEAD_A,
                "paths": ["src/app.py"],
            },
        )
        rebound = rebind_full_evidence(
            session,
            source_head_sha=HEAD_A,
            exact_head_sha=HEAD_B,
            exact_git_tree=TREE_B,
            changed_paths=[GENERATED],
            generated_paths=[GENERATED],
            owned_paths=["src/app.py"],
            underlying_source_digest_source=UNDERLYING,
            underlying_source_digest_head=UNDERLYING,
            dependency_digest=DEP,
            profile_digest=PROFILE,
            workflow_digest=WORKFLOW,
            source_full_receipt=source_receipt,
            narrow_hosted_checks=checks(HEAD_B),
            scanner=scanner(HEAD_B),
        )
        self.assertTrue(rebound["valid"])
        self.assertFalse(rebound["fullSuiteRerun"])
        self.assertEqual(rebound["reusedFromSourceHead"], HEAD_A)
        self.assertEqual(len(session.full_runs), 1)

    def test_product_repair_cannot_rebind_full_evidence(self) -> None:
        session, entries, _clock = open_default(require_full_before_review=True)
        review(session, entries, [finding("authz")])
        record_full_evidence(session, head_sha=HEAD_A)
        source_receipt = full_receipt(head=HEAD_A, tree=TREE_A)
        consolidate_repair_batch(session, entries)
        apply_repair(session, entries, new_head=HEAD_B, new_tree=TREE_B, touched_paths=["src/authz.py"])
        record_focused_changed_path_checks(
            session,
            head_sha=HEAD_B,
            git_tree=TREE_B,
            changed_paths=["src/authz.py"],
            results=[{"path": "src/authz.py", "status": "success"}],
        )
        ingest_delta_review(
            session,
            entries,
            {"headSha": HEAD_B, "gitTree": TREE_B, "findings": [], "changedPaths": ["src/authz.py"]},
            actor=session.reviewer_actor,
            role="reviewer",
            changed_paths=["src/authz.py"],
            accepted_unchanged_evidence={
                "valid": True,
                "sourceHeadSha": HEAD_A,
                "paths": ["src/other.py"],
            },
        )
        with self.assertRaises(ConvergenceError) as raised:
            rebind_full_evidence(
                session,
                source_head_sha=HEAD_A,
                exact_head_sha=HEAD_B,
                exact_git_tree=TREE_B,
                changed_paths=["src/authz.py"],
                generated_paths=[GENERATED],
                owned_paths=["src/authz.py"],
                underlying_source_digest_source=UNDERLYING,
                underlying_source_digest_head=UNDERLYING,
                dependency_digest=DEP,
                profile_digest=PROFILE,
                workflow_digest=WORKFLOW,
                source_full_receipt=source_receipt,
                narrow_hosted_checks=checks(HEAD_B),
                scanner=scanner(HEAD_B),
            )
        self.assertIn(raised.exception.code, {"non_generated_file", "owned_path_changed"})


if __name__ == "__main__":
    unittest.main()
