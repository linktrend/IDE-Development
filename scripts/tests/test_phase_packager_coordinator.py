"""WP-U03 Phase Packager/Coordinator unit, negative, and contract tests."""

from __future__ import annotations

import contextlib
import hashlib
import io
import inspect
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jsonschema import Draft202012Validator, RefResolver

from scripts.gitops import packager_coordinator as coordinator
from scripts.gitops import packager_discover as discover
from scripts.ide_development.constants import RC_REQUIRED_SCHEMA_RELS


ROOT = Path(__file__).resolve().parents[2]


def git(repo: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(["git", *args], cwd=repo, text=True, capture_output=True, check=False)
    if check and result.returncode:
        raise AssertionError(result.stderr or result.stdout)
    return (result.stdout or "").strip()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def remote_sha(repo: Path, branch: str) -> str:
    output = git(repo, "ls-remote", "--heads", "origin", f"refs/heads/{branch}", check=False)
    if not output:
        return ""
    return output.split()[0]


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
        git(self.work, "remote", "add", "origin", "https://github.com/owner/name.git")
        git(self.work, "config", "url." + self.origin.as_uri() + ".insteadOf", "https://github.com/owner/name.git")
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

    def accept_issue_history(self, number: int, filename: str, contents: list[str]) -> coordinator.AcceptedSource:
        branch = f"issue/{number}-{filename.split('.')[0]}"
        git(self.work, "checkout", "-B", branch, "development")
        for index, content in enumerate(contents, start=1):
            write(self.work / filename, content)
            git(self.work, "add", filename)
            git(self.work, "commit", "-qm", f"issue {number} step {index}")
        sha = git(self.work, "rev-parse", "HEAD")
        git(self.work, "push", "-q", "-u", "origin", branch)
        git(self.work, "checkout", "development")
        source = coordinator.AcceptedSource(branch=branch, sha=sha, order=number)
        self.github.ready_shas.add(sha)
        self.github.evidence[sha] = {"schemaVersion": 1, "headSha": sha, "classification": "tests"}
        return source

    def advance_issue(self, source: coordinator.AcceptedSource, filename: str, content: str) -> coordinator.AcceptedSource:
        git(self.work, "checkout", source.branch)
        write(self.work / filename, content)
        git(self.work, "add", filename)
        git(self.work, "commit", "-qm", f"advance {source.branch}")
        sha = git(self.work, "rev-parse", "HEAD")
        git(self.work, "push", "-q", "origin", source.branch)
        git(self.work, "checkout", "development")
        successor = coordinator.AcceptedSource(branch=source.branch, sha=sha, order=source.order)
        self.github.ready_shas.add(sha)
        self.github.evidence[sha] = {"schemaVersion": 1, "headSha": sha, "classification": "tests"}
        return successor

    def phase_record(self, result: dict[str, object]) -> tuple[Path, dict[str, object]]:
        state_dir = Path(str(result["stateDir"]))
        path = state_dir / "phase-delivery-record.json"
        return path, json.loads(path.read_text(encoding="utf-8"))

    def assemble(self, sources: list[coordinator.AcceptedSource], **kwargs):
        ordered = [
            coordinator.AcceptedSource(branch=item.branch, sha=item.sha, order=index)
            for index, item in enumerate(sources, start=1)
        ]
        prefix = kwargs.get("phase_branch_prefix")
        return coordinator.assemble_phase(
            repo=self.work,
            repository="owner/name",
            sources=ordered,
            github=kwargs.get("github", self.github),
            pusher=kwargs.get("pusher", coordinator.GitPushAdapter(prefix or coordinator.DEFAULT_PHASE_PREFIX)),
            phase_branch=kwargs.get("phase_branch", "phase/next"),
            phase_branch_prefix=prefix,
            require_evidence=kwargs.get("require_evidence", True),
            expected_repository=kwargs.get("expected_repository", "owner/name"),
            require_live_pr=kwargs.get("require_live_pr", False),
            evidence_payloads=kwargs.get("evidence_payloads"),
            provider_consumer_handoff=kwargs.get("provider_consumer_handoff"),
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
        self.assertEqual(git(self.fx.work, "rev-parse", "--abbrev-ref", "HEAD"), "development")
        self.assertEqual(remote_sha(self.fx.work, "phase/next"), result["headSha"])
        self.assertEqual(result["remoteSha"], result["headSha"])
        git(self.fx.work, "cat-file", "-e", f"{result['headSha']}:alpha.txt")
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
        git(self.fx.work, "cat-file", "-e", f"{result['headSha']}:one.txt")
        git(self.fx.work, "cat-file", "-e", f"{result['headSha']}:two.txt")
        log = git(self.fx.work, "log", "--oneline", f"origin/development..{result['headSha']}")
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

    def test_custom_phase_prefix_is_bound_in_coordinator_pusher_and_generated_outputs(self) -> None:
        one = self.fx.accept_issue(50, "custom-prefix.txt", "custom\n")
        result = self.fx.assemble(
            [one],
            phase_branch="wave/next",
            phase_branch_prefix="wave/",
            pusher=coordinator.GitPushAdapter("wave/"),
        )
        self.assertEqual(result["phaseBranch"], "wave/next")
        self.assertEqual(remote_sha(self.fx.work, "wave/next"), result["headSha"])
        for schema_name, payload in (
            ("phase-record.schema.json", result["record"]),
            ("phase-handoff.schema.json", result["handoff"]),
        ):
            schema_path = ROOT / "core/managed-core/schemas" / schema_name
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            errors = list(Draft202012Validator(schema).iter_errors(payload))
            self.assertEqual(errors, [], schema_name)

    def test_configured_custom_phase_prefix_is_loaded_by_assembly(self) -> None:
        one = self.fx.accept_issue(51, "configured-prefix.txt", "configured\n")
        write(
            self.fx.work / ".github/linktrend-delivery-mode.json",
            json.dumps({"schemaVersion": 1, "deliveryMode": "phase-integration", "phaseBranchPrefix": "candidate/"}),
        )
        result = self.fx.assemble(
            [one],
            phase_branch="candidate/next",
            pusher=coordinator.GitPushAdapter("candidate/"),
        )
        self.assertEqual(result["phaseBranch"], "candidate/next")
        self.assertEqual(remote_sha(self.fx.work, "candidate/next"), result["headSha"])

    def test_retained_sources_must_be_exact_leading_prefix_before_push(self) -> None:
        first = self.fx.accept_issue(52, "prefix-first.txt", "first\n")
        second = self.fx.accept_issue(53, "prefix-second.txt", "second\n")
        third = self.fx.accept_issue(54, "prefix-third.txt", "third\n")
        created = self.fx.assemble([first, second])
        before = remote_sha(self.fx.work, "phase/next")
        with self.assertRaisesRegex(coordinator.CoordinatorError, "retained accepted issues must remain"):
            self.fx.assemble([first, third, second])
        self.assertEqual(remote_sha(self.fx.work, "phase/next"), before)
        self.assertEqual(created["record"]["dependencyOrder"], [first.branch, second.branch])

    def test_same_issue_long_linear_successor_fast_forwards_and_reuses_pr(self) -> None:
        first = self.fx.accept_issue_history(34, "linear.txt", ["one\n", "two\n", "three\n", "four\n"])
        created = self.fx.assemble([first])
        successor = self.fx.advance_issue(first, "linear.txt", "five\n")
        updated = self.fx.assemble([successor])
        self.assertEqual(updated["action"], "updated")
        self.assertEqual(updated["phasePr"], created["phasePr"])
        self.assertEqual(updated["phasePr"]["number"], 1)
        self.assertNotEqual(updated["headSha"], created["headSha"])
        self.assertTrue(coordinator._is_ancestor(self.fx.work, created["headSha"], updated["headSha"]))
        self.assertEqual(remote_sha(self.fx.work, "phase/next"), updated["headSha"])
        self.assertEqual(updated["remoteSha"], updated["headSha"])
        self.assertNotEqual(updated["candidateRevision"], created["candidateRevision"])
        self.assertEqual(updated["record"]["invalidatedFromSha"], created["headSha"])
        self.assertEqual(updated["record"]["fast"]["status"], "invalidated")
        ok, detail = coordinator.consume_handoff(created["handoff"], live_head=updated["headSha"])
        self.assertFalse(ok)
        self.assertEqual(detail, "handoff_stale_head")

    def test_one_successor_among_multiple_accepted_issues_preserves_order(self) -> None:
        first = self.fx.accept_issue_history(35, "first-long.txt", ["1\n", "2\n", "3\n"])
        second = self.fx.accept_issue_history(36, "second-long.txt", ["a\n", "b\n", "c\n"])
        created = self.fx.assemble([first, second])
        successor = self.fx.advance_issue(second, "second-long.txt", "d\n")
        updated = self.fx.assemble([first, successor])
        self.assertEqual([row["branch"] for row in updated["acceptedCommits"]], [first.branch, second.branch])
        self.assertEqual(updated["phasePr"]["number"], created["phasePr"]["number"])
        self.assertTrue(coordinator._is_ancestor(self.fx.work, created["headSha"], updated["headSha"]))
        self.assertEqual(remote_sha(self.fx.work, "phase/next"), updated["headSha"])

    def test_successor_invalidates_old_receipt_and_gate_identity_without_copying_proof(self) -> None:
        first = self.fx.accept_issue_history(37, "proof.txt", ["old-1\n", "old-2\n", "old-3\n"])
        created = self.fx.assemble([first])
        path, record = self.fx.phase_record(created)
        old_head = str(created["headSha"])
        record.update(
            {
                "sealed": False,
                "sealedSha": old_head,
                "candidateId": "sha256:" + ("a" * 64),
                "candidateIdentity": {"sourceSha": old_head},
                "retainedReceipt": {"headSha": old_head, "gitTree": created["gitTree"]},
                "fast": {"status": "passed", "sha": old_head},
                "bugbot": {"status": "passed", "sha": old_head},
                "full": {"status": "passed", "sha": old_head},
                "staging": {"status": "passed", "sha": old_head},
                "release": {"status": "passed", "sha": old_head},
            }
        )
        write(path, json.dumps(record, indent=2) + "\n")
        successor = self.fx.advance_issue(first, "proof.txt", "new\n")
        updated = self.fx.assemble([successor])
        fresh = updated["record"]
        self.assertFalse(fresh["sealed"])
        self.assertIsNone(fresh["candidateId"])
        self.assertIsNone(fresh["candidateIdentity"])
        self.assertIsNone(fresh["sealedSha"])
        for gate in ("fast", "bugbot", "full", "staging", "release"):
            self.assertEqual(fresh[gate]["status"], "invalidated")
            self.assertNotIn("sha", fresh[gate])
        self.assertNotIn("retainedReceipt", fresh)
        self.assertNotEqual(updated["handoff"]["headCommit"], old_head)
        self.assertFalse(fresh["fullMayStart"]["allowed"])

    def test_reconciliation_rejects_omitted_duplicate_and_rewritten_sources_without_push(self) -> None:
        first = self.fx.accept_issue_history(38, "omit.txt", ["old\n", "older\n", "oldest\n"])
        created = self.fx.assemble([first])
        second = self.fx.accept_issue(39, "other.txt", "other\n")
        before = remote_sha(self.fx.work, "phase/next")
        with self.assertRaisesRegex(coordinator.CoordinatorError, "unique_phase_divergence"):
            self.fx.assemble([second])
        self.assertEqual(remote_sha(self.fx.work, "phase/next"), before)
        with self.assertRaisesRegex(coordinator.CoordinatorError, "duplicate_issue"):
            self.fx.assemble([first, coordinator.AcceptedSource(first.branch, first.sha, 2)])
        self.assertEqual(remote_sha(self.fx.work, "phase/next"), before)

        git(self.fx.work, "checkout", "-B", first.branch, "development")
        write(self.fx.work / "omit.txt", "rewritten\n")
        git(self.fx.work, "add", "omit.txt")
        git(self.fx.work, "commit", "-qm", "rewritten source")
        rewritten = git(self.fx.work, "rev-parse", "HEAD")
        git(self.fx.work, "push", "-q", "--force", "origin", first.branch)
        git(self.fx.work, "checkout", "development")
        self.fx.github.ready_shas.add(rewritten)
        self.fx.github.evidence[rewritten] = {"schemaVersion": 1, "headSha": rewritten, "classification": "tests"}
        with self.assertRaisesRegex(coordinator.CoordinatorError, "unique_phase_divergence"):
            self.fx.assemble([coordinator.AcceptedSource(first.branch, rewritten, 1)])
        self.assertEqual(remote_sha(self.fx.work, "phase/next"), before)

    def test_reconciliation_rejects_record_mismatch_and_stale_or_cross_repository_pr(self) -> None:
        first = self.fx.accept_issue_history(40, "identity.txt", ["one\n", "two\n", "three\n"])
        created = self.fx.assemble([first])
        successor = self.fx.advance_issue(first, "identity.txt", "four\n")
        path, record = self.fx.phase_record(created)
        record["candidateRevision"] = "tampered"
        write(path, json.dumps(record, indent=2) + "\n")
        before = remote_sha(self.fx.work, "phase/next")
        with self.assertRaisesRegex(coordinator.CoordinatorError, "invalid_phase_record"):
            self.fx.assemble([successor])
        self.assertEqual(remote_sha(self.fx.work, "phase/next"), before)
        write(path, "{\n")
        with self.assertRaisesRegex(coordinator.CoordinatorError, "invalid_phase_record"):
            self.fx.assemble([successor])
        self.assertEqual(remote_sha(self.fx.work, "phase/next"), before)
        write(path, json.dumps({**record, "candidateRevision": created["candidateRevision"]}, indent=2) + "\n")
        key = "owner/name|phase/next|development"
        self.fx.github.prs[key]["headSha"] = "a" * 40
        with self.assertRaisesRegex(coordinator.CoordinatorError, "stale_phase_pr"):
            self.fx.assemble([successor])
        self.assertEqual(remote_sha(self.fx.work, "phase/next"), before)
        self.fx.github.prs[key]["headSha"] = created["headSha"]
        self.fx.github.prs[key]["url"] = "https://github.com/other/repo/pull/1"
        with self.assertRaisesRegex(coordinator.CoordinatorError, "cross_repository_phase_pr"):
            self.fx.assemble([successor])
        self.assertEqual(remote_sha(self.fx.work, "phase/next"), before)

    def test_reconciliation_rejects_retained_repository_and_phase_identity_tamper_without_push(self) -> None:
        first = self.fx.accept_issue_history(43, "record-identity.txt", ["one\n", "two\n", "three\n"])
        created = self.fx.assemble([first])
        successor = self.fx.advance_issue(first, "record-identity.txt", "four\n")
        path, baseline = self.fx.phase_record(created)
        self.assertEqual(baseline["repository"], "owner/name")
        self.assertEqual(baseline["phaseBranch"], "phase/next")
        self.assertEqual(baseline["phaseId"], "next")

        cases = (
            ("repository tamper", {"repository": "other/name"}, ()),
            ("repository missing", {}, ("repository",)),
            ("phaseId tamper", {"phaseId": "other"}, ()),
            ("phaseId missing", {}, ("phaseId",)),
            ("phaseBranch tamper", {"phaseBranch": "phase/other"}, ()),
            ("phaseBranch missing", {}, ("phaseBranch",)),
        )
        for label, updates, removals in cases:
            with self.subTest(label=label):
                record = dict(baseline)
                record.update(updates)
                for key in removals:
                    record.pop(key, None)
                write(path, json.dumps(record, indent=2) + "\n")
                before = remote_sha(self.fx.work, "phase/next")
                with self.assertRaises(coordinator.CoordinatorError) as raised:
                    self.fx.assemble([successor])
                self.assertIn(raised.exception.code, {"invalid_phase_record", "duplicate_active_phase"})
                self.assertEqual(remote_sha(self.fx.work, "phase/next"), before)

    def test_reconciliation_rejects_duplicate_live_phase_pr_before_push(self) -> None:
        first = self.fx.accept_issue_history(42, "duplicate-pr.txt", ["one\n", "two\n", "three\n"])
        created = self.fx.assemble([first])
        successor = self.fx.advance_issue(first, "duplicate-pr.txt", "four\n")

        class DuplicateGitHub:
            repository = "owner/name"

            def __init__(self, wrapped: coordinator.MemoryGitHub) -> None:
                self.wrapped = wrapped

            def list_open_phase_prs(self, **kwargs):
                rows = self.wrapped.list_open_phase_prs(**kwargs)
                return rows + [dict(rows[0])] if rows else rows

            def __getattr__(self, name: str):
                return getattr(self.wrapped, name)

        before = remote_sha(self.fx.work, "phase/next")
        with self.assertRaisesRegex(coordinator.CoordinatorError, "duplicate_phase_pr"):
            self.fx.assemble([successor], github=DuplicateGitHub(self.fx.github))
        self.assertEqual(remote_sha(self.fx.work, "phase/next"), before)
        self.assertEqual(created["phasePr"]["number"], 1)

    def test_reconciliation_rejects_tampered_merge_and_manual_force_is_not_available(self) -> None:
        first = self.fx.accept_issue_history(41, "tamper.txt", ["one\n", "two\n", "three\n"])
        created = self.fx.assemble([first])
        successor = self.fx.advance_issue(first, "tamper.txt", "four\n")
        git(self.fx.work, "checkout", "-B", "phase/next", created["headSha"])
        git(self.fx.work, "commit", "--amend", "-qm", "tampered phase merge")
        tampered = git(self.fx.work, "rev-parse", "HEAD")
        git(self.fx.work, "push", "-q", "--force", "origin", "phase/next")
        git(self.fx.work, "checkout", "development")
        path, record = self.fx.phase_record(created)
        record["headSha"] = tampered
        record["gitTree"] = git(self.fx.work, "rev-parse", f"{tampered}^{{tree}}")
        write(path, json.dumps(record, indent=2) + "\n")
        self.fx.github.prs["owner/name|phase/next|development"]["headSha"] = tampered
        before = remote_sha(self.fx.work, "phase/next")
        with self.assertRaisesRegex(coordinator.CoordinatorError, "unique_phase_divergence"):
            self.fx.assemble([successor])
        self.assertEqual(remote_sha(self.fx.work, "phase/next"), before)
        signature = inspect.signature(coordinator.GitPushAdapter.push_phase_ref)
        self.assertNotIn("force", signature.parameters)
        self.assertNotIn("--force", inspect.getsource(coordinator.GitPushAdapter.push_phase_ref))

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

    def test_invalid_source_order_cannot_move_phase_ref(self) -> None:
        ready = self.fx.accept_issue(10, "order.txt", "order\n")
        before = remote_sha(self.fx.work, "phase/next")
        with self.assertRaisesRegex(coordinator.CoordinatorError, "invalid_source_order"):
            coordinator.assemble_phase(
                repo=self.fx.work,
                repository="owner/name",
                sources=[coordinator.AcceptedSource(ready.branch, ready.sha, 99)],
                github=self.fx.github,
                pusher=coordinator.GitPushAdapter(),
                phase_branch="phase/next",
                expected_repository="owner/name",
            )
        self.assertEqual(remote_sha(self.fx.work, "phase/next"), before)

        bare = self.fx.accept_issue(10, "noevidence.txt", "x\n", ready=False)
        with self.assertRaisesRegex(coordinator.CoordinatorError, "evidence_missing"):
            self.fx.assemble([bare])

        status_only = self.fx.accept_issue(32, "statusonly.txt", "status-only\n", ready=False)
        self.fx.github.ready_shas.add(status_only.sha)
        with self.assertRaisesRegex(coordinator.CoordinatorError, "evidence_missing"):
            self.fx.assemble([status_only])

    def test_lean_evidence_payload_accepts_without_review_ready_status(self) -> None:
        source = self.fx.accept_issue(33, "lean.txt", "lean\n", ready=False)
        tree = git(self.fx.work, "rev-parse", f"{source.sha}^{{tree}}")
        payload = {
            "schemaVersion": 1,
            "kind": "v25-issue-checkpoint",
            "headSha": source.sha,
            "gitTree": tree,
            "pushed": True,
            "scopedDiff": True,
            "focusedTests": {"passed": True},
            "independentNarrowReview": {
                "accepted": True,
                "headSha": source.sha,
                "gitTree": tree,
                "paths": ["declared-checkpoint-scope"],
                "reviewer": {"actor": "independent-reviewer", "role": "reviewer"},
                "implementerActor": "implementer",
            },
            "manifestEvidence": True,
            "classification": "tests",
            "acceptance": "PKT-05 lean checkpoint",
        }
        result = self.fx.assemble([source], evidence_payloads={source.sha: payload})
        self.assertEqual(result["acceptedCommits"][0]["sha"], source.sha)
        self.assertNotIn(source.sha, self.fx.github.ready_shas)

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
        self.fx.github.evidence[right_sha] = {
            "schemaVersion": 1,
            "headSha": right_sha,
            "classification": "tests",
            "acceptance": "lean-or-schema-v1",
        }
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
        git(self.fx.work, "cat-file", "-e", f"{result['headSha']}:wanted.txt")
        missing = subprocess.run(
            ["git", "cat-file", "-e", f"{result['headSha']}:extra.txt"],
            cwd=self.fx.work,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(missing.returncode, 0)
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

    def test_typed_provider_consumer_handoff_is_carried_and_written_separately(self) -> None:
        one = self.fx.accept_issue(171, "typed.txt", "typed\n")
        provider = {"repository": "owner/provider", "commit": "a" * 40, "tree": "b" * 40}
        consumer = {"repository": "owner/consumer", "commit": "c" * 40, "tree": "d" * 40}
        receipt = {
            "status": "accepted",
            "protected": True,
            "receiptDigest": "sha256:" + "e" * 64,
            "provider": provider,
        }
        typed = coordinator.build_provider_consumer_handoff(
            provider=provider,
            consumer=consumer,
            artifact_digest="sha256:" + "f" * 64,
            contract_digest="sha256:" + "1" * 64,
            verdict="accepted",
            lifecycle_state="accepted",
            accepted_receipt=receipt,
        )
        result = self.fx.assemble([one], provider_consumer_handoff=typed)
        self.assertEqual(result["providerConsumerHandoff"], typed)
        state_dir = Path(result["stateDir"])
        self.assertEqual(
            json.loads((state_dir / "provider-consumer-handoff.json").read_text(encoding="utf-8")),
            typed,
        )
        phase_schema_path = ROOT / "core/managed-core/schemas/phase-handoff.schema.json"
        phase_schema = json.loads(phase_schema_path.read_text(encoding="utf-8"))
        typed_schema_path = ROOT / "core/managed-core/schemas/provider-consumer-handoff.schema.json"
        typed_schema = json.loads(typed_schema_path.read_text(encoding="utf-8"))
        resolver = RefResolver(
            phase_schema_path.as_uri(),
            phase_schema,
            store={typed_schema_path.as_uri(): typed_schema, typed_schema["$id"]: typed_schema},
        )
        errors = list(Draft202012Validator(phase_schema, resolver=resolver).iter_errors(result["handoff"]))
        self.assertEqual(errors, [])

    def test_does_not_push_protected_branches(self) -> None:
        one = self.fx.accept_issue(18, "protect.txt", "protect\n")
        before = git(self.fx.work, "rev-parse", "origin/development")
        result = self.fx.assemble([one])
        after = git(self.fx.work, "rev-parse", "origin/development")
        self.assertEqual(before, after)
        self.assertEqual(git(self.fx.work, "rev-parse", "--abbrev-ref", "HEAD"), "development")
        self.assertEqual(remote_sha(self.fx.work, "phase/next"), result["headSha"])
        with self.assertRaisesRegex(coordinator.CoordinatorError, "invalid_phase_branch"):
            coordinator.assemble_phase(
                repo=self.fx.work,
                repository="owner/name",
                sources=[one],
                github=self.fx.github,
                pusher=coordinator.GitPushAdapter(),
                phase_branch="development",
            )


class PhasePackagerCoordinatorAdversarialTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fx = Fixture()
        self.addCleanup(self.fx.cleanup)

    def test_cli_assemble_refuses_memory_github_without_credentials(self) -> None:
        one = self.fx.accept_issue(21, "cli.txt", "cli\n")
        env_keys = (
            "AUTOMATION_TOKEN",
            "AUTOMATION_TOKEN_SOURCE",
            "LINKTREND_BUGBOT_USER_TOKEN",
            "BUGBOT_USER_TOKEN",
            "GH_TOKEN",
            "GITHUB_TOKEN",
        )
        saved = {key: os.environ.pop(key, None) for key in env_keys}
        stdout = io.StringIO()
        try:
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(io.StringIO()):
                code = coordinator.main(
                    [
                        "assemble",
                        "--repository",
                        "owner/name",
                        "--repo-path",
                        str(self.fx.work),
                        "--phase-branch",
                        "phase/next",
                        "--accept",
                        f"{one.branch}@{one.sha}",
                        "--no-evidence",
                    ]
                )
        finally:
            for key, value in saved.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
        payload = json.loads(stdout.getvalue())
        self.assertEqual(code, 2)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["code"], "missing_github_credentials")
        self.assertNotIn("example.invalid", stdout.getvalue())
        self.assertNotIn("example.invalid", json.dumps(payload))
        self.assertEqual(remote_sha(self.fx.work, "phase/next"), "")

    def test_cli_wires_configured_phase_prefix_to_production_adapters(self) -> None:
        source = self.fx.accept_issue(58, "cli-prefix.txt", "cli prefix\n")
        write(
            self.fx.work / ".github/linktrend-delivery-mode.json",
            json.dumps({"schemaVersion": 1, "deliveryMode": "phase-integration", "phaseBranchPrefix": "candidate/"}),
        )
        observed: dict[str, object] = {}

        def fake_resolve(repository: str, *, phase_branch_prefix: str):
            observed["adapterRepository"] = repository
            observed["adapterPrefix"] = phase_branch_prefix
            return self.fx.github, coordinator.GitPushAdapter(phase_branch_prefix)

        def fake_assemble(**kwargs):
            observed.update(kwargs)
            return {"ok": True}

        stdout = io.StringIO()
        with patch.object(coordinator, "resolve_production_adapters", fake_resolve), patch.object(
            coordinator, "assemble_phase", fake_assemble
        ), contextlib.redirect_stdout(stdout):
            code = coordinator.main(
                [
                    "assemble",
                    "--repository",
                    "owner/name",
                    "--repo-path",
                    str(self.fx.work),
                    "--accept",
                    f"{source.branch}@{source.sha}",
                    "--no-evidence",
                ]
            )
        self.assertEqual(code, 0)
        self.assertEqual(observed["adapterRepository"], "owner/name")
        self.assertEqual(observed["adapterPrefix"], "candidate/")
        self.assertEqual(observed["phase_branch_prefix"], "candidate/")
        self.assertEqual(observed["phase_branch"], "candidate/next")

    def test_production_success_rejects_example_invalid_pr(self) -> None:
        one = self.fx.accept_issue(22, "livepr.txt", "live\n")
        with self.assertRaisesRegex(coordinator.CoordinatorError, "invalid_phase_pr"):
            self.fx.assemble([one], require_live_pr=True)
        self.assertEqual(remote_sha(self.fx.work, "phase/next"), "")

    def test_malformed_phase_branch_cannot_move_any_phase_ref(self) -> None:
        one = self.fx.accept_issue(27, "badbranch.txt", "badbranch\n")
        for phase_branch in ("phase/", "phase/a/b", "phase/-", "phase/.", "phase/a..b", "phase/a~b"):
            with self.subTest(phase_branch=phase_branch):
                with self.assertRaisesRegex(coordinator.CoordinatorError, "invalid_phase_branch"):
                    self.fx.assemble([one], phase_branch=phase_branch, require_evidence=False)
                self.assertEqual(remote_sha(self.fx.work, phase_branch), "")

    def _live_transport(
        self,
        *,
        url: str,
        draft: bool,
        sha: str | None = None,
        head_variant: str | None = None,
    ):
        created: dict[str, object] = {}

        def transport(method: str, request_url: str, token: str, body):
            if method == "GET" and "/pulls?" in request_url:
                return [dict(created)] if created else []
            if method == "GET" and request_url.endswith("/pulls/42"):
                readback = dict(created)
                readback.update(
                    {
                        "html_url": "https://github.com/owner/name/pull/42",
                        "draft": created.get("draft") if isinstance(created.get("draft"), bool) else True,
                        "head": {"ref": "phase/next", "sha": remote_sha(self.fx.work, "phase/next")},
                        "base": {"ref": "development"},
                        "state": created.get("state", "open"),
                    }
                )
                return readback
            if method == "POST" and request_url.endswith("/pulls"):
                head_sha = sha or remote_sha(self.fx.work, "phase/next")
                head = {} if head_variant == "missing" else {"sha": head_variant or head_sha}
                created.update(
                    {
                        "number": 42,
                        "html_url": url,
                        "draft": draft,
                        "head": {"ref": "phase/next", **head},
                        "base": {"ref": "development"},
                        "title": body.get("title") if isinstance(body, dict) else "Phase: phase/next",
                        "body": body.get("body") if isinstance(body, dict) else "",
                        "state": "open",
                    }
                )
                return dict(created)
            if method == "PATCH":
                if isinstance(body, dict) and body.get("state") == "closed":
                    created["state"] = "closed"
                elif isinstance(body, dict):
                    created.update({key: body[key] for key in ("title", "body") if key in body})
                return dict(created)
            raise AssertionError(f"unexpected GitHub call {method} {request_url}")

        return coordinator.LiveGitHub(
            repository="owner/name",
            automation_token="ltfx.coordinator.auto_token.v1",
            user_token="ltfx.coordinator.user_token.v1",
            transport=transport,
        )

    def test_live_draft_fields_must_be_unambiguous_booleans(self) -> None:
        live = self._live_transport(url="https://github.com/owner/name/pull/42", draft=True)
        valid = {
            "number": 42,
            "html_url": "https://github.com/owner/name/pull/42",
            "head": {"ref": "phase/next", "sha": "a" * 40},
            "base": {"ref": "development"},
        }
        for fields in (
            {"draft": True, "isDraft": False},
            {"draft": "true"},
            {"draft": 1},
            {"draft": None},
            {"draft": True, "isDraft": "true"},
            {},
        ):
            with self.subTest(fields=fields):
                with self.assertRaisesRegex(coordinator.CoordinatorError, "invalid_phase_pr"):
                    live._pr_identity(dict(valid, **fields), created=False)

    def test_live_pr_lists_reject_malformed_mixed_entries(self) -> None:
        def transport(method: str, request_url: str, token: str, body):
            if method == "GET" and "/pulls?" in request_url:
                return [
                    {
                        "number": 7,
                        "html_url": "https://github.com/owner/name/pull/7",
                        "draft": True,
                        "head": {"ref": "phase/next", "sha": "a" * 40},
                        "base": {"ref": "development"},
                    },
                    "malformed-entry",
                ]
            raise AssertionError(f"unexpected GitHub call {method} {request_url}")

        live = coordinator.LiveGitHub(
            repository="owner/name",
            automation_token="auto",
            user_token="user",
            transport=transport,
        )
        with self.assertRaisesRegex(coordinator.CoordinatorError, "invalid_phase_pr"):
            live.list_open_phase_prs(repository="owner/name", head="phase/next", base="development")

    def test_new_pr_and_phase_ref_are_compensated_after_state_write_failure(self) -> None:
        one = self.fx.accept_issue(70, "transaction-new.txt", "new transaction\n")
        with patch.object(coordinator, "_write_isolated_state", side_effect=OSError("state write failed")):
            with self.assertRaisesRegex(OSError, "state write failed"):
                self.fx.assemble([one], phase_branch="phase/transaction-new")
        self.assertEqual(self.fx.github.prs, {})
        self.assertEqual(remote_sha(self.fx.work, "phase/transaction-new"), "")
        self.assertEqual(
            git(self.fx.work, "rev-parse", "--verify", "refs/remotes/origin/phase/transaction-new", check=False),
            "",
        )

    def test_live_new_pr_compensation_order_is_readback_close_readback(self) -> None:
        one = self.fx.accept_issue(74, "live-transaction.txt", "live transaction\n")
        calls: list[str] = []
        created: dict[str, object] = {}

        def transport(method: str, request_url: str, token: str, body):
            if method == "GET" and "/pulls?" in request_url:
                calls.append("GET:list")
                return [dict(created)] if created else []
            if method == "POST" and request_url.endswith("/pulls"):
                calls.append("POST:create")
                created.update(
                    {
                        "number": 74,
                        "html_url": "https://github.com/owner/name/pull/74",
                        "draft": True,
                        "head": {"ref": "phase/live-transaction", "sha": remote_sha(self.fx.work, "phase/live-transaction")},
                        "base": {"ref": "development"},
                        "title": body["title"],
                        "body": body["body"],
                        "state": "open",
                    }
                )
                return dict(created)
            if method == "GET" and request_url.endswith("/pulls/74"):
                calls.append("GET:item")
                return dict(created)
            if method == "PATCH" and request_url.endswith("/pulls/74"):
                calls.append("PATCH:close")
                created["state"] = "closed"
                return dict(created)
            raise AssertionError(f"unexpected GitHub call {method} {request_url}")

        live = coordinator.LiveGitHub(
            repository="owner/name",
            automation_token="auto",
            user_token="user",
            transport=transport,
        )
        with patch.object(coordinator, "_write_isolated_state", side_effect=OSError("state write failed")):
            with self.assertRaisesRegex(OSError, "state write failed"):
                self.fx.assemble(
                    [one],
                    github=live,
                    phase_branch="phase/live-transaction",
                    require_live_pr=True,
                    require_evidence=False,
                )
        self.assertEqual(
            calls,
            ["GET:list", "GET:list", "POST:create", "GET:list", "GET:item", "PATCH:close", "GET:item"],
        )
        self.assertEqual(created["state"], "closed")
        self.assertEqual(remote_sha(self.fx.work, "phase/live-transaction"), "")

    def test_existing_pr_and_phase_ref_restore_exact_state_after_state_write_failure(self) -> None:
        first = self.fx.accept_issue_history(71, "transaction-existing.txt", ["one\n", "two\n", "three\n"])
        created = self.fx.assemble([first])
        key = "owner/name|phase/next|development"
        prior_pr = json.loads(json.dumps(self.fx.github.prs[key]))
        prior_tracking = git(self.fx.work, "rev-parse", "refs/remotes/origin/phase/next")
        successor = self.fx.advance_issue(first, "transaction-existing.txt", "four\n")
        with patch.object(coordinator, "_write_isolated_state", side_effect=OSError("state write failed")):
            with self.assertRaisesRegex(OSError, "state write failed"):
                self.fx.assemble([successor])
        self.assertEqual(self.fx.github.prs[key], prior_pr)
        self.assertEqual(remote_sha(self.fx.work, "phase/next"), created["headSha"])
        self.assertEqual(git(self.fx.work, "rev-parse", "refs/remotes/origin/phase/next"), prior_tracking)

    def test_compensation_failure_is_explicit_and_ref_is_still_attempted(self) -> None:
        one = self.fx.accept_issue(72, "compensation-failure.txt", "compensation\n")

        class Uncompensable:
            repository = "owner/name"

            def __init__(self, wrapped):
                self.wrapped = wrapped

            def __getattr__(self, name: str):
                return getattr(self.wrapped, name)

            def rollback_phase_pr(self, mutation):
                raise coordinator.CoordinatorError("pr_compensation_failed", "synthetic close readback failure")

        with patch.object(coordinator, "_write_isolated_state", side_effect=OSError("state write failed")):
            with self.assertRaisesRegex(coordinator.CoordinatorError, "pr_compensation_failed"):
                self.fx.assemble([one], github=Uncompensable(self.fx.github), phase_branch="phase/compensation")
        self.assertEqual(remote_sha(self.fx.work, "phase/compensation"), "")
        self.assertEqual(
            git(self.fx.work, "rev-parse", "--verify", "refs/remotes/origin/phase/compensation", check=False),
            "",
        )

    def test_new_ref_replacement_race_is_not_deleted_and_tracking_witness_is_cleaned(self) -> None:
        one = self.fx.accept_issue(73, "ref-race.txt", "race\n")
        alternate = self.fx.development_sha()

        class RacingPusher:
            def push_phase_ref(self, repo, remote, branch, sha):
                verified = coordinator.GitPushAdapter().push_phase_ref(repo, remote, branch, sha)
                git(repo, "push", "-q", "--force", "--", remote, f"{alternate}:refs/heads/{branch}")
                git(repo, "update-ref", f"refs/remotes/{remote}/{branch}", verified)
                return verified

        with patch.object(coordinator, "_write_isolated_state", side_effect=OSError("state write failed")):
            with self.assertRaisesRegex(coordinator.CoordinatorError, "phase_ref_rollback_failed"):
                self.fx.assemble([one], phase_branch="phase/ref-race", pusher=RacingPusher())
        self.assertEqual(remote_sha(self.fx.work, "phase/ref-race"), alternate)
        self.assertEqual(
            git(self.fx.work, "rev-parse", "--verify", "refs/remotes/origin/phase/ref-race", check=False),
            "",
        )
        self.assertIn("--force-with-lease=refs/heads/{phase_branch}:{current}", inspect.getsource(coordinator._rollback_phase_ref))

    def test_live_github_rejects_example_invalid_pr_url(self) -> None:
        invalid = self.fx.accept_issue(28, "badurl.txt", "badurl\n")
        with self.assertRaisesRegex(coordinator.CoordinatorError, "invalid_phase_pr"):
            self.fx.assemble(
                [invalid],
                github=self._live_transport(url="https://example.invalid/owner/name/pull/42", draft=True),
                require_live_pr=True,
                require_evidence=False,
            )

    def test_live_invalid_pr_url_is_rejected_before_successor_push(self) -> None:
        first = self.fx.accept_issue_history(45, "live-identity.txt", ["one\n", "two\n", "three\n"])
        created = self.fx.assemble([first])
        successor = self.fx.advance_issue(first, "live-identity.txt", "four\n")
        calls: list[str] = []

        def transport(method: str, request_url: str, token: str, body):
            calls.append(method)
            if method == "GET" and "/pulls?" in request_url:
                return [
                    {
                        "number": created["phasePr"]["number"],
                        "html_url": "https://evil.example/owner/name/pull/1",
                        "draft": True,
                        "head": {"ref": "phase/next", "sha": created["headSha"]},
                        "base": {"ref": "development"},
                    }
                ]
            raise AssertionError(f"unexpected GitHub call {method} {request_url}")

        live = self._live_transport(url="https://github.com/owner/name/pull/42", draft=True)
        live.transport = transport

        class CountingPusher:
            def __init__(self) -> None:
                self.calls = 0

            def push_phase_ref(self, *args, **kwargs):
                self.calls += 1
                return coordinator.GitPushAdapter().push_phase_ref(*args, **kwargs)

        pusher = CountingPusher()
        before = remote_sha(self.fx.work, "phase/next")
        with self.assertRaisesRegex(coordinator.CoordinatorError, "cross_repository_phase_pr"):
            self.fx.assemble(
                [successor],
                github=live,
                pusher=pusher,
                require_live_pr=True,
                require_evidence=False,
            )
        self.assertEqual(pusher.calls, 0)
        self.assertEqual(remote_sha(self.fx.work, "phase/next"), before)
        self.assertEqual(calls, ["GET"])

    def test_local_origin_repository_mismatch_cannot_move_phase_ref(self) -> None:
        one = self.fx.accept_issue(46, "remote-mismatch.txt", "remote mismatch\n")
        git(self.fx.work, "remote", "set-url", "origin", "https://github.com/other/name.git")
        before = remote_sha(self.fx.work, "phase/next")
        with self.assertRaisesRegex(coordinator.CoordinatorError, "wrong_repository"):
            self.fx.assemble([one], require_evidence=False)
        self.assertEqual(remote_sha(self.fx.work, "phase/next"), before)

    def test_remote_identity_parser_rejects_ambiguous_github_forms(self) -> None:
        valid = (
            "https://github.com/owner/name.git",
            "https://github.com:443/owner/name.git",
            "ssh://git@github.com/owner/name.git",
            "ssh://org-123@github.com:22/owner/name.git",
            "git@github.com:owner/name.git",
            "org-123@github.com:owner/name.git",
        )
        invalid = (
            "https://user:secret@github.com/owner/name.git",
            "https://github.com.evil/owner/name.git",
            "https://GITHUB.com/owner/name.git",
            "https://github.com/owner/name.git?x=1",
            "https://github.com/owner/name.git/extra",
            "ssh://git@github.com.evil/owner/name.git",
            "git@github.com:owner/../name.git",
            "git@github.com:../name.git",
            "https://github.com/../name.git",
            "https://github.com/owner/..git",
            "https://github.com//owner/name.git",
            "https://github.com///owner/name.git",
            "https://github.com/owner//name.git",
            "https://github.com/owner/....git",
            "https://github.com/%2Fowner/name.git",
            "https://github.com/owner/%2E%2E.git",
            "git@github.com:owner/....git",
            "file:///tmp/owner/name.git",
        )
        for url in valid:
            with self.subTest(url=url):
                self.assertEqual(coordinator._repository_from_remote_url(url), "owner/name")
        for url in invalid:
            with self.subTest(url=url):
                self.assertIsNone(coordinator._repository_from_remote_url(url))

    def test_phase_pr_url_identity_is_canonical_and_exact(self) -> None:
        self.assertTrue(coordinator._phase_pr_url_matches_repository(
            "https://github.com/owner/name/pull/7", "owner/name", 7
        ))
        for url in (
            "https://evil.example/owner/name/pull/7",
            "http://github.com/owner/name/pull/7",
            "https://github.com/Owner/name/pull/7",
            "https://github.com/owner/name/pull/8",
            "https://github.com/owner/name/pull/7?x=1",
            "https://github.com/owner/name/pull/7#fragment",
            "https://github.com/owner/name/pull/7/",
        ):
            with self.subTest(url=url):
                self.assertFalse(coordinator._phase_pr_url_matches_repository(url, "owner/name", 7))

    def test_live_github_rejects_non_draft_pr(self) -> None:
        ready = self.fx.accept_issue(29, "nondraft.txt", "nondraft\n")
        with self.assertRaisesRegex(coordinator.CoordinatorError, "phase_pr_not_draft"):
            self.fx.assemble(
                [ready],
                github=self._live_transport(url="https://github.com/owner/name/pull/42", draft=False),
                require_live_pr=True,
                require_evidence=False,
            )

    def test_live_github_rejects_malformed_draft_without_residual_new_phase_ref(self) -> None:
        for index, draft in enumerate(("false", 0, 1, None), start=1):
            with self.subTest(draft=draft):
                ready = self.fx.accept_issue(55 + index, f"malformed-draft-{index}.txt", "malformed draft\n")
                with self.assertRaisesRegex(coordinator.CoordinatorError, "invalid_phase_pr"):
                    self.fx.assemble(
                        [ready],
                        github=self._live_transport(
                            url=f"https://github.com/owner/name/pull/{55 + index}",
                            draft=draft,
                        ),
                        require_live_pr=True,
                        require_evidence=False,
                    )
                self.assertEqual(remote_sha(self.fx.work, "phase/next"), "")

    def test_live_github_requires_exact_lowercase_nonzero_head_and_rolls_back_new_ref(self) -> None:
        for index, (label, head_variant) in enumerate(
            (
            ("missing", "missing"),
            ("malformed", "not-a-sha"),
            ("uppercase", "A" * 40),
            ("zero", "0" * 40),
            ("mismatch", "a" * 40),
            ),
            start=1,
        ):
            with self.subTest(label=label):
                ready = self.fx.accept_issue(60 + index, f"head-{label}.txt", f"{label}\n")
                phase_branch = f"phase/{label}"
                live = self._live_transport(
                    url=f"https://github.com/owner/name/pull/{60 + index}",
                    draft=True,
                    head_variant=head_variant,
                )
                with self.assertRaisesRegex(coordinator.CoordinatorError, "stale_phase_pr"):
                    self.fx.assemble(
                        [ready],
                        github=live,
                        phase_branch=phase_branch,
                        require_live_pr=True,
                        require_evidence=False,
                    )
                self.assertEqual(remote_sha(self.fx.work, phase_branch), "")

    def test_successor_live_witness_failure_restores_preexisting_phase_ref(self) -> None:
        first = self.fx.accept_issue_history(57, "successor-witness.txt", ["one\n", "two\n", "three\n"])
        created = self.fx.assemble([first])
        successor = self.fx.advance_issue(first, "successor-witness.txt", "four\n")

        class BadHeadAfterPush:
            repository = "owner/name"

            def __init__(self, wrapped):
                self.wrapped = wrapped

            def list_open_phase_prs(self, **kwargs):
                return self.wrapped.list_open_phase_prs(**kwargs)

            def ensure_draft_phase_pr(self, **kwargs):
                result = self.wrapped.ensure_draft_phase_pr(**kwargs)
                result["headSha"] = "not-a-sha"
                return result

            def __getattr__(self, name: str):
                return getattr(self.wrapped, name)

        before = remote_sha(self.fx.work, "phase/next")
        with self.assertRaisesRegex(coordinator.CoordinatorError, "stale_phase_pr"):
            self.fx.assemble(
                [successor],
                github=BadHeadAfterPush(self.fx.github),
                require_evidence=False,
            )
        self.assertEqual(before, created["headSha"])
        self.assertEqual(remote_sha(self.fx.work, "phase/next"), before)

    def test_live_github_success_requires_real_draft_pr_and_remote_sha(self) -> None:
        one = self.fx.accept_issue(30, "goodpr.txt", "goodpr\n")
        result = self.fx.assemble(
            [one],
            github=self._live_transport(url="https://github.com/owner/name/pull/42", draft=True),
            require_live_pr=True,
            require_evidence=False,
        )
        self.assertEqual(result["phasePr"]["number"], 42)
        self.assertEqual(result["phasePr"]["url"], "https://github.com/owner/name/pull/42")
        self.assertTrue(result["phasePr"]["isDraft"])
        self.assertEqual(remote_sha(self.fx.work, "phase/next"), result["headSha"])
        self.assertNotIn("example.invalid", json.dumps(result["phasePr"]))

    def test_success_requires_verified_remote_phase_ref(self) -> None:
        one = self.fx.accept_issue(23, "push.txt", "push\n")
        result = self.fx.assemble([one])
        self.assertEqual(remote_sha(self.fx.work, "phase/next"), result["headSha"])
        self.assertEqual(result["remoteSha"], result["headSha"])
        self.assertEqual(result["phasePr"]["number"], 1)

    def test_existing_unique_phase_work_is_preserved(self) -> None:
        one = self.fx.accept_issue(24, "keep.txt", "keep\n")
        git(self.fx.work, "checkout", "-B", "phase/next", "development")
        write(self.fx.work / "unique.txt", "unique phase work\n")
        git(self.fx.work, "add", "unique.txt")
        git(self.fx.work, "commit", "-qm", "unique phase work")
        unique_sha = git(self.fx.work, "rev-parse", "HEAD")
        git(self.fx.work, "push", "-q", "-u", "origin", "phase/next")
        git(self.fx.work, "checkout", "development")
        with self.assertRaisesRegex(coordinator.CoordinatorError, "unique_phase_divergence"):
            self.fx.assemble([one])
        self.assertEqual(remote_sha(self.fx.work, "phase/next"), unique_sha)
        git(self.fx.work, "cat-file", "-e", f"{unique_sha}:unique.txt")
        self.assertEqual(git(self.fx.work, "rev-parse", "--abbrev-ref", "HEAD"), "development")

    def test_unique_commits_on_assembled_phase_block_identical_reuse(self) -> None:
        one = self.fx.accept_issue(31, "keep2.txt", "keep2\n")
        created = self.fx.assemble([one])
        git(self.fx.work, "checkout", "-B", "phase/next", created["headSha"])
        write(self.fx.work / "unique-reuse.txt", "unique reuse work\n")
        git(self.fx.work, "add", "unique-reuse.txt")
        git(self.fx.work, "commit", "-qm", "unique reuse work")
        unique_sha = git(self.fx.work, "rev-parse", "HEAD")
        git(self.fx.work, "push", "-q", "origin", "phase/next")
        git(self.fx.work, "checkout", "development")
        with self.assertRaisesRegex(coordinator.CoordinatorError, "unique_phase_divergence"):
            self.fx.assemble([one])
        self.assertEqual(remote_sha(self.fx.work, "phase/next"), unique_sha)
        git(self.fx.work, "cat-file", "-e", f"{unique_sha}:unique-reuse.txt")
        git(self.fx.work, "cat-file", "-e", f"{unique_sha}:keep2.txt")
        self.assertEqual(git(self.fx.work, "rev-parse", "--abbrev-ref", "HEAD"), "development")

    def test_existing_phase_drift_is_rejected(self) -> None:
        one = self.fx.accept_issue(25, "drift.txt", "drift\n")
        created = self.fx.assemble([one])
        git(self.fx.work, "checkout", "-B", "phase/next", created["headSha"])
        write(self.fx.work / "drifted.txt", "drifted\n")
        git(self.fx.work, "add", "drifted.txt")
        git(self.fx.work, "commit", "-qm", "drifted phase")
        drifted = git(self.fx.work, "rev-parse", "HEAD")
        git(self.fx.work, "push", "-q", "origin", "phase/next")
        git(self.fx.work, "update-ref", "refs/heads/phase/next", created["headSha"])
        git(self.fx.work, "checkout", "development")
        with self.assertRaisesRegex(coordinator.CoordinatorError, "phase_ref_drift"):
            self.fx.assemble([one])
        self.assertEqual(remote_sha(self.fx.work, "phase/next"), drifted)

    def test_assemble_uses_isolated_worktree_and_state(self) -> None:
        one = self.fx.accept_issue(26, "isolated.txt", "isolated\n")
        caller_head = git(self.fx.work, "rev-parse", "HEAD")
        result = self.fx.assemble([one])
        self.assertEqual(git(self.fx.work, "rev-parse", "HEAD"), caller_head)
        self.assertEqual(git(self.fx.work, "rev-parse", "--abbrev-ref", "HEAD"), "development")
        self.assertFalse((self.fx.work / "isolated.txt").exists())
        self.assertFalse((self.fx.work / ".linktrend" / "phase-handoff.json").exists())
        state_dir = Path(result["stateDir"])
        self.assertTrue(state_dir.is_dir())
        self.assertTrue((state_dir / "phase-handoff.json").is_file())
        self.assertTrue((state_dir / "phase-delivery-record.json").is_file())
        common = Path(git(self.fx.work, "rev-parse", "--git-common-dir"))
        if not common.is_absolute():
            common = (self.fx.work / common).resolve()
        self.assertEqual(
            state_dir.resolve().relative_to(common.resolve()).parts[:2],
            ("ide-development", "phase-packager"),
        )
        listed = git(self.fx.work, "worktree", "list", "--porcelain")
        self.assertNotIn("phase-assemble", listed)

    def test_index_manifest_schema_and_hosted_fast_cover_coordinator(self) -> None:
        index = (ROOT / "core/managed-core/INDEX.yaml").read_text(encoding="utf-8")
        self.assertIn("schemas/phase-handoff.schema.json", index)
        self.assertIn("schemas/phase-record.schema.json", index)
        self.assertIn("core/managed-core/schemas/phase-handoff.schema.json", RC_REQUIRED_SCHEMA_RELS)
        self.assertIn("core/managed-core/schemas/phase-record.schema.json", RC_REQUIRED_SCHEMA_RELS)
        manifest = json.loads((ROOT / "core/managed-core/MANIFEST.json").read_text(encoding="utf-8"))
        sources = {row["source"] for row in manifest["files"]}
        self.assertIn("core/managed-core/schemas/phase-handoff.schema.json", sources)
        self.assertIn("core/managed-core/schemas/phase-record.schema.json", sources)
        self.assertIn("scripts/gitops/packager_coordinator.py", sources)
        self.assertIn("scripts/tests/test_phase_packager_coordinator.py", sources)
        index_entry = next(row for row in manifest["files"] if row["source"] == "core/managed-core/INDEX.yaml")
        index_digest = "sha256:" + hashlib.sha256((ROOT / "core/managed-core/INDEX.yaml").read_bytes()).hexdigest()
        self.assertEqual(index_entry["sourceHash"], index_digest)
        runtime = json.loads((ROOT / "core/github/managed-runtime/MANIFEST.json").read_text(encoding="utf-8"))
        self.assertIn("scripts/gitops/packager_coordinator.py", runtime["files"])
        fast = json.loads((ROOT / ".github/linktrend-delivery-mode.json").read_text(encoding="utf-8"))
        blob = json.dumps(fast["profiles"]["fast"]["commands"])
        self.assertIn("packager_coordinator.py", blob)
        self.assertIn("test_phase_packager_coordinator", blob)
        one = self.fx.accept_issue(27, "schema.txt", "schema\n")
        result = self.fx.assemble([one])
        handoff_schema = json.loads(
            (ROOT / "core/managed-core/schemas/phase-handoff.schema.json").read_text(encoding="utf-8")
        )
        record_schema = json.loads(
            (ROOT / "core/managed-core/schemas/phase-record.schema.json").read_text(encoding="utf-8")
        )
        for key in handoff_schema["required"]:
            self.assertIn(key, result["handoff"])
        extra_handoff = set(result["handoff"]) - set(handoff_schema["properties"])
        self.assertEqual(extra_handoff, set())
        for key in record_schema["required"]:
            self.assertIn(key, result["record"])

    def test_memory_github_stays_test_only(self) -> None:
        self.assertIn("Never talks to GitHub", coordinator.MemoryGitHub.__doc__)
        adapters = coordinator.resolve_production_adapters
        with self.assertRaisesRegex(coordinator.CoordinatorError, "missing_github_credentials"):
            adapters("owner/name")


if __name__ == "__main__":
    unittest.main()
