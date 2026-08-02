"""Fail-closed exit codes and deterministic JSON for every refusal class."""

from __future__ import annotations

import json
import unittest

from harness import DisposableRepoTestCase, load_manifest, parse_json_stdout, run_cli, write_manifest

from ide_development.constants import (
    EXIT_CONFLICT,
    EXIT_DRIFT,
    EXIT_ERROR,
    EXIT_INVALID_PACKAGE,
    EXIT_OK,
    EXIT_ROLLBACK_FAILURE,
)
from ide_development.engine import run_install_or_update, run_drift


class CliJsonRefusalTests(DisposableRepoTestCase):
    def test_invalid_package_json_shape(self) -> None:
        data = load_manifest(self.package)
        data["files"][0]["sourceHash"] = "sha256:" + ("b" * 64)
        write_manifest(self.package, data)
        proc = run_cli(
            "plan",
            "--package",
            str(self.package),
            "--target",
            str(self.target),
            "--json",
        )
        self.assertEqual(proc.returncode, EXIT_INVALID_PACKAGE)
        payload = parse_json_stdout(proc)
        self.assertEqual(payload["schemaVersion"], 1)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["command"], "plan")
        self.assertEqual(payload["exitCode"], EXIT_INVALID_PACKAGE)
        self.assertIsInstance(payload["error"], str)
        self.assertIsInstance(payload.get("details"), dict)

    def test_conflict_plan_exit_11_deterministic(self) -> None:
        dest = self.target / ".ide-development"
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "CORE.txt").write_text("foreign content\n", encoding="utf-8")
        proc = run_cli(
            "install",
            "--package",
            str(self.package),
            "--target",
            str(self.target),
            "--json",
        )
        self.assertEqual(proc.returncode, EXIT_CONFLICT)
        payload = parse_json_stdout(proc)
        self.assertEqual(payload["schemaVersion"], 1)
        self.assertGreaterEqual(payload["summary"]["conflictCount"], 1)
        for key in ("actions", "conflicts", "drift", "summary"):
            self.assertIn(key, payload)
        # Second run must be identical conflict class (deterministic)
        proc2 = run_cli(
            "install",
            "--package",
            str(self.package),
            "--target",
            str(self.target),
            "--json",
        )
        self.assertEqual(proc2.returncode, EXIT_CONFLICT)
        payload2 = parse_json_stdout(proc2)
        self.assertEqual(
            [c["kind"] for c in payload["conflicts"]],
            [c["kind"] for c in payload2["conflicts"]],
        )

    def test_drift_exit_10(self) -> None:
        ok = run_install_or_update(
            target=self.target,
            package=self.package,
            command="install",
            dry_run=False,
        )
        self.assertEqual(ok.exit_code, EXIT_OK)
        (self.target / ".ide-development" / "CORE.txt").write_text("drifted\n", encoding="utf-8")
        proc = run_cli(
            "drift",
            "--package",
            str(self.package),
            "--target",
            str(self.target),
            "--json",
        )
        self.assertEqual(proc.returncode, EXIT_DRIFT)
        payload = parse_json_stdout(proc)
        self.assertGreaterEqual(payload["summary"]["driftCount"], 1)

    def test_rollback_without_history_exit_13(self) -> None:
        proc = run_cli("rollback", "--target", str(self.target), "--json")
        self.assertEqual(proc.returncode, EXIT_ROLLBACK_FAILURE)
        payload = parse_json_stdout(proc)
        self.assertFalse(payload["ok"])
        self.assertIn("error", payload)
        self.assertEqual(payload["exitCode"], EXIT_ROLLBACK_FAILURE)

    def test_self_install_refused_exit_12(self) -> None:
        # Make package a git repo identical path target==package
        import subprocess
        from pathlib import Path

        subprocess.run(["git", "init"], cwd=str(self.package), check=True, capture_output=True)
        (self.package / "README.md").write_text("pkg\n", encoding="utf-8")
        subprocess.run(["git", "add", "README.md"], cwd=str(self.package), check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "t@example.com"],
            cwd=str(self.package),
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "t"],
            cwd=str(self.package),
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=str(self.package),
            check=True,
            capture_output=True,
        )
        proc = run_cli(
            "install",
            "--package",
            str(self.package),
            "--target",
            str(self.package),
            "--json",
        )
        self.assertEqual(proc.returncode, EXIT_INVALID_PACKAGE)
        payload = parse_json_stdout(proc)
        self.assertIn("itself", payload["error"].lower())

    def test_exit_code_contract_constants(self) -> None:
        self.assertEqual(EXIT_OK, 0)
        self.assertEqual(EXIT_ERROR, 1)
        self.assertEqual(EXIT_DRIFT, 10)
        self.assertEqual(EXIT_CONFLICT, 11)
        self.assertEqual(EXIT_INVALID_PACKAGE, 12)
        self.assertEqual(EXIT_ROLLBACK_FAILURE, 13)


if __name__ == "__main__":
    unittest.main()
