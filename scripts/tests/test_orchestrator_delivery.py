#!/usr/bin/env python3
"""Tests for the v3 orchestrator delivery scripts (stdlib only, no network).

package.py and promote_main.py run against temp repos with a local bare remote;
merge_check.py and promotion_check.py get a fake GitHub API via ``github_api.from_env``.
"""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "orchestrator"))

import git_local  # noqa: E402
import github_api  # noqa: E402
import merge_check  # noqa: E402
import package  # noqa: E402
import promote_main  # noqa: E402
import promotion_check  # noqa: E402

REPO = "linktrend/Fixture"
GIT_TEST_CONFIG = (
    "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false",
    "-c", "init.defaultBranch=development", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
)


def git(cwd: Path, *args: str) -> str:
    proc = subprocess.run(["git", *GIT_TEST_CONFIG, *args], cwd=cwd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {proc.stderr}")
    return proc.stdout.strip()


def commit_file(cwd: Path, name: str, text: str, message: str) -> str:
    path = cwd / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    git(cwd, "add", name)
    git(cwd, "commit", "-q", "-m", message)
    return git(cwd, "rev-parse", "HEAD")


def run_main(module: Any, argv: list[str]) -> tuple[int, dict[str, Any]]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = module.main(argv)
    return code, json.loads(buf.getvalue())


class RemoteFixture:
    """A bare ``origin`` plus a seed clone for authoring and a work clone for the scripts."""

    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        base = Path(self._tmp.name)
        self.remote = base / "origin.git"
        self.seed = base / "seed"
        self.work = base / "work"
        git(base, "init", "-q", "--bare", str(self.remote))
        git(base, "init", "-q", str(self.seed))
        git(self.seed, "remote", "add", "origin", str(self.remote))
        commit_file(self.seed, "shared.txt", "base\n", "base")
        git(self.seed, "push", "-q", "origin", "HEAD:refs/heads/development", "HEAD:refs/heads/main")
        git(base, "clone", "-q", str(self.remote), str(self.work))
        for key, value in (("user.name", "Orchestrator"), ("user.email", "orch@example.invalid"),
                           ("commit.gpgsign", "false")):
            git(self.work, "config", key, value)

    def branch(self, name: str, start: str, files: dict[str, str]) -> str:
        git(self.seed, "checkout", "-q", "-B", name, start)
        sha = ""
        for fname, text in files.items():
            sha = commit_file(self.seed, fname, text, f"{name}: {fname}")
        git(self.seed, "push", "-q", "-f", "origin", f"{name}:refs/heads/{name}")
        return sha

    def remote_sha(self, branch: str) -> str:
        return git(self.remote, "rev-parse", f"refs/heads/{branch}")

    def cleanup(self) -> None:
        self._tmp.cleanup()


class FakeApi:
    def __init__(
        self,
        runs: dict[str, list[dict[str, Any]]] | None = None,
        pull: dict[str, Any] | None = None,
        statuses: dict[str, list[dict[str, Any]]] | None = None,
        files: list[dict[str, Any]] | None = None,
    ):
        self.runs = runs or {}
        self._pull = pull or {}
        self.statuses = statuses or {}
        self.files = files or []
        self.fail_actions = False
        self.calls: list[tuple[str, str]] = []
        self._workflows: dict[str, dict[str, Any]] = {}
        self._suites: dict[int, list[dict[str, Any]]] = {}

    def pull(self, repo: str, number: int) -> dict[str, Any]:
        return self._pull

    def pull_files(self, repo: str, number: int) -> list[dict[str, Any]]:
        self.calls.append(("pull_files", str(number)))
        return list(self.files)

    def check_runs(self, repo: str, sha: str) -> list[dict[str, Any]]:
        self.calls.append(("check_runs", sha))
        rows = self.runs.get(sha, [])
        for row in rows:
            workflow = row.get("_workflow_run")
            if not isinstance(workflow, dict):
                continue
            stored = dict(workflow)
            if not stored.get("head_sha"):
                stored["head_sha"] = sha
            self._workflows[str(stored.get("id"))] = stored
            suite = row.get("check_suite") if isinstance(row.get("check_suite"), dict) else {}
            suite_id = suite.get("id")
            if isinstance(suite_id, int) and not isinstance(suite_id, bool):
                self._suites[suite_id] = [stored]
        return rows

    def commit_statuses(self, repo: str, sha: str) -> list[dict[str, Any]]:
        self.calls.append(("commit_statuses", sha))
        return self.statuses.get(sha, [])

    def actions_run(self, repo: str, run_id: str) -> dict[str, Any]:
        self.calls.append(("actions_run", str(run_id)))
        if self.fail_actions:
            raise github_api.GitHubApiError("http_error", "workflow run lookup failed")
        found = self._workflows.get(str(run_id))
        if found is None:
            raise github_api.GitHubApiError("not_found", "workflow run was not found")
        return found

    def actions_runs_by_suite(self, repo: str, suite_id: int) -> list[dict[str, Any]]:
        self.calls.append(("actions_runs_by_suite", str(suite_id)))
        if self.fail_actions:
            raise github_api.GitHubApiError("http_error", "workflow run lookup failed")
        return list(self._suites.get(int(suite_id), []))


def run(
    name: str,
    conclusion: str | None,
    *,
    rid: int = 1,
    started: str = "2026-09-29T00:00:00Z",
    app: str = "github-actions",
    workflow: str | None = None,
    identity: bool = True,
    head_sha: str | None = None,
    head_repo: str | None = None,
    event: str = "push",
    head_branch: str = "development",
    suite_id: int | None = None,
    details: bool = True,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "id": rid,
        "name": name,
        "status": "completed" if conclusion else "in_progress",
        "conclusion": conclusion,
        "started_at": started,
        "html_url": f"https://example.invalid/{rid}",
        "app": {"slug": app},
    }
    if not identity:
        return row
    path = workflow if workflow is not None else github_api.EXPECTED_WORKFLOWS.get(name, ".github/workflows/unmapped.yml")
    row["_workflow_run"] = {
        "id": rid,
        "path": path,
        "head_sha": head_sha,
        "head_repository": {"full_name": head_repo or REPO},
        "event": event,
        "head_branch": head_branch,
    }
    if details:
        row["details_url"] = f"https://github.com/{REPO}/actions/runs/{rid}/job/1"
    if suite_id is not None:
        row["check_suite"] = {"id": suite_id}
    return row


def green(sha: str) -> dict[str, list[dict[str, Any]]]:
    return {sha: [run("Verify IDE Development", "success")]}


class PackageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fx = RemoteFixture()
        base = self.fx.remote_sha("development")
        self.a = self.fx.branch("issue/IDE-1-a", base, {"a.txt": "a\n"})
        self.b = self.fx.branch("issue/IDE-2-b", base, {"b.txt": "b\n", "shared.txt": "from b\n"})
        self.c = self.fx.branch("issue/IDE-3-c", base, {"shared.txt": "from c\n"})

    def tearDown(self) -> None:
        self.fx.cleanup()

    def test_clean_merge_creates_phase_branch_and_pushes(self) -> None:
        code, out = run_main(package, ["--name", "wave-1", "--branches", "issue/IDE-1-a", "issue/IDE-2-b",
                                       "--push", "--git-dir", str(self.fx.work)])
        self.assertEqual(code, 0, out)
        self.assertEqual(out["phaseBranch"], "phase/wave-1")
        self.assertEqual([m["branch"] for m in out["merged"]], ["issue/IDE-1-a", "issue/IDE-2-b"])
        self.assertEqual([m["sha"] for m in out["merged"]], [self.a, self.b])
        self.assertTrue(out["pushed"])
        self.assertIsNone(out["fast"])
        head = out["headSha"]
        self.assertEqual(self.fx.remote_sha("phase/wave-1"), head)
        parents = git(self.fx.work, "rev-list", "--parents", "-n", "1", head).split()
        self.assertEqual(len(parents), 3, "each branch lands as a --no-ff merge commit")
        self.assertEqual(git(self.fx.work, "show", f"{head}:shared.txt"), "from b")
        # Re-running reuses the phase branch: only clean phase merges are on it.
        code, again = run_main(package, ["--name", "wave-1", "--branches", "issue/IDE-1-a", "issue/IDE-2-b",
                                         "--git-dir", str(self.fx.work)])
        self.assertEqual(code, 0, again)
        self.assertTrue(again["reused"])
        self.assertEqual(again["headSha"], head)
        self.assertTrue(all(m["alreadyMerged"] for m in again["merged"]))

    def test_conflict_aborts_and_exits_3(self) -> None:
        code, out = run_main(package, ["--name", "wave-2", "--branches", "issue/IDE-1-a", "issue/IDE-2-b",
                                       "issue/IDE-3-c", "--push", "--git-dir", str(self.fx.work)])
        self.assertEqual(code, 3, out)
        self.assertFalse(out["ok"])
        self.assertEqual(out["conflict"]["branch"], "issue/IDE-3-c")
        self.assertEqual(out["conflict"]["files"], ["shared.txt"])
        self.assertEqual([m["branch"] for m in out["merged"]], ["issue/IDE-1-a", "issue/IDE-2-b"])
        self.assertFalse(out["pushed"])
        self.assertEqual(git(self.fx.work, "ls-remote", "--heads", "origin", "phase/wave-2"), "")
        self.assertEqual(git(self.fx.work, "worktree", "list").count("\n"), 0, "scratch worktree removed")

    def test_reuse_refuses_foreign_commits(self) -> None:
        self.fx.branch("phase/wave-3", self.fx.remote_sha("development"), {"stray.txt": "not from a branch\n"})
        code, out = run_main(package, ["--name", "wave-3", "--branches", "issue/IDE-1-a",
                                       "--git-dir", str(self.fx.work)])
        self.assertEqual(code, 2, out)
        self.assertEqual(out["error"], "phase_has_foreign_commits")

    def test_single_branch_reports_up_to_date(self) -> None:
        code, out = run_main(package, ["--branches", "issue/IDE-1-a", "--git-dir", str(self.fx.work)])
        self.assertEqual(code, 0, out)
        self.assertIsNone(out["phaseBranch"])
        self.assertTrue(out["upToDate"])
        self.assertEqual((out["aheadBy"], out["behindBy"]), (1, 0))
        self.assertEqual(out["headSha"], self.a)

        self.fx.branch("development", self.fx.remote_sha("development"), {"dev.txt": "moved\n"})
        code, out = run_main(package, ["--branches", "issue/IDE-1-a", "--git-dir", str(self.fx.work)])
        self.assertEqual(code, 0, out)
        self.assertFalse(out["upToDate"])
        self.assertEqual(out["behindBy"], 1)


class PromoteMainTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fx = RemoteFixture()
        self.main0 = self.fx.remote_sha("main")

    def tearDown(self) -> None:
        self.fx.cleanup()

    def _promote(self, api: FakeApi, *extra: str) -> tuple[int, dict[str, Any]]:
        with mock.patch.object(github_api, "from_env", return_value=api):
            return run_main(promote_main, ["--repo", REPO, "--git-dir", str(self.fx.work), *extra])

    def test_happy_path_main_subset_of_development(self) -> None:
        dev = self.fx.branch("development", self.main0, {"feature.txt": "v1\n"})
        code, out = self._promote(FakeApi(green(dev)), "--push")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["developmentSha"], dev)
        self.assertEqual(out["promoteBranch"], f"promote/main/{dev[:12]}")
        self.assertEqual(out["headSha"], dev, "main is an ancestor, so no merge commit is needed")
        self.assertEqual(out["tree"], git(self.fx.work, "rev-parse", f"{dev}^{{tree}}"))
        self.assertTrue(out["pushed"])
        self.assertEqual(self.fx.remote_sha(out["promoteBranch"]), dev)
        self.assertIn("merge commit", out["prBody"])
        self.assertEqual(out["prTitle"], f"Promote development {dev[:12]} to main")

    def test_previous_promotion_merge_on_main_is_merged_in_with_same_tree(self) -> None:
        dev1 = self.fx.branch("development", self.main0, {"feature.txt": "v1\n"})
        git(self.fx.seed, "checkout", "-q", "-B", "main", self.main0)
        git(self.fx.seed, "merge", "-q", "--no-ff", "-m", "Merge promote/main/x", dev1)
        git(self.fx.seed, "push", "-q", "origin", "main:refs/heads/main")
        dev2 = self.fx.branch("development", dev1, {"feature.txt": "v2\n"})
        code, out = self._promote(FakeApi(green(dev2)))
        self.assertEqual(code, 0, out)
        self.assertNotEqual(out["headSha"], dev2)
        self.assertEqual(git(self.fx.work, "rev-parse", f"{out['headSha']}^{{tree}}"), out["tree"])
        self.assertFalse(out["pushed"])

    def test_main_with_extra_change_exits_3(self) -> None:
        dev = self.fx.branch("development", self.main0, {"feature.txt": "v1\n"})
        self.fx.branch("main", self.main0, {"hotfix.txt": "only on main\n"})
        code, out = self._promote(FakeApi(green(dev)), "--push")
        self.assertEqual(code, 3, out)
        self.assertEqual(out["changedFiles"], ["hotfix.txt"])
        self.assertIn("missing from development", out["reason"])
        self.assertFalse(out["pushed"])

    def test_second_parent_ancestor_is_not_on_development(self) -> None:
        dev = self.fx.branch("development", self.main0, {"feature.txt": "v1\n"})
        side = self.fx.branch("side", self.main0, {"side.txt": "only side\n"})
        git(self.fx.seed, "checkout", "-q", "-B", "development", dev)
        git(self.fx.seed, "merge", "-q", "--no-ff", "-m", "merge side", side)
        git(self.fx.seed, "push", "-q", "origin", "development:refs/heads/development")
        tip = self.fx.remote_sha("development")
        code, out = self._promote(FakeApi(green(side)), "--sha", side)
        self.assertEqual(code, 2)
        self.assertEqual(out["error"], "not_on_development")
        self.assertIn("first-parent", out["message"])
        code, out = self._promote(FakeApi(green(tip)))
        self.assertEqual(code, 0, out)

    def test_sha_outside_first_parent_window_is_rejected(self) -> None:
        older = self.fx.branch("development", self.main0, {"feature.txt": "v1\n"})
        tip = self.fx.branch("development", older, {"feature.txt": "v2\n"})
        with mock.patch.object(git_local, "DEVELOPMENT_FIRST_PARENT_WINDOW", 1):
            code, out = self._promote(FakeApi(green(older)), "--sha", older)
        self.assertEqual(code, 2)
        self.assertEqual(out["error"], "not_on_development")
        self.assertIn("last 1 first-parent", out["message"])
        code, out = self._promote(FakeApi(green(tip)), "--sha", tip)
        self.assertEqual(code, 0, out)

    def test_red_development_sha_exits_1(self) -> None:
        dev = self.fx.branch("development", self.main0, {"feature.txt": "v1\n"})
        code, out = self._promote(FakeApi({dev: [run("Verify IDE Development", "failure")]}))
        self.assertEqual(code, 1, out)
        self.assertEqual(out["check"]["conclusion"], "failure")


