"""Tests for the Codex orchestrator dispatch helpers (v3 Wave 0.4)."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

from scripts.codex import codex_orchestrator as co


def window(used: int, mins: int | None) -> dict:
    return {"usedPercent": used, "windowDurationMins": mins, "resetsAt": 1790000000}


def limits(primary=None, secondary=None, **extra) -> dict:
    snapshot = {"primary": primary, "secondary": secondary, "planType": "pro", "rateLimitReachedType": None}
    snapshot.update(extra.pop("snapshot", {}))
    return {"rateLimits": snapshot, **extra}


def auth_blob(last_refresh: str, refresh_token: str = "rt") -> bytes:
    return json.dumps(
        {"auth_mode": "chatgpt", "tokens": {"refresh_token": refresh_token, "access_token": "at"}, "last_refresh": last_refresh}
    ).encode()


MODELS = [
    {"id": "gpt-6-luna", "hidden": False, "supportedReasoningEfforts": [{"reasoningEffort": e} for e in ("medium", "high")]},
    {"id": "gpt-5.6-luna", "hidden": False, "supportedReasoningEfforts": [{"reasoningEffort": "high"}]},
    {"id": "gpt-7-luna", "hidden": True, "supportedReasoningEfforts": [{"reasoningEffort": "high"}]},
    {"id": "gpt-6-sol", "hidden": False, "supportedReasoningEfforts": [{"reasoningEffort": "medium"}]},
    {"id": "gpt-5.6-sol", "hidden": False, "supportedReasoningEfforts": [{"reasoningEffort": "medium"}]},
]


class AllowanceTests(unittest.TestCase):
    def test_both_windows_below_threshold_allows_codex(self) -> None:
        result = co.evaluate_allowance(limits(window(40, 300), window(74, 10080)))
        self.assertTrue(result["allowed"])
        self.assertEqual(result["windows"]["fiveHour"]["usedPercent"], 40)
        self.assertEqual(result["windows"]["weekly"]["usedPercent"], 74)

    def test_five_hour_at_threshold_overflows(self) -> None:
        result = co.evaluate_allowance(limits(window(75, 300), window(10, 10080)))
        self.assertFalse(result["allowed"])
        self.assertEqual(result["reasons"], ["fiveHour_used_75pct"])

    def test_weekly_over_threshold_overflows(self) -> None:
        result = co.evaluate_allowance(limits(window(5, 300), window(90, 10080)))
        self.assertEqual(result["reasons"], ["weekly_used_90pct"])

    def test_windows_classified_by_duration_not_position(self) -> None:
        result = co.evaluate_allowance(limits(window(80, 10080), window(10, 300)))
        self.assertEqual(result["windows"]["weekly"]["position"], "primary")
        self.assertEqual(result["reasons"], ["weekly_used_80pct"])

    def test_missing_window_fails_safe_to_overflow(self) -> None:
        result = co.evaluate_allowance(limits(window(10, 300), None))
        self.assertFalse(result["allowed"])
        self.assertEqual(result["reasons"], ["weekly_window_unknown"])

    def test_limit_reached_and_backend_denial_overflow(self) -> None:
        reached = co.evaluate_allowance(limits(window(1, 300), window(1, 10080), snapshot={"rateLimitReachedType": "rate_limit_reached"}))
        self.assertIn("limit_reached:rate_limit_reached", reached["reasons"])
        denied = co.evaluate_allowance(limits(window(1, 300), window(1, 10080), ordinaryUsageAllowed=False))
        self.assertIn("ordinary_usage_not_allowed", denied["reasons"])

    def test_codex_bucket_preferred_over_legacy_view(self) -> None:
        payload = limits(window(99, 300), window(99, 10080))
        payload["rateLimitsByLimitId"] = {"codex": {"primary": window(1, 300), "secondary": window(2, 10080)}}
        self.assertTrue(co.evaluate_allowance(payload)["allowed"])


class ModelResolutionTests(unittest.TestCase):
    def test_highest_visible_generation_wins(self) -> None:
        self.assertEqual(co.resolve_model(MODELS, "luna"), {"tier": "luna", "model": "gpt-6-luna", "effort": "high", "override": False})
        self.assertEqual(co.resolve_model(MODELS, "sol")["model"], "gpt-6-sol")
        self.assertEqual(co.resolve_model(MODELS, "sol")["effort"], "medium")

    def test_falls_back_to_older_generation(self) -> None:
        older = [m for m in MODELS if not m["id"].startswith("gpt-6")]
        self.assertEqual(co.resolve_model(older, "luna")["model"], "gpt-5.6-luna")

    def test_env_override_and_unsupported_effort(self) -> None:
        with mock.patch.dict(os.environ, {"CODEX_MODEL_LUNA": "gpt-5.6-luna"}):
            self.assertEqual(co.resolve_model(MODELS, "luna")["model"], "gpt-5.6-luna")
        with self.assertRaises(co.ToolError):
            co.resolve_model(MODELS, "sol", effort="high")
        with self.assertRaises(co.ToolError):
            co.resolve_model([], "luna")


class LivenessTests(unittest.TestCase):
    def test_classification(self) -> None:
        self.assertEqual(co.classify_liveness(0, ""), "live")
        self.assertEqual(co.classify_liveness(1, "Not signed in. Please run 'codex login'"), "logged_out")
        self.assertEqual(co.classify_liveness(1, "error: 401 Unauthorized"), "logged_out")
        self.assertEqual(co.classify_liveness(1, "Your refresh token has expired"), "logged_out")
        self.assertEqual(co.classify_liveness(1, "connection reset by peer"), "error")


class AuthSyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.env = mock.patch.dict(os.environ, {"CODEX_HOME": str(self.tmp / "home"), "CODEX_AUTH_STORE": str(self.tmp / "store")})
        self.env.start()
        os.environ.pop(co.STORE_KEY_ENV, None)

    def tearDown(self) -> None:
        self.env.stop()
        shutil.rmtree(self.tmp)

    def test_restore_from_store_when_local_missing(self) -> None:
        co.write_store(auth_blob("2026-09-01T00:00:00Z"))
        result = co.sync_auth()
        self.assertEqual(result["action"], "restored")
        self.assertTrue(result["usable"])
        self.assertEqual(stat.S_IMODE(co.local_auth_path().stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(co.codex_home().stat().st_mode), 0o700)

    def test_newer_local_is_saved_and_never_rolled_back(self) -> None:
        co.write_store(auth_blob("2026-09-01T00:00:00Z", "old"))
        co.write_local(auth_blob("2026-09-20T00:00:00Z", "new"))
        self.assertEqual(co.sync_auth()["action"], "saved")
        self.assertEqual(json.loads(co.read_store())["tokens"]["refresh_token"], "new")
        self.assertEqual(co.sync_auth()["action"], "in_sync")

    def test_newer_store_replaces_older_local(self) -> None:
        co.write_local(auth_blob("2026-09-01T00:00:00Z", "old"))
        co.write_store(auth_blob("2026-09-20T00:00:00Z", "new"))
        self.assertEqual(co.sync_auth()["action"], "restored")
        self.assertEqual(json.loads(co.read_local())["tokens"]["refresh_token"], "new")

    def test_nanosecond_last_refresh_orders_correctly(self) -> None:
        older = co.auth_freshness({"last_refresh": "2026-09-29T03:54:04.504051777Z"})
        newer = co.auth_freshness({"last_refresh": "2026-09-29T03:54:04.504052001Z"})
        self.assertLess(older, newer)
        self.assertEqual(older.year, 2026)

    def test_nothing_usable(self) -> None:
        co.write_store(b"not json")
        result = co.sync_auth()
        self.assertEqual(result["action"], "none")
        self.assertFalse(result["usable"])

    @unittest.skipUnless(shutil.which("openssl"), "openssl required")
    def test_encrypted_store_round_trip(self) -> None:
        with mock.patch.dict(os.environ, {co.STORE_KEY_ENV: "test-passphrase"}):
            co.write_local(auth_blob("2026-09-20T00:00:00Z", "secret-rt"))
            self.assertEqual(co.sync_auth()["action"], "saved")
            raw = (self.tmp / "store" / "auth.json.enc").read_bytes()
            self.assertNotIn(b"secret-rt", raw)
            co.local_auth_path().unlink()
            self.assertEqual(co.sync_auth()["action"], "restored")
            self.assertEqual(json.loads(co.read_local())["tokens"]["refresh_token"], "secret-rt")

    def test_status_never_contains_tokens(self) -> None:
        co.write_local(auth_blob("2026-09-20T00:00:00Z", "secret-rt"))
        self.assertNotIn("secret-rt", json.dumps(co.auth_status()))


class GateTests(unittest.TestCase):
    def run_gate(self, *, usable=True, live="live", rate=None, rate_error=None):
        sync = {"action": "in_sync", "usable": usable}
        with mock.patch.object(co, "sync_auth", return_value=sync) as synced, \
             mock.patch.object(co, "liveness", return_value={"state": live, "detail": ""}), \
             mock.patch.object(co, "read_rate_limits", side_effect=rate_error, return_value=rate):
            code, decision = co.gate()
        self.assertGreaterEqual(synced.call_count, 2)
        return code, decision

    def test_logged_out_stops_and_asks_carlos(self) -> None:
        for kwargs in ({"usable": False}, {"live": "logged_out"}, {"rate_error": co.LoggedOut("auth required")}):
            code, decision = self.run_gate(**kwargs)
            self.assertEqual(code, co.EXIT_ASK_CARLOS)
            self.assertEqual(decision["route"], "stop")
            self.assertTrue(decision["askCarlos"])

    def test_low_five_hour_allowance_overflows_to_cursor_002(self) -> None:
        code, decision = self.run_gate(rate=limits(window(80, 300), window(10, 10080)))
        self.assertEqual(code, co.EXIT_OVERFLOW)
        self.assertEqual(decision["route"], "cursor-002")
        self.assertEqual(decision["reasons"], ["fiveHour_used_80pct"])

    def test_liveness_or_rpc_error_overflows_without_asking(self) -> None:
        self.assertEqual(self.run_gate(live="error")[0], co.EXIT_OVERFLOW)
        code, decision = self.run_gate(rate_error=co.AppServerError("timed out"))
        self.assertEqual((code, decision["askCarlos"]), (co.EXIT_OVERFLOW, False))

    def test_healthy_routes_to_codex(self) -> None:
        code, decision = self.run_gate(rate=limits(window(10, 300), window(20, 10080)))
        self.assertEqual((code, decision["route"]), (co.EXIT_CODEX, "codex"))


FAKE_CODEX = textwrap.dedent(
    """\
    #!/usr/bin/env python3
    import json, subprocess, sys
    args = sys.argv[1:]
    if args[0] == "app-server":
        for line in sys.stdin:
            msg = json.loads(line)
            if "id" not in msg:
                continue
            result = {"data": MODELS, "nextCursor": None} if msg["method"] == "model/list" else {}
            print(json.dumps({"id": msg["id"], "result": result}), flush=True)
    elif args[0] == "exec":
        cwd = args[args.index("-C") + 1]
        out = args[args.index("-o") + 1]
        with open(sys.argv[0] + ".args", "w") as handle:
            json.dump(args, handle)
        prompt = sys.stdin.read()
        open(cwd + "/DONE.md", "a").write("done\\n")
        subprocess.run(["git", "add", "DONE.md"], cwd=cwd, check=True)
        subprocess.run(["git", "commit", "-qm", "IDE-9: done"], cwd=cwd, check=True)
        open(cwd + "/UNCOMMITTED.md", "w").write("wip\\n")
        print(json.dumps({"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 5}}))
        open(out, "w").write("Lessons:\\n- none\\nMODEL_SELF_REPORT: fake-luna high\\n")
    """
)


class RunIssueTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        origin, seed = self.tmp / "origin.git", self.tmp / "seed"
        subprocess.run(["git", "init", "-q", "--bare", str(origin)], check=True)
        subprocess.run(["git", "init", "-q", "-b", "development", str(seed)], check=True)
        for key, value in (("user.name", "t"), ("user.email", "t@example.com")):
            subprocess.run(["git", "config", key, value], cwd=seed, check=True)
        (seed / "README.md").write_text("seed\n")
        subprocess.run(["git", "add", "."], cwd=seed, check=True)
        subprocess.run(["git", "commit", "-qm", "seed"], cwd=seed, check=True)
        subprocess.run(["git", "remote", "add", "origin", str(origin)], cwd=seed, check=True)
        subprocess.run(["git", "push", "-q", "origin", "development"], cwd=seed, check=True)
        self.repo, self.origin = seed, origin
        fake = self.tmp / "codex"
        fake.write_text(FAKE_CODEX.replace("MODELS", repr(MODELS)))
        fake.chmod(0o755)
        self.fake = fake
        self.env = mock.patch.dict(os.environ, {
            "CODEX_BIN": str(fake),
            "CODEX_HOME": str(self.tmp / "home"),
            "CODEX_AUTH_STORE": str(self.tmp / "store"),
            "IDE_CODEX_STATE": str(self.tmp / "state"),
            "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.com",
            "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.com",
        })
        self.env.start()

    def tearDown(self) -> None:
        self.env.stop()
        shutil.rmtree(self.tmp)

    def args(self, **overrides) -> argparse.Namespace:
        prompt = self.tmp / "prompt.md"
        prompt.write_text("Add DONE.md.")
        values = dict(
            issue="IDE-9", slug="fake-run", prompt_file=str(prompt), tier="luna", effort=None, repo=str(self.repo),
            base=None, worktree_root=str(self.tmp / "wt"), timeout=60, threshold=75, network=False,
            no_push=False, skip_gate=True,
        )
        values.update(overrides)
        return argparse.Namespace(**values)

    def test_worktree_run_commits_pushes_and_logs(self) -> None:
        code, record = co.run_issue(self.args())
        self.assertEqual(code, co.EXIT_CODEX, record)
        self.assertEqual(record["branch"], "issue/IDE-9-fake-run")
        self.assertEqual(record["base"], "development")
        self.assertEqual((record["requestedModel"], record["requestedEffort"]), ("gpt-6-luna", "high"))
        self.assertEqual(record["selfReport"], "fake-luna high")
        self.assertEqual(record["newCommits"], 2)
        self.assertTrue(record["autosaveCommit"])
        self.assertTrue(record["pushed"])
        self.assertEqual(record["usage"], {"input_tokens": 10, "output_tokens": 5})
        remote = subprocess.run(["git", "ls-remote", "--heads", str(self.origin), "issue/IDE-9-fake-run"], capture_output=True, text=True)
        self.assertIn(record["head"], remote.stdout)
        argv = json.loads(Path(str(self.fake) + ".args").read_text())
        self.assertIn('model_reasoning_effort="high"', argv)
        self.assertEqual(argv[argv.index("-s") + 1], "workspace-write")
        self.assertNotIn("sandbox_workspace_write.network_access=true", argv)
        log = Path(record["runLog"]).read_text().splitlines()
        self.assertEqual(json.loads(log[-1])["issue"], "IDE-9")

    def test_rerun_reuses_pushed_branch_for_repair(self) -> None:
        co.run_issue(self.args())
        shutil.rmtree(self.tmp / "wt")
        subprocess.run(["git", "worktree", "prune"], cwd=self.repo, check=True)
        subprocess.run(["git", "branch", "-D", "issue/IDE-9-fake-run"], cwd=self.repo, check=True, capture_output=True)
        code, record = co.run_issue(self.args(tier="sol", no_push=True))
        self.assertEqual(code, co.EXIT_CODEX)
        self.assertEqual(record["requestedModel"], "gpt-6-sol")
        self.assertFalse(record["pushed"])

    def test_gate_refusal_skips_dispatch(self) -> None:
        with mock.patch.object(co, "gate", return_value=(co.EXIT_OVERFLOW, {"route": "cursor-002"})):
            code, record = co.run_issue(self.args(skip_gate=False))
        self.assertEqual(code, co.EXIT_OVERFLOW)
        self.assertFalse(record["dispatched"])
        self.assertFalse((self.tmp / "wt").exists())

    def test_rejects_bad_issue_ids(self) -> None:
        with self.assertRaises(co.ToolError):
            co.run_issue(self.args(issue="42"))


if __name__ == "__main__":
    unittest.main()
