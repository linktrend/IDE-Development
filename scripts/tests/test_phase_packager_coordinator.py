"""WP-U03 Phase Packager/Coordinator unit, negative, and contract tests."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.gitops import packager_coordinator as coordinator
from scripts.gitops import packager_discover as discover


ROOT = Path(__file__).resolve().parents[2]


def git(repo: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True, check=False)
    if check and result.returncode:
        raise AssertionError(result.stderr or result.stdout)
    return (result.stdout or "").strip()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


class Fixture:
    def __init__(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.origin = root / "origin.git"
        self.work = root / "work"
        self.work.mkdir()
        git(root, "init", "--bare", str(self.origin))
        git(self.work, "init", "-q", "-b", "development")
        git(self.work, "config", "user.email", "packager@example.invalid")
        git(self.work, "config", "user.name", "Phase Packager tests")
        git(self.work, "remote", "add", "origin", str(self.origin))
        write(self.work / "base.txt", "base\n")
        git(self.work, "add", "base.txt")
        git(self.work, "commit", "-qm", "base")
        git(self.work, "push", "-q", "-u", "origin", "development")
        self.github = coordinator.MemoryGitHub(repository="owner/name")

    def cleanup(self) -> None:
        self.tmp.cleanup()

    def development_sha(self) -> str:
        return git(self.work, "rev-parse", "origin/development")

    def accept_issue(self, number: int, filename: str, content: str, *, ready: bool = True) -> coordinator.AcceptedSource:
        branch = f"issue/{number}-{filename.split('.')[0]}"
        git(self.work, "checkout", "-B", branch, "development")
        write(self.work / filename, content)
        git(self.work, "add", filename)
        git(self.work, "commit", "-qm", f"issue {number}")
        sha = git(self.work, "rev-parse", "HEAD")
        git(self.work, "push", "-q", "-u", "origin", branch)
        git(self.work, "checkout", "development")
        source = coordinator.AcceptedSource(branch=branch, sha=sha, order=number)
        if ready:
            self.github.ready_shas.add(sha)
            self.github.evidence[sha] = {"schemaVersion": 1, "headSha": sha, "classification": "tests"}
        return source

    def assemble(self, sources: list[coordinator.AcceptedSource], **kwargs):
        ordered = [
            coordinator.AcceptedSource(branch=item.branch, sha=item.sha, order=index)
            for index, item in enumerate(sources, start=1)
        ]
        return coordinator.assemble_phase(
            repo=self.work,
            repository="owner/name",
            sources=ordered,
            github=self.github,
            phase_branch=kwargs.get("phase_branch", "phase/next"),
            require_evidence=kwargs.get("require_evidence", True),
            expected_repository=kwargs.get("expected_repository", "owner/name"),
        )


class PhasePackagerCoordinatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fx = Fixture()
        self.addCleanup(self.fx.cleanup)

    def test_discover_is_not_phase_packager(self) -> None:
        self.assertFalse(discover.IS_PHASE_PACKAGER)
        self.assertNotEqual(discover.COMPONENT_KIND, coordinator.COMPONENT_KIND)
        self.assertTrue(coordinator.IS_PHASE_PACKAGER)
        self.assertIn("not** the Update 3 Phase Packager/Coordinator", discover.__doc__)

    def test_one_issue_creates_one_phase_branch_and_draft_pr(self) -> None:
        one = self.fx.accept_issue(11, "alpha.txt", "alpha\n")
        result = self.fx.assemble([one])
        self.assertEqual(result["action"], "created")
        self.assertEqual(result["phaseBranch"], "phase/next")
        self.assertEqual(result["phasePr"]["number"], 1)
        self.assertTrue(result["phasePr"]["isDraft"])
        self.assertEqual(len(self.fx.github.prs), 1)
        self.assertEqual(git(self.fx.work, "rev-parse", "--abbrev-ref", "HEAD"), "phase/next")
        self.assertTrue((self.fx.work / "alpha.txt").is_file())
        self.assertEqual(result["acceptedCommits"][0]["sha"], one.sha)
        self.assertFalse(result["record"]["sealed"])
        self.assertFalse(result["fullDispatchAllowed"])

    def test_many_compatible_issues_create_one_ordered_phase(self) -> None:
        first = self.fx.accept_issue(1, "one.txt", "one\n")
        second = self.fx.accept_issue(2, "two.txt", "two\n")
        result = self.fx.assemble([first, second])
        self.assertEqual([row["branch"] for row in result["acceptedCommits"]], [first.branch, second.branch])
        self.assertEqual(result["record"]["dependencyOrder"], [first.branch, second.branch])
        self.assertEqual(len(self.fx.github.prs), 1)
        self.assertTrue((self.fx.work / "one.txt").is_file())
        self.assertTrue((self.fx.work / "two.txt").is_file())
        log = git(self.fx.work, "log", "--oneline", "origin/development..HEAD")
        self.assertIn("issue 1", log)
        self.assertIn("issue 2", log)

    def test_identical_invocation_is_idempotent(self) -> None:
        one = self.fx.accept_issue(3, "same.txt", "same\n")
        first = self.fx.assemble([one])
        second = self.fx.assemble([one])
        self.assertTrue(second["idempotent"])
        self.assertEqual(second["action"], "reused")
        self.assertEqual(first["phasePr"]["number"], second["phasePr"]["number"])
        self.assertEqual(first["headSha"], second["headSha"])
        self.assertEqual(first["candidateRevision"], second["candidateRevision"])
        self.assertEqual(len(self.fx.github.prs), 1)
        self.assertEqual(self.fx.github.ensure_calls, 2)
        self.assertEqual(self.fx.github.labels, [])
        self.assertEqual(self.fx.github.workflow_dispatches, [])

    def test_new_accepted_commit_updates_phase_and_invalidates_old_evidence(self) -> None:
        first = self.fx.accept_issue(4, "first.txt", "first\n")
        created = self.fx.assemble([first])
        second = self.fx.accept_issue(5, "second.txt", "second\n")
        updated = self.fx.assemble([first, second])
        self.assertEqual(updated["action"], "updated")
        self.assertNotEqual(updated["headSha"], created["headSha"])
        self.assertNotEqual(updated["candidateRevision"], created["candidateRevision"])
        self.assertEqual(updated["phasePr"]["number"], created["phasePr"]["number"])
        self.assertEqual(updated["record"]["invalidatedFromSha"], created["headSha"])
        self.assertEqual(updated["record"]["fast"]["status"], "invalidated")
        stale = coordinator.invalidate_handoff_if_head_changed(created["handoff"], live_head=updated["headSha"])
        self.assertFalse(stale["valid"])
        ok, detail = coordinator.consume_handoff(created["handoff"], live_head=updated["headSha"])
        self.assertFalse(ok)
        self.assertEqual(detail, "handoff_stale_head")
        ok, detail = coordinator.consume_handoff(updated["handoff"], live_head=updated["headSha"], live_tree=updated["gitTree"])
        self.assertTrue(ok, detail)

    def test_rejects_uncommitted_unpushed_wrong_repo_stale_missing(self) -> None:
        ready = self.fx.accept_issue(6, "ready.txt", "ready\n")
        git(self.fx.work, "checkout", ready.branch)
        write(self.fx.work / "dirty.txt", "dirty\n")
        with self.assertRaisesRegex(coordinator.CoordinatorError, "uncommitted"):
            self.fx.assemble([ready])
        (self.fx.work / "dirty.txt").unlink()
        git(self.fx.work, "checkout", "-f", "development")

        git(self.fx.work, "checkout", "-B", "issue/7-unpushed", "development")
        write(self.fx.work / "unpushed.txt", "unpushed\n")
        git(self.fx.work, "add", "unpushed.txt")
        git(self.fx.work, "commit", "-qm", "unpushed")
        unpushed_sha = git(self.fx.work, "rev-parse", "HEAD")
        git(self.fx.work, "checkout", "development")
        self.fx.github.ready_shas.add(unpushed_sha)
        with self.assertRaisesRegex(coordinator.CoordinatorError, "unpushed"):
            self.fx.assemble([coordinator.AcceptedSource("issue/7-unpushed", unpushed_sha, 1)])

        with self.assertRaisesRegex(coordinator.CoordinatorError, "wrong_repository"):
            self.fx.assemble([ready], expected_repository="other/name")

        stale = self.fx.accept_issue(8, "stale.txt", "stale\n")
        git(self.fx.work, "checkout", stale.branch)
        write(self.fx.work / "stale.txt", "newer\n")
        git(self.fx.work, "add", "stale.txt")
        git(self.fx.work, "commit", "-qm", "newer stale")
        git(self.fx.work, "push", "-q")
        git(self.fx.work, "checkout", "development")
        with self.assertRaisesRegex(coordinator.CoordinatorError, "stale_commit"):
            self.fx.assemble([stale])

        with self.assertRaisesRegex(coordinator.CoordinatorError, "missing_commit"):
            self.fx.assemble([coordinator.AcceptedSource("issue/9-missing", "a" * 40, 1)])

        bare = self.fx.accept_issue(10, "noevidence.txt", "x\n", ready=False)
        with self.assertRaisesRegex(coordinator.CoordinatorError, "evidence_missing"):
            self.fx.assemble([bare])

    def test_overlapping_and_conflicting_commits_stop(self) -> None:
        left = self.fx.accept_issue(12, "shared.txt", "left\n")
        git(self.fx.work, "checkout", "-B", "issue/13-shared", "development")
        write(self.fx.work / "shared.txt", "right\n")
        git(self.fx.work, "add", "shared.txt")
        git(self.fx.work, "commit", "-qm", "right")
        right_sha = git(self.fx.work, "rev-parse", "HEAD")
        git(self.fx.work, "push", "-q", "-u", "origin", "issue/13-shared")
        git(self.fx.work, "checkout", "development")
        self.fx.github.ready_shas.add(right_sha)
        with self.assertRaisesRegex(coordinator.CoordinatorError, "overlapping_commits"):
            self.fx.assemble(
                [
                    left,
                    coordinator.AcceptedSource("issue/13-shared", right_sha, 2),
                ]
            )

    def test_unrelated_commits_are_not_included(self) -> None:
        wanted = self.fx.accept_issue(14, "wanted.txt", "wanted\n")
        extra = self.fx.accept_issue(15, "extra.txt", "extra\n")
        result = self.fx.assemble([wanted])
        self.assertEqual([row["sha"] for row in result["acceptedCommits"]], [wanted.sha])
        self.assertTrue((self.fx.work / "wanted.txt").is_file())
        self.assertFalse((self.fx.work / "extra.txt").is_file())
        self.assertFalse(coordinator._is_ancestor(self.fx.work, extra.sha, result["headSha"]))

    def test_checkpoint_push_does_not_start_managed_ci_and_phase_pr_starts_fast(self) -> None:
        fast = (ROOT / coordinator.FAST_WORKFLOW_REL).read_text(encoding="utf-8")
        contract = coordinator.parse_fast_trigger_contract(fast)
        self.assertTrue(contract["namedFast"])
        self.assertFalse(contract["checkpointPush"])
        self.assertTrue(contract["phasePullRequest"])
        self.assertTrue(contract["phaseHeadOnly"])
        self.assertTrue(contract["checksExactHead"])
        self.assertTrue(contract["cancelObsolete"])
        self.assertFalse(contract["startsFull"])
        live = (ROOT / ".github/workflows/linktrend-review-packager.yml").read_text(encoding="utf-8")
        self.assertEqual(fast, live)
        full = (ROOT / coordinator.FULL_WORKFLOW_REL).read_text(encoding="utf-8")
        self.assertNotRegex(full, r"(?m)^\s+push:")
        self.assertIn("types: [labeled]", full)
        one = self.fx.accept_issue(16, "fast.txt", "fast\n")
        result = self.fx.assemble([one])
        self.assertEqual(result["fastTrigger"], "phase_pr")
        self.assertFalse(result["checkpointCI"])
        self.assertFalse(result["fullDispatchAllowed"])
        self.assertEqual(self.fx.github.labels, [])
        self.assertEqual(self.fx.github.workflow_dispatches, [])

    def test_full_cannot_start_before_fast_and_required_ci(self) -> None:
        allowed, detail = coordinator.full_may_start(
            sealed=False,
            fast_status="passed",
            required_ci={"CI": "success"},
            live_head_sha="a" * 40,
        )
        self.assertFalse(allowed)
        self.assertEqual(detail, "unsealed")
        allowed, detail = coordinator.full_may_start(
            sealed=True,
            fast_status="running",
            required_ci={"CI": "success"},
            live_head_sha="a" * 40,
        )
        self.assertFalse(allowed)
        self.assertIn("fast_not_passed", detail)
        allowed, detail = coordinator.full_may_start(
            sealed=True,
            fast_status="passed",
            required_ci={"CI": "pending"},
            live_head_sha="a" * 40,
        )
        self.assertFalse(allowed)
        self.assertIn("required_ci_not_passed", detail)

    def test_handoff_schema_and_agent_agnostic_behavior(self) -> None:
        one = self.fx.accept_issue(17, "handoff.txt", "handoff\n")
        os.environ["CURSOR_AGENT"] = "1"
        os.environ["CODEX_HOME"] = "/tmp/codex-fixture"
        try:
            cursor = self.fx.assemble([one])
        finally:
            os.environ.pop("CURSOR_AGENT", None)
            os.environ.pop("CODEX_HOME", None)
        os.environ["TERRA_AGENT"] = "terra"
        try:
            terra = self.fx.assemble([one])
        finally:
            os.environ.pop("TERRA_AGENT", None)
        self.assertEqual(cursor["headSha"], terra["headSha"])
        self.assertEqual(cursor["candidateRevision"], terra["candidateRevision"])
        self.assertEqual(cursor["phasePr"]["number"], terra["phasePr"]["number"])
        self.assertIn("CURSOR_AGENT", cursor["agentEnvIgnored"])
        handoff = cursor["handoff"]
        for key in (
            "schemaVersion",
            "kind",
            "repository",
            "phaseBranch",
            "phasePr",
            "headCommit",
            "gitTree",
            "baseCommit",
            "candidateRevision",
            "acceptedCommits",
            "evidenceLocations",
            "valid",
            "component",
        ):
            self.assertIn(key, handoff)
        self.assertEqual(handoff["kind"], "phase-handoff")
        self.assertEqual(handoff["component"], coordinator.COMPONENT_KIND)
        schema = json.loads((ROOT / "core/managed-core/schemas/phase-handoff.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(schema["required"], list(key for key in schema["required"]))
        for key in schema["required"]:
            self.assertIn(key, handoff)
        record_schema = json.loads((ROOT / "core/managed-core/schemas/phase-record.schema.json").read_text(encoding="utf-8"))
        for key in record_schema["required"]:
            self.assertIn(key, cursor["record"])

    def test_does_not_push_protected_branches(self) -> None:
        one = self.fx.accept_issue(18, "protect.txt", "protect\n")
        before = git(self.fx.work, "rev-parse", "origin/development")
        self.fx.assemble([one])
        after = git(self.fx.work, "rev-parse", "origin/development")
        self.assertEqual(before, after)
        self.assertEqual(git(self.fx.work, "rev-parse", "--abbrev-ref", "HEAD"), "phase/next")
        with self.assertRaisesRegex(coordinator.CoordinatorError, "invalid_phase_branch"):
            coordinator.assemble_phase(
                repo=self.fx.work,
                repository="owner/name",
                sources=[one],
                github=self.fx.github,
                phase_branch="development",
            )


if __name__ == "__main__":
    unittest.main()