class MergeCheckTests(unittest.TestCase):
    HEAD = "a" * 40

    def _pull(self, **over: Any) -> dict[str, Any]:
        pr = {"number": 7, "state": "open", "merged": False, "mergeable": True, "mergeable_state": "clean",
              "head": {"sha": self.HEAD, "ref": "phase/wave-1"}, "base": {"ref": "development"}}
        pr.update(over)
        return pr

    def _runs(self, **over: str | None) -> dict[str, list[dict[str, Any]]]:
        names = {name: "success" for name in merge_check.DEFAULT_REQUIRED}
        names.update(over)
        return {self.HEAD: [run(n, c, rid=i) for i, (n, c) in enumerate(names.items(), 1) if c != "absent"]}

    def _check(self, api: FakeApi, *extra: str, sha: str | None = None) -> tuple[int, dict[str, Any]]:
        argv = ["--repo", REPO, "--pr", "7", "--review-sha", sha or self.HEAD, "--review-verdict", "APPROVE", *extra]
        with mock.patch.object(github_api, "from_env", return_value=api):
            return run_main(merge_check, argv)

    def test_all_green(self) -> None:
        code, out = self._check(FakeApi(self._runs(), self._pull()))
        self.assertEqual(code, 0, out)
        self.assertTrue(out["ok"])
        self.assertEqual(out["reasons"], [])
        self.assertEqual(out["workflowFilesChanged"], [])
        self.assertTrue(all(row["ok"] for row in out["required"]))

    def test_workflow_files_changed_lists_workflow_paths(self) -> None:
        api = FakeApi(self._runs(), self._pull(), files=[
            {"filename": "README.md"},
            {"filename": ".github/workflows/ci.yml"},
            {"filename": ".github/workflows/branch-source-policy.yml"},
            {"filename": "scripts/orchestrator/merge_check.py"},
        ])
        code, out = self._check(api)
        self.assertEqual(code, 0, out)
        self.assertEqual(out["workflowFilesChanged"], [
            ".github/workflows/ci.yml",
            ".github/workflows/branch-source-policy.yml",
        ])

    def test_sha_mismatch(self) -> None:
        code, out = self._check(FakeApi(self._runs(), self._pull()), sha="b" * 40)
        self.assertEqual(code, 1)
        self.assertIn("does not equal reviewed SHA", out["reasons"][0])

    def test_request_changes_is_not_ok(self) -> None:
        with mock.patch.object(github_api, "from_env", return_value=FakeApi(self._runs(), self._pull())):
            code, out = run_main(merge_check, ["--repo", REPO, "--pr", "7", "--review-sha", self.HEAD,
                                               "--review-verdict", "REQUEST_CHANGES"])
        self.assertEqual(code, 1)
        self.assertIn("REQUEST_CHANGES", out["reasons"][0])

    def test_failed_check(self) -> None:
        runs = self._runs(**{"Verify IDE Development": "failure"})
        runs[self.HEAD].append(run("Unrelated Lint", "cancelled", rid=99))
        code, out = self._check(FakeApi(runs, self._pull()))
        self.assertEqual(code, 1)
        self.assertIn("required check 'Verify IDE Development' concluded failure", out["reasons"])
        self.assertIn("check 'Unrelated Lint' concluded cancelled", out["reasons"])

    def test_rerun_success_supersedes_earlier_failure(self) -> None:
        runs = self._runs()
        runs[self.HEAD].append(run("Linktrend Fast Checks", "failure", rid=0, started="2026-09-28T00:00:00Z"))
        code, out = self._check(FakeApi(runs, self._pull()))
        self.assertEqual(code, 0, out)

    def test_missing_required(self) -> None:
        code, out = self._check(FakeApi(self._runs(**{"Linktrend Branch Source Policy": "absent"}), self._pull()))
        self.assertEqual(code, 1)
        self.assertIn(f"required check 'Linktrend Branch Source Policy' has not run on {self.HEAD}", out["reasons"])

    def test_same_name_status_does_not_satisfy(self) -> None:
        statuses = {self.HEAD: [{"context": name, "state": "success"} for name in merge_check.DEFAULT_REQUIRED]}
        code, out = self._check(FakeApi({}, self._pull(), statuses))
        self.assertEqual(code, 1)
        self.assertTrue(all(not row["ok"] for row in out["required"]))
        self.assertTrue(any("has not run" in reason for reason in out["reasons"]))

    def test_other_app_check_run_does_not_satisfy(self) -> None:
        runs = {
            self.HEAD: [
                run(name, "success", rid=i, app="third-party")
                for i, name in enumerate(merge_check.DEFAULT_REQUIRED, 1)
            ]
        }
        code, out = self._check(FakeApi(runs, self._pull()))
        self.assertEqual(code, 1)
        self.assertTrue(any("allowed app" in reason for reason in out["reasons"]))

    def test_later_failing_rerun_overrides_success(self) -> None:
        runs = self._runs()
        runs[self.HEAD].append(run("Linktrend Fast Checks", "failure", rid=50, started="2026-09-29T12:00:00Z"))
        code, out = self._check(FakeApi(runs, self._pull()))
        self.assertEqual(code, 1)
        self.assertIn("required check 'Linktrend Fast Checks' concluded failure", out["reasons"])

    def test_failing_status_fails_even_when_checks_are_green(self) -> None:
        statuses = {self.HEAD: [{"context": "Custom", "state": "failure"}]}
        code, out = self._check(FakeApi(self._runs(), self._pull(), statuses))
        self.assertEqual(code, 1)
        self.assertIn("commit status 'Custom' concluded failure", out["reasons"])

    def test_mergeability_fail_closed(self) -> None:
        cases = (
            ({"mergeable": None, "mergeable_state": "clean"}, "mergeability not yet computed; retry"),
            ({"mergeable": True, "mergeable_state": "unknown"}, "mergeability not yet computed; retry"),
            ({"mergeable": False, "mergeable_state": "dirty"}, "PR has merge conflicts with its base"),
            ({"mergeable": False, "mergeable_state": "blocked"}, "PR mergeable_state is blocked"),
            ({"mergeable": True, "mergeable_state": "clean"}, None),
        )
        for over, expected in cases:
            with self.subTest(state=over["mergeable_state"], mergeable=over["mergeable"]):
                code, out = self._check(FakeApi(self._runs(), self._pull(**over)))
                if expected is None:
                    self.assertEqual(code, 0, out)
                    self.assertEqual(out["reasons"], [])
                else:
                    self.assertEqual(code, 1)
                    self.assertIn(expected, out["reasons"])

    def test_unstable_only_when_listed_nonrequired_pending(self) -> None:
        runs = self._runs()
        runs[self.HEAD].append(run("Optional Lint", None, rid=40))
        pr = self._pull(mergeable=True, mergeable_state="unstable")
        code, out = self._check(FakeApi(runs, pr))
        self.assertEqual(code, 1)
        self.assertTrue(any("unstable" in reason for reason in out["reasons"]))
        code, out = self._check(FakeApi(runs, pr), "--allow-nonrequired-pending", "Optional Lint")
        self.assertEqual(code, 0, out)

    def test_skipped_only_when_allowed_and_base_checked(self) -> None:
        runs = self._runs(**{"Verify IDE Development": "skipped"})
        code, _ = self._check(FakeApi(runs, self._pull()))
        self.assertEqual(code, 1)
        code, out = self._check(FakeApi(runs, self._pull()), "--allow-skipped", "Verify IDE Development")
        self.assertEqual(code, 0, out)
        code, out = self._check(FakeApi(self._runs(), self._pull(base={"ref": "release"})))
        self.assertEqual(code, 1)
        self.assertIn("base 'release'", out["reasons"][0])


class PromotionCheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self.fx = RemoteFixture()
        main0 = self.fx.remote_sha("main")
        self.dev = self.fx.branch("development", main0, {"feature.txt": "v1\n"})
        self.fx.branch("main", main0, {"feature.txt": "v1\n"})
        # Promote branch: development SHA with main merged in -> same tree, different SHA.
        git(self.fx.seed, "checkout", "-q", "-B", "promote/main/x", self.dev)
        git(self.fx.seed, "merge", "-q", "--no-edit", "main")
        git(self.fx.seed, "push", "-q", "origin", "promote/main/x:refs/heads/promote/main/x")
        self.head = self.fx.remote_sha("promote/main/x")
        self.other = self.fx.branch("issue/IDE-9-z", self.dev, {"other.txt": "x\n"})
        git(self.fx.work, "fetch", "-q", "origin")

    def tearDown(self) -> None:
        self.fx.cleanup()

    def _check(self, api: FakeApi, head_sha: str, head_ref: str, *extra: str) -> tuple[int, dict[str, Any]]:
        argv = ["--head-sha", head_sha, "--head-ref", head_ref, "--base-ref", "main", "--repo", REPO,
                "--git-dir", str(self.fx.work), *extra]
        with mock.patch.object(github_api, "from_env", return_value=api):
            return run_main(promotion_check, argv)

    def test_tree_match_and_green(self) -> None:
        self.assertNotEqual(self.head, self.dev)
        code, out = self._check(FakeApi(green(self.dev)), self.head, "promote/main/x")
        self.assertEqual(code, 0, out)
        self.assertEqual(out["developmentSha"], self.dev)
        self.assertEqual(out["context"], "Linktrend Receipt Gate")
        self.assertTrue(out["check"]["ok"])
        self.assertEqual(out["check"]["workflow"], ".github/workflows/ci.yml")
        self.assertIsNone(out["check"]["workflowReason"])

    def test_pull_request_event_is_not_development_evidence(self) -> None:
        runs = {self.dev: [run("Verify IDE Development", "success", event="pull_request", head_sha=self.dev)]}
        code, out = self._check(FakeApi(runs), self.head, "promote/main/x")
        self.assertEqual(code, 1)
        self.assertFalse(out["check"]["ok"])
        self.assertIn("is not 'push'", out["reasons"][0])

    def test_push_on_another_branch_is_not_development_evidence(self) -> None:
        runs = {self.dev: [run(
            "Verify IDE Development", "success", event="push", head_branch="feature", head_sha=self.dev,
        )]}
        code, out = self._check(FakeApi(runs), self.head, "promote/main/x")
        self.assertEqual(code, 1)
        self.assertIn("is not 'development'", out["reasons"][0])

    def test_tree_match_and_red(self) -> None:
        code, out = self._check(FakeApi({self.dev: [run("Verify IDE Development", "failure")]}), self.head,
                                "promote/main/x")
        self.assertEqual(code, 1)
        self.assertEqual(out["developmentSha"], self.dev)
        self.assertIn("has not concluded success", out["reasons"][0])

    def test_no_tree_match(self) -> None:
        api = FakeApi(green(self.dev))
        code, out = self._check(api, self.other, "promote/main/x")
        self.assertEqual(code, 1)
        self.assertIsNone(out["developmentSha"])
        self.assertIn("no commit in the last 200", out["reasons"][0])
        self.assertEqual(api.calls, [])

    def test_wrong_branch_name(self) -> None:
        code, out = self._check(FakeApi(green(self.dev)), self.head, "issue/IDE-9-z")
        self.assertEqual(code, 1)
        self.assertIn("is not promote/main/*", out["reasons"][0])

    def test_fork_head_fails(self) -> None:
        code, out = self._check(FakeApi(green(self.dev)), self.head, "promote/main/x", "--head-fork", "true")
        self.assertEqual(code, 1)
        self.assertIn("fork", out["reasons"][0])


