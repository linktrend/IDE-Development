import unittest

from host.coordinator.resources import HostSnapshot, ResourceLimits, admit_job


class ResourceAdmissionTests(unittest.TestCase):
    def test_two_fast_jobs_then_third_is_refused(self):
        limits = ResourceLimits()
        request = {"job_id": "fast-3", "test_profile": "fast"}
        running = [
            {"job_id": "fast-1", "test_profile": "fast", "status": "running"},
            {"job_id": "fast-2", "test_profile": "fast", "status": "running"},
        ]
        verdict = admit_job(request, HostSnapshot(), running, limits)
        self.assertFalse(verdict.admitted)
        self.assertEqual(verdict.reason, "fast_capacity_exhausted")

    def test_one_heavy_job_cannot_overlap(self):
        request = {"job_id": "full-2", "test_profile": "full"}
        running = [{"job_id": "full-1", "test_profile": "full", "status": "running"}]
        verdict = admit_job(request, HostSnapshot(), running, ResourceLimits())
        self.assertFalse(verdict.admitted)
        self.assertEqual(verdict.reason, "heavy_capacity_exhausted")

    def test_terminal_jobs_do_not_consume_capacity(self):
        running = [
            {"job_id": "fast-old", "test_profile": "fast", "status": "completed"},
            {"job_id": "full-old", "test_profile": "full", "status": "cancelled"},
        ]
        self.assertTrue(admit_job({"test_profile": "fast"}, HostSnapshot(), running).admitted)
        self.assertTrue(admit_job({"test_profile": "full"}, HostSnapshot(), running).admitted)

    def test_cpu_memory_disk_docker_and_interactive_pressure_pause(self):
        snapshot = HostSnapshot(
            cpu_percent=80,
            memory_percent=80,
            free_disk_gib=19.9,
            docker_available=False,
            interactive_use=True,
        )
        verdict = admit_job({"test_profile": "fast"}, snapshot, [])
        self.assertFalse(verdict.admitted)
        self.assertEqual(
            verdict.pressure_reasons,
            ("cpu_pressure", "memory_pressure", "disk_pressure", "docker_unavailable", "interactive_use"),
        )

    def test_mapping_config_uses_frozen_camel_case_names(self):
        limits = ResourceLimits.from_mapping(
            {"maxFastJobs": 1, "maxHeavyJobs": 1, "minimumFreeDiskGiB": 5}
        )
        self.assertEqual(limits.max_fast_jobs, 1)
        verdict = admit_job(
            {"testProfile": "fast"},
            {"cpuPercent": 1, "memoryPercent": 1, "freeDiskGiB": 10, "dockerAvailable": True},
            [],
            limits,
        )
        self.assertTrue(verdict.admitted)


if __name__ == "__main__":
    unittest.main()
