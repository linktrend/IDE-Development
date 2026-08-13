"""Tests for exact-head consumer CI discovery used by Full Suite."""
from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.gitops.require_exact_ci_success import require_success


class ExactCiSuccessTests(unittest.TestCase):
    head = "a" * 40

    def root(self, tmp: str) -> Path:
        root = Path(tmp)
        config = root / ".github" / "linktrend-gitops-consumer.json"
        config.parent.mkdir()
        config.write_text(json.dumps({"ciWorkflowName": "Consumer CI"}), encoding="utf-8")
        return root

    def test_accepts_only_declared_success_at_exact_head(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {"LINKTREND_ACTIONS_RUNS_JSON": json.dumps({"workflow_runs": [
                {"name": "Consumer CI", "head_sha": self.head, "conclusion": "success"},
                {"name": "Consumer CI", "head_sha": "b" * 40, "conclusion": "success"},
            ]})}, clear=False):
                self.assertEqual(require_success("linktrend/fixture", self.head, self.root(tmp)), "Consumer CI")

    def test_rejects_missing_exact_success_and_malformed_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = self.root(tmp)
            with patch.dict(os.environ, {"LINKTREND_ACTIONS_RUNS_JSON": '{"workflow_runs": []}'}, clear=False):
                with self.assertRaisesRegex(SystemExit, "full_suite_required_ci_missing_for_exact_head"):
                    require_success("linktrend/fixture", self.head, root)
            (root / ".github" / "linktrend-gitops-consumer.json").write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(SystemExit, "consumer_ci_config_invalid"):
                require_success("linktrend/fixture", self.head, root)
