"""CLI entrypoint tests."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from ide_development.constants import EXIT_OK
from ide_development_tests import ENTRYPOINT, FIXTURE_PACKAGE, TempRepoTestCase


class CliTests(TempRepoTestCase):
    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        cmd = [sys.executable, str(ENTRYPOINT), *args]
        return subprocess.run(cmd, text=True, capture_output=True)

    def test_cli_version_json(self) -> None:
        proc = self._run("version", "--package", str(self.package), "--json")
        self.assertEqual(proc.returncode, EXIT_OK, proc.stderr + proc.stdout)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["packageVersion"], "2.1.0")

    def test_cli_install_dry_run(self) -> None:
        proc = self._run(
            "install",
            "--package",
            str(self.package),
            "--target",
            str(self.target),
            "--dry-run",
            "--json",
        )
        self.assertEqual(proc.returncode, EXIT_OK, proc.stderr + proc.stdout)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["dryRun"])
        self.assertFalse((self.target / ".ide-development").exists())

    def test_cli_install_and_verify(self) -> None:
        proc = self._run(
            "install",
            "--package",
            str(self.package),
            "--target",
            str(self.target),
            "--json",
        )
        self.assertEqual(proc.returncode, EXIT_OK, proc.stderr + proc.stdout)
        verify = self._run(
            "verify",
            "--package",
            str(self.package),
            "--target",
            str(self.target),
            "--json",
        )
        self.assertEqual(verify.returncode, EXIT_OK, verify.stderr + verify.stdout)


if __name__ == "__main__":
    unittest.main()
