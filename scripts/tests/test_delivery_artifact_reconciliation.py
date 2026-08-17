"""Focused unit/negative/contract tests for WP-U08 delivery-artifact reconciliation."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.gitops.delivery_artifact_reconciliation import (
    ACTION_ALREADY_ABSENT,
    ACTION_CLEAN,
    ACTION_KEEP,
    ACTION_PRESERVE_FOR_DECISION,
    CLASS_EMPTY,
    CLASS_PARTIALLY_INTEGRATED,
    CLASS_PROTECTED,
    CLASS_TREE_EQUIVALENT_SUPERSEDED,
    CLASS_UNCOMMITTED,
    CLASS_UNIQUE_WORK,
    CLASS_UNKNOWN,
    KIND_BRANCH,
    KIND_PR,
    KIND_RUNTIME_RESIDUE,
    KIND_WORKTREE,
    OWNER_CONTROLLER,
    OWNER_WORKER,
    Artifact,
    IdentityUncertainty,
    InfrastructureError,
    classify_artifact,
    decide_action,
    default_mutator,
    reconcile,
    resolve_state_dir,
)


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=False)
    if result.returncode:
        raise AssertionError(result.stderr or result.stdout)
    return result.stdout.strip()


def sha(root: Path, spec: str = "HEAD") -> str:
    return git(root, "rev-parse", spec)


def tree(root: Path, spec: str = "HEAD^{tree}") -> str:
    return git(root, "rev-parse", spec)


def init_repo() -> tuple[tempfile.TemporaryDirectory[str], Path, str, str]:
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name) / "repo"
    root.mkdir()
    git(root, "init", "-q", "-b", "development")
    git(root, "config", "user.email", "u08@example.invalid")
    git(root, "config", "user.name", "WP-U08 tests")
    git(root, "config", "core.autocrlf", "false")
    (root / ".gitignore").write_text(".linktrend/\n", encoding="utf-8")
    (root / "base.txt").write_text("base\n", encoding="utf-8")
    git(root, "add", ".gitignore", "base.txt")
    git(root, "commit", "-qm", "base")
    return tmp, root, sha(root), tree(root)


def pr(
    *,
    name: str,
    head: str,
    tree_sha: str,
    base: str,
    base_tree: str,
    ahead: int,
    unique: tuple[str, ...] = (),
    integrated_paths: tuple[str, ...] = (),
    changed: tuple[str, ...] = (),
    integrated_trees: tuple[str, ...] = (),
    controller_owned: bool = True,
    owner: str = OWNER_CONTROLLER,
    uncommitted: bool = False,
    exists: bool = True,
) -> Artifact:
    return Artifact(
        id=f"pr:{name}",
        kind=KIND_PR,
        name=name,
        controller_owned=controller_owned,
        owner=owner,
        head_sha=head,
        tree_sha=tree_sha,
        base_sha=base,
        base_tree_sha=base_tree,
        integrated_trees=integrated_trees,
        changed_paths=changed or unique + integrated_paths,
        unique_paths=unique,
        integrated_paths=integrated_paths,
        uncommitted=uncommitted,
        commits_ahead=ahead,
        exists=exists,
    )


class ClassificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.base = "a" * 40
        self.base_tree = "b" * 40
        self.head = "c" * 40
        self.other_tree = "d" * 40
        self.integrated_tree = "e" * 40

    def test_distinguishes_empty_superseded_partial_and_unique(self) -> None:
        empty = classify_artifact(
            pr(
                name="empty-pr",
                head=self.base,
                tree_sha=self.base_tree,
                base=self.base,
                base_tree=self.base_tree,
                ahead=0,
            )
        )
        superseded = classify_artifact(
            pr(
                name="superseded-pr",
                head=self.head,
                tree_sha=self.integrated_tree,
                base=self.base,
                base_tree=self.base_tree,
                ahead=3,
                integrated_trees=(self.integrated_tree,),
            )
        )
        partial = classify_artifact(
            pr(
                name="partial-pr",
                head=self.head,
                tree_sha=self.other_tree,
                base=self.base,
                base_tree=self.base_tree,
                ahead=2,
                unique=("unique.txt",),
                integrated_paths=("landed.txt",),
            )
        )
        unique = classify_artifact(
            pr(
                name="unique-pr",
                head=self.head,
                tree_sha=self.other_tree,
                base=self.base,
                base_tree=self.base_tree,
                ahead=1,
                unique=("novel.txt",),
            )
        )
        self.assertEqual(empty.classification, CLASS_EMPTY)
        self.assertEqual(superseded.classification, CLASS_TREE_EQUIVALENT_SUPERSEDED)
        self.assertEqual(partial.classification, CLASS_PARTIALLY_INTEGRATED)
        self.assertEqual(unique.classification, CLASS_UNIQUE_WORK)

    def test_uncommitted_and_missing_identity_are_preserved(self) -> None:
        dirty = Artifact(
            id="wt:dirty",
            kind=KIND_WORKTREE,
            name="issue/1-dirty",
            controller_owned=True,
            owner=OWNER_CONTROLLER,
            head_sha=self.head,
            tree_sha=self.other_tree,
            base_sha=self.base,
            base_tree_sha=self.base_tree,
            uncommitted=True,
            commits_ahead=0,
        )
        unknown = Artifact(
            id="pr:unknown",
            kind=KIND_PR,
            name="issue/2-unknown",
            controller_owned=True,
            owner=OWNER_CONTROLLER,
        )
        protected = Artifact(
            id="branch:main",
            kind=KIND_BRANCH,
            name="main",
            controller_owned=True,
            owner=OWNER_CONTROLLER,
            head_sha=self.base,
            tree_sha=self.base_tree,
            base_sha=self.base,
            base_tree_sha=self.base_tree,
            commits_ahead=0,
        )
        self.assertEqual(classify_artifact(dirty).classification, CLASS_UNCOMMITTED)
        self.assertEqual(classify_artifact(unknown).classification, CLASS_UNKNOWN)
        self.assertEqual(classify_artifact(protected).classification, CLASS_PROTECTED)
        self.assertEqual(decide_action(dirty, classify_artifact(dirty)), ACTION_PRESERVE_FOR_DECISION)
        self.assertEqual(decide_action(unknown, classify_artifact(unknown)), ACTION_PRESERVE_FOR_DECISION)
        self.assertEqual(decide_action(protected, classify_artifact(protected)), ACTION_KEEP)

    def test_worker_and_unowned_empty_artifacts_are_never_cleaned(self) -> None:
        worker = pr(
            name="issue/9-worker",
            head=self.base,
            tree_sha=self.base_tree,
            base=self.base,
            base_tree=self.base_tree,
            ahead=0,
            controller_owned=False,
            owner=OWNER_WORKER,
        )
        unowned = pr(
            name="issue/8-mystery",
            head=self.base,
            tree_sha=self.base_tree,
            base=self.base,
            base_tree=self.base_tree,
            ahead=0,
            controller_owned=False,
            owner="unknown",
        )
        self.assertEqual(classify_artifact(worker).classification, CLASS_EMPTY)
        self.assertEqual(decide_action(worker, classify_artifact(worker)), ACTION_PRESERVE_FOR_DECISION)
        self.assertEqual(decide_action(unowned, classify_artifact(unowned)), ACTION_PRESERVE_FOR_DECISION)

    def test_unique_work_has_no_keep_or_delete_choice(self) -> None:
        unique = pr(
            name="issue/4-unique",
            head=self.head,
            tree_sha=self.other_tree,
            base=self.base,
            base_tree=self.base_tree,
            ahead=1,
            unique=("novel.txt",),
        )
        action = decide_action(unique, classify_artifact(unique))
        self.assertEqual(action, ACTION_PRESERVE_FOR_DECISION)
        self.assertNotEqual(action, ACTION_CLEAN)
        self.assertNotEqual(action, ACTION_KEEP)


class ReconciliationRepoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp, self.root, self.base, self.base_tree = init_repo()
        self.addCleanup(self.tmp.cleanup)

    def test_success_cleans_root_residue_and_transients(self) -> None:
        residue = self.root / "gitops-outcome.json"
        residue.write_text('{"status":"packaged"}\n', encoding="utf-8")
        report = reconcile(repo=self.root, artifacts=[], apply=False)
        self.assertTrue(report["ok"])
        self.assertFalse(residue.exists())
        self.assertEqual(report["rootResidue"], [])
        self.assertEqual(report["checkoutDirty"], [])
        state = Path(report["stateDir"])
        self.assertEqual(state, resolve_state_dir(self.root))
        self.assertTrue((state / "reconciliation-report.json").is_file())
        self.assertFalse((state / "outcome.json").exists())
        self.assertFalse((state / "run.json").exists())
        self.assertFalse((state / "failure-diagnostics.json").exists())
        porcelain = git(self.root, "status", "--porcelain")
        self.assertEqual(porcelain, "")

    def test_failure_retains_diagnostics_in_state_dir_not_repo_root(self) -> None:
        residue = self.root / "gitops-outcome.json"
        residue.write_text('{"status":"failed"}\n', encoding="utf-8")
        with self.assertRaises(InfrastructureError):
            reconcile(repo=self.root, artifacts=[], apply=False, force_failure="boom")
        self.assertFalse(residue.exists())
        state = resolve_state_dir(self.root)
        self.assertTrue((state / "failure-diagnostics.json").is_file())
        self.assertTrue((state / "outcome.json").is_file())
        retained = state / "retained-root-residue" / "gitops-outcome.json"
        self.assertTrue(retained.is_file())
        outcome = json.loads((state / "outcome.json").read_text(encoding="utf-8"))
        self.assertEqual(outcome["status"], "failed")
        porcelain = git(self.root, "status", "--porcelain")
        self.assertEqual(porcelain, "")

    def test_apply_cleans_controller_owned_empty_and_superseded_only(self) -> None:
        git(self.root, "branch", "controller/empty")
        git(self.root, "checkout", "-qb", "controller/superseded")
        (self.root / "gone.txt").write_text("later integrated\n", encoding="utf-8")
        git(self.root, "add", "gone.txt")
        git(self.root, "commit", "-qm", "superseded content")
        superseded_head = sha(self.root)
        superseded_tree = tree(self.root)
        git(self.root, "checkout", "-q", "development")
        git(self.root, "merge", "--ff-only", "-q", "controller/superseded")
        integrated = tree(self.root)
        self.assertEqual(integrated, superseded_tree)
        git(self.root, "checkout", "-qb", "issue/7-unique")
        (self.root / "novel.txt").write_text("keep me\n", encoding="utf-8")
        git(self.root, "add", "novel.txt")
        git(self.root, "commit", "-qm", "unique work")
        unique_head = sha(self.root)
        unique_tree = tree(self.root)
        git(self.root, "checkout", "-q", "development")
        closed: list[str] = []

        def mutator(artifact: Artifact) -> str:
            if artifact.kind == KIND_PR:
                closed.append(artifact.name)
                return ACTION_CLEAN
            return default_mutator(self.root)(artifact)

        artifacts = [
            Artifact(
                id="branch:controller/empty",
                kind=KIND_BRANCH,
                name="controller/empty",
                controller_owned=True,
                owner=OWNER_CONTROLLER,
                head_sha=self.base,
                tree_sha=self.base_tree,
                base_sha=self.base,
                base_tree_sha=self.base_tree,
                commits_ahead=0,
            ),
            pr(
                name="superseded-pr",
                head=superseded_head,
                tree_sha=superseded_tree,
                base=self.base,
                base_tree=self.base_tree,
                ahead=1,
                integrated_trees=(integrated,),
            ),
            pr(
                name="unique-pr",
                head=unique_head,
                tree_sha=unique_tree,
                base=self.base,
                base_tree=self.base_tree,
                ahead=1,
                unique=("novel.txt",),
            ),
            pr(
                name="partial-pr",
                head=unique_head,
                tree_sha=unique_tree,
                base=self.base,
                base_tree=self.base_tree,
                ahead=2,
                unique=("novel.txt",),
                integrated_paths=("gone.txt",),
            ),
            Artifact(
                id="branch:issue/7-unique",
                kind=KIND_BRANCH,
                name="issue/7-unique",
                controller_owned=False,
                owner=OWNER_WORKER,
                head_sha=unique_head,
                tree_sha=unique_tree,
                base_sha=self.base,
                base_tree_sha=self.base_tree,
                unique_paths=("novel.txt",),
                commits_ahead=1,
            ),
        ]
        report = reconcile(repo=self.root, artifacts=artifacts, apply=True, mutator=mutator)
        self.assertTrue(report["ok"])
        self.assertIn("branch:controller/empty", report["cleaned"])
        self.assertIn("pr:superseded-pr", report["cleaned"])
        self.assertIn("pr:unique-pr", report["preservedForDecision"])
        self.assertIn("pr:partial-pr", report["preservedForDecision"])
        self.assertIn("branch:issue/7-unique", report["preservedForDecision"])
        self.assertEqual(closed, ["superseded-pr"])
        self.assertNotIn("unique-pr", closed)
        branches = git(self.root, "branch", "--list")
        self.assertNotIn("controller/empty", branches)
        self.assertIn("issue/7-unique", branches)
        unique_still = git(self.root, "rev-parse", "issue/7-unique")
        self.assertEqual(unique_still, unique_head)

    def test_controller_owned_empty_worktree_is_removed_worker_is_kept(self) -> None:
        controller_wt = Path(self.tmp.name) / "controller-empty-wt"
        worker_wt = Path(self.tmp.name) / "worker-wt"
        git(self.root, "worktree", "add", "-q", "-b", "controller/tmp-wt", str(controller_wt), "development")
        git(self.root, "branch", "issue/3-worker")
        git(self.root, "worktree", "add", "-q", str(worker_wt), "issue/3-worker")
        (worker_wt / "wip.txt").write_text("uncommitted worker\n", encoding="utf-8")
        artifacts = [
            Artifact(
                id="wt:controller",
                kind=KIND_WORKTREE,
                name="controller/tmp-wt",
                controller_owned=True,
                owner=OWNER_CONTROLLER,
                head_sha=self.base,
                tree_sha=self.base_tree,
                base_sha=self.base,
                base_tree_sha=self.base_tree,
                commits_ahead=0,
                path=str(controller_wt),
            ),
            Artifact(
                id="wt:worker",
                kind=KIND_WORKTREE,
                name="issue/3-worker",
                controller_owned=False,
                owner=OWNER_WORKER,
                head_sha=self.base,
                tree_sha=self.base_tree,
                base_sha=self.base,
                base_tree_sha=self.base_tree,
                uncommitted=True,
                commits_ahead=0,
                path=str(worker_wt),
            ),
        ]
        report = reconcile(repo=self.root, artifacts=artifacts, apply=True)
        self.assertTrue(report["ok"])
        self.assertFalse(controller_wt.exists())
        self.assertTrue(worker_wt.exists())
        self.assertTrue((worker_wt / "wip.txt").is_file())
        self.assertIn("wt:worker", report["preservedForDecision"])

    def test_protected_branch_is_not_deleted(self) -> None:
        artifacts = [
            Artifact(
                id="branch:main",
                kind=KIND_BRANCH,
                name="main",
                controller_owned=True,
                owner=OWNER_CONTROLLER,
                head_sha=self.base,
                tree_sha=self.base_tree,
                base_sha=self.base,
                base_tree_sha=self.base_tree,
                commits_ahead=0,
            )
        ]
        report = reconcile(repo=self.root, artifacts=artifacts, apply=True)
        self.assertTrue(report["ok"])
        self.assertEqual(report["kept"], ["branch:main"])
        self.assertEqual(git(self.root, "rev-parse", "--abbrev-ref", "HEAD"), "development")

    def test_pr_close_without_mutator_fails_closed_and_preserves_unique_work(self) -> None:
        unique = pr(
            name="unique-pr",
            head="1" * 40,
            tree_sha="2" * 40,
            base=self.base,
            base_tree=self.base_tree,
            ahead=1,
            unique=("novel.txt",),
        )
        empty = pr(
            name="empty-pr",
            head=self.base,
            tree_sha=self.base_tree,
            base=self.base,
            base_tree=self.base_tree,
            ahead=0,
        )
        report = reconcile(repo=self.root, artifacts=[unique], apply=True)
        self.assertTrue(report["ok"])
        self.assertEqual(report["preservedForDecision"], ["pr:unique-pr"])
        (self.root / "gitops-outcome.json").write_text("{}\n", encoding="utf-8")
        with self.assertRaises(IdentityUncertainty):
            reconcile(repo=self.root, artifacts=[empty], apply=True)
        self.assertFalse((self.root / "gitops-outcome.json").exists())
        state = resolve_state_dir(self.root)
        self.assertTrue((state / "failure-diagnostics.json").is_file())
        self.assertTrue((state / "retained-root-residue" / "gitops-outcome.json").is_file())

    def test_repeated_reconciliation_is_idempotent(self) -> None:
        residue = self.root / "integrator-result.json"
        residue.write_text("{}\n", encoding="utf-8")
        git(self.root, "branch", "controller/empty")
        empty = Artifact(
            id="branch:controller/empty",
            kind=KIND_BRANCH,
            name="controller/empty",
            controller_owned=True,
            owner=OWNER_CONTROLLER,
            head_sha=self.base,
            tree_sha=self.base_tree,
            base_sha=self.base,
            base_tree_sha=self.base_tree,
            commits_ahead=0,
        )
        first = reconcile(repo=self.root, artifacts=[empty], apply=True)
        self.assertTrue(first["ok"])
        self.assertIn("branch:controller/empty", first["cleaned"])
        self.assertFalse(residue.exists())
        gone = Artifact(
            id="branch:controller/empty",
            kind=KIND_BRANCH,
            name="controller/empty",
            controller_owned=True,
            owner=OWNER_CONTROLLER,
            head_sha=self.base,
            tree_sha=self.base_tree,
            base_sha=self.base,
            base_tree_sha=self.base_tree,
            commits_ahead=0,
            exists=False,
        )
        second = reconcile(repo=self.root, artifacts=[gone], apply=True)
        self.assertTrue(second["ok"])
        self.assertEqual(second["alreadyAbsent"], ["branch:controller/empty"])
        self.assertTrue(second["idempotentReplay"])
        third = reconcile(repo=self.root, artifacts=[gone], apply=True)
        self.assertEqual(second["cleaned"], third["cleaned"])
        self.assertEqual(second["preservedForDecision"], third["preservedForDecision"])
        self.assertEqual(second["alreadyAbsent"], third["alreadyAbsent"])
        self.assertEqual(git(self.root, "status", "--porcelain"), "")

    def test_unknown_artifact_is_not_auto_deleted(self) -> None:
        unknown = Artifact(
            id="pr:opaque",
            kind=KIND_PR,
            name="mystery",
            controller_owned=True,
            owner=OWNER_CONTROLLER,
        )
        closed: list[str] = []

        def mutator(artifact: Artifact) -> str:
            closed.append(artifact.name)
            return ACTION_CLEAN

        report = reconcile(repo=self.root, artifacts=[unknown], apply=True, mutator=mutator)
        self.assertTrue(report["ok"])
        self.assertEqual(report["preservedForDecision"], ["pr:opaque"])
        self.assertEqual(closed, [])
        self.assertEqual(classify_artifact(unknown).classification, CLASS_UNKNOWN)


class NegativeContractTests(unittest.TestCase):
    def test_default_mutator_refuses_live_github(self) -> None:
        tmp, root, base, base_tree = init_repo()
        self.addCleanup(tmp.cleanup)
        artifact = pr(
            name="empty-pr",
            head=base,
            tree_sha=base_tree,
            base=base,
            base_tree=base_tree,
            ahead=0,
        )
        with self.assertRaises(IdentityUncertainty) as ctx:
            default_mutator(root)(artifact)
        self.assertEqual(ctx.exception.code, "github_mutation_not_injected")

    def test_infrastructure_retry_bound_does_not_retry_identity(self) -> None:
        tmp, root, base, base_tree = init_repo()
        self.addCleanup(tmp.cleanup)
        calls = {"n": 0}

        def flaky(artifact: Artifact) -> str:
            calls["n"] += 1
            raise IdentityUncertainty("missing_commit_or_tree", artifact.name)

        empty = Artifact(
            id="branch:controller/empty",
            kind=KIND_BRANCH,
            name="controller/empty",
            controller_owned=True,
            owner=OWNER_CONTROLLER,
            head_sha=base,
            tree_sha=base_tree,
            base_sha=base,
            base_tree_sha=base_tree,
            commits_ahead=0,
        )
        with self.assertRaises(IdentityUncertainty):
            reconcile(repo=root, artifacts=[empty], apply=True, mutator=flaky)
        self.assertEqual(calls["n"], 1)


if __name__ == "__main__":
    unittest.main()
