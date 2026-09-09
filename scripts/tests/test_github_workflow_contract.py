"""Focused static checks for the lean workflow/ruleset contract."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]
LIVE = ROOT / ".github" / "workflows"
MANAGED = ROOT / "core" / "github" / "managed-workflows"


class GithubWorkflowContractTests(unittest.TestCase):
    def test_authoritative_profiles_run_with_runtime_preflight(self) -> None:
        targets = (
            "linktrend-review-packager.yml",
            "linktrend-integrator-merge.yml",
        )
        invocation = re.compile(
            r"python3 scripts/gitops/run_delivery_profile.py (fast|full)(?: --preflight)?$",
            re.MULTILINE,
        )
        for directory in (LIVE, MANAGED):
            for filename in targets:
                path = directory / filename
                lines = [
                    match.group(0)
                    for match in invocation.finditer(path.read_text(encoding="utf-8"))
                ]
                self.assertTrue(lines, path)
                self.assertTrue(
                    all(line.endswith(" --preflight") for line in lines),
                    path,
                )

    def test_authoritative_workflows_match_managed_mirrors(self) -> None:
        for filename in (
            "linktrend-review-packager.yml",
            "linktrend-integrator-merge.yml",
        ):
            live = (LIVE / filename).read_text(encoding="utf-8")
            managed = (MANAGED / filename).read_text(encoding="utf-8")
            self.assertEqual(live, managed, filename)

    def test_full_trigger_dispatch_inputs_are_declared(self) -> None:
        required = (
            "dependency_digest:",
            "target_baseline_sha:",
            "target_baseline_ref:",
        )
        for directory in (LIVE, MANAGED):
            text = (directory / "linktrend-integrator-merge.yml").read_text(encoding="utf-8")
            dispatch = text.split("workflow_dispatch:", 1)[1].split("\nenv:", 1)[0]
            for name in required:
                self.assertIn(name, dispatch, f"{directory.name}: missing {name}")

    def test_managed_workflows_have_unique_job_contexts(self) -> None:
        for path in sorted(MANAGED.glob("*.yml")):
            document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            jobs = document.get("jobs") or {}
            contexts = [
                str(job.get("name"))
                for job in jobs.values()
                if isinstance(job, dict) and job.get("name")
            ]
            self.assertEqual(len(contexts), len(set(contexts)), path.name)

    def test_required_contexts_have_event_scoped_producers(self) -> None:
        contract = json.loads(
            (ROOT / ".github" / "linktrend-repository-ci-contract.json").read_text()
        )
        required = {
            context
            for profile in contract["profiles"].values()
            for context in profile.get("requiredCheckContexts", [])
        }
        producers: dict[str, list[str]] = {context: [] for context in required}
        for path in sorted(LIVE.glob("*.yml")):
            document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            for job_id, job in (document.get("jobs") or {}).items():
                if not isinstance(job, dict):
                    continue
                context = str(job.get("name") or "")
                if context in producers:
                    producers[context].append(f"{path.name}:{job_id}")
        self.assertEqual(
            producers,
            {
                "Linktrend Fast Checks": ["linktrend-review-packager.yml:fast"],
                "Linktrend Full Suite": ["linktrend-integrator-merge.yml:full"],
                "Linktrend Branch Source Policy": [
                    "branch-source-policy.yml:branch-source-policy",
                    "linktrend-development-to-staging.yml:branch-source-policy",
                    "linktrend-staging-to-main.yml:branch-source-policy",
                ],
                "Linktrend Receipt Gate": [
                    "linktrend-development-to-staging.yml:receipt-gate",
                    "linktrend-staging-to-main.yml:receipt-gate",
                ],
                "Verify IDE Development": ["ci.yml:verify"],
            },
        )

    def test_source_policy_and_checkouts_are_bounded(self) -> None:
        source = (LIVE / "branch-source-policy.yml").read_text(encoding="utf-8")
        self.assertIn("branches: [development]", source)
        promotion = (
            "linktrend-development-to-staging.yml",
            "linktrend-staging-to-main.yml",
            "branch-source-policy.yml",
        )
        for directory in (LIVE, MANAGED):
            for filename in promotion:
                path = directory / filename
                text = path.read_text(encoding="utf-8")
                self.assertNotIn("fetch-depth: 0", text, path.name)
                for line in text.splitlines():
                    if "git fetch" in line:
                        self.assertIn("--depth=1", line, path.name)

        packager = (MANAGED / "linktrend-review-packager.yml").read_text(encoding="utf-8")
        self.assertIn("name: Linktrend Reconciled Fast Checks", packager)
        self.assertIn(
            "needs: branch-source-policy",
            (MANAGED / "linktrend-development-to-staging.yml").read_text(),
        )

    def test_promotion_receipt_gate_requires_authenticated_transition_receipt(self) -> None:
        for filename in (
            "linktrend-development-to-staging.yml",
            "linktrend-staging-to-main.yml",
        ):
            for directory in (LIVE, MANAGED):
                text = (directory / filename).read_text(encoding="utf-8")
                self.assertIn("promotion_receipt_gate.py", text)
                self.assertIn("--transition-receipt", text)
                self.assertIn("git/refs/linktrend/transition-receipts/", text)
                self.assertIn("EXPECTED_SOURCE_BRANCH", text)
                self.assertIn("gate_receipt.py", text)
                self.assertNotIn("github.event.pull_request.body", text)
                self.assertIn("persist-credentials: false", text)
                self.assertIn("pull_request_target:", text)
                self.assertNotIn("workflow_dispatch:", text)


if __name__ == "__main__":
    unittest.main()
