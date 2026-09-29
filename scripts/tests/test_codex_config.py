"""Tests for scripts/codex/set_codex_config.py (top-level Codex config key, TOML scope)."""

from __future__ import annotations

import stat
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

from scripts.codex import set_codex_config as cfg

ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "scripts" / "codex" / "set_codex_config.py"
TABLE_CONFIG = 'model = "gpt-6-luna"\n\n[mcp_servers.docs]\ncommand = "docs-mcp"\nargs = ["--port", "1"]\n'


class SetTopLevelTests(unittest.TestCase):
    def test_existing_table_config_gets_a_top_level_key(self) -> None:
        updated = cfg.set_top_level(TABLE_CONFIG, cfg.DEFAULT_KEY, "file")
        parsed = tomllib.loads(updated)
        self.assertEqual(parsed["cli_auth_credentials_store"], "file")
        self.assertNotIn("cli_auth_credentials_store", parsed["mcp_servers"]["docs"])
        self.assertEqual(parsed["mcp_servers"]["docs"]["args"], ["--port", "1"])
        self.assertEqual(parsed["model"], "gpt-6-luna")

    def test_naive_append_would_land_in_the_last_table(self) -> None:
        appended = tomllib.loads(TABLE_CONFIG + 'cli_auth_credentials_store = "file"\n')
        self.assertNotIn("cli_auth_credentials_store", appended)

    def test_replaces_other_top_level_value_and_keeps_table_keys(self) -> None:
        text = 'cli_auth_credentials_store = "keyring"\n[profiles.x]\ncli_auth_credentials_store = "keyring"\n'
        parsed = tomllib.loads(cfg.set_top_level(text, cfg.DEFAULT_KEY, "file"))
        self.assertEqual(parsed["cli_auth_credentials_store"], "file")
        self.assertEqual(parsed["profiles"]["x"]["cli_auth_credentials_store"], "keyring")

    def test_idempotent_and_empty(self) -> None:
        once = cfg.set_top_level("", cfg.DEFAULT_KEY, "file")
        self.assertEqual(once, 'cli_auth_credentials_store = "file"\n')
        self.assertEqual(cfg.set_top_level(once, cfg.DEFAULT_KEY, "file"), once)

    def test_invalid_toml_is_refused(self) -> None:
        with self.assertRaises(cfg.ConfigError):
            cfg.set_top_level("model = \n[broken", cfg.DEFAULT_KEY, "file")


class CliTests(unittest.TestCase):
    def test_cli_updates_file_in_place_with_private_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.toml"
            path.write_text(TABLE_CONFIG)
            proc = subprocess.run([sys.executable, str(HELPER), str(path)], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertEqual(tomllib.loads(path.read_text())["cli_auth_credentials_store"], "file")
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            again = subprocess.run([sys.executable, str(HELPER), str(path)], capture_output=True, text=True)
            self.assertIn("unchanged", again.stdout)

    def test_cli_leaves_invalid_file_untouched(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.toml"
            path.write_text("[broken\n")
            proc = subprocess.run([sys.executable, str(HELPER), str(path)], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 1)
            self.assertEqual(path.read_text(), "[broken\n")

    def test_installers_use_the_helper(self) -> None:
        for script in ("scripts/setup.sh", "scripts/codex/install.sh"):
            text = (ROOT / script).read_text()
            self.assertIn("set_codex_config.py", text, script)
            self.assertNotIn(">> \"$HOME/.codex/config.toml\"", text, script)


if __name__ == "__main__":
    unittest.main()
