import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from host.coordinator import executor
from host.coordinator.cleanup import CleanupResult, cleanup_job, recover_orphans, register_job
from host.coordinator.executor import Job, build_docker_invocation, run_job
from host.coordinator.resources import ResourceLimits


class _FakeProcess:
    def __init__(self, *, exit_code=None):
        self.returncode = exit_code
        self.terminated = False
        self.killed = False
        self.poll_count = 0

    def poll(self):
        self.poll_count += 1
        return self.returncode

    def terminate(self):
        self.terminated = True
        self.returncode = 143

    def kill(self):
        self.killed = True
        self.returncode = 137

    def wait(self, timeout=None):
        return self.returncode

    def communicate(self, timeout=None):
        return "candidate output", "candidate error"


class _FakeDockerResult:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


class ExecutorTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory()
        self.root = Path(self.workspace.name)
        self.checkout = self.root / "checkout-job-1"
        self.checkout.mkdir()

    def tearDown(self):
        self.workspace.cleanup()

    def job(self, **overrides):
        values = dict(
            job_id="job-1",
            checkout_path=str(self.checkout),
            workspace_root=str(self.root),
            image="alpine:3.20",
            command=("sh", "-c", "printf candidate"),
        )
        values.update(overrides)
        return Job(**values)

    def test_candidate_command_is_after_image_and_never_host_shell(self):
        job = self.job()
        argv = build_docker_invocation(job, ResourceLimits())
        image_index = argv.index(job.image)
        self.assertEqual(argv[image_index + 1 :], job.command)
        self.assertIn("--platform", argv)
        self.assertIn("linux/amd64", argv)
        self.assertIn("--cpus", argv)
        self.assertIn("--memory", argv)
        self.assertIn("--memory-swap", argv)
        self.assertIn("--pids-limit", argv)
        self.assertIn("--stop-timeout", argv)
        self.assertIn("--mount", argv)
        self.assertIn("--workdir", argv)
        self.assertIn("type=bind,src={},dst=/workspace,readonly".format(self.checkout.resolve()), argv)

    def test_writable_workspace_is_limited_to_disposable_checkout(self):
        argv = build_docker_invocation(self.job(temporary_checkout=True, writable_workspace=True), ResourceLimits())
        self.assertIn("type=bind,src={},dst=/workspace".format(self.checkout.resolve()), argv)
        self.assertNotIn("type=bind,src={},dst=/workspace,readonly".format(self.checkout.resolve()), argv)
        with self.assertRaises(ValueError):
            build_docker_invocation(self.job(writable_workspace=True), ResourceLimits())

    def test_registered_worker_architecture_selects_container_platform(self):
        argv = build_docker_invocation(self.job(worker_arch="arm64"), ResourceLimits())
        self.assertIn("linux/arm64", argv)
        with self.assertRaises(ValueError):
            build_docker_invocation(self.job(worker_arch="s390x"), ResourceLimits())

    def test_shell_string_and_path_escape_are_rejected(self):
        with self.assertRaises(ValueError):
            build_docker_invocation(self.job(command="printf unsafe"), ResourceLimits())
        with self.assertRaises(ValueError):
            build_docker_invocation(self.job(checkout_path=str(self.root.parent)), ResourceLimits())
        with self.assertRaises(ValueError):
            build_docker_invocation(
                self.job(volumes=({"source": "/var/run/docker.sock", "target": "/docker"},)),
                ResourceLimits(),
            )

    def test_nested_docker_requires_protected_bounded_config_and_never_socket(self):
        with self.assertRaises(ValueError):
            build_docker_invocation(self.job(nested_docker=True), ResourceLimits())
        nested = {"protected": True, "image": "docker:dind", "memoryMiB": 1024, "pidsLimit": 128}
        argv = build_docker_invocation(self.job(nested_docker=True, protected_nested_config=nested), ResourceLimits())
        self.assertNotIn("/var/run/docker.sock", argv)

    def test_cancellation_terminates_fake_container(self):
        process = _FakeProcess()
        calls = {"count": 0}

        def cancel():
            calls["count"] += 1
            return calls["count"] > 1

        with patch.object(executor.subprocess, "Popen", return_value=process), patch.object(
            executor, "cleanup_job", return_value=CleanupResult(True, "job-1")
        ):
            result = run_job(self.job(), ResourceLimits(), cancel)
        self.assertEqual(result.status, "cancelled")
        self.assertTrue(process.terminated)

    def test_timeout_terminates_fake_container(self):
        process = _FakeProcess()
        with patch.object(executor.subprocess, "Popen", return_value=process), patch.object(
            executor, "cleanup_job", return_value=CleanupResult(True, "job-1")
        ), patch.object(executor.time, "monotonic", side_effect=[0, 0, 10]):
            result = run_job(self.job(timeout_seconds=1), ResourceLimits(), None)
        self.assertEqual(result.status, "timed_out")
        self.assertTrue(process.terminated)

    def test_pre_execution_cancellation_does_not_start_process(self):
        cancellation = threading.Event()
        cancellation.set()
        with patch.object(executor.subprocess, "Popen") as popen, patch.object(
            executor, "cleanup_job", return_value=CleanupResult(True, "job-1")
        ):
            result = run_job(self.job(), ResourceLimits(), cancellation)
        self.assertEqual(result.status, "cancelled")
        popen.assert_not_called()

    def test_cleanup_failure_remains_visible(self):
        calls = []

        def runner(argv):
            calls.append(argv)
            if argv[1:2] == ["ps"]:
                return _FakeDockerResult(stdout="deadbeefdead\n")
            return _FakeDockerResult(returncode=1, stderr="permission denied")

        register_job("cleanup-1", container_name="linktrend-coordinator-cleanup-1")
        result = cleanup_job("cleanup-1", runner=runner)
        self.assertFalse(result.success)
        self.assertTrue(result.errors)
        self.assertTrue(any("removal failed" in error for error in result.errors))
        self.assertEqual(calls[0][1], "ps")

    def test_broad_cleanup_target_is_rejected(self):
        register_job(
            "broad-1",
            container_name="linktrend-coordinator-broad-1",
            checkout_path=str(self.root),
            workspace_root=str(self.root),
            temporary_checkout=True,
        )
        result = cleanup_job("broad-1", runner=lambda argv: _FakeDockerResult())
        self.assertFalse(result.success)
        self.assertTrue(any("outside" in error or "broad" in error for error in result.errors))

    def test_disposable_checkout_removes_its_empty_private_parent(self):
        workspace = self.root / "linktrend-coordinator-private"
        checkout = workspace / "candidate"
        checkout.mkdir(parents=True)
        (checkout / "input.txt").write_text("candidate", encoding="utf-8")
        register_job(
            "private-1",
            container_name="linktrend-coordinator-private-1",
            checkout_path=str(checkout),
            workspace_root=str(workspace),
            temporary_checkout=True,
        )
        result = cleanup_job("private-1", runner=lambda argv: _FakeDockerResult())
        self.assertTrue(result.success)
        self.assertFalse(workspace.exists())
        self.assertEqual(set(result.removed_paths), {str(checkout.resolve()), str(workspace.resolve())})

    def test_startup_removes_labelled_orphan_only(self):
        orphan = "a" * 12
        active = "b" * 12
        calls = []

        def runner(argv):
            calls.append(argv)
            if argv[1:2] == ["ps"]:
                return _FakeDockerResult(stdout=orphan + "\n" + active + "\n")
            if argv[1:2] == ["inspect"]:
                return _FakeDockerResult(stdout="live-job" if argv[-1] == active else "orphan-job")
            if argv[1:2] == ["rm"]:
                return _FakeDockerResult()
            return _FakeDockerResult(returncode=1)

        result = recover_orphans({"live-job"}, runner=runner)
        self.assertTrue(result.success)
        self.assertEqual(result.removed_containers, (orphan,))
        self.assertEqual([call[1] for call in calls if len(call) > 1 and call[1] == "rm"], ["rm"])

    def test_sanitizes_secrets(self):
        text = executor.sanitize_output("token=abc123 Authorization: Bearer secret-value ghp_abcdef")
        self.assertNotIn("abc123", text)
        self.assertNotIn("secret-value", text)
        self.assertNotIn("ghp_abcdef", text)


if __name__ == "__main__":
    unittest.main()