class GithubApiTests(unittest.TestCase):
    def test_pagination_follows_next_links(self) -> None:
        api = github_api.GitHubApi(token=None, base="https://api.example.invalid")
        pages = {
            "https://api.example.invalid/x?per_page=100": ({"check_runs": [1, 2]}, '<https://p2>; rel="next"'),
            "https://p2": ({"check_runs": [3]}, None),
        }
        with mock.patch.object(api, "_request", side_effect=lambda url: pages[url]):
            self.assertEqual(api.paginate("/x", key="check_runs"), [1, 2, 3])

    def test_statuses_are_reported_and_never_count_as_success(self) -> None:
        sha = "c" * 40
        checks = github_api.head_checks(
            FakeApi(
                {sha: [run("A", "success")]},
                statuses={sha: [
                    {"context": "B", "state": "error"},
                    {"context": "B", "state": "success"},
                    {"context": "A", "state": "failure"},
                ]},
            ),
            REPO,
            sha,
        )
        self.assertEqual(checks["A"]["conclusion"], "success")
        self.assertTrue(checks["A"]["countsAsCheck"])
        self.assertEqual(checks["A"]["statusReport"]["conclusion"], "failure")
        self.assertFalse(checks["A"]["statusReport"]["countsAsSuccess"])
        self.assertFalse(checks["B"]["countsAsCheck"])
        self.assertNotEqual(checks["B"]["conclusion"], "success")
        self.assertEqual(checks["B"]["statusReport"]["conclusion"], "failure")
        self.assertEqual(github_api.token_from_env({"GITHUB_TOKEN": "t2", "GH_TOKEN": "t1"}), "t1")
        self.assertEqual(github_api.repo_from_remote_url("git@github.com:linktrend/IDE-Development.git"),
                         "linktrend/IDE-Development")

    def test_workflow_identity_fails_closed(self) -> None:
        sha = "d" * 40
        name = "Verify IDE Development"
        expected = github_api.EXPECTED_WORKFLOWS[name]

        def checks(row: dict[str, Any], *, fail_actions: bool = False) -> dict[str, Any]:
            api = FakeApi({sha: [row]})
            api.fail_actions = fail_actions
            return github_api.head_checks(api, REPO, sha)[name]

        absent = checks(run(name, "success", identity=False))
        self.assertFalse(absent["countsAsCheck"])
        self.assertFalse(absent["workflowOk"])
        self.assertEqual(absent["workflowReason"], "workflow identity is absent")

        # A path stuck on the check-run payload is not identity. The list API omits it.
        payload_only = run(name, "success", identity=False)
        payload_only["check_suite"] = {"path": expected}
        self.assertFalse(checks(payload_only)["countsAsCheck"])

        mismatch = checks(run(name, "success", workflow=".github/workflows/other.yml"))
        self.assertFalse(mismatch["countsAsCheck"])
        self.assertFalse(mismatch["workflowOk"])
        self.assertIn(".github/workflows/other.yml", mismatch["workflowReason"])
        self.assertIn(expected, mismatch["workflowReason"])

        fork = checks(run(name, "success", head_repo="attacker/fork"))
        self.assertFalse(fork["countsAsCheck"])
        self.assertIn("attacker/fork", fork["workflowReason"])
        self.assertIn("head_repository", fork["workflowReason"])

        wrong_sha = checks(run(name, "success", head_sha="e" * 40))
        self.assertFalse(wrong_sha["countsAsCheck"])
        self.assertIn("head_sha", wrong_sha["workflowReason"])

        api_error = checks(run(name, "success"), fail_actions=True)
        self.assertFalse(api_error["countsAsCheck"])
        self.assertEqual(api_error["workflowReason"], "workflow run could not be resolved")

        right = checks(run(name, "success", workflow=expected, head_sha=sha))
        self.assertTrue(right["countsAsCheck"])
        self.assertEqual(right["workflow"], expected)

        via_suite = checks(run(name, "success", rid=7, details=False, suite_id=42, head_sha=sha))
        self.assertTrue(via_suite["countsAsCheck"])
        self.assertEqual(via_suite["workflow"], expected)

        receipt = "Linktrend Receipt Gate"
        receipt_ok = github_api.head_checks(FakeApi({sha: [run(receipt, "success", head_sha=sha)]}), REPO, sha)[receipt]
        self.assertTrue(receipt_ok["countsAsCheck"])
        self.assertEqual(receipt_ok["workflow"], github_api.EXPECTED_WORKFLOWS[receipt])


