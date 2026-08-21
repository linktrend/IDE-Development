"""PKT-06 delivery profile inventory, identity, and recovery tests."""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.gitops import run_delivery_profile as runner


def profile(commands: list[list[str]]) -> dict:
    return {
        "schemaVersion": 2,
        "profiles": {
            "fast": {"commands": commands},
            "full": {"commands": commands},
            "focused": {"commands": commands},
        },
    }


def identity(seed: str = "a") -> dict[str, str]:
    return {
        "repository": "linktrend/IDE-Development",
        "gitTree": seed * 40,
        "headCommit": seed * 40,
        "dependencyDigest": "sha256:" + ("1" * 64),
        "profileDigest": "sha256:" + ("2" * 64),
        "workflowDigest": "sha256:" + ("3" * 64),
    }


class FakeClock:
    def __init__(self) -> None:
        self.value = 100.0

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


class DeliveryProfileRunnerTests(unittest.TestCase):
    def test_source_declares_internal_profiles(self) -> None:
        root = Path(__file__).resolve().parents[2]
        path, commands = runner.load_profile(root, "fast")
        self.assertEqual(path, root / ".github/linktrend-delivery-mode.json")
        self.assertTrue(any("scripts.tests.test_candidate_lifecycle" in command for command in commands))

    def test_local_checkout_head_precedes_merge_ref_environment_sha(self) -> None:
        def fake_git(_root: Path, *args: str) -> str:
            if args == ("rev-parse", "HEAD"):
                return "a" * 40
            return ""

        with patch.dict(os.environ, {"GITHUB_SHA": "b" * 40}, clear=False):
            with patch.object(runner, "_run_git", side_effect=fake_git):
                result = runner.build_identity(
                    Path(tempfile.mkdtemp()),
                    repository="linktrend/IDE-Development",
                    git_tree="c" * 40,
                    dependency_digest="sha256:" + ("1" * 64),
                    profile_digest="sha256:" + ("2" * 64),
                    workflow_digest="sha256:" + ("3" * 64),
                )
        self.assertIsNotNone(result)
        self.assertEqual(result["headCommit"], "a" * 40)

    def test_consumer_without_ide_modules_uses_declared_managed_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / ".ide-development/config/delivery.json"
            config.parent.mkdir(parents=True)
            config.write_text(json.dumps(profile([["python3", "consumer_fast.py"]])), encoding="utf-8")
            path, commands = runner.load_profile(root, "fast")
            self.assertEqual(path, config)
            self.assertEqual(commands, [["python3", "consumer_fast.py"]])
            result = runner.run_profile(
                root,
                "fast",
                config_path=config,
                commands=commands,
                executor=lambda command, cwd: subprocess.CompletedProcess(command, 0, "", ""),
            )
            self.assertTrue(result["ok"])
            self.assertEqual(result["executedCount"], 1)

    def test_dependency_digest_ignores_worktree_shared_git_objects(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repository = root / "repository"
            subprocess.run(["git", "init", "-q", repository], check=True)
            subprocess.run(
                ["git", "-C", str(repository), "config", "user.email", "pkt06@example.invalid"],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(repository), "config", "user.name", "PKT-06"],
                check=True,
            )
            (repository / "README.md").write_text("root\n", encoding="utf-8")
            subprocess.run(["git", "-C", str(repository), "add", "README.md"], check=True)
            subprocess.run(
                ["git", "-C", str(repository), "commit", "-qm", "root"],
                check=True,
            )
            worktree = root / "worktree"
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(repository),
                    "worktree",
                    "add",
                    "-q",
                    "-b",
                    "profile-test",
                    str(worktree),
                ],
                check=True,
            )
            (worktree / "requirements.txt").write_text("jsonschema\n", encoding="utf-8")
            shared_objects = repository / ".git" / "objects" / "aa"
            shared_objects.mkdir(parents=True)
            (shared_objects / "disappearing.lock").write_text("not a dependency", encoding="utf-8")
            digest = runner._digest_files(worktree, ("**/*lock*", "**/requirements*.txt"))
            expected = runner.digest_json(
                [
                    {
                        "path": "requirements.txt",
                        "digest": runner.digest_bytes(b"jsonschema\n"),
                    }
                ]
            )
            self.assertEqual(digest, expected)
            self.assertNotIn(".git/", digest)

    def test_disappearing_working_tree_dependency_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            declaration = root / "requirements.txt"
            declaration.write_text("jsonschema\n", encoding="utf-8")
            original_read_bytes = Path.read_bytes

            def disappear() -> bytes:
                declaration.unlink()
                return original_read_bytes(declaration)

            with patch.object(Path, "read_bytes", side_effect=disappear):
                with self.assertRaisesRegex(
                    runner.DeliveryProfileError,
                    "dependency_declaration_unreadable:requirements.txt",
                ):
                    runner._digest_files(root, ("**/requirements*.txt",))

    def test_missing_or_empty_profile_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(SystemExit, "delivery_profile_config_missing"):
                runner.load_profile(Path(tmp), "fast")
            root = Path(tmp)
            config = root / ".github/linktrend-delivery-mode.json"
            config.parent.mkdir()
            config.write_text(json.dumps(profile([])), encoding="utf-8")
            with self.assertRaisesRegex(SystemExit, "delivery_profile_commands_missing"):
                runner.load_profile(root, "fast")

    def test_complete_inventory_keeps_later_failing_test_visible(self) -> None:
        """The previously omitted failure must remain in machine-readable proof."""
        clock = FakeClock()
        calls: list[list[str]] = []

        def execute(command: list[str], root: Path) -> subprocess.CompletedProcess[str]:
            del root
            calls.append(command)
            clock.advance(0.25)
            code = 7 if command[-1] == "omitted-failing-test" else 0
            return subprocess.CompletedProcess(command, code, "", "assertion failed" if code else "")

        result = runner.run_profile(
            Path(tempfile.mkdtemp()),
            "fast",
            commands=[["python3", "first-pass"], ["python3", "omitted-failing-test"], ["python3", "later-pass"]],
            executor=execute,
            clock=clock,
        )
        self.assertFalse(result["ok"])
        self.assertTrue(result["complete"])
        self.assertEqual(calls, [
            ["python3", "first-pass"],
            ["python3", "omitted-failing-test"],
            ["python3", "later-pass"],
        ])
        self.assertEqual(result["failedCount"], 1)
        self.assertEqual(result["commands"][1]["status"], "failed")
        self.assertIn("assertion failed", result["commands"][1]["stderrTail"])
        self.assertEqual(result["commands"][2]["status"], "passed")
        self.assertGreater(result["elapsedMs"], 0)

    def test_unauthorized_omission_cannot_be_reused(self) -> None:
        previous = {
            "kind": runner.INVENTORY_KIND,
            "ok": False,
            "complete": True,
            "identityDigest": runner.identity_digest(identity()),
            "workspaceMutated": False,
        }
        result = runner.can_reuse_evidence(previous, identity())
        self.assertFalse(result["reusable"])
        self.assertEqual(result["code"], "evidence_not_complete_success")

    def test_unchanged_identity_reuses_and_changed_identity_invalidates(self) -> None:
        previous = {
            "kind": runner.INVENTORY_KIND,
            "ok": True,
            "complete": True,
            "identityDigest": runner.identity_digest(identity()),
            "workspaceMutated": False,
        }
        reused = runner.can_reuse_evidence(previous, identity())
        self.assertTrue(reused["reusable"])
        changed = runner.can_reuse_evidence(previous, identity("b"))
        self.assertFalse(changed["reusable"])
        self.assertEqual(changed["code"], "evidence_identity_changed")

    def test_risk_classifier_and_boundaries_are_machine_readable(self) -> None:
        focused = runner.classify_risk(["src/app.py"], profile="focused", commands=[["python3", "-m", "unittest"]])
        self.assertEqual(focused["level"], "medium")
        full = runner.classify_risk([".github/workflows/ci.yml"], profile="full")
        self.assertEqual(full["level"], "high")
        unsafe = runner.classify_risk(["../escape"], profile="fast")
        self.assertEqual(unsafe["level"], "critical")
        blocked = runner.run_profile(
            Path(tempfile.mkdtemp()),
            "fast",
            commands=[["python3", "must-not-run"]],
            changed_paths=["../escape"],
            executor=lambda command, root: self.fail("critical risk executed a command"),
        )
        self.assertFalse(blocked["ok"])
        self.assertEqual(blocked["commands"][0]["reason"], "critical_risk_requires_authorized_recovery")

    def test_controlled_clock_and_recovery_simulations(self) -> None:
        clock = FakeClock()

        def execute(command: list[str], root: Path) -> subprocess.CompletedProcess[str]:
            del command, root
            clock.advance(1.5)
            return subprocess.CompletedProcess([], 0, "", "")

        result = runner.run_profile(
            Path(tempfile.mkdtemp()),
            "focused",
            commands=[["python3", "focused"]],
            executor=execute,
            clock=clock,
        )
        self.assertEqual(result["elapsedMs"], 1500)
        for kwargs, code, action in (
            ({"agent_stale": True}, "stale_agent", "requeue_without_reuse"),
            ({"capacity_available": False}, "capacity_exhausted", "defer_without_mutation"),
            ({"host_available": False}, "host_unavailable", "retry_infrastructure"),
            ({"workspace_mutated": True}, "workspace_mutated", "discard_and_recompute"),
        ):
            recovery = runner.classify_recovery(**kwargs)
            self.assertTrue(recovery["safe"])
            self.assertEqual(recovery["code"], code)
            self.assertEqual(recovery["action"], action)
            self.assertFalse(recovery["reuse"])

    def test_inventory_matches_packaged_ci_evidence_schema(self) -> None:
        schema_path = Path(__file__).resolve().parents[2] / "core/managed-core/schemas/ci-evidence.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        result = runner.run_profile(
            Path(tempfile.mkdtemp()),
            "fast",
            commands=[["python3", "focused"]],
            identity=identity(),
            executor=lambda command, root: subprocess.CompletedProcess(command, 0, "", ""),
        )
        inventory_schema = schema["$defs"]["profileInventoryEvidence"]
        self.assertIn(result["kind"], {inventory_schema["properties"]["kind"]["const"]})
        self.assertEqual(result["schemaVersion"], inventory_schema["properties"]["schemaVersion"]["const"])
        self.assertTrue(result["complete"])
        self.assertTrue(result["identityDigest"].startswith("sha256:"))

    def test_tracked_workspace_mutation_invalidates_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "pkt06@example.invalid"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "PKT-06"], cwd=root, check=True)
            tracked = root / "tracked.txt"
            tracked.write_text("before\n", encoding="utf-8")
            subprocess.run(["git", "add", "tracked.txt"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "fixture"], cwd=root, check=True)

            def mutate(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
                del command
                (cwd / "tracked.txt").write_text("after\n", encoding="utf-8")
                return subprocess.CompletedProcess([], 0, "", "")

            result = runner.run_profile(
                root,
                "fast",
                commands=[["python3", "mutating-command"], ["python3", "must-not-run"]],
                identity=identity(),
                executor=mutate,
            )
            self.assertFalse(result["ok"])
            self.assertTrue(result["workspaceMutated"])
            self.assertEqual(result["commands"][1]["status"], "omitted")
            self.assertEqual(
                runner.can_reuse_evidence(result, identity())["code"],
                "evidence_not_complete_success",
            )

    def test_invalid_identity_fails_closed(self) -> None:
        with self.assertRaisesRegex(runner.DeliveryProfileError, "identity_commit_invalid"):
            runner.identity_digest({**identity(), "headCommit": "not-a-sha"})
