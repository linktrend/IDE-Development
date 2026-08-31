"""Focused fail-closed tests for generated-only exact-head evidence-rebind."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from jsonschema import Draft202012Validator

from scripts.gitops.coordinator import receipts
from scripts.gitops.evidence_rebind import (
    admit_evidence_rebind,
    issue_evidence_rebind_receipt,
    new_rebind_state,
    persist_rebind_state,
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
from scripts.gitops.promotion_receipt_gate import verify_receipt_file
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
ROOT = Path(__file__).resolve().parents[2]


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


def checks(head: str, tree: str = sha(4)) -> dict[str, object]:
    return {
        "fast": {"conclusion": "success", "headCommit": head, "gitTree": tree},
        "secret-scan": {"conclusion": "success", "headCommit": head, "gitTree": tree},
    }


def scanner(head: str, tree: str = sha(4)) -> dict[str, object]:
    return {"conclusion": "success", "headCommit": head, "gitTree": tree}


from scripts.gitops import evidence_rebind as evidence_rebind_module

_REAL_COMMIT_TREE = evidence_rebind_module.git_commit_tree
_REAL_CHANGED_PATHS = evidence_rebind_module.git_changed_paths


def fake_commit_tree(_repo: Path, commit: str) -> tuple[str, str]:
    fake_trees = {sha(1): sha(3), sha(2): sha(4), HEAD_A: TREE_A, HEAD_B: TREE_B}
    if commit in fake_trees:
        return commit, fake_trees[commit]
    return _REAL_COMMIT_TREE(_repo, commit)


def fake_changed_paths(repo: Path, source: str, head: str) -> tuple[str, ...]:
    if repo == ROOT:
        return (GENERATED,)
    return _REAL_CHANGED_PATHS(repo, source, head)


_COMMIT_TREE_PATCH = mock.patch(
    "scripts.gitops.evidence_rebind.git_commit_tree", side_effect=fake_commit_tree
)
_CHANGED_PATHS_PATCH = mock.patch(
    "scripts.gitops.evidence_rebind.git_changed_paths", side_effect=fake_changed_paths
)
_COMMIT_TREE_PATCH.start()
_CHANGED_PATHS_PATCH.start()


def tearDownModule() -> None:
    _CHANGED_PATHS_PATCH.stop()
    _COMMIT_TREE_PATCH.stop()


def issue_from_kwargs(kwargs: dict[str, object]) -> dict[str, object]:
    return issue_evidence_rebind_receipt(
        kwargs["source_full_receipt"],
        repo_root=ROOT,
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
        durable_state=kwargs.get("durable_state") or new_rebind_state(),
    )


def admit_kwargs(**overrides: object) -> dict[str, object]:
    source = sha(1)
    head = sha(2)
    source_tree = sha(3)
    head_tree = sha(4)
    payload = {
        "repo_root": ROOT,
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
        "durable_state": new_rebind_state(),
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

    def test_raw_success_strings_and_missing_exact_trees_are_rejected(self) -> None:
        raw_checks = admit_evidence_rebind(
            **admit_kwargs(
                narrow_hosted_checks={"fast": "success", "secret-scan": "success"}
            )
        )
        self.assertFalse(raw_checks.allowed)
        self.assertEqual(raw_checks.code, "narrow_checks_failed")
        missing_tree = admit_evidence_rebind(
            **admit_kwargs(
                delta_review={"valid": True, "headSha": sha(2), "paths": [GENERATED]}
            )
        )
        self.assertFalse(missing_tree.allowed)
        self.assertEqual(missing_tree.code, "delta_review_missing")
        missing_scan_tree = admit_evidence_rebind(
            **admit_kwargs(scanner={"conclusion": "success", "headCommit": sha(2)})
        )
        self.assertFalse(missing_scan_tree.allowed)
        self.assertEqual(missing_scan_tree.code, "scanner_failure")

    def test_generated_paths_must_match_repository_policy(self) -> None:
        decision = admit_evidence_rebind(**admit_kwargs(generated_paths=["src/app.py"]))
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.code, "generated_policy_mismatch")

    def test_caller_changed_paths_cannot_hide_a_trusted_non_generated_change(self) -> None:
        with mock.patch(
            "scripts.gitops.evidence_rebind.git_changed_paths", return_value=("src/app.py",)
        ):
            decision = admit_evidence_rebind(**admit_kwargs(changed_paths=[GENERATED]))
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.code, "non_generated_file")

    def test_caller_changed_paths_cannot_hide_a_real_git_tree_change(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "tests@example.invalid"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "evidence tests"], cwd=repo, check=True)
            graph_path = repo / "core/managed-core/config/generated-output-closure.json"
            graph_path.parent.mkdir(parents=True)
            shutil.copy(ROOT / "core/managed-core/config/generated-output-closure.json", graph_path)
            (repo / ".github").mkdir()
            (repo / ".github/linktrend-secret-scan-fixtures.json").write_text("before\n", encoding="utf-8")
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "source"], cwd=repo, check=True)
            source = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
            source_tree = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=repo, text=True).strip()
            (repo / ".github/linktrend-secret-scan-fixtures.json").write_text("after\n", encoding="utf-8")
            (repo / "src").mkdir()
            (repo / "src/app.py").write_text("changed\n", encoding="utf-8")
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "candidate"], cwd=repo, check=True)
            head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
            head_tree = subprocess.check_output(["git", "rev-parse", "HEAD^{tree}"], cwd=repo, text=True).strip()
            kwargs = admit_kwargs(
                source_commit=source,
                source_tree=source_tree,
                exact_head_commit=head,
                exact_head_tree=head_tree,
                changed_paths=[GENERATED],
                delta_review=review_payload(head, head_tree, [GENERATED]),
                narrow_hosted_checks=checks(head, head_tree),
                scanner=scanner(head, head_tree),
                source_full_receipt=full_receipt(head=source, tree=source_tree),
                repo_root=repo,
            )
            decision = admit_evidence_rebind(**kwargs)
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.code, "non_generated_file")

    def test_receipt_verification_requires_supplied_exact_evidence(self) -> None:
        kwargs = admit_kwargs()
        signed = issue_from_kwargs(kwargs)
        target = dict(kwargs["source_full_receipt"]["candidateIdentity"])
        target.update({"headCommit": signed["exactHeadCommit"], "gitTree": signed["exactHeadTree"]})
        decision = verify_evidence_rebind_receipt(
            signed,
            kwargs["source_full_receipt"],
            target,
            repo_root=ROOT,
            delta_review=None,
            narrow_hosted_checks=None,
            scanner=None,
            durable_state=kwargs["durable_state"],
        )
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.code, "evidence_missing")

    def test_second_rebind_for_same_underlying_source_is_a_loop(self) -> None:
        first = issue_from_kwargs(admit_kwargs())
        stopped = admit_evidence_rebind(
            **admit_kwargs(
                durable_state={
                    "evidenceRebinds": [{"receiptDigest": first["receiptDigest"]}],
                    "evidenceRebindCount": 1,
                    "schemaVersion": 1,
                    "kind": "evidence-rebind-state",
                    "verifiedEvidenceRebinds": [],
                }
            )
        )
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
        state_path = Path(tempfile.mkdtemp()) / "rebind-state.json"
        persist_rebind_state(state_path, kwargs["durable_state"])
        mismatch = receipts.verify_receipt(source_receipt, target, "full-gate")
        self.assertEqual(mismatch.code, "tree_mismatch")
        reused = receipts.verify_receipt(
            source_receipt,
            target,
            "full-gate",
            evidence_rebind_receipt=signed,
            workflow_head_commit=signed["exactHeadCommit"],
            repository_root=ROOT,
            evidence_rebind_delta_review=kwargs["delta_review"],
            evidence_rebind_hosted_checks=kwargs["narrow_hosted_checks"],
            evidence_rebind_scanner=kwargs["scanner"],
            evidence_rebind_state_path=state_path,
        )
        self.assertTrue(reused.accepted, reused.message)
        self.assertEqual(reused.source_commit, signed["sourceCommit"])
        self.assertEqual(reused.promotion_commit, signed["exactHeadCommit"])
        replay = receipts.verify_receipt(
            source_receipt,
            target,
            "full-gate",
            evidence_rebind_receipt=signed,
            workflow_head_commit=signed["exactHeadCommit"],
            repository_root=ROOT,
            evidence_rebind_delta_review=kwargs["delta_review"],
            evidence_rebind_hosted_checks=kwargs["narrow_hosted_checks"],
            evidence_rebind_scanner=kwargs["scanner"],
            evidence_rebind_state_path=state_path,
        )
        self.assertEqual(replay.code, "evidence_rebind_rejected")
        self.assertIn("receipt_replay", replay.message)
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
        signed = issue_from_kwargs(kwargs)
        forged = dict(signed)
        forged["changedPaths"] = ["src/app.py"]
        target = dict(source_receipt["candidateIdentity"])
        target["headCommit"] = signed["exactHeadCommit"]
        target["gitTree"] = signed["exactHeadTree"]
        digest = verify_evidence_rebind_receipt(
            forged,
            source_receipt,
            target,
            repo_root=ROOT,
            delta_review=kwargs["delta_review"],
            narrow_hosted_checks=kwargs["narrow_hosted_checks"],
            scanner=kwargs["scanner"],
            durable_state=kwargs["durable_state"],
        )
        self.assertFalse(digest.allowed)
        self.assertEqual(digest.code, "stale_identity")

    def test_promotion_verification_persists_state_and_rejects_receipt_replay(self) -> None:
        kwargs = admit_kwargs()
        signed = issue_from_kwargs(kwargs)
        target = dict(kwargs["source_full_receipt"]["candidateIdentity"])
        target.update({"headCommit": signed["exactHeadCommit"], "gitTree": signed["exactHeadTree"]})
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            receipt_path = directory / "full.json"
            identity_path = directory / "identity.json"
            rebind_path = directory / "rebind.json"
            review_path = directory / "review.json"
            checks_path = directory / "checks.json"
            scanner_path = directory / "scanner.json"
            state_path = directory / "state.json"
            for path, payload in (
                (receipt_path, kwargs["source_full_receipt"]),
                (identity_path, target),
                (rebind_path, signed),
                (review_path, kwargs["delta_review"]),
                (checks_path, kwargs["narrow_hosted_checks"]),
                (scanner_path, kwargs["scanner"]),
            ):
                path.write_text(json.dumps(payload), encoding="utf-8")
            persist_rebind_state(state_path, kwargs["durable_state"])
            verify_kwargs = {
                "identity_path": identity_path,
                "repo_path": ROOT,
                "evidence_rebind_receipt_path": rebind_path,
                "evidence_rebind_delta_review_path": review_path,
                "evidence_rebind_hosted_checks_path": checks_path,
                "evidence_rebind_scanner_path": scanner_path,
                "evidence_rebind_state_path": state_path,
                "workflow_head_commit": signed["exactHeadCommit"],
            }
            accepted = verify_receipt_file(receipt_path, **verify_kwargs)
            replay = verify_receipt_file(receipt_path, **verify_kwargs)
            persisted = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertTrue(accepted.accepted, accepted.detail)
        self.assertEqual(replay.code, "evidence_rebind_rejected")
        self.assertIn(signed["receiptDigest"], persisted["verifiedEvidenceRebinds"])

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
        state_path = Path(tempfile.mkdtemp()) / "rebind-state.json"
        persist_rebind_state(state_path, kwargs["durable_state"])
        ok = phase_merge_eligibility_with_receipt(
            record,
            live_head_sha=head,
            retained_receipt=source_receipt,
            expected_tree=tree,
            evidence_rebind_receipt=signed,
            repository_root=ROOT,
            evidence_rebind_delta_review=kwargs["delta_review"],
            evidence_rebind_hosted_checks=kwargs["narrow_hosted_checks"],
            evidence_rebind_scanner=kwargs["scanner"],
            evidence_rebind_state_path=state_path,
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
            repo_root=ROOT,
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
            narrow_hosted_checks=checks(HEAD_B, TREE_B),
            scanner=scanner(HEAD_B, TREE_B),
        )
        self.assertTrue(rebound["valid"])
        self.assertEqual(rebound["execution"], "hosted")
        self.assertEqual(rebound["priorHeadSha"], HEAD_A)
        self.assertTrue(rebound["reusedForUnchangedPaths"])
        self.assertEqual(len(session.full_runs), 1)
        self.assertEqual(session.to_dict()["evidenceRebindCount"], 1)
        schema = json.loads(
            (ROOT / "core/managed-core/schemas/review-session.schema.json").read_text(
                encoding="utf-8"
            )
        )
        errors = list(Draft202012Validator(schema).iter_errors(session.to_dict()))
        self.assertEqual(errors, [])
        with self.assertRaises(ConvergenceError) as raised:
            rebind_full_evidence(
                session,
                repo_root=ROOT,
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
                narrow_hosted_checks=checks(HEAD_B, TREE_B),
                scanner=scanner(HEAD_B, TREE_B),
            )
        self.assertEqual(raised.exception.code, "receipt_loop_detected")

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
            with mock.patch(
                "scripts.gitops.evidence_rebind.git_changed_paths", return_value=("src/authz.py",)
            ):
                rebind_full_evidence(
                    session,
                    repo_root=ROOT,
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
                    narrow_hosted_checks=checks(HEAD_B, TREE_B),
                    scanner=scanner(HEAD_B, TREE_B),
                )
        self.assertIn(raised.exception.code, {"non_generated_file", "owned_path_changed"})


if __name__ == "__main__":
    unittest.main()
