"""Portable Fast/Full profile contract for source and installed consumers."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.gitops import run_delivery_profile as runner


def profile(commands: list[list[str]]) -> dict:
    return {"schemaVersion": 2, "profiles": {"fast": {"commands": commands}, "full": {"commands": commands}}}


class DeliveryProfileRunnerTests(unittest.TestCase):
    def test_source_declares_internal_profiles(self) -> None:
        root = Path(__file__).resolve().parents[2]
        path, commands = runner.load_profile(root, "fast")
        self.assertEqual(path, root / ".github/linktrend-delivery-mode.json")
        self.assertTrue(any("scripts.tests.test_candidate_lifecycle" in command for command in commands))

    def test_consumer_without_ide_modules_uses_declared_managed_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / ".ide-development/config/delivery.json"
            config.parent.mkdir(parents=True)
            config.write_text(json.dumps(profile([["python3", "consumer_fast.py"]])), encoding="utf-8")
            path, commands = runner.load_profile(root, "fast")
            self.assertEqual(path, config)
            self.assertEqual(commands, [["python3", "consumer_fast.py"]])
            with patch.object(runner.subprocess, "run") as run:
                run.return_value = None
                for command in commands:
                    runner.subprocess.run(command, cwd=root, check=True)
            run.assert_called_once_with(["python3", "consumer_fast.py"], cwd=root, check=True)

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
