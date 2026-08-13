import base64
import json
import tempfile
import unittest
from pathlib import Path

from host.coordinator.daemon import CoordinatorDaemon
from host.coordinator.github_client import GitHubClient
from host.coordinator.queue import QueueRequest


def identity():
    return {"repository": "owner/repo", "sourceSha": "a" * 40, "gitTreeSha": "b" * 40, "dependencyDigests": {}, "testProfile": "fast"}


class FakeGitHub:
    token = "test-secret"

    def load_protected_policy(self, repository, *, candidate_ref=None):
        return {"schemaVersion": 1, "deliveryMode": "phase-integration"}, "development"

    def poll(self, path, *, etag=None, failures=0):
        from host.coordinator.github_client import GitHubResponse, PollResult
        return PollResult(GitHubResponse(304, etag=etag, not_modified=True), 5, False, "not-modified")

    def publish_status(self, *args, **kwargs):
        return None


class DaemonTests(unittest.TestCase):
    def test_allowlist_and_protected_config(self):
        with tempfile.TemporaryDirectory() as directory:
            daemon = CoordinatorDaemon(Path(directory) / "state.sqlite3", github=FakeGitHub())
            daemon.register("owner/repo", directory, "development")
            config = daemon.load_protected_config("owner/repo", candidate_ref="refs/pull/3/head")
            self.assertTrue(config.is_phase_integration)
            with self.assertRaises(Exception):
                daemon.enqueue_request(QueueRequest("other/repo", "fast-gate", identity()))
            daemon.close()

    def test_conditional_poll_does_not_mutate_jobs(self):
        with tempfile.TemporaryDirectory() as directory:
            daemon = CoordinatorDaemon(Path(directory) / "state.sqlite3", github=FakeGitHub())
            daemon.register("owner/repo", directory)
            before = daemon.status()["jobs"]
            result = daemon.poll_once("owner/repo")
            self.assertEqual(result["status"], "not-modified")
            self.assertEqual(daemon.status()["jobs"], before)
            daemon.close()

    def test_restart_recovers_truthful_queue(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "state.sqlite3"
            first = CoordinatorDaemon(database, github=FakeGitHub())
            first.register("owner/repo", directory)
            queued = first.enqueue_request(QueueRequest("owner/repo", "fast-gate", identity()))
            first.close()
            second = CoordinatorDaemon(database, github=FakeGitHub())
            self.assertEqual(second.store.get(queued.job_id)["status"], "queued")
            second.close()

    def test_candidate_payload_cannot_replace_protected_execution_policy(self):
        class ProtectedGitHub(FakeGitHub):
            def load_protected_policy(self, repository, *, candidate_ref=None):
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
                        "fast": {"commands": [["protected-command", "--safe"]], "timeoutSeconds": 300},
                        "full": {"commands": [], "timeoutSeconds": 3600, "required": False},
                        "release": {"commands": [], "timeoutSeconds": 300},
                    },
                    "dependencyFiles": [],
                    "resourceLimits": {
                        "fastCpus": 1.0, "fastMemoryMiB": 2048, "heavyCpus": 2.0, "heavyMemoryMiB": 4096,
                        "pidsLimit": 768, "pauseCpuPercent": 80, "pauseMemoryPercent": 80, "minimumFreeDiskGiB": 20,
                    },
                }, "development"

        seen = []
        def fake_runner(job, limits, cancellation):
            seen.append(job.command)
            from host.coordinator.executor import ExecutionResult
            return ExecutionResult("passed", job.job_id, 0, "2026-01-01T00:00:00Z", "2026-01-01T00:00:01Z", "container")

        with tempfile.TemporaryDirectory() as directory:
            daemon = CoordinatorDaemon(Path(directory) / "state.sqlite3", github=ProtectedGitHub(), runner=fake_runner)
            daemon.register("owner/repo", directory)
            daemon.load_protected_config("owner/repo", candidate_ref="refs/pull/8/head")
            daemon.enqueue_request(QueueRequest("owner/repo", "fast-gate", identity(), payload={"command": ["candidate-command", "--unsafe"]}))
            daemon.run_next()
            self.assertEqual(seen, [("protected-command", "--safe")])
            daemon.close()

    def test_missing_token_fails_closed_before_attempt_start(self):
        with tempfile.TemporaryDirectory() as directory:
            daemon = CoordinatorDaemon(Path(directory) / "state.sqlite3", github=GitHubClient(""))
            daemon.register("owner/repo", directory)
            queued = daemon.enqueue_request(QueueRequest("owner/repo", "fast-gate", identity()))
            result = daemon.run_next()
            self.assertEqual(result["status"], "failed-closed")
            self.assertEqual(daemon.store.get(queued.job_id)["attempt_count"], 0)
            daemon.close()

    def test_pause_and_resume_survive_cli_style_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "state.sqlite3"
            first = CoordinatorDaemon(database, github=FakeGitHub())
            first.pause()
            first.close()
            second = CoordinatorDaemon(database, github=FakeGitHub())
            self.assertTrue(second.paused)
            second.resume()
            second.close()
            third = CoordinatorDaemon(database, github=FakeGitHub())
            self.assertFalse(third.paused)
            third.close()


if __name__ == "__main__":
    unittest.main()
