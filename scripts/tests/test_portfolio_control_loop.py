"""Focused tests for the durable portfolio control loop."""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from jsonschema import Draft202012Validator

from core.execution.protocol import control_loop_invocation_key
from scripts.gitops.portfolio_control_loop import (
    MemoryControlLoopStore,
    PortfolioControlLoop,
    UTILIZATION_GAP,
    calculate_safe_capacity,
    configure_automation,
    create_handover,
    due_automations,
    load_control_loop_config,
    load_control_loop_schema,
    new_control_loop_state,
    JsonFileControlLoopStore,
    record_automation_delivery,
    transfer_terminal_event,
)
from core.execution.manifest_persistence import persist_durable_state

ROOT = Path(__file__).resolve().parents[2]
NOW = datetime(2026, 8, 28, 12, 0, tzinfo=timezone.utc)


class PortfolioControlLoopTests(unittest.TestCase):
    def setUp(self) -> None:
        self.store = MemoryControlLoopStore()
        self.loop = PortfolioControlLoop(self.store, repo_root=ROOT)
        self.loop.initialize(
            coordinator_task_id="coord-1",
            owner_id="owner-1",
            now=NOW,
            capacity=2,
        )

    def test_config_schema_and_shared_trigger_key(self) -> None:
        config = load_control_loop_config(ROOT)
        schema = load_control_loop_schema(ROOT)
        self.assertFalse(list(Draft202012Validator(schema).iter_errors(config)))
        self.assertEqual(
            control_loop_invocation_key(
                coordinator_task_id="coord-1", trigger="hourly", invocation_id="slot-1"
            ),
            control_loop_invocation_key(
                coordinator_task_id="coord-1", trigger="PULSE", invocation_id="slot-1"
            ),
        )
        stages = config["stagedCapacityPolicy"]["stages"]
        self.assertEqual([(row["cursor"], row["luna"]) for row in stages], [(5, 2), (10, 4), (20, 4)])
        self.assertEqual([row["underfillLuna"] for row in stages], [1, 1, 2])

    def test_staged_provider_capacity_dispatches_available_work_and_reports_gap(self) -> None:
        store = MemoryControlLoopStore()
        loop = PortfolioControlLoop(store, repo_root=ROOT)
        loop.initialize(
            coordinator_task_id="coord-staged",
            owner_id="owner-1",
            now=NOW,
            capacity={"cursor": 50, "luna": 50, "macMemoryAvailable": True},
        )
        for index in range(6):
            loop.register_lane(f"cursor-{index}", provider="cursor")
        for index in range(3):
            loop.register_lane(f"luna-{index}", provider="luna")
        result = loop.invoke(
            coordinator_task_id="coord-staged",
            holder="owner-1",
            trigger="PULSE",
            invocation_id="staged-1",
            now=NOW,
        )
        state = loop.state()
        running = [worker for worker in state["workers"].values() if worker["state"] == "RUNNING"]
        self.assertEqual(sum(worker["provider"] == "cursor" for worker in running), 5)
        self.assertEqual(sum(worker["provider"] == "luna" for worker in running), 2)
        self.assertEqual(result["utilizationGap"]["code"], UTILIZATION_GAP)

    def test_safe_capacity_is_bounded_by_stage_and_mac_memory(self) -> None:
        config = load_control_loop_config(ROOT)
        state = new_control_loop_state(
            coordinator_task_id="coord-staged",
            owner_id="owner-1",
            now=NOW,
            capacity={"cursor": 99, "luna": 99, "macMemoryAvailable": True},
            stage=3,
            stage_verification="stage-2",
        )
        capacity = calculate_safe_capacity(config, state)
        self.assertEqual((capacity["cursor"], capacity["luna"], capacity["underfillLuna"]), (20, 4, 2))
        state["capacity"]["macMemoryAvailable"] = False
        capacity = calculate_safe_capacity(config, state)
        self.assertEqual((capacity["cursor"], capacity["luna"]), (0, 0))
        state["stageVerification"] = "baseline"
        state["stage"] = 2
        capacity = calculate_safe_capacity(config, state)
        self.assertEqual(capacity["source"], "stage_verification_required")

    def test_dependency_ready_disjoint_capacity_is_filled(self) -> None:
        self.loop.register_lane("a", priority=1, conflicts=("shared",))
        self.loop.register_lane("b", priority=0, conflicts=("shared",))
        self.loop.register_lane("c", dependencies=("a",))
        result = self.loop.invoke(
            coordinator_task_id="coord-1",
            holder="owner-1",
            trigger="PULSE",
            invocation_id="slot-1",
            now=NOW,
        )
        self.assertEqual(result["status"], "RUNNING")
        state = self.loop.state()
        self.assertEqual(state["lanes"]["a"]["state"], "RUNNING")
        self.assertEqual(state["lanes"]["b"]["state"], "PREPARED")
        self.assertEqual(state["lanes"]["c"]["state"], "WAITING_DEPENDENCY")
        self.assertEqual(len([w for w in state["workers"].values() if w["state"] == "RUNNING"]), 1)

    def test_live_lease_blocks_second_owner_and_nested_turn_coalesces(self) -> None:
        self.loop.register_lane("a")
        nested: list[dict] = []

        def dispatch(lane: dict) -> dict:
            nested.append(
                self.loop.invoke(
                    coordinator_task_id="coord-1",
                    holder="owner-1",
                    trigger="PULSE",
                    invocation_id="nested",
                    now=NOW,
                )
            )
            return {"provider": "test-provider"}

        result = self.loop.invoke(
            coordinator_task_id="coord-1",
            holder="owner-1",
            invocation_id="slot-1",
            now=NOW,
            dispatch_worker=dispatch,
        )
        self.assertEqual(result["status"], "RUNNING")
        self.assertTrue(nested[0]["coalesced"])
        blocked = self.loop.invoke(
            coordinator_task_id="coord-1",
            holder="other-owner",
            invocation_id="slot-2",
            now=NOW,
        )
        self.assertEqual(blocked["status"], "HOLD")
        self.assertEqual(blocked["blocker"], "controller_lease_held")

    def test_terminal_worker_is_archived_before_report_and_unblocks_successor(self) -> None:
        self.loop.register_lane("a")
        self.loop.register_lane("b", dependencies=("a",))
        self.loop.invoke(
            coordinator_task_id="coord-1", holder="owner-1", invocation_id="slot-1", now=NOW
        )
        worker_id = self.loop.state()["lanes"]["a"]["workerId"]
        order: list[str] = []

        def archive(worker: dict) -> dict:
            order.append("archive")
            self.assertEqual(worker["observation"]["status"], "COMPLETED")
            return {"archived": True, "readback": True, "archiveId": "arc-a"}

        def dispatch(lane: dict) -> dict:
            order.append(f"dispatch:{lane['laneId']}")
            return {"provider": "test-provider"}

        result = self.loop.invoke(
            coordinator_task_id="coord-1",
            holder="owner-1",
            trigger="hourly",
            invocation_id="slot-2",
            now=NOW + timedelta(minutes=1),
            observations={worker_id: {"status": "COMPLETED", "result": "SUCCESS"}},
            archive_worker=archive,
            dispatch_worker=dispatch,
        )
        self.assertEqual(order, ["archive", "dispatch:b"])
        self.assertEqual(result["status"], "RUNNING")
        self.assertEqual(self.loop.state()["lanes"]["a"]["state"], "COMPLETE")

    def test_report_is_done_only_after_archived_acceptance_and_hold_has_exact_blocker(self) -> None:
        self.loop.register_lane("a")
        self.loop.invoke(
            coordinator_task_id="coord-1", holder="owner-1", invocation_id="slot-1", now=NOW
        )
        worker_id = self.loop.state()["lanes"]["a"]["workerId"]
        done = self.loop.invoke(
            coordinator_task_id="coord-1",
            holder="owner-1",
            invocation_id="slot-2",
            now=NOW + timedelta(minutes=1),
            observations={worker_id: {"status": "COMPLETED", "result": "SUCCESS"}},
        )
        self.assertEqual(done["status"], "DONE")
        self.assertEqual(done["language"], "FINISHED")

        held = self.loop.invoke(
            coordinator_task_id="coord-1",
            holder="owner-1",
            invocation_id="slot-3",
            now=NOW + timedelta(minutes=2),
            protected_truth={"valid": False, "blocker": "protected_refs_not_refreshed"},
        )
        self.assertEqual(held["status"], "HOLD")
        self.assertEqual(held["report"]["blocker"], "protected_refs_not_refreshed")

    def test_same_invocation_coalesces_and_stalled_worker_is_replaced_once(self) -> None:
        self.loop.register_lane("a")
        first = self.loop.invoke(
            coordinator_task_id="coord-1", holder="owner-1", invocation_id="slot-1", now=NOW
        )
        second = self.loop.invoke(
            coordinator_task_id="coord-1", holder="owner-1", trigger="PULSE", invocation_id="slot-1", now=NOW
        )
        self.assertEqual(first, second)
        worker_id = self.loop.state()["lanes"]["a"]["workerId"]
        result = self.loop.invoke(
            coordinator_task_id="coord-1",
            holder="owner-1",
            invocation_id="slot-2",
            now=NOW + timedelta(minutes=10),
        )
        self.assertNotEqual(result["status"], "HOLD")
        state = self.loop.state()
        self.assertEqual(state["workers"][worker_id]["state"], "REPLACED")
        self.assertTrue(state["lanes"]["a"]["workerId"].startswith(worker_id + "-replacement-"))

    def test_automation_cadence_change_preserves_one_record_and_decrements_on_confirmation_only(self) -> None:
        state = new_control_loop_state(coordinator_task_id="coord-1", owner_id="owner-1", now=NOW)
        first = configure_automation(
            state,
            automation_id="update",
            target_task_id="coord-1",
            remaining_runs=3,
            now=NOW,
        )
        changed = configure_automation(
            state,
            automation_id="update",
            target_task_id="coord-1",
            cadence_seconds=7200,
            remaining_runs=99,
            now=NOW + timedelta(minutes=1),
        )
        self.assertEqual(first["automationId"], changed["automationId"])
        self.assertEqual(changed["remainingRuns"], 3)
        self.assertEqual(len(state["automations"]), 1)
        record_automation_delivery(
            state,
            automation_id="update",
            delivery_id="d1",
            scheduled_at=NOW,
            actual_delivery_at=None,
            result="FAILED",
            target_task_id="coord-1",
        )
        self.assertEqual(state["automations"]["update"]["remainingRuns"], 3)
        record_automation_delivery(
            state,
            automation_id="update",
            delivery_id="d2",
            scheduled_at=NOW,
            actual_delivery_at=NOW + timedelta(seconds=2),
            result="DELIVERED",
            target_task_id="coord-1",
        )
        self.assertEqual(state["automations"]["update"]["remainingRuns"], 2)
        self.assertEqual(due_automations(state, now=NOW), ())

    def test_heartbeat_creation_and_one_shot_delivery_remain_unproven(self) -> None:
        state = new_control_loop_state(coordinator_task_id="coord-1", owner_id="owner-1", now=NOW)
        self.assertEqual(state["heartbeatAcceptance"]["status"], "PENDING")
        configure_automation(
            state,
            automation_id="heartbeat",
            target_task_id="coord-1",
            remaining_runs=3,
            now=NOW,
        )
        record_automation_delivery(
            state,
            automation_id="heartbeat",
            delivery_id="delivery-1",
            scheduled_at=NOW,
            actual_delivery_at=NOW + timedelta(seconds=2),
            result="DELIVERED",
            target_task_id="coord-1",
        )
        self.assertEqual(state["heartbeatAcceptance"]["status"], "PENDING")
        self.assertEqual(state["heartbeatAcceptance"]["consecutiveScheduledInvocations"], 1)

    def test_heartbeat_proven_only_after_consecutive_delivery_and_reconciled_dependent_dispatch(self) -> None:
        state = new_control_loop_state(coordinator_task_id="coord-1", owner_id="owner-1", now=NOW)
        configure_automation(
            state,
            automation_id="heartbeat",
            target_task_id="coord-1",
            remaining_runs=3,
            now=NOW,
        )
        state["capacity"] = 2
        loop = PortfolioControlLoop(MemoryControlLoopStore(state), repo_root=ROOT)
        loop.register_lane("a")
        loop.register_lane("b", dependencies=("a",))
        first = loop.invoke(
            coordinator_task_id="coord-1",
            holder="owner-1",
            trigger="hourly",
            invocation_id="slot-1",
            now=NOW,
        )
        self.assertEqual(first["status"], "RUNNING")
        persisted = loop.state()
        record_automation_delivery(
            persisted,
            automation_id="heartbeat",
            delivery_id="delivery-1",
            scheduled_at=NOW,
            actual_delivery_at=NOW + timedelta(seconds=2),
            result="DELIVERED",
            target_task_id="coord-1",
        )
        record_automation_delivery(
            persisted,
            automation_id="heartbeat",
            delivery_id="delivery-2",
            scheduled_at=NOW + timedelta(hours=1),
            actual_delivery_at=NOW + timedelta(hours=1, seconds=2),
            result="DELIVERED",
            target_task_id="coord-1",
        )
        persist_durable_state(persisted, loop.store)
        worker_id = loop.state()["lanes"]["a"]["workerId"]
        result = loop.invoke(
            coordinator_task_id="coord-1",
            holder="owner-1",
            trigger="hourly",
            invocation_id="slot-2",
            now=NOW + timedelta(hours=1),
            observations={worker_id: {"status": "COMPLETED", "result": "SUCCESS"}},
        )
        evidence = result["report"]["heartbeatContinuity"]
        self.assertEqual(evidence["status"], "PROVEN")
        self.assertEqual(evidence["consecutiveScheduledInvocations"], 2)
        self.assertTrue(evidence["terminalWorkerReconciled"])
        self.assertTrue(evidence["dependencyReadyPacketDispatched"])

    def test_handover_is_finite_and_terminal_event_transfers_once(self) -> None:
        state = self.loop.state()
        configure_automation(
            state,
            automation_id="update",
            target_task_id="coord-1",
            remaining_runs=1,
            now=NOW,
        )
        handed = create_handover(
            state,
            predecessor_task_id="coord-1",
            successor_task_id="coord-2",
            successor_owner_id="owner-2",
            now=NOW,
        )
        self.assertTrue(handed["handover"]["finite"])
        self.assertEqual(handed["controller"]["taskId"], "coord-2")
        event = {"id": "terminal-1", "workerId": "a"}
        self.assertTrue(transfer_terminal_event(handed, event, successor_task_id="coord-2"))
        self.assertFalse(transfer_terminal_event(handed, event, successor_task_id="coord-2"))
        self.assertFalse(transfer_terminal_event(handed, {"id": "terminal-2"}, successor_task_id="coord-1"))

    def test_json_store_restart_reads_exact_durable_state(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory(prefix="portfolio-loop-") as tmp:
            path = Path(tmp) / "state.json"
            first = PortfolioControlLoop(JsonFileControlLoopStore(path), repo_root=ROOT)
            first.initialize(coordinator_task_id="coord-r", owner_id="owner-r", now=NOW, capacity=2)
            first.register_lane("a")
            second = PortfolioControlLoop(JsonFileControlLoopStore(path), repo_root=ROOT)
            recovered = second.recover(
                coordinator_task_id="coord-r",
                holder="owner-r",
                trigger="PULSE",
                invocation_id="restart-1",
                now=NOW + timedelta(seconds=1),
            )
            self.assertEqual(recovered["status"], "RUNNING")
            self.assertEqual(second.state()["lanes"]["a"]["state"], "RUNNING")


if __name__ == "__main__":
    unittest.main()
