"""Adversarial PKT-08 final-control tests against an isolated extract."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness.installer import materialize_isolated_rc_extract


ROOT = Path(__file__).resolve().parents[2]
RUNTIME_FILES = (
    "core/execution/__init__.py",
    "core/execution/protocol.py",
    "core/execution/lifecycle.py",
    "core/execution/scheduler.py",
    "core/execution/verification_liveness.py",
    "core/execution/manifest_persistence.py",
    "core/execution/transactional_dispatch.py",
    "core/contracts/PKT08-REVISION-60-FINAL-CONTROLS.md",
    "core/managed-core/content/config/transactional-dispatch.json",
    "core/managed-core/schemas/transactional-dispatch.schema.json",
)


class ExtractedFinalControlTests(unittest.TestCase):
    def test_extracted_runtime_rejects_all_named_adversarial_paths(self) -> None:
        with tempfile.TemporaryDirectory(prefix="pkt08-final-cleanroom-") as tmp:
            source = Path(tmp) / "source"
            extract = Path(tmp) / "extract"
            for rel in RUNTIME_FILES:
                destination = source / rel
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / rel, destination)
            materialize_isolated_rc_extract(extract, source=source)

            script = r"""
from datetime import datetime, timedelta, timezone
from core.execution.protocol import LeaseState
from core.execution.transactional_dispatch import (
    DispatchBudget, DispatchInterrupted, DispatchRequest,
    DurableDesignResumeStore, DurableDispatchIntentStore,
    design_approval_decision, dispatch_transactionally,
    resume_unsolicited_design_result,
)

now = datetime(2026, 8, 20, tzinfo=timezone.utc)
req = DispatchRequest("PKT-08", "linktrend/IDE-Development", "a" * 40, "b" * 40,
                      "cleanroom", {"x": 1})
def lease(expires):
    return LeaseState("holder", "PKT-08", req.repository, "nonce", expires)
class External:
    def __init__(self, interrupt=False, wrong_authority=False):
        self.calls = 0
        self.interrupt = interrupt
        self.wrong_authority = wrong_authority
        self.authority = {}
    def dispatch(self, request, key):
        self.calls += 1
        self.authority[key] = {
            "dispatchId": "d-1",
            "idempotencyKey": "attacker-key" if self.wrong_authority else key,
        }
        if self.interrupt:
            self.interrupt = False
            raise DispatchInterrupted(201, key)
        return {"statusCode": 201, "dispatchId": "d-1"}
    def read_by_idempotency_key(self, key):
        return self.authority.get(key)
budget = DispatchBudget(30, 4)

store, ext = DurableDispatchIntentStore(), External()
dispatch_transactionally(req, store, ext, lease=lease(now + timedelta(minutes=5)),
                         holder="holder", now=now, budget=budget)
assert dispatch_transactionally(req, store, ext, lease=lease(now + timedelta(minutes=5)),
                                holder="holder", now=now, budget=budget).status == "duplicate"
assert ext.calls == 1

collision, collision_ext = DurableDispatchIntentStore(), External()
collision.collide_next_commit = True
assert dispatch_transactionally(req, collision, collision_ext,
                                lease=lease(now + timedelta(minutes=5)),
                                holder="holder", now=now, budget=budget).status == "committed"
assert collision_ext.calls == 1

injected, injected_ext = DurableDispatchIntentStore(), External(
    interrupt=True, wrong_authority=True
)
try:
    dispatch_transactionally(req, injected, injected_ext,
                             lease=lease(now + timedelta(minutes=5)),
                             holder="holder", now=now, budget=budget)
except RuntimeError as error:
    assert "external_authority_identity_mismatch" in str(error)
else:
    raise AssertionError("injected authority admitted")

stale, stale_ext = DurableDispatchIntentStore(), External()
try:
    dispatch_transactionally(req, stale, stale_ext, lease=lease(now - timedelta(seconds=1)),
                             holder="holder", now=now, budget=budget)
except RuntimeError as error:
    assert "stale_or_invalid_lease" in str(error)
else:
    raise AssertionError("stale lease admitted")
assert stale.write_count == 0 and stale_ext.calls == 0

short, short_ext = DurableDispatchIntentStore(), External()
try:
    dispatch_transactionally(req, short, short_ext, lease=lease(now + timedelta(minutes=5)),
                             holder="holder", now=now, budget=DispatchBudget(3, 4))
except RuntimeError as error:
    assert "deadline_budget_insufficient" in str(error)
else:
    raise AssertionError("insufficient budget admitted")
assert short.write_count == 0 and short_ext.calls == 0

recover, recovering_ext = DurableDispatchIntentStore(), External(interrupt=True)
assert dispatch_transactionally(req, recover, recovering_ext,
                                lease=lease(now + timedelta(minutes=5)),
                                holder="holder", now=now, budget=budget).status == "recovered"
assert recovering_ext.calls == 1

approved = {"designAuthority": {"status": "APPROVED", "manifestDigest": "sha256:" + "c" * 64}}
assert design_approval_decision(approved, conversation={"status": "PENDING"}).suppress_executor_approval
assert not design_approval_decision({"designAuthority": {"status": "PENDING"}},
                                    conversation={"status": "APPROVED"}).approved
resume_store = DurableDesignResumeStore()
result = {"resultId": "r-1", "kind": "design-only", "terminal": True, "solicited": False}
assert resume_unsolicited_design_result(approved, result, resume_store).resumed
assert not resume_unsolicited_design_result(approved, result, resume_store).resumed
"""
            proc = subprocess.run(
                [sys.executable, "-c", script],
                cwd=extract,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)


if __name__ == "__main__":
    unittest.main()
