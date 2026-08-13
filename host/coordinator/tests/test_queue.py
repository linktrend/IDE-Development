import tempfile
import unittest
from pathlib import Path

from host.coordinator.queue import QueueRequest, QueueStore


def identity(source="a" * 40, tree="b" * 40):
    return {"repository": "owner/repo", "sourceSha": source, "gitTreeSha": tree, "dependencyDigests": {}, "testProfile": "fast"}


class QueueTests(unittest.TestCase):
    def test_duplicate_event_is_one_row(self):
        store = QueueStore()
        request = QueueRequest("owner/repo", "fast-gate", identity(), priority=2)
        first = store.enqueue(request)
        second = store.enqueue(request)
        self.assertFalse(first.duplicate)
        self.assertTrue(second.duplicate)
        self.assertEqual(len(store.list_jobs()), 1)

    def test_pre_start_cancel_does_not_increment_attempt(self):
        store = QueueStore()
        result = store.enqueue(QueueRequest("owner/repo", "fast-gate", identity(), pr_number=7))
        self.assertEqual(store.cancel_obsolete("owner/repo", 7, None), [result.job_id])
        started = store.mark_started(result.job_id)
        self.assertFalse(started["started"])
        self.assertEqual(store.get(result.job_id)["attempt_count"], 0)

    def test_second_failure_stops_and_upserts_one_alert(self):
        store = QueueStore()
        result = store.enqueue(QueueRequest("owner/repo", "full-gate", identity(), priority=4))
        store.mark_started(result.job_id)
        store.record_result(result.job_id, "failed", {"sanitized": "failure one"})
        self.assertEqual(store.get(result.job_id)["status"], "queued")
        store.mark_started(result.job_id)
        store.record_result(result.job_id, "failed", {"sanitized": "failure two"}, failure_category="test", evidence_location="evidence/one.json")
        self.assertEqual(store.get(result.job_id)["status"], "stopped")
        self.assertEqual(len(store.alerts()), 1)
        refused = store.mark_started(result.job_id)
        self.assertFalse(refused["started"])
        store.record_result(result.job_id, "failed", {"sanitized": "re-observation"}, failure_category="test")
        self.assertEqual(len(store.alerts()), 1)

    def test_restart_preserves_queue_and_marks_started_truthfully(self):
        with tempfile.TemporaryDirectory() as directory:
            database = str(Path(directory) / "coordinator.sqlite3")
            first = QueueStore(database)
            queued = first.enqueue(QueueRequest("owner/repo", "fast-gate", identity()))
            running = first.enqueue(QueueRequest("owner/repo", "full-gate", identity(tree="c" * 40)))
            first.mark_started(running.job_id)
            first.close()
            second = QueueStore(database)
            self.assertEqual(second.get(queued.job_id)["status"], "queued")
            self.assertEqual(second.recover(), [running.job_id])
            self.assertEqual(second.get(running.job_id)["status"], "interrupted")

    def test_identity_change_cancels_only_obsolete_pr_work(self):
        store = QueueStore()
        old = store.enqueue(QueueRequest("owner/repo", "fast-gate", identity(), pr_number=3))
        current = identity(source="d" * 40, tree="e" * 40)
        self.assertEqual(store.cancel_obsolete("owner/repo", 3, current), [old.job_id])


if __name__ == "__main__":
    unittest.main()
