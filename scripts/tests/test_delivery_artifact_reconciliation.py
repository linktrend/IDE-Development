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
        unique_branch = Artifact(
            id="branch:controller/unique",
            kind=KIND_BRANCH,
            name="controller/unique",
            controller_owned=True,
            owner=OWNER_CONTROLLER,
            head_sha=self.head,
            tree_sha=self.other_tree,
            base_sha=self.base,
            base_tree_sha=self.base_tree,
            unique_paths=("novel.txt",),
            commits_ahead=1,
            derived=True,
        )
        branch_action = decide_action(unique_branch, classify_artifact(unique_branch))
        self.assertEqual(branch_action, ACTION_PRESERVE_FOR_DECISION)
        self.assertNotEqual(branch_action, ACTION_CLEAN)
        self.assertNotEqual(branch_action, ACTION_KEEP)

    def test_underived_inventory_cannot_self_authorize_clean(self) -> None:
        empty = pr(
            name="controller/empty",
            head=self.base,
            tree_sha=self.base_tree,
            base=self.base,
            base_tree=self.base_tree,
            ahead=0,
            controller_owned=True,
            owner=OWNER_CONTROLLER,
        )
        classification = classify_artifact(empty)
        self.assertEqual(classification.classification, CLASS_EMPTY)
        self.assertEqual(decide_action(empty, classification), ACTION_PRESERVE_FOR_DECISION)
        self.assertFalse(empty.derived)
        empty_branch = Artifact(
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
        self.assertFalse(empty_branch.derived)
        self.assertEqual(
            decide_action(empty_branch, classify_artifact(empty_branch)),
            ACTION_PRESERVE_FOR_DECISION,
        )


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
                controller_owned=False,
                owner=OWNER_WORKER,
                head_sha="0" * 40,
                tree_sha="1" * 40,
                base_sha="2" * 40,
                base_tree_sha="3" * 40,
                unique_paths=("forged.txt",),
                commits_ahead=9,
            ),
            Artifact(
                id="branch:controller/superseded",
                kind=KIND_BRANCH,
                name="controller/superseded",
                controller_owned=False,
                owner=OWNER_WORKER,
                head_sha="0" * 40,
                tree_sha="1" * 40,
                base_sha="2" * 40,
                base_tree_sha="3" * 40,
                unique_paths=("forged.txt",),
                commits_ahead=9,
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
        self.assertIn("branch:controller/superseded", report["cleaned"])
        self.assertNotIn("pr:superseded-pr", report["cleaned"])
        self.assertIn("pr:superseded-pr", report["preservedForDecision"])
        self.assertIn("pr:unique-pr", report["preservedForDecision"])
        self.assertIn("pr:partial-pr", report["preservedForDecision"])
        self.assertIn("branch:issue/7-unique", report["preservedForDecision"])
        self.assertEqual(closed, [])
        self.assertNotIn("unique-pr", closed)
        branches = git(self.root, "branch", "--list")
        self.assertNotIn("controller/empty", branches)
        self.assertNotIn("controller/superseded", branches)
        self.assertIn("issue/7-unique", branches)
        unique_still = git(self.root, "rev-parse", "issue/7-unique")
        self.assertEqual(unique_still, unique_head)

    def test_squash_superseded_controller_branch_is_cleaned_after_live_tree_proof(self) -> None:
        git(self.root, "checkout", "-qb", "controller/squash")
        (self.root / "landed.txt").write_text("squash me\n", encoding="utf-8")
        git(self.root, "add", "landed.txt")
        git(self.root, "commit", "-qm", "squash candidate")
        squash_head = sha(self.root)
        squash_tree = tree(self.root)
        git(self.root, "checkout", "-q", "development")
        git(self.root, "merge", "--squash", "controller/squash")
        git(self.root, "commit", "-qm", "squashed landing")
        self.assertEqual(tree(self.root), squash_tree)
        self.assertNotEqual(sha(self.root), squash_head)
        report = reconcile(
            repo=self.root,
            artifacts=[
                Artifact(
                    id="branch:controller/squash",
                    kind=KIND_BRANCH,
                    name="controller/squash",
                    controller_owned=False,
                    owner=OWNER_WORKER,
                    head_sha="0" * 40,
                    tree_sha="1" * 40,
                    unique_paths=("forged.txt",),
                    commits_ahead=9,
                )
            ],
            apply=True,
        )
        self.assertTrue(report["ok"])
        self.assertIn("branch:controller/squash", report["cleaned"])
        self.assertNotIn("controller/squash", git(self.root, "branch", "--list"))

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

    def test_unverifiable_prs_are_preserved_without_github(self) -> None:
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
        report = reconcile(repo=self.root, artifacts=[unique, empty], apply=True)
        self.assertTrue(report["ok"])
        self.assertIn("pr:unique-pr", report["preservedForDecision"])
        self.assertIn("pr:empty-pr", report["preservedForDecision"])
        self.assertEqual(report["cleaned"], [])

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


class AdversarialInventoryTests(unittest.TestCase):
    """Inventory JSON is a locator, not deletion authority."""

    def setUp(self) -> None:
        self.tmp, self.root, self.base, self.base_tree = init_repo()
        self.addCleanup(self.tmp.cleanup)

    def test_forged_controller_owned_cannot_delete_unique_branch(self) -> None:
        git(self.root, "checkout", "-qb", "issue/5-unique")
        (self.root / "novel.txt").write_text("keep unique branch\n", encoding="utf-8")
        git(self.root, "add", "novel.txt")
        git(self.root, "commit", "-qm", "unique work")
        unique_head = sha(self.root)
        git(self.root, "checkout", "-q", "development")
        forged = Artifact(
            id="branch:issue/5-unique",
            kind=KIND_BRANCH,
            name="issue/5-unique",
            controller_owned=True,
            owner=OWNER_CONTROLLER,
            head_sha=self.base,
            tree_sha=self.base_tree,
            base_sha=self.base,
            base_tree_sha=self.base_tree,
            commits_ahead=0,
            unique_paths=(),
            changed_paths=(),
        )
        report = reconcile(repo=self.root, artifacts=[forged], apply=True)
        self.assertTrue(report["ok"])
        self.assertNotIn("branch:issue/5-unique", report["cleaned"])
        self.assertIn("issue/5-unique", git(self.root, "branch", "--list"))
        self.assertEqual(git(self.root, "rev-parse", "issue/5-unique"), unique_head)
        self.assertEqual(git(self.root, "log", "-1", "--format=%s", "issue/5-unique"), "unique work")

    def test_forged_tree_and_base_cannot_delete_unique_branch(self) -> None:
        git(self.root, "checkout", "-qb", "issue/6-unique")
        (self.root / "novel.txt").write_text("tree forge target\n", encoding="utf-8")
        git(self.root, "add", "novel.txt")
        git(self.root, "commit", "-qm", "unique tree")
        unique_head = sha(self.root)
        unique_tree = tree(self.root)
        git(self.root, "checkout", "-q", "development")
        forged = Artifact(
            id="branch:issue/6-unique",
            kind=KIND_BRANCH,
            name="issue/6-unique",
            controller_owned=True,
            owner=OWNER_CONTROLLER,
            head_sha=unique_head,
            tree_sha=self.base_tree,
            base_sha=self.base,
            base_tree_sha=unique_tree,
            integrated_trees=(unique_tree, self.base_tree),
            commits_ahead=0,
            unique_paths=(),
            changed_paths=(),
        )
        report = reconcile(repo=self.root, artifacts=[forged], apply=True)
        self.assertTrue(report["ok"])
        self.assertNotIn("branch:issue/6-unique", report["cleaned"])
        self.assertEqual(git(self.root, "rev-parse", "issue/6-unique"), unique_head)
        self.assertEqual(git(self.root, "rev-parse", "issue/6-unique^{tree}"), unique_tree)

    def test_forged_path_cannot_remove_dirty_unique_or_external_worktree(self) -> None:
        worker_wt = Path(self.tmp.name) / "worker-wt"
        git(self.root, "branch", "issue/3-worker")
        git(self.root, "worktree", "add", "-q", str(worker_wt), "issue/3-worker")
        (worker_wt / "wip.txt").write_text("uncommitted worker\n", encoding="utf-8")

        other_root = Path(self.tmp.name) / "other-repo"
        other_root.mkdir()
        git(other_root, "init", "-q", "-b", "development")
        git(other_root, "config", "user.email", "u08@example.invalid")
        git(other_root, "config", "user.name", "WP-U08 tests")
        (other_root / "base.txt").write_text("other\n", encoding="utf-8")
        git(other_root, "add", "base.txt")
        git(other_root, "commit", "-qm", "other base")
        other_wt = Path(self.tmp.name) / "other-wt"
        git(other_root, "worktree", "add", "-q", "-b", "controller/other", str(other_wt), "development")
        (other_wt / "foreign.txt").write_text("external unique\n", encoding="utf-8")

        artifacts = [
            Artifact(
                id="wt:forged-worker",
                kind=KIND_WORKTREE,
                name="controller/forged-wt",
                controller_owned=True,
                owner=OWNER_CONTROLLER,
                head_sha=self.base,
                tree_sha=self.base_tree,
                base_sha=self.base,
                base_tree_sha=self.base_tree,
                commits_ahead=0,
                uncommitted=False,
                path=str(worker_wt),
            ),
            Artifact(
                id="wt:forged-external",
                kind=KIND_WORKTREE,
                name="controller/other",
                controller_owned=True,
                owner=OWNER_CONTROLLER,
                head_sha=self.base,
                tree_sha=self.base_tree,
                base_sha=self.base,
                base_tree_sha=self.base_tree,
                commits_ahead=0,
                uncommitted=False,
                path=str(other_wt),
            ),
        ]
        report = reconcile(repo=self.root, artifacts=artifacts, apply=True)
        self.assertTrue(report["ok"])
        self.assertNotIn("wt:forged-worker", report["cleaned"])
        self.assertNotIn("wt:forged-external", report["cleaned"])
        self.assertTrue(worker_wt.exists())
        self.assertTrue((worker_wt / "wip.txt").is_file())
        self.assertTrue(other_wt.exists())
        self.assertTrue((other_wt / "foreign.txt").is_file())
        self.assertIn("issue/3-worker", git(self.root, "branch", "--list"))
        self.assertIn("controller/other", git(other_root, "branch", "--list"))

    def test_trusted_owned_refs_cannot_reclassify_issue_branch(self) -> None:
        git(self.root, "branch", "issue/5-empty")
        state = resolve_state_dir(self.root)
        state.mkdir(parents=True, exist_ok=True)
        (state / "owned-refs.json").write_text(
            json.dumps(["issue/5-empty", "controller/empty"]),
            encoding="utf-8",
        )
        git(self.root, "branch", "controller/empty")
        report = reconcile(
            repo=self.root,
            artifacts=[
                Artifact(
                    id="branch:issue/5-empty",
                    kind=KIND_BRANCH,
                    name="issue/5-empty",
                    controller_owned=True,
                    owner=OWNER_CONTROLLER,
                    head_sha=self.base,
                    tree_sha=self.base_tree,
                    commits_ahead=0,
                ),
                Artifact(
                    id="branch:controller/empty",
                    kind=KIND_BRANCH,
                    name="controller/empty",
                    controller_owned=False,
                    owner=OWNER_WORKER,
                    head_sha="0" * 40,
                    tree_sha="1" * 40,
                    commits_ahead=9,
                ),
            ],
            apply=True,
        )
        self.assertTrue(report["ok"])
        self.assertIn("issue/5-empty", git(self.root, "branch", "--list"))
        self.assertNotIn("branch:issue/5-empty", report["cleaned"])
        self.assertIn("branch:issue/5-empty", report["preservedForDecision"])
        self.assertNotIn("controller/empty", git(self.root, "branch", "--list"))
        self.assertIn("branch:controller/empty", report["cleaned"])

    def test_pr_locator_cannot_delete_matching_local_branch(self) -> None:
        git(self.root, "branch", "controller/empty")
        report = reconcile(
            repo=self.root,
            artifacts=[
                Artifact(
                    id="pr:controller/empty",
                    kind=KIND_PR,
                    name="controller/empty",
                    controller_owned=True,
                    owner=OWNER_CONTROLLER,
                    head_sha=self.base,
                    tree_sha=self.base_tree,
                    base_sha=self.base,
                    base_tree_sha=self.base_tree,
                    commits_ahead=0,
                )
            ],
            apply=True,
        )
        self.assertTrue(report["ok"])
        self.assertIn("controller/empty", git(self.root, "branch", "--list"))
        self.assertNotIn("pr:controller/empty", report["cleaned"])
        self.assertIn("pr:controller/empty", report["preservedForDecision"])

    def test_tag_only_controller_name_is_not_deleted(self) -> None:
        git(self.root, "tag", "controller/tagged")
        report = reconcile(
            repo=self.root,
            artifacts=[
                Artifact(
                    id="branch:controller/tagged",
                    kind=KIND_BRANCH,
                    name="controller/tagged",
                    controller_owned=True,
                    owner=OWNER_CONTROLLER,
                    head_sha=self.base,
                    tree_sha=self.base_tree,
                    commits_ahead=0,
                )
            ],
            apply=True,
        )
        self.assertTrue(report["ok"])
        self.assertNotIn("branch:controller/tagged", report["cleaned"])
        self.assertEqual(git(self.root, "rev-parse", "refs/tags/controller/tagged"), self.base)
        self.assertEqual(git(self.root, "status", "--porcelain"), "")

    def test_name_path_mismatch_does_not_remove_either_worktree(self) -> None:
        controller_wt = Path(self.tmp.name) / "controller-empty-wt"
        worker_wt = Path(self.tmp.name) / "worker-wt"
        git(self.root, "worktree", "add", "-q", "-b", "controller/tmp-wt", str(controller_wt), "development")
        git(self.root, "branch", "issue/3-worker")
        git(self.root, "worktree", "add", "-q", str(worker_wt), "issue/3-worker")
        report = reconcile(
            repo=self.root,
            artifacts=[
                Artifact(
                    id="wt:mismatch",
                    kind=KIND_WORKTREE,
                    name="controller/tmp-wt",
                    controller_owned=True,
                    owner=OWNER_CONTROLLER,
                    head_sha=self.base,
                    tree_sha=self.base_tree,
                    commits_ahead=0,
                    uncommitted=False,
                    path=str(worker_wt),
                )
            ],
            apply=True,
        )
        self.assertTrue(report["ok"])
        self.assertNotIn("wt:mismatch", report["cleaned"])
        self.assertTrue(controller_wt.exists())
        self.assertTrue(worker_wt.exists())
        row = next(item for item in report["artifacts"] if item["id"] == "wt:mismatch")
        self.assertFalse(row["evidence"]["derivedFromRepo"])


class NegativeContractTests(unittest.TestCase):
    def test_mutator_refuses_empty_issue_branch_despite_forged_controller_owner(self) -> None:
        tmp, root, base, base_tree = init_repo()
        self.addCleanup(tmp.cleanup)
        git(root, "branch", "issue/8-empty")
        forged = Artifact(
            id="branch:issue/8-empty",
            kind=KIND_BRANCH,
            name="issue/8-empty",
            controller_owned=True,
            owner=OWNER_CONTROLLER,
            head_sha=base,
            tree_sha=base_tree,
            base_sha=base,
            base_tree_sha=base_tree,
            commits_ahead=0,
            derived=True,
        )
        with self.assertRaises(IdentityUncertainty) as ctx:
            default_mutator(root)(forged)
        self.assertEqual(ctx.exception.code, "not_controller_owned")
        self.assertIn("issue/8-empty", git(root, "branch", "--list"))

    def test_mutator_refuses_worker_worktree_matched_only_by_path(self) -> None:
        tmp, root, base, base_tree = init_repo()
        self.addCleanup(tmp.cleanup)
        worker_wt = Path(tmp.name) / "worker-empty-wt"
        git(root, "branch", "issue/9-empty")
        git(root, "worktree", "add", "-q", str(worker_wt), "issue/9-empty")
        forged = Artifact(
            id="wt:forged-controller",
            kind=KIND_WORKTREE,
            name="controller/empty",
            controller_owned=True,
            owner=OWNER_CONTROLLER,
            head_sha=base,
            tree_sha=base_tree,
            base_sha=base,
            base_tree_sha=base_tree,
            commits_ahead=0,
            path=str(worker_wt),
            derived=True,
        )
        with self.assertRaises(IdentityUncertainty) as ctx:
            default_mutator(root)(forged)
        self.assertEqual(ctx.exception.code, "worktree_name_mismatch")
        self.assertTrue(worker_wt.exists())
        self.assertIn("issue/9-empty", git(root, "branch", "--list"))

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

        git(root, "branch", "controller/empty")
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
