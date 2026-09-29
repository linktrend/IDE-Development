#!/usr/bin/env python3
"""Tests for scripts/orchestrator/runlog.py and watchdog.py (stdlib only)."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "orchestrator"))

import runlog  # noqa: E402
import watchdog  # noqa: E402

SCHEMA_PATH = ROOT / "core" / "contracts" / "RUN-LOG-RECORD.schema.json"


def _iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")


class RunLogTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "runlog"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_one_file_per_attempt_with_incrementing_numbers(self) -> None:
        a = runlog.start_run(self.root, issue="IDE-4", executor="cursor-002", requested_model="grok-4.7",
                             reasoning_effort="medium", branch="issue/IDE-4-ledger-schema")
        runlog.finish_run(self.root, issue="IDE-4", run_key=a["run_key"], result="failure",
                          self_reported_model="Grok 4.7", failure_summary="tests red", cost_usd=0.05)
        b = runlog.start_run(self.root, issue="IDE-4", executor="codex-cli", requested_model="gpt-6-sol",
                             repair_rung=1)
        done = runlog.finish_run(self.root, issue="IDE-4", run_key=b["run_key"], result="success",
                                 self_reported_model="gpt-6-sol", head_sha="abc1234")
        self.assertEqual([p.name for p in sorted((self.root / "IDE-4").iterdir())],
                         ["attempt-001.json", "attempt-002.json"])
        self.assertEqual(done["attempt"], 2)
        self.assertEqual(done["head_sha"], "abc1234")
        self.assertIsNotNone(done["ended_at"])

    def test_start_is_idempotent_on_run_key(self) -> None:
        first = runlog.start_run(self.root, issue="IDE-5", executor="codex-cli", requested_model="gpt-6-luna",
                                 run_key="run-fixed-key")
        again = runlog.start_run(self.root, issue="IDE-5", executor="codex-cli", requested_model="gpt-6-luna",
                                 run_key="run-fixed-key")
        self.assertEqual(first, again)
        self.assertEqual(len(list(runlog.iter_records(self.root))), 1)

    def test_finish_rules(self) -> None:
        rec = runlog.start_run(self.root, issue="IDE-6", executor="cursor-002", requested_model="grok-4.7")
        runlog.finish_run(self.root, issue="IDE-6", run_key=rec["run_key"], result="success")
        runlog.finish_run(self.root, issue="IDE-6", run_key=rec["run_key"], result="success")
        with self.assertRaises(runlog.RunLogError):
            runlog.finish_run(self.root, issue="IDE-6", run_key=rec["run_key"], result="failure")
        with self.assertRaises(runlog.RunLogError):
            runlog.finish_run(self.root, issue="IDE-6", run_key=rec["run_key"], result="running")

    def test_rejects_bad_input(self) -> None:
        for kwargs in (
            {"issue": "ide-4", "executor": "codex-cli", "requested_model": "m"},
            {"issue": "IDE-4", "executor": "laptop", "requested_model": "m"},
            {"issue": "IDE-4", "executor": "codex-cli", "requested_model": ""},
            {"issue": "IDE-4", "executor": "codex-cli", "requested_model": "m", "repair_rung": 4},
        ):
            with self.assertRaises(runlog.RunLogError, msg=kwargs):
                runlog.start_run(self.root, **kwargs)
        rec = runlog.start_run(self.root, issue="IDE-4", executor="codex-cli", requested_model="m")
        with self.assertRaises(runlog.RunLogError):
            runlog.finish_run(self.root, issue="IDE-4", run_key=rec["run_key"], result="success", head_sha="XYZ")

    def test_concurrent_starts_get_distinct_attempts(self) -> None:
        results: list[int] = []

        def worker() -> None:
            rec = runlog.start_run(self.root, issue="IDE-9", executor="codex-cli", requested_model="gpt-6-luna")
            results.append(rec["attempt"])

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(sorted(results), list(range(1, 9)))

    def test_records_match_json_schema(self) -> None:
        try:
            import jsonschema
        except ImportError:
            self.skipTest("jsonschema not installed")
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        rec = runlog.start_run(self.root, issue="IDE-4", executor="cursor-002", requested_model="grok-4.7")
        jsonschema.validate(rec, schema)
        done = runlog.finish_run(self.root, issue="IDE-4", run_key=rec["run_key"], result="failure", cost_usd=0.1)
        jsonschema.validate(done, schema)
        self.assertEqual(set(schema["required"]), set(runlog.FIELDS))

    def test_export_sql_quotes_and_orders(self) -> None:
        rec = runlog.start_run(self.root, issue="IDE-4", executor="cursor-002", requested_model="grok-4.7",
                               run_key="run-quote-test")
        runlog.finish_run(self.root, issue="IDE-4", run_key=rec["run_key"], result="failure",
                          failure_summary="it's broken'; drop table x; --")
        sql = runlog.export_sql(self.root)
        self.assertIn("select ide_ledger.start_run('run-quote-test', 'IDE-4', 'cursor-002'", sql)
        self.assertIn("'it''s broken''; drop table x; --'", sql)
        self.assertTrue(sql.startswith("begin;") and sql.rstrip().endswith("commit;"))

    def test_cli_round_trip(self) -> None:
        script = ROOT / "scripts" / "orchestrator" / "runlog.py"

        def cli(*args: str) -> dict:
            out = subprocess.run([sys.executable, str(script), "--root", str(self.root), *args],
                                 capture_output=True, text=True, check=True)
            return json.loads(out.stdout)

        rec = cli("start", "--issue", "IDE-7", "--executor", "cursor-001-subagent",
                  "--requested-model", "composer-2.5")
        cli("heartbeat", "--issue", "IDE-7", "--run-key", rec["run_key"])
        done = cli("finish", "--issue", "IDE-7", "--run-key", rec["run_key"], "--result", "success",
                   "--self-reported-model", "composer-2.5")
        self.assertEqual(done["result"], "success")


class WatchdogTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.root = self.tmp / "runlog"
        self.now = datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _args(self, **overrides) -> argparse.Namespace:
        base = dict(root=str(self.root), repo=None, stall_minutes=90, max_failures=3, fetch=False, exit_zero=False)
        base.update(overrides)
        return argparse.Namespace(**base)

    def _attempt(self, issue: str, result: str, rung: int = 0, model: str = "gpt-6-luna",
                 started: datetime | None = None) -> dict:
        started = started or self.now - timedelta(minutes=30)
        rec = runlog.start_run(self.root, issue=issue, executor="codex-cli", requested_model=model,
                               repair_rung=rung, started_at=_iso(started))
        if result != "running":
            rec = runlog.finish_run(self.root, issue=issue, run_key=rec["run_key"], result=result,
                                    ended_at=_iso(started + timedelta(minutes=5)))
        return rec

    def test_clean_log_is_ok(self) -> None:
        self._attempt("IDE-1", "success")
        self._attempt("IDE-2", "running")
        report = watchdog.run(self._args(), now=self.now)
        self.assertTrue(report["ok"], report)
        self.assertEqual(report["runs_seen"], 2)

    def test_flags_deliberately_stalled_run(self) -> None:
        stalled = self._attempt("IDE-3", "running", started=self.now - timedelta(hours=3))
        report = watchdog.run(self._args(), now=self.now)
        kinds = [(f["kind"], f.get("run_key")) for f in report["findings"]]
        self.assertEqual(kinds, [("stalled_run", stalled["run_key"])])
        self.assertEqual(report["findings"][0]["idle_minutes"], 180)

    def test_repeated_failures_follow_the_repair_ladder(self) -> None:
        for _ in range(2):
            self._attempt("IDE-10", "failure")
        self.assertTrue(watchdog.run(self._args(), now=self.now)["ok"], "2 of 3 tries is not yet a finding")

        self._attempt("IDE-10", "failure")
        finding = watchdog.run(self._args(), now=self.now)["findings"][0]
        self.assertEqual(finding["recommended_action"], "escalate to repair rung 1")

        self._attempt("IDE-10", "failure", rung=1, model="gpt-6-sol")
        finding = watchdog.run(self._args(), now=self.now)["findings"][0]
        self.assertEqual((finding["recommended_action"], finding["severity"]), ("flag Carlos", "error"))

        self._attempt("IDE-11", "failure", model="claude-opus-5-5")
        self._attempt("IDE-11", "failure", model="claude-opus-5-5")
        self._attempt("IDE-11", "failure", model="claude-opus-5-5")
        self._attempt("IDE-11", "failure", rung=1, model="gpt-6-sol")
        actions = {f["issue"]: f["recommended_action"] for f in watchdog.run(self._args(), now=self.now)["findings"]}
        self.assertEqual(actions["IDE-11"], "escalate to repair rung 2")

        self._attempt("IDE-10", "success", rung=1, model="gpt-6-sol")
        issues = {f["issue"] for f in watchdog.run(self._args(), now=self.now)["findings"]}
        self.assertNotIn("IDE-10", issues)

    def _git(self, cwd: Path, *args: str) -> str:
        return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, check=True).stdout

    def test_unpushed_work(self) -> None:
        remote = self.tmp / "remote.git"
        repo = self.tmp / "repo"
        subprocess.run(["git", "init", "-q", "--bare", str(remote)], check=True)
        subprocess.run(["git", "init", "-q", "-b", "development", str(repo)], check=True)
        self._git(repo, "config", "user.email", "t@example.invalid")
        self._git(repo, "config", "user.name", "t")
        (repo / "a.txt").write_text("a\n")
        self._git(repo, "add", "a.txt")
        self._git(repo, "commit", "-qm", "init")
        self._git(repo, "remote", "add", "origin", str(remote))
        self._git(repo, "push", "-q", "origin", "development")

        self._git(repo, "checkout", "-qb", "issue/IDE-20-pushed")
        self._git(repo, "push", "-q", "origin", "issue/IDE-20-pushed")
        self.assertTrue(watchdog.run(self._args(repo=[str(repo)]), now=self.now)["ok"])

        (repo / "a.txt").write_text("changed\n")
        self._git(repo, "commit", "-qam", "local only")
        self._git(repo, "branch", "issue/IDE-21-never-pushed")
        wt = self.tmp / "wt"
        self._git(repo, "worktree", "add", "-q", str(wt), "issue/IDE-21-never-pushed")
        (wt / "new.txt").write_text("dirty\n")
        self._git(repo, "branch", "cursor/ignored-branch")

        findings = watchdog.run(self._args(repo=[str(repo)]), now=self.now)["findings"]
        states = sorted((f["branch"], f["state"]) for f in findings)
        self.assertEqual(states, [
            ("issue/IDE-20-pushed", "ahead"),
            ("issue/IDE-21-never-pushed", "dirty"),
            ("issue/IDE-21-never-pushed", "no_remote"),
        ])

    def test_cli_exit_codes(self) -> None:
        script = ROOT / "scripts" / "orchestrator" / "watchdog.py"
        base = [sys.executable, str(script), "--root", str(self.root)]
        self.assertEqual(subprocess.run(base, capture_output=True).returncode, 0)
        self._attempt("IDE-30", "running", started=datetime.now(timezone.utc) - timedelta(hours=5))
        self.assertEqual(subprocess.run(base, capture_output=True).returncode, 1)
        self.assertEqual(subprocess.run(base + ["--exit-zero"], capture_output=True).returncode, 0)
        bad = subprocess.run(base + ["--repo", str(self.tmp / "missing")], capture_output=True, text=True)
        self.assertEqual(bad.returncode, 2)
        self.assertIn("error", json.loads(bad.stdout))


if __name__ == "__main__":
    unittest.main()
