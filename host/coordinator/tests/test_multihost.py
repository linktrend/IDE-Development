import tempfile
import time
import unittest
from pathlib import Path

from host.coordinator.executor import Job, build_docker_invocation
from host.coordinator.multihost import MultiHostCoordinator
from host.coordinator.queue import QueueRequest
from host.coordinator.workers import Worker, WorkerRegistry


def identity(repository="owner/repo", source="a", profile="fast"):
    return {
        "repository": repository,
        "sourceSha": source * 40,
        "gitTreeSha": ("b" if source == "a" else "c") * 40,
        "dependencyDigests": {},
        "testProfile": profile,
    }


def worker(worker_id, platform="macos", capabilities=("fast",), *, repos=("owner/repo",), heartbeat=1000):
    return Worker(
        worker_id, platform, "arm64", capabilities=frozenset(capabilities),
        max_fast_jobs=2, max_heavy_jobs=1, cpu_limit=4, memory_mib=8192,
        repositories=tuple(repos), last_heartbeat=heartbeat,
    )


class MultiHostTests(unittest.TestCase):
    def test_registry_lifecycle_and_vps_privilege_rejection(self):
        registry = WorkerRegistry()
        registered = registry.register(worker("mac-mini-primary", heartbeat=time.time()))
        self.assertEqual(registered.status, "enabled")
        self.assertEqual(registry.drain(registered.worker_id).status, "draining")
        self.assertEqual(registry.enable(registered.worker_id).status, "enabled")
        self.assertEqual(registry.mark_offline(registered.worker_id).status, "offline")
        with self.assertRaisesRegex(ValueError, "privileged"):
            registry.register({
                "workerId": "vps-root", "platform": "linux", "arch": "amd64",
                "trust": "privileged-coordinator", "capabilities": ["fast"],
            })
        self.assertTrue(registry.remove(registered.worker_id))
        registry.close()

    def test_fair_queue_capability_match_and_pressure_admission(self):
        with tempfile.TemporaryDirectory() as directory:
            coordinator = MultiHostCoordinator(Path(directory) / "state.sqlite3")
            coordinator.register_worker(worker("mac", capabilities=("fast",), repos=("a/repo", "b/repo")))
            coordinator.enqueue(QueueRequest("a/repo", "fast-gate", identity("a/repo", "a"), priority=2))
            coordinator.enqueue(QueueRequest("b/repo", "fast-gate", identity("b/repo", "d"), priority=2))
            first = coordinator.claim("mac", now=1000)
            self.assertEqual(first.candidate_identity["repository"], "a/repo")
            coordinator.complete(first, "completed")
            second = coordinator.claim("mac", now=1000)
            self.assertEqual(second.candidate_identity["repository"], "b/repo")
            coordinator.complete(second, "completed")
            coordinator.enqueue(QueueRequest("a/repo", "fast-gate", identity("a/repo", "e"), priority=2))
            self.assertIsNone(coordinator.claim("mac", snapshot={"cpuPercent": 90}, now=1000))
            pressure_recovered = coordinator.claim("mac", snapshot={"cpuPercent": 0}, now=1000)
            coordinator.complete(pressure_recovered, "completed")
            coordinator.enqueue(QueueRequest("a/repo", "full-gate", identity("a/repo", "e", "full"), priority=4))
            self.assertIsNone(coordinator.claim("mac", now=1000))
            coordinator.close()

    def test_linux_worker_add_nested_capability_and_drain(self):
        with tempfile.TemporaryDirectory() as directory:
            coordinator = MultiHostCoordinator(Path(directory) / "state.sqlite3")
            coordinator.register_worker(worker("mac", capabilities=("fast",), repos=("owner/repo",)))
            coordinator.register_worker(worker("linux", "linux", ("heavy", "nestedDocker"), repos=("owner/repo",)))
            coordinator.enqueue(QueueRequest("owner/repo", "full-gate", identity(source="f", profile="full"), priority=4, payload={"nestedDocker": True, "requiredCapability": "nestedDocker"}))
            lease = coordinator.claim("linux", now=1000)
            self.assertEqual(lease.capability, "nestedDocker")
            coordinator.complete(lease, "completed")
            coordinator.registry.drain("linux")
            coordinator.enqueue(QueueRequest("owner/repo", "full-gate", identity(source="d", profile="full"), priority=4))
            self.assertIsNone(coordinator.claim("linux", now=1000))
            coordinator.close()

    def test_expired_inflight_lease_reuses_attempt_and_rejects_old_result(self):
        with tempfile.TemporaryDirectory() as directory:
            coordinator = MultiHostCoordinator(Path(directory) / "state.sqlite3")
            coordinator.register_worker(worker("mac", heartbeat=1000))
            coordinator.register_worker(worker("linux", "linux", heartbeat=1000))
            result = coordinator.enqueue(QueueRequest("owner/repo", "fast-gate", identity(), priority=2))
            first = coordinator.claim("mac", now=1000, lease_seconds=10)
            self.assertEqual(first.attempt, 1)
            self.assertEqual(coordinator.recover_lost_workers(now=1011), [result.job_id])
            second = coordinator.claim("linux", now=1011, lease_seconds=10)
            self.assertEqual(second.attempt, 1)
            with self.assertRaisesRegex(ValueError, "stale or duplicate"):
                coordinator.complete(first, "completed")
            coordinator.complete(second, "completed")
            self.assertEqual(coordinator.store.get(result.job_id)["attempt_count"], 1)
            coordinator.close()

    def test_duplicate_pickup_and_stale_heartbeat_are_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            coordinator = MultiHostCoordinator(Path(directory) / "state.sqlite3")
            coordinator.register_worker(worker("one", heartbeat=1000))
            coordinator.register_worker(worker("two", heartbeat=1000))
            coordinator.enqueue(QueueRequest("owner/repo", "fast-gate", identity(), priority=2))
            self.assertIsNotNone(coordinator.claim("one", now=1000))
            self.assertIsNone(coordinator.claim("two", now=1000))
            coordinator.registry.mark_offline("one")
            self.assertEqual(coordinator.registry.get("one").status, "offline")
            self.assertEqual(coordinator.registry.get("two", now=1100).status, "offline")
            coordinator.close()

    def test_executor_rejects_privileged_worker_and_unmatched_capability(self):
        with tempfile.TemporaryDirectory() as directory:
            checkout = Path(directory) / "checkout"
            checkout.mkdir()
            base = dict(job_id="job-trust", checkout_path=str(checkout), workspace_root=directory, image="alpine:3.20", command=("true",), worker_id="vps")
            with self.assertRaisesRegex(ValueError, "privileged"):
                build_docker_invocation(Job(**base, worker_trust="privileged-coordinator"))
            with self.assertRaisesRegex(ValueError, "does not match"):
                build_docker_invocation(Job(**base, worker_trust="isolated-candidate", test_profile="full", worker_capabilities=("fast",)))


if __name__ == "__main__":
    unittest.main()
