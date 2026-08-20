import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CANARY = ROOT / "scripts" / "ide_development" / "app_canary.mjs"


def run_canary(profile: str) -> dict:
    result = subprocess.run(
        ["node", str(CANARY), "--json", "--profile", profile],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


class AppCanaryTests(unittest.TestCase):
    def test_canary_profile_proves_both_applications_without_raw_evidence(self):
        result = run_canary("canary")

        self.assertTrue(result["ok"])
        self.assertEqual(result["profile"], "canary")
        self.assertEqual(result["applications"], ["codex", "cursor"])
        self.assertEqual(result["tools"], [
            "platform.identity.resolve",
            "brain.projection.read",
            "skills.release.read",
            "brain.handoff.create",
        ])
        self.assertEqual(
            [row["application"] for row in result["runs"]],
            ["codex", "cursor"],
        )
        for row in result["runs"]:
            self.assertTrue(row["session"]["isolated"])
            self.assertTrue(row["session"]["cleaned"])
            self.assertEqual(row["status"], "passed")
        evidence = json.dumps(result)
        self.assertNotIn("token", evidence.lower())
        self.assertNotIn(str(ROOT), evidence)

    def test_release_profile_is_narrow_and_live_for_both_applications(self):
        result = run_canary("release")

        self.assertTrue(result["ok"])
        self.assertEqual(result["profile"], "release")
        self.assertEqual(result["applications"], ["codex", "cursor"])
        self.assertGreater(len(result["tools"]), 4)
        self.assertNotIn("skills.telemetry.submit", result["tools"])
        self.assertNotIn("autowork.request.submit", result["tools"])
        for row in result["runs"]:
            self.assertEqual(row["status"], "passed")
            self.assertEqual(row["providerCalls"], 4)
