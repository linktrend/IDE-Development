# W1-P2 — Candidate Lifecycle, Sealing, Cancellation, and Attempt Limits

## Objective

Implement the pure lifecycle/state logic that distinguishes free checkpoints from
compute-consuming candidates, invalidates obsolete candidates, and stops retry
loops. Do not implement workflow YAML in this packet.

## Dependencies and base

- Depends on Terra preflight and frozen lifecycle/events.
- Branch/worktree from immutable `B0`.
- Consume W1-P1 configuration through the frozen interface; use fixtures until
  Wave 1 integration.

## Owned paths

- `scripts/gitops/coordinator/state.py` or replacement lifecycle module
- delivery runtime/state schemas under `core/managed-core/schemas/`
- new candidate/seal/attempt modules under `scripts/gitops/` assigned by Terra
- lifecycle/state-focused unit tests and fixtures

Do not edit workflow YAML, installer, manifest, receipt modules, or auth modules.

## Required implementation

1. Model checkpoint, integrating, draft Phase PR, sealed candidate, fast/full/
   review, eligibility, superseded, failure, retry, and stopped-alert states.
2. A checkpoint event records Git state but returns no CI-dispatch instruction.
3. A seal must bind to repository, PR, branch, head commit, and candidate identity.
4. Any later head commit invalidates the seal and any pending/successful result for
   that earlier candidate.
5. Generate a deterministic concurrency key scoped to repository + workflow + PR.
6. Mark older candidate work superseded so workflow integration can use
   `cancel-in-progress: true` without cross-PR cancellation.
7. Count infrastructure attempts per exact candidate identity. Attempt 1 may retry;
   attempt 2 transitions to stopped-alert. A new commit creates a new identity but
   also counts toward maximum two sealed candidate revisions for the Phase.
8. Distinguish infrastructure failure from code/test failure. Code failure never
   blindly reruns the same candidate; it returns to development.
9. State writes must be atomic/durable using repository conventions and safe under
   duplicate/out-of-order GitHub events.
10. Emit plain outcome codes consumed later by workflows and Terra.

## Acceptance criteria

- Checkpoint fixture yields zero dispatch.
- Two quick candidate commits leave only the newest active; keys for different PRs
  cannot cancel each other.
- Duplicate event is idempotent.
- Late success for superseded commit is rejected.
- First infrastructure failure yields exactly one retry; second yields stop-alert.
- Code failure yields no automatic retry.
- Third sealed candidate revision yields HOLD/stop.
- Restart/reload preserves counters and terminal state.
- No external GitHub write is required by unit logic.

## Validation

```bash
python3 -m unittest scripts.tests.test_streamlined_delivery_integration
python3 -m compileall -q scripts/gitops
```

Add a focused lifecycle suite if the existing integration suite is not isolated.

## Prohibited

- No workflow dispatch, PR, merge, promotion, billing, App/token, runner, Docker,
  host-service, installer, manifest, version, or consumer operation.
- Do not implement receipts or Git-tree comparison owned by W1-P3.

## Handoff

Return one exact commit, transition table, test evidence for every required edge,
and the stable outcome codes expected by W2-P1.
