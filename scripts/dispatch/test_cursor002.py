"""Offline tests for the cursor-002 dispatch client. Run: python3 -m unittest scripts/dispatch/test_cursor002.py"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

import cursor002 as c  # noqa: E402


def _variant(**params: str) -> dict[str, Any]:
    return {"params": [{"id": k, "value": v} for k, v in params.items()]}


MODELS = {
    "items": [
        {
            "id": "grok-4.7",
            "variants": [
                _variant(context="500k", reasoning_effort="high", fast="true"),
                _variant(context="500k", reasoning_effort="medium", fast="false"),
            ],
        },
        {"id": "claude-opus-5-5", "variants": [_variant(context="1m", effort="medium", fast="false")]},
    ]
}


class FakeClient(c.Client):
    def __init__(self, responses: dict[tuple[str, str], list[tuple[int, Any]]]) -> None:
        super().__init__("test-key", base="https://example.invalid")
        self.responses = responses
        self.calls: list[tuple[str, str, Any]] = []

    def request(self, method, path, body=None, *, timeout=c.DEFAULT_TIMEOUT_S):  # type: ignore[override]
        self.calls.append((method, path, body))
        queue = self.responses[(method, path.split("?")[0])]
        item = queue.pop(0) if len(queue) > 1 else queue[0]
        if isinstance(item, BaseException):
            raise item
        return item


class ResolveModelTests(unittest.TestCase):
    def test_grok_medium_resolves_to_pinned_variant(self) -> None:
        model = c.resolve_model(MODELS, "grok-medium")
        self.assertEqual(model["id"], "grok-4.7")
        self.assertEqual(
            {p["id"]: p["value"] for p in model["params"]},
            {"context": "500k", "reasoning_effort": "medium", "fast": "false"},
        )

    def test_opus_medium_uses_exact_id(self) -> None:
        self.assertEqual(c.resolve_model(MODELS, "opus-medium")["id"], "claude-opus-5-5")

    def test_renamed_model_fails_closed(self) -> None:
        with self.assertRaises(c.DispatchError) as ctx:
            c.resolve_model({"items": [{"id": "grok-5"}]}, "grok-medium")
        self.assertEqual(ctx.exception.code, "model_unavailable")

    def test_missing_variant_fails_closed(self) -> None:
        models = {"items": [{"id": "grok-4.7", "variants": [_variant(context="500k", reasoning_effort="high", fast="true")]}]}
        with self.assertRaises(c.DispatchError) as ctx:
            c.resolve_model(models, "grok-medium")
        self.assertEqual(ctx.exception.code, "variant_unavailable")

    def test_unknown_route(self) -> None:
        with self.assertRaises(c.DispatchError):
            c.resolve_model(MODELS, "opus")


class PromptTests(unittest.TestCase):
    def test_wrapper_pins_branch_and_self_report(self) -> None:
        text = c.build_prompt("Do X.", issue_id="IDE-9", branch="issue/IDE-9-x")
        self.assertIn("issue/IDE-9-x", text)
        self.assertIn("Do not open pull requests", text)
        self.assertIn(c.SELF_REPORT_TAG, text)
        self.assertTrue(text.rstrip().endswith("Do X."))

    def test_extract_self_report(self) -> None:
        reply = "Done.\nLessons: none\n`MODEL-SELF-REPORT: Grok 4.7`"
        self.assertEqual(c.extract_self_report(reply), "Grok 4.7")
        self.assertIsNone(c.extract_self_report("no tag"))
        self.assertIsNone(c.extract_self_report(None))

    def test_branch_pattern(self) -> None:
        with self.assertRaises(c.DispatchError):
            c.ensure_remote_branch("https://github.com/o/r", "cursor/foo", "development", git_dir=None)


class ApiFlowTests(unittest.TestCase):
    def test_create_sends_pinned_model_and_no_pr(self) -> None:
        client = FakeClient({
            ("GET", "/v1/models"): [(200, MODELS)],
            ("POST", "/v1/agents"): [(201, {"agent": {"id": "bc-1", "url": "u"}, "run": {"id": "run-1"}})],
        })
        out = c.create_agent(
            client, route="grok-medium", prompt="p", repo_url="https://github.com/o/r",
            ref="issue/IDE-9-x", work_on_current_branch=True, name=None,
        )
        body = client.calls[-1][2]
        self.assertEqual(body["model"]["id"], "grok-4.7")
        self.assertFalse(body["autoCreatePR"])
        self.assertTrue(body["workOnCurrentBranch"])
        self.assertTrue(body["agentId"].startswith("bc-"))
        self.assertEqual(out["runId"], "run-1")

    def test_create_timeout_recovers_via_client_agent_id(self) -> None:
        client = FakeClient({
            ("GET", "/v1/models"): [(200, MODELS)],
            ("POST", "/v1/agents"): [TimeoutError(), (409, {"code": "agent_id_conflict"})],
        })
        original = client.request

        def request(method, path, body=None, *, timeout=c.DEFAULT_TIMEOUT_S):
            if method == "GET" and path.startswith("/v1/agents/bc-"):
                client.calls.append((method, path, body))
                return 200, {"id": path.rsplit("/", 1)[-1], "latestRunId": "run-9"}
            return original(method, path, body, timeout=timeout)

        client.request = request  # type: ignore[method-assign]
        out = c.create_agent(client, route="grok-medium", prompt="p", repo_url=None, ref=None,
                             work_on_current_branch=False, name=None)
        self.assertEqual(out["runId"], "run-9")
        posts = [call for call in client.calls if call[0] == "POST"]
        self.assertEqual(len(posts), 2)
        self.assertEqual(posts[0][2]["agentId"], posts[1][2]["agentId"])

    def test_archive_sends_no_body(self) -> None:
        client = FakeClient({("POST", "/v1/agents/bc-1/archive"): [(200, {"id": "bc-1"})]})
        self.assertTrue(c.archive(client, "bc-1")["archived"])
        self.assertIsNone(client.calls[0][2])

    def test_read_result_extracts_branch_and_self_report(self) -> None:
        client = FakeClient({
            ("GET", "/v1/agents/bc-1"): [(200, {"status": "IDLE", "latestRunId": "run-1", "url": "u"})],
            ("GET", "/v1/agents/bc-1/runs/run-1"): [(200, {
                "status": "FINISHED", "durationMs": 5, "result": "ok\nMODEL-SELF-REPORT: Grok 4.7",
                "git": {"branches": [{"repoUrl": "github.com/o/r", "branch": "issue/IDE-9-x"}]},
            })],
            ("GET", "/v1/agents/bc-1/usage"): [(200, {"totalUsage": {"totalTokens": 3}})],
        })
        res = c.read_result(client, "bc-1")
        self.assertTrue(res["terminal"])
        self.assertEqual(res["branches"][0]["branch"], "issue/IDE-9-x")
        self.assertEqual(res["selfReportedModel"], "Grok 4.7")

    def test_run_log_omits_result_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "log", "runs.jsonl")
            c.append_run_log(path, {"agentId": "bc-1", "result": "long"})
            record = json.loads(Path(path).read_text().strip())
        self.assertEqual(record["agentId"], "bc-1")
        self.assertNotIn("result", record)

    def test_missing_key(self) -> None:
        with self.assertRaises(c.DispatchError):
            c.Client("")


class GitIsolationTests(unittest.TestCase):
    """Reviewer reproduction: a local pre-push hook must never see CURSOR_002_API_KEY."""

    SECRET = "sentinel-cursor-002-key"

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        tmp = Path(self._tmp.name)
        self.origin, self.clone, self.sentinel = tmp / "origin.git", tmp / "clone", tmp / "sentinel"
        run = lambda *a, cwd=None: subprocess.run(a, cwd=cwd, check=True, capture_output=True)  # noqa: E731
        run("git", "init", "-q", "--bare", str(self.origin))
        run("git", "init", "-q", "-b", "development", str(self.clone))
        run("git", "config", "user.name", "t", cwd=self.clone)
        run("git", "config", "user.email", "t@example.com", cwd=self.clone)
        run("git", "config", "commit.gpgsign", "false", cwd=self.clone)
        (self.clone / "README.md").write_text("seed\n")
        run("git", "add", ".", cwd=self.clone)
        run("git", "commit", "-qm", "seed", cwd=self.clone)
        run("git", "remote", "add", "origin", str(self.origin), cwd=self.clone)
        run("git", "push", "-q", "origin", "development", cwd=self.clone)
        hook = f"#!/bin/sh\nprintf '%s' \"$CURSOR_002_API_KEY\" > '{self.sentinel}'\n"
        custom = tmp / "custom-hooks"
        custom.mkdir()
        for hooks_dir in (self.clone / ".git" / "hooks", custom):
            path = hooks_dir / "pre-push"
            path.write_text(hook)
            path.chmod(0o755)
        self.custom_hooks = custom
        self.env = {**os.environ, "CURSOR_002_API_KEY": self.SECRET}

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_control_hook_recovers_secret_with_plain_git(self) -> None:
        subprocess.run(["git", "push", "-q", "origin", "development:refs/heads/control"], cwd=self.clone,
                       env=self.env, check=True, capture_output=True)
        self.assertEqual(self.sentinel.read_text(), self.SECRET)

    def test_ensure_remote_branch_runs_no_hooks_and_no_secrets(self) -> None:
        for hooks_path in (None, str(self.custom_hooks)):
            if hooks_path:
                subprocess.run(["git", "config", "core.hooksPath", hooks_path], cwd=self.clone, check=True)
            branch = "issue/IDE-99-hook-check" if not hooks_path else "issue/IDE-98-hook-check"
            with unittest.mock.patch.dict(os.environ, {"CURSOR_002_API_KEY": self.SECRET}):
                sha = c.ensure_remote_branch(str(self.origin), branch, "development", git_dir=str(self.clone))
            listed = subprocess.run(["git", "ls-remote", "--heads", str(self.origin), branch],
                                    capture_output=True, text=True, check=True).stdout
            self.assertIn(sha, listed)
            self.assertFalse(self.sentinel.exists(), "a repository hook ran during dispatch git calls")

    def test_git_env_is_allowlisted(self) -> None:
        with unittest.mock.patch.dict(os.environ, {"CURSOR_002_API_KEY": self.SECRET, "IDE_LEDGER_DATABASE_URL": "x",
                                                   "CODEX_AUTH_STORE_KEY": "y", "GIT_CONFIG_PARAMETERS": "z"}):
            env = c.git_env()
        for name in ("CURSOR_002_API_KEY", "IDE_LEDGER_DATABASE_URL", "CODEX_AUTH_STORE_KEY", "GIT_CONFIG_PARAMETERS"):
            self.assertNotIn(name, env)
        self.assertIn("PATH", env)


if __name__ == "__main__":
    unittest.main()
