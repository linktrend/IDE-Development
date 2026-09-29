#!/usr/bin/env python3
"""Founder-readable portfolio status derived from durable control-loop state."""

from __future__ import annotations

from typing import Any, Mapping


def build_portfolio_status(
    state: Mapping[str, Any],
    *,
    protected_truth: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the finite, founder-readable status from durable state only."""

    lanes = state.get("lanes") if isinstance(state.get("lanes"), Mapping) else {}
    workers = state.get("workers") if isinstance(state.get("workers"), Mapping) else {}
    lane_rows = list(lanes.values())
    completed = sum(
        1 for lane in lane_rows if isinstance(lane, Mapping) and lane.get("state") == "COMPLETE"
    )
    active = [
        worker
        for worker in workers.values()
        if isinstance(worker, Mapping)
        and str(worker.get("state") or worker.get("status") or "").upper()
        in {"RUNNING", "STARTED", "LIVE", "RESTARTED"}
    ]
    blockers = [str(item) for item in (state.get("blockers") or []) if str(item)]
    rejected = [
        str(lane.get("laneId") or lane_id)
        for lane_id, lane in lanes.items()
        if isinstance(lane, Mapping) and lane.get("state") == "TERMINAL_REJECT"
    ]
    blockers.extend(f"lane={lane_id}:terminal_reject" for lane_id in rejected)
    blocked = [
        str(lane.get("laneId") or lane_id)
        for lane_id, lane in lanes.items()
        if isinstance(lane, Mapping) and lane.get("state") == "BLOCKED"
    ]
    blockers.extend(f"lane={lane_id}:blocked" for lane_id in blocked)
    if protected_truth:
        blockers.extend(str(item) for item in (protected_truth.get("blockers") or []) if str(item))
    total = len(lane_rows)
    percentage = 100 if total == 0 else int(completed * 100 / total)
    if blockers:
        status = "HOLD"
        language = "NOT ISSUED"
        blocker = blockers[0]
    elif completed == total and total > 0:
        status = "DONE"
        language = "FINISHED"
        blocker = ""
    elif active:
        status = "RUNNING"
        language = "RUNNING"
        blocker = ""
    elif total:
        status = "RUNNING"
        language = "ISSUED"
        blocker = ""
    else:
        status = "HOLD"
        language = "NOT ISSUED"
        blocker = "no_canonical_lanes"
    providers = sorted(
        {
            str(worker.get("provider"))
            for worker in active
            if worker.get("provider")
        }
    )
    raw_capacity = state.get("capacity")
    if isinstance(raw_capacity, Mapping):
        capacity = sum(
            int(raw_capacity.get(provider) or 0) if str(raw_capacity.get(provider) or "").lstrip("-").isdigit() else 0
            for provider in ("cursor", "luna")
        )
    else:
        capacity = int(raw_capacity or 0)
    maximum_parallelism = bool(capacity and len(active) >= capacity)
    return {
        "schemaVersion": 1,
        "status": status,
        "language": language,
        "percentage": percentage,
        "completedCanonicalPackets": [
            str(lane.get("packetId") or lane_id)
            for lane_id, lane in lanes.items()
            if isinstance(lane, Mapping) and lane.get("state") == "COMPLETE"
        ],
        "activePartialPackets": [
            str(lane.get("packetId") or lane_id)
            for lane_id, lane in lanes.items()
            if isinstance(lane, Mapping) and lane.get("state") not in {"COMPLETE", "BLOCKED"}
        ],
        "currentWork": [str(worker.get("laneId") or worker.get("workerId")) for worker in active],
        "nextWork": [
            str(lane.get("laneId") or lane_id)
            for lane_id, lane in lanes.items()
            if isinstance(lane, Mapping) and lane.get("state") == "PREPARED"
        ],
        "blocker": blocker,
        "blockers": blockers,
        "dependency": state.get("dependencyGraph") or {},
        "workerProvider": providers,
        "maximumSafeParallelismInUse": maximum_parallelism,
        "safeCapacity": dict(state.get("safeCapacity") or {}),
        "utilizationGap": dict(state.get("utilizationGap") or {}),
        "protectedTruth": dict(protected_truth or {}),
        "heartbeatContinuity": dict(state.get("heartbeatAcceptance") or {
            "status": "PENDING",
            "confirmedScheduledInvocations": 0,
            "consecutiveScheduledInvocations": 0,
            "terminalWorkerReconciled": False,
            "dependencyReadyPacketDispatched": False,
            "requirements": ["consecutive_scheduled_invocations"],
        }),
    }


portfolio_status = build_portfolio_status
