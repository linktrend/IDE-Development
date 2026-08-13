"""W1-P1 contract and negative probes for config and lifecycle state."""

from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from scripts.gitops.coordinator.config import ConfigError, load_delivery_config
from scripts.gitops.coordinator.state import (
    CandidateIdentity,
    DeliveryState,
    StateError,
    load_state,
    save_state,
    transition,
)


BASE = "c" * 40
IDENTITY = CandidateIdentity("owner/name", "a" * 40, "b" * 40, {}, "fast")


def v2_payload() -> dict:
    return {
        "schemaVersion": 2,
        "deliveryMode": "phase-integration",
        "phaseBranchPrefix": "phase/",
        "orchestrationMode": "local-coordinator",
        "fastTargetSeconds": 300,
        "maxAttemptsPerCandidate": 2,
        "maxSealedCandidateRevisions": 2,
        "maxFastJobs": 2,
        "maxHeavyJobs": 1,
        "stagingPromotion": "automatic",
        "mainPromotion": "principal-approval",
        "testProfiles": {
            "fast": {"commands": [["scripts/check.sh", "--fast"]], "timeoutSeconds": 300},
            "full": {"required": False, "commands": [], "timeoutSeconds": 3600},
            "release": {"commands": [], "timeoutSeconds": 300},
        },
        "dependencyFiles": ["package-lock.json", "package.json", "package.json"],
        "resourceLimits": {
            "fastCpus": 1.0,
            "fastMemoryMiB": 2048,
            "heavyCpus": 2.0,
            "heavyMemoryMiB": 4096,
            "pidsLimit": 768,
            "pauseCpuPercent": 80,
            "pauseMemoryPercent": 80,
            "minimumFreeDiskGiB": 20,
        },
    }


class DeliveryConfigTests(unittest.TestCase):
    def test_v1_fixture_loads_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".github").mkdir()
            (root / ".github/linktrend-delivery-mode.json").write_text(
                '{"schemaVersion": 1, "deliveryMode": "phase-integration", "phaseBranchPrefix": "phase/"}\n',
                encoding="utf-8",
            )
            config = load_delivery_config(root, env={})
        self.assertEqual(config.schema_version, 1)
        self.assertEqual(config.delivery_mode, "phase-integration")
        self.assertEqual(config.phase_branch_prefix, "phase/")

    def test_v2_normalizes_deterministically(self) -> None:
        first = load_delivery_config(v2_payload())
        payload = v2_payload()
        payload["dependencyFiles"] = ["package.json", "package-lock.json"]
        second = load_delivery_config(payload)
        self.assertEqual(first.to_dict(), second.to_dict())
        self.assertEqual(first.dependency_files, ("package-lock.json", "package.json"))
        self.assertEqual(first.test_profiles["fast"].commands, (("scripts/check.sh", "--fast"),))

    def assert_config_rejected(self, payload: dict, code: str) -> None:
        with self.assertRaises(ConfigError) as raised:
            load_delivery_config(payload)
        self.assertEqual(raised.exception.code, code)

    def test_unknown_and_unsafe_config_is_rejected(self) -> None:
        unknown = v2_payload()
        unknown["unexpected"] = True
        self.assert_config_rejected(unknown, "unknown_or_missing_field")

        absolute = v2_payload()
        absolute["testProfiles"]["fast"]["commands"] = ["/bin/echo"]
        self.assert_config_rejected(absolute, "unsafe_path")

        outside = v2_payload()
        outside["dependencyFiles"] = ["../secrets.txt"]
        self.assert_config_rejected(outside, "path_escape")

        limits = v2_payload()
        limits["maxFastJobs"] = 3
        self.assert_config_rejected(limits, "invalid_limits")

    def test_v1_unknown_fields_are_rejected(self) -> None:
        payload = {"schemaVersion": 1, "deliveryMode": "issue-pr", "unknown": True}
        self.assert_config_rejected(payload, "unknown_field")


class DeliveryStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.state = DeliveryState.new("owner/name", "phase/streamlined", "P1", BASE)

    def seal(self, state: DeliveryState, identity: CandidateIdentity = IDENTITY) -> DeliveryState:
        return transition(
            transition(state, {"type": "phase-opened"}) if state.status == "created" else state,
            {"type": "sealed", "candidateIdentity": identity.to_dict()},
        )

    def test_structured_lifecycle_and_passive_events_do_not_increment_attempts(self) -> None:
        state = transition(self.state, {"type": "phase-opened"})
        state = transition(state, {"type": "issue-accepted", "issue": {"branch": "issue/1-x", "sha": "d" * 40}})
        state = transition(state, {"type": "issue-included", "issue": {"branch": "issue/1-x", "sha": "d" * 40}})
        state = transition(state, {"type": "draft-pr-created", "draftPr": {"number": 10, "url": "sanitized"}})
        state = transition(state, {"type": "sealed", "candidateIdentity": IDENTITY.to_dict()})
        for event in ("observe", "deduplicate", "passive-observation", "cancel-before-start"):
            if event == "cancel-before-start":
                observed = transition(state, event)
                self.assertEqual(observed.attempts, 0)
                self.assertEqual(observed.status, "cancelled")
                continue
            self.assertEqual(transition(state, event), state)
        state = transition(state, {"type": "execution-started", "gate": "fast-gate"})
        self.assertEqual(state.attempts, 1)

    def test_stale_sha_and_promotion_before_gates_are_rejected(self) -> None:
        state = self.seal(self.state)
        with self.assertRaisesRegex(StateError, "stale_identity"):
            transition(state, {"type": "fast-gate-passed", "sourceSha": "d" * 40})
        with self.assertRaisesRegex(StateError, "illegal_order"):
            transition(state, {"type": "promote-staging", "stagingSha": "e" * 40})

    def test_two_attempt_stop_and_third_seal(self) -> None:
        state = self.seal(self.state)
        state = transition(state, {"type": "execution-started", "gate": "fast-gate"})
        state = transition(state, {"type": "execution-failed", "gate": "fast-gate", "detail": "sanitized failure"})
        self.assertEqual(state.attempts, 1)
        second = CandidateIdentity("owner/name", "d" * 40, "e" * 40, {}, "fast")
        state = transition(state, {"type": "sealed", "candidateIdentity": second.to_dict()})
        with self.assertRaisesRegex(StateError, "third_seal"):
            transition(state, {"type": "sealed", "candidateIdentity": IDENTITY.to_dict()})
        state = transition(state, {"type": "execution-started", "gate": "fast-gate"})
        state = transition(state, {"type": "execution-failed", "gate": "fast-gate", "detail": "sanitized failure"})
        self.assertEqual((state.status, state.attempts), ("stopped", 2))
        with self.assertRaisesRegex(StateError, "terminal_state"):
            transition(state, "observe")

    def test_terminal_states_cannot_auto_transition(self) -> None:
        for terminal in ("stopped", "blocked", "main-promoted"):
            state = replace(self.state, status=terminal)
            with self.subTest(terminal=terminal), self.assertRaisesRegex(StateError, "terminal_state"):
                transition(state, "observe")

    def test_atomic_write_preserves_previous_state_on_interruption(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            save_state(self.state, path)
            original = path.read_bytes()
            with patch("scripts.gitops.coordinator.state.os.replace", side_effect=OSError("interrupted")):
                with self.assertRaises(OSError):
                    save_state(replace(self.state, status="collecting"), path)
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(load_state(path), self.state)


if __name__ == "__main__":
    unittest.main()
