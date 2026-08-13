import json
import tempfile
import unittest
from pathlib import Path

from host.coordinator.multihost import MultiHostCoordinator
from host.coordinator.queue import QueueRequest
from host.coordinator.workers import Worker
from scripts.gitops.coordinator.config import load_delivery_config
from scripts.gitops.coordinator.receipts import verify_receipt, write_receipt


class W4PolicyAndReceiptTests(unittest.TestCase):
    def test_repository_policy_is_complete_local_coordinator_v2(self):
        payload = json.loads(Path(".github/linktrend-delivery-mode.json").read_text())
        config = load_delivery_config(payload, env={})
        self.assertEqual(config.orchestration_mode, "local-coordinator")
        self.assertEqual(config.main_promotion, "principal-approval")
        self.assertEqual(config.test_profiles["fast"].commands[0], ("bash", "scripts/tests/test_local_coordinator_workflow_profile.sh"))
        self.assertEqual(config.test_profiles["full"].commands[0], ("bash", "scripts/verify-ide-development.sh"))

    def test_receipt_metadata_does_not_change_exact_content_reuse(self):
        with tempfile.TemporaryDirectory() as directory:
            coordinator = MultiHostCoordinator(Path(directory) / "state.sqlite3", coordinator_id="coord-test")
            coordinator.register_worker(Worker("mac", "macos", "arm64", capabilities=frozenset({"fast"}), max_fast_jobs=1, last_heartbeat=1000, repositories=("owner/repo",)))
            candidate = {"repository": "owner/repo", "sourceSha": "a" * 40, "gitTreeSha": "b" * 40, "dependencyDigests": {}, "testProfile": "fast"}
            queued = coordinator.enqueue(QueueRequest("owner/repo", "fast-gate", candidate, priority=2))
            lease = coordinator.claim("mac", now=1000)
            metadata = coordinator.receipt_metadata(lease, execution_environment={"platform": "linux", "arch": "amd64", "container": "alpine:3.20"})
            receipt = {
                "schemaVersion": 1, "status": "passed", "repository": "owner/repo", "gate": "fast-gate",
                "sourceSha": "a" * 40, "testedCheckoutSha": "a" * 40, "gitTreeSha": "b" * 40,
                "dependencyDigests": {}, "testProfile": "fast", "attempt": lease.attempt,
                "coordinatorVersion": metadata["coordinatorVersion"], "startedAt": "2026-08-13T01:00:00Z",
                "completedAt": "2026-08-13T01:01:00Z", "evidenceDigests": {}, "github": {"pullRequest": None, "runUrl": None},
                **metadata,
            }
            path = Path(directory) / "receipt.json"
            write_receipt(receipt, path)
            parsed = json.loads(path.read_text())
            self.assertEqual(parsed["workerId"], "mac")
            self.assertEqual(parsed["workerTrust"], "isolated-candidate")
            self.assertTrue(verify_receipt(parsed, candidate, "fast-gate"))
            coordinator.complete(lease, "completed")
            self.assertEqual(coordinator.store.get(queued.job_id)["attempt_count"], 1)
            coordinator.close()


if __name__ == "__main__":
    unittest.main()
