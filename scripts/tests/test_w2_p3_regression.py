"""W2-P3 fixture regression, doctrine, and cleanup safety tests."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.gitops.coordinator.config import ConfigError, load_delivery_config
from scripts.gitops.coordinator.state import DeliveryState, StateError, transition
from scripts.gitops.promotion_receipt_gate import evaluate_release_path


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "scripts/tests/fixtures"
FORBIDDEN_ACTIVE_DOCTRINE = (
    "Mac Mini",
    "self-hosted",
    "linktrend-private",
    "linktrend-privileged",
    "local-coordinator",
    "App-backed",
    "custom GitHub App",
    "LINKTREND_GITOPS_APP",
)
ACTIVE_DOCS = (
    ROOT / "docs/contracts/STREAMLINED-DELIVERY.md",
    ROOT / "docs/contracts/DELIVERY-MODES.md",
    ROOT / "docs/contracts/ACTIONS-COST-CONTROLS.md",
    ROOT / "docs/contracts/GITHUB-APP-GITOPS-CREDENTIALS.md",
    ROOT / "docs/runbooks/hosted-delivery-operations.md",
    ROOT / "docs/runbooks/release-candidate.md",
    ROOT / "docs/GITOPS-CONSUMER-ROLLOUT.md",
    ROOT / "docs/AUTONOMOUS-GIT-OPERATIONS.md",
    ROOT / "core/managed-core/content/doctrine/STREAMLINED-DELIVERY.md",
    ROOT / "core/managed-core/content/doctrine/DELIVERY-MODES.md",
    ROOT / "core/managed-core/content/doctrine/AUTONOMOUS-GIT-OPERATIONS.md",
    ROOT / "core/managed-core/content/doctrine/0005-streamlined-delivery-coordinator.md",
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class W2P3RegressionTests(unittest.TestCase):
    def test_old_profile_fails_and_hosted_profile_passes(self) -> None:
        hosted = load_delivery_config(FIXTURES / "w2-p3-hosted-profile.json")
        self.assertEqual(hosted.compute.provider, "github-hosted")
        self.assertEqual(hosted.compute.runner, "ubuntu-24.04-arm")
        self.assertFalse(hosted.compute.checkpoint_ci)
        self.assertTrue(hosted.compute.cancel_obsolete)
        self.assertEqual(hosted.compute.max_infrastructure_attempts, 2)
        self.assertEqual(hosted.compute.max_sealed_candidates, 2)
        self.assertEqual(hosted.review.bugbot, "final-candidate-only")
        with self.assertRaises(ConfigError):
            load_delivery_config(FIXTURES / "w2-p3-legacy-profile.json")

    def test_frozen_event_matrix(self) -> None:
        state = DeliveryState.new("linktrend/IDE-Development", "phase/w2-p3", "W2-P3", "a" * 40)
        state = transition(state, {"type": "phase-opened"})
        state = transition(state, {"type": "sealed", "candidateIdentity": {
            "repository": "linktrend/IDE-Development", "sourceSha": "b" * 40,
            "gitTreeSha": "c" * 40, "dependencyDigests": {}, "testProfile": "fast",
        }})
        with self.assertRaisesRegex(StateError, "stale_identity"):
            transition(state, {"type": "fast-gate-passed", "sourceSha": "e" * 40})
        state = transition(state, {"type": "execution-started", "gate": "fast-gate"})
        state = transition(state, {"type": "execution-failed", "gate": "fast-gate", "detail": "fixture"})
        state = transition(state, {"type": "sealed", "candidateIdentity": {
            "repository": "linktrend/IDE-Development", "sourceSha": "f" * 40,
            "gitTreeSha": "0" * 40, "dependencyDigests": {}, "testProfile": "fast",
        }})
        state = transition(state, {"type": "execution-started", "gate": "fast-gate"})
        state = transition(state, {"type": "execution-failed", "gate": "fast-gate", "detail": "fixture"})
        self.assertEqual((state.attempts, state.status), (2, "stopped"))
        with self.assertRaisesRegex(StateError, "terminal_state"):
            transition(state, "observe")

    def test_old_workflow_contract_fails_and_hosted_contract_passes(self) -> None:
        hosted = load_json(FIXTURES / "w2-p3-workflow-contract.json")
        legacy = load_json(FIXTURES / "w2-p3-workflow-contract-legacy.json")
        self.assertEqual(hosted["fast"]["runner"], "ubuntu-24.04-arm")
        self.assertEqual(hosted["fast"]["concurrency"], "repository:workflow:pr-number")
        self.assertEqual(hosted["permissions"], {
            "contents": "read", "actions": "none", "pullRequests": "none", "statuses": "none",
        })
        self.assertEqual(hosted["seal"]["fullSuiteRuns"], 1)
        self.assertFalse(hosted["promotion"]["fullSuiteRerun"])
        self.assertNotEqual(legacy, hosted)
        self.assertNotEqual(legacy["fast"]["runner"], hosted["fast"]["runner"])
        self.assertTrue(legacy["checkpoint"]["ci"])

    def test_static_workflow_profile_rejects_legacy_fixture(self) -> None:
        hosted = (FIXTURES / "w2-p3-hosted-workflow.yml").read_text(encoding="utf-8")
        legacy = (FIXTURES / "w2-p3-legacy-workflow.yml").read_text(encoding="utf-8")
        self.assertIn("permissions:\n  contents: read", hosted)
        self.assertIn("runs-on: ubuntu-24.04-arm", hosted)
        self.assertIn("cancel-in-progress: true", hosted)
        self.assertIn("github.event.pull_request.number", hosted)
        for forbidden in FORBIDDEN_ACTIVE_DOCTRINE:
            self.assertNotIn(forbidden, hosted)
        self.assertTrue(any(forbidden in legacy for forbidden in FORBIDDEN_ACTIVE_DOCTRINE))

    def test_receipt_reuse_and_promotion_do_not_reenter_full_suite(self) -> None:
        decision = evaluate_release_path({
            "status": "passed",
            "testProfile": "release",
            "fullSuiteInvoked": False,
        })
        self.assertTrue(decision.accepted)
        self.assertEqual(decision.code, "accepted")
        rejected = evaluate_release_path({
            "status": "passed",
            "testProfile": "release",
            "fullSuiteInvoked": True,
        })
        self.assertEqual(rejected.code, "full_suite_reentered")

    def test_doctrine_is_hosted_and_mirrored(self) -> None:
        for path in ACTIVE_DOCS:
            text = path.read_text(encoding="utf-8")
            for forbidden in FORBIDDEN_ACTIVE_DOCTRINE:
                self.assertNotIn(forbidden, text, f"stale active doctrine: {path}: {forbidden}")
        for name in ("STREAMLINED-DELIVERY.md", "DELIVERY-MODES.md", "AUTONOMOUS-GIT-OPERATIONS.md"):
            self.assertEqual(
                (ROOT / "docs/contracts" / name).read_bytes()
                if name != "AUTONOMOUS-GIT-OPERATIONS.md"
                else (ROOT / "docs/AUTONOMOUS-GIT-OPERATIONS.md").read_bytes(),
                (ROOT / "core/managed-core/content/doctrine" / name).read_bytes(),
                name,
            )

    def test_cleanup_plan_dry_run_and_fixture_apply(self) -> None:
        tool = ROOT / "scripts/external/cleanup_plan.py"
        committed = FIXTURES / "w2-p3-cleanup"
        before = hashlib.sha256((committed / "resources/app-ide-owned.json").read_bytes()).hexdigest()
        dry = subprocess.run([
            "python3", str(tool), "--scope", "repository",
            "--inventory", str(committed / "repository.json"),
        ], check=True, capture_output=True, text=True)
        self.assertIn('"externalMutation": "none"', dry.stdout)
        self.assertIn("FORMER_DELIVERY_TOKEN", dry.stdout)
        self.assertNotIn("token-value", dry.stdout)
        self.assertEqual(before, hashlib.sha256((committed / "resources/app-ide-owned.json").read_bytes()).hexdigest())

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "fixture"
            shutil.copytree(committed, root)
            applied = subprocess.run([
                "python3", str(tool), "--scope", "host", "--apply",
                "--inventory", str(root / "host.json"), "--fixture-root", str(root),
            ], check=True, capture_output=True, text=True)
            self.assertIn('"mode": "fixture-apply"', applied.stdout)
            self.assertFalse((root / "resources/service-ide-owned.json").exists())
            self.assertTrue((root / "resources/container-lookalike.json").exists())
            self.assertNotIn("secret-value", applied.stdout)

    def test_cleanup_refuses_broad_or_live_apply(self) -> None:
        tool = ROOT / "scripts/external/cleanup_plan.py"
        inventory = FIXTURES / "w2-p3-cleanup/repository.json"
        missing_root = subprocess.run([
            "python3", str(tool), "--scope", "repository", "--apply", "--inventory", str(inventory),
        ], capture_output=True, text=True)
        self.assertEqual(missing_root.returncode, 2)
        self.assertIn("fixture-root", missing_root.stderr)
        with tempfile.TemporaryDirectory() as tmp:
            unsafe = load_json(inventory)
            unsafe["resources"][0]["id"] = "*"
            unsafe_path = Path(tmp) / "unsafe.json"
            unsafe_path.write_text(json.dumps(unsafe), encoding="utf-8")
            wildcard = subprocess.run([
                "python3", str(tool), "--scope", "repository", "--inventory", str(unsafe_path),
            ], capture_output=True, text=True)
            self.assertEqual(wildcard.returncode, 2)
            self.assertIn("exact", wildcard.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
