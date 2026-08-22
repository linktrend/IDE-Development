"""Deterministic continuous-utilization scheduler tests. None may skip."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from jsonschema import Draft202012Validator  # noqa: E402

from core.execution.scheduler import (  # noqa: E402
    BACKSTOP_SECONDS,
    COMPLETE_SNAPSHOT,
    CONFIG_RELATIVE_PATH,
    EXAMPLE_RELATIVE_PATH,
    HOSTED_CONCURRENCY_AUTHORITY,
    SCHEMA_RELATIVE_PATH,
    UTILIZATION_GAP,
    ContinuousUtilizationScheduler,
    WorkItem,
    load_continuous_utilization_config,
    load_continuous_utilization_schema,
)

NOW = datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc)
PACKAGED_RELATIVE = (
    "core/execution/__init__.py",
    "core/execution/lifecycle.py",
    "core/execution/manifest_persistence.py",
    "core/execution/protocol.py",
    "core/execution/rollout.py",
    "core/execution/scheduler.py",
    "core/execution/transactional_dispatch.py",
    "core/execution/cursor_cloud_dispatch.py",
    "core/execution/verification_liveness.py",
    "core/managed-core/content/doctrine/HOSTED-CAPACITY-SCHEDULER.md",
    "core/managed-core/content/doctrine/CODING-EXECUTION-PROTOCOL.md",
    "core/managed-core/content/config/continuous-utilization.json",
    "core/managed-core/content/config/manifest-persistence.json",
    "core/managed-core/content/config/transactional-dispatch.json",
    "core/managed-core/schemas/continuous-utilization.schema.json",
    "core/managed-core/schemas/manifest-persistence.schema.json",
    "core/managed-core/schemas/transactional-dispatch.schema.json",
    "core/managed-core/examples/continuous-utilization.example.json",
)


def _config(**hosted: int) -> dict:
    document = load_continuous_utilization_config(ROOT)
    if hosted:
        document["_test_hosted_capacity"] = hosted["hosted"]
    return document


def _item(
    item_id: str,
    lane: str = "hosted",
    *,
    priority: int = 0,
    dependencies: tuple[str, ...] = (),
    conflicts: tuple[str, ...] = (),
    offset: int = 0,
) -> WorkItem:
    return WorkItem(
        item_id=item_id,
        lane=lane,
        priority=priority,
        dependencies=dependencies,
        conflicts=conflicts,
        identity=item_id,
        submitted_at=NOW + timedelta(seconds=offset),
    )


def _scheduler(*, hosted: int | None = None, snapshot=COMPLETE_SNAPSHOT) -> ContinuousUtilizationScheduler:
    config = _config(hosted=hosted) if hosted is not None else _config()
    if hosted is not None:
        snapshot = dict(snapshot) if snapshot is not None else None
        if snapshot is not None:
            snapshot["cursorCapacity"] = {**snapshot["cursorCapacity"], "availableWorkers": hosted}
            snapshot["spendCeiling"] = {"maxWorkers": hosted}
            snapshot["safetyLimit"] = {"maxWorkers": hosted}
    return ContinuousUtilizationScheduler(config, snapshot=snapshot, now=NOW)


class PackagedConfigTests(unittest.TestCase):
    def test_canonical_config_matches_schema_and_authority(self) -> None:
        document = load_continuous_utilization_config(ROOT)
        schema = load_continuous_utilization_schema(ROOT)
        self.assertEqual(document["hostedConcurrencyAuthority"], HOSTED_CONCURRENCY_AUTHORITY)
        self.assertEqual(document["maxAdmittedSlots"]["local"], 1)
        self.assertNotIn("hosted", document["maxAdmittedSlots"])
        self.assertEqual(document["adaptiveConcurrency"]["mode"], "minimum_of_live_evidence")
        self.assertEqual(document["unknownProbeSeconds"], BACKSTOP_SECONDS)
        self.assertEqual(document["backstopSeconds"], BACKSTOP_SECONDS)
        self.assertEqual(document["utilizationGapEvent"], UTILIZATION_GAP)
        self.assertFalse(
            list(Draft202012Validator(schema).iter_errors(document))
        )
        example = json.loads((ROOT / EXAMPLE_RELATIVE_PATH).read_text(encoding="utf-8"))
        self.assertEqual(document, example)


class PrioritizationTests(unittest.TestCase):
    def test_higher_priority_fills_the_open_slot(self) -> None:
        scheduler = _scheduler(hosted=1, snapshot=None)
        scheduler.submit(_item("low", priority=0, offset=1))
        scheduler.submit(_item("high", priority=10, offset=2))
        self.assertEqual(scheduler.admitted_ids(), ())
        snapshot = dict(COMPLETE_SNAPSHOT)
        snapshot["cursorCapacity"] = {**snapshot["cursorCapacity"], "availableWorkers": 1}
        snapshot["spendCeiling"] = {"maxWorkers": 1}
        snapshot["safetyLimit"] = {"maxWorkers": 1}
        scheduler.set_snapshot(snapshot, recompute=False)
        scheduler.repair_utilization_gap()
        self.assertEqual(scheduler.admitted_ids(), ("high",))


class AdaptiveCapacityTests(unittest.TestCase):
    def test_live_capacity_above_two_is_filled(self) -> None:
        scheduler = _scheduler(hosted=3)
        scheduler.submit(_item("h1", offset=1))
        scheduler.submit(_item("h2", offset=2))
        self.assertEqual(scheduler.admitted_ids(), ("h1", "h2"))
        self.assertEqual(scheduler._free_slots("hosted"), 1)
        self.assertEqual(len(scheduler.admitted_ids()), 2)

    def test_effective_capacity_is_minimum_of_provider_spend_and_safety(self) -> None:
        snapshot = dict(COMPLETE_SNAPSHOT)
        snapshot["cursorCapacity"] = {**snapshot["cursorCapacity"], "availableWorkers": 7}
        snapshot["spendCeiling"] = {"maxWorkers": 4}
        snapshot["safetyLimit"] = {"maxWorkers": 3}
        scheduler = _scheduler(snapshot=snapshot)
        for item_id in ("h1", "h2", "h3", "h4"):
            scheduler.submit(_item(item_id))
        self.assertEqual(scheduler.admitted_ids(), ("h1", "h2", "h3"))
        report = scheduler.admission_report()
        self.assertEqual(report["providerCapacity"], 7)
        self.assertEqual(report["spendCeiling"], 4)
        self.assertEqual(report["safetyLimit"], 3)
        self.assertEqual(report["effectiveHostedCapacity"], 3)
        self.assertEqual(report["admittedWorkers"], ["h1", "h2", "h3"])

    def test_missing_spend_ceiling_blocks(self) -> None:
        snapshot = dict(COMPLETE_SNAPSHOT)
        snapshot.pop("spendCeiling")
        scheduler = _scheduler(snapshot=snapshot)
        scheduler.submit(_item("h1"))
        self.assertEqual(scheduler.admitted_ids(), ())
        self.assertIsNone(scheduler.admission_report()["spendCeiling"])

    def test_stale_capacity_evidence_blocks(self) -> None:
        snapshot = dict(COMPLETE_SNAPSHOT)
        snapshot["cursorCapacity"] = {
            **snapshot["cursorCapacity"],
            "observedAt": "2026-08-20T00:00:00+00:00",
        }
        scheduler = _scheduler(snapshot=snapshot)
        scheduler.submit(_item("h1"))
        self.assertEqual(scheduler.admitted_ids(), ())

    def test_overlapping_ownership_blocks_only_conflicting_work(self) -> None:
        scheduler = _scheduler(hosted=4)
        scheduler.submit(_item("shared-a", conflicts=("path:src/shared",)))
        scheduler.submit(_item("shared-b", conflicts=("path:src/shared",)))
        scheduler.submit(_item("independent", conflicts=("path:src/other",)))
        self.assertEqual(scheduler.admitted_ids(), ("independent", "shared-a"))
        self.assertIn("shared-b", scheduler.queued_ids())


class ConflictDependencyTests(unittest.TestCase):
    def test_conflict_and_dependency_block_without_preempting_others(self) -> None:
        scheduler = _scheduler(hosted=2)
        scheduler.submit(_item("h1", conflicts=("lock-a",), offset=1))
        scheduler.submit(_item("h2", conflicts=("lock-a",), offset=2))
        scheduler.submit(_item("h3", dependencies=("h4",), offset=3))
        self.assertEqual(scheduler.admitted_ids(), ("h1",))
        self.assertIn("h2", scheduler.queued_ids())
        self.assertIn("h3", scheduler.queued_ids())
        scheduler.submit(_item("h5", offset=4))
        self.assertEqual(scheduler.admitted_ids(), ("h1", "h5"))


class CompletionUnlockTests(unittest.TestCase):
    def test_completion_unlocks_next_eligible_job(self) -> None:
        scheduler = _scheduler(hosted=2)
        scheduler.submit(_item("h1", offset=1))
        scheduler.submit(_item("h2", offset=2))
        scheduler.submit(_item("h3", offset=3))
        self.assertEqual(scheduler.admitted_ids(), ("h1", "h2"))
        scheduler.complete("h1")
        self.assertEqual(scheduler.admitted_ids(), ("h2", "h3"))
        self.assertIn("completion", scheduler.event_kinds())


class InvalidationSelectiveDelayTests(unittest.TestCase):
    def test_invalidation_delays_only_that_identity(self) -> None:
        scheduler = _scheduler(hosted=2)
        scheduler.submit(_item("h1", offset=1))
        scheduler.submit(_item("h2", offset=2))
        scheduler.submit(_item("h3", offset=3))
        scheduler.invalidate("h1")
        self.assertEqual(scheduler.delayed_ids(), ("h1",))
        self.assertIn("h2", scheduler.admitted_ids())
        self.assertIn("h3", scheduler.admitted_ids())
        self.assertNotIn("h1", scheduler.admitted_ids())


class LocalOneHostedTwoTests(unittest.TestCase):
    def test_local_one_versus_hosted_two(self) -> None:
        scheduler = _scheduler(hosted=2)
        scheduler.submit(_item("l1", "local", offset=1))
        scheduler.submit(_item("l2", "local", offset=2))
        scheduler.submit(_item("h1", offset=3))
        scheduler.submit(_item("h2", offset=4))
        scheduler.submit(_item("h3", offset=5))
        self.assertEqual(scheduler.admitted_ids(), ("l1", "h1", "h2"))
        self.assertIn("l2", scheduler.queued_ids())
        self.assertIn("h3", scheduler.queued_ids())


class ApiRejectionNoPaidFallbackTests(unittest.TestCase):
    def test_api_rejection_does_not_fall_back_to_paid(self) -> None:
        scheduler = _scheduler()
        scheduler.submit(_item("h1", offset=1))
        reason = scheduler.note_api_rejection("h1", fallback="paid")
        self.assertEqual(reason, "paid_fallback_forbidden")
        self.assertNotIn("h1", scheduler.admitted_ids())
        self.assertIn("api_rejection", scheduler.event_kinds())
        fast = scheduler.note_api_rejection("h1", fallback="fast")
        self.assertEqual(fast, "paid_fallback_forbidden")


class UtilizationGapRepairTests(unittest.TestCase):
    def test_utilization_gap_is_repaired_after_complete_snapshot(self) -> None:
        scheduler = _scheduler(snapshot=None)
        scheduler.submit(_item("h1", offset=1))
        scheduler.submit(_item("h2", offset=2))
        self.assertEqual(scheduler.admitted_ids(), ())
        self.assertIn(UTILIZATION_GAP, scheduler.event_kinds())
        scheduler.set_snapshot(COMPLETE_SNAPSHOT, recompute=False)
        repaired = scheduler.repair_utilization_gap()
        self.assertTrue(repaired)
        self.assertEqual(scheduler.admitted_ids(), ("h1", "h2"))
        self.assertIn("utilization_gap_repair", scheduler.event_kinds())

    def test_utilization_gap_recovers_after_twenty_minute_heartbeat_window(self) -> None:
        scheduler = _scheduler(snapshot=None)
        scheduler.submit(_item("h1", offset=1))
        self.assertIn(UTILIZATION_GAP, scheduler.event_kinds())
        scheduler.tick(NOW + timedelta(minutes=20))
        self.assertEqual(scheduler.admitted_ids(), ())

        snapshot = dict(COMPLETE_SNAPSHOT)
        snapshot["cursorCapacity"] = {
            **snapshot["cursorCapacity"],
            "observedAt": "2026-08-20T12:20:00+00:00",
        }
        scheduler.set_snapshot(snapshot, recompute=False)
        self.assertTrue(scheduler.repair_utilization_gap())
        self.assertEqual(scheduler.admitted_ids(), ("h1",))
        self.assertIn("utilization_gap_repair", scheduler.event_kinds())


class TimerRecoveryTests(unittest.TestCase):
    def test_ten_minute_backstop_recovers_unknown_probe(self) -> None:
        scheduler = _scheduler()
        scheduler.submit(_item("h1", offset=1))
        self.assertEqual(scheduler.admitted_ids(), ("h1",))
        scheduler.start_unknown_probe("h1")
        self.assertNotIn("h1", scheduler.admitted_ids())
        scheduler.tick(NOW + timedelta(seconds=BACKSTOP_SECONDS - 1))
        self.assertNotIn("h1", scheduler.admitted_ids())
        scheduler.tick(NOW + timedelta(seconds=BACKSTOP_SECONDS))
        self.assertIn("probe_timeout", scheduler.event_kinds())
        self.assertEqual(scheduler.admitted_ids(), ("h1",))


class ExtractedInstallerCleanroomTests(unittest.TestCase):
    def test_extracted_package_validates_without_checkout(self) -> None:
        manifest = json.loads((ROOT / "core/managed-core/MANIFEST.json").read_text(encoding="utf-8"))
        wanted = {
            entry["source"]
            for entry in manifest["files"]
            if "continuous-utilization" in entry["id"]
            or entry["id"]
            in {
                "doctrine-hosted-capacity-scheduler-md",
                "doctrine-coding-execution-protocol-md",
            }
        }
        self.assertTrue(wanted)
        tmp = Path(tempfile.mkdtemp(prefix="cu-extract-"))
        try:
            extract = tmp / "package"
            copied = []
            by_source = {entry["source"]: entry for entry in manifest["files"]}
            for rel in PACKAGED_RELATIVE:
                self.assertIn(rel, by_source, rel)
                entry = by_source[rel]
                source = ROOT / rel
                digest = "sha256:" + hashlib.sha256(source.read_bytes()).hexdigest()
                self.assertEqual(digest, entry["sourceHash"], rel)
                dest = extract / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, dest)
                installed = extract / entry["destination"]
                installed.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, installed)
                copied.append(rel)
            subset = {
                "schemaVersion": 1,
                "packageName": "ide-development-managed-core",
                "packageVersion": "2.4.0",
                "files": [by_source[rel] for rel in PACKAGED_RELATIVE],
            }
            (extract / "core/managed-core/MANIFEST.json").parent.mkdir(parents=True, exist_ok=True)
            (extract / "core/managed-core/MANIFEST.json").write_text(
                json.dumps(subset, indent=2) + "\n",
                encoding="utf-8",
            )
            checkout = str(ROOT.resolve())
            for path in extract.rglob("*"):
                if not path.is_file():
                    continue
                text = path.read_text(encoding="utf-8")
                self.assertNotIn(checkout, text)
            schema = json.loads((extract / SCHEMA_RELATIVE_PATH).read_text(encoding="utf-8"))
            config = json.loads((extract / CONFIG_RELATIVE_PATH).read_text(encoding="utf-8"))
            self.assertFalse(list(Draft202012Validator(schema).iter_errors(config)))
            probe = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    (
                        "import json\n"
                        "from datetime import datetime, timedelta, timezone\n"
                        "from pathlib import Path\n"
                        "from core.execution.scheduler import "
                        "COMPLETE_SNAPSHOT, ContinuousUtilizationScheduler, WorkItem\n"
                        "root = Path.cwd()\n"
                        "config = json.loads((root / "
                        "'core/managed-core/content/config/continuous-utilization.json').read_text())\n"
                        "scheduler = ContinuousUtilizationScheduler(\n"
                        "    config, snapshot=None,\n"
                        "    now=datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc),\n"
                        ")\n"
                        "scheduler.submit(WorkItem('h1', 'hosted'))\n"
                        "scheduler.tick(datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc) + timedelta(minutes=20))\n"
                        "assert scheduler.admitted_ids() == ()\n"
                        "fresh = dict(COMPLETE_SNAPSHOT)\n"
                        "fresh['cursorCapacity'] = {**fresh['cursorCapacity'], 'observedAt': '2026-08-20T12:20:00+00:00'}\n"
                        "scheduler.set_snapshot(fresh, recompute=False)\n"
                        "assert scheduler.repair_utilization_gap()\n"
                        "assert scheduler.admitted_ids() == ('h1',)\n"
                    ),
                ],
                cwd=extract,
                env={**os.environ, "PYTHONPATH": str(extract)},
                text=True,
                capture_output=True,
            )
            self.assertEqual(probe.returncode, 0, probe.stderr)
            self.assertEqual(len(copied), 18)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