class GitArgTests(unittest.TestCase):
    def test_option_injection_and_bad_branch_do_not_run_git(self) -> None:
        with mock.patch("git_local.subprocess.run") as run:
            for remote in ("--upload-pack=x", "-x"):
                with self.assertRaises(git_local.GitError):
                    git_local.fetch(remote, ["development"], "/tmp/not-a-repo")
            with self.assertRaises(git_local.GitError):
                git_local.fetch("origin", ["bad branch"], "/tmp/not-a-repo")
            with self.assertRaises(git_local.GitError):
                package.package(
                    name="wave",
                    branches=["issue/IDE-1-a"],
                    base="development",
                    remote="--upload-pack=x",
                    git_dir="/tmp/not-a-repo",
                    fast=False,
                    push=False,
                )
            with self.assertRaises(git_local.GitError):
                package.package(
                    name="wave",
                    branches=["-x"],
                    base="development",
                    remote="origin",
                    git_dir="/tmp/not-a-repo",
                    fast=False,
                    push=False,
                )
            with self.assertRaises(git_local.GitError):
                promote_main.promote(
                    sha=None,
                    repo=REPO,
                    remote="-x",
                    git_dir="/tmp/not-a-repo",
                    push=False,
                    required_check="Verify IDE Development",
                    api=FakeApi(),
                )
            with self.assertRaises(git_local.GitError):
                promotion_check.check(
                    head_sha="a" * 40,
                    head_ref="promote/main/x",
                    base_ref="main",
                    repo=REPO,
                    head_fork=False,
                    git_dir="/tmp/not-a-repo",
                    remote="--upload-pack=x",
                    depth=promotion_check.SEARCH_DEPTH,
                    required_check="Verify IDE Development",
                    api=FakeApi(),
                )
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
