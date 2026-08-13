# W2-P1 — Managed Workflows and Phase Integration

## Objective

Wire the accepted Wave 1 interfaces into the managed workflow and Phase PR
lifecycle using GitHub-hosted ARM64. Implement actual no-checkpoint, fast, sealed
full-suite, cancellation, Bugbot-final-only, and receipt-gated promotion behavior.

## Dependencies and base

- Wave 1 combined PASS and exact Phase integration SHA.
- Branch/worktree from that Phase SHA, not stale `B0`.
- Consume frozen config, lifecycle outcomes, and receipts without redefining them.

## Owned paths

- `core/github/managed-workflows/*.yml`
- `.github/workflows/*.yml` source/self-verification counterparts assigned by Terra
- workflow-specific helpers under `scripts/gitops/` assigned during preflight
- `scripts/gitops/phase_integrator.py`
- `scripts/gitops/promote_staging.sh` and `promote_main.sh` only for workflow wiring
- workflow/phase integration tests

Do not edit installer/manifest/version or delete host/App files owned by W2-P2/P3.

## Required implementation

1. Remove managed push triggers for ordinary `issue/*`/`dev/*` checkpoints.
2. Route managed candidate jobs to scalar `ubuntu-24.04-arm`.
3. Add fast PR workflow/job with stable name `Linktrend Fast Checks`, least
   permissions, five-minute target/timeout policy, and concurrency key scoped to
   workflow + PR with cancellation of obsolete runs.
4. Implement explicit exact-head sealing. The full suite cannot run merely because
   a draft opens. A later commit invalidates seal/review/receipt.
5. Trigger `Linktrend Full Suite` once for the sealed exact head. Respect two
   infrastructure attempts and two sealed candidates.
6. Trigger Bugbot only for the final sealed candidate, using the repository's
   existing supported Bugbot mechanism; do not use the former App to wake it.
7. Produce and retain the full-suite receipt after success.
8. Make development/staging/main promotion workflows call `Linktrend Receipt Gate`
   and `Linktrend Branch Source Policy`; do not rerun the full suite when exact
   identity matches.
9. Changed identity must stop and explain which digest differs.
10. Use explicit minimal `permissions:` blocks. Remove App-token minting steps and
    references from workflows touched here.
11. Keep workflow names stable and union required checks with consumer-owned checks.
12. Avoid event recursion: use a single workflow chain or explicit dispatch where
    built-in `GITHUB_TOKEN` events would not automatically trigger another flow.

## Acceptance criteria

- Workflow syntax/actionlint passes.
- Static event tests prove checkpoint pushes match no managed workflow.
- Two PR commits cancel only the older run for the same PR.
- Separate PRs do not cancel each other.
- Full suite requires seal matching current exact head.
- Push after seal invalidates the candidate and does not reuse old Bugbot/full
  results.
- One exact candidate cannot run a third infrastructure attempt.
- Promotion with exact receipt runs no full-suite job; changed tree fails.
- No touched workflow references self-hosted/Mac/ephemeral labels or custom App.

## Validation

```bash
bash scripts/tests/test-gitops-phase-delivery.sh
bash scripts/tests/test-gitops-lifecycle.sh
bash scripts/tests/test-managed-runner-routing.sh
bash scripts/tests/test-local-coordinator-workflow-profile.sh
```

Run repository actionlint/managed-workflow parity validation discovered in
preflight. Rename/replace the obsolete local-coordinator test only in W2-P3.

## Prohibited

- No external GitHub mutation, PR, merge, promotion, billing change, App deletion,
  runner deletion, host/Docker cleanup, consumer change, or release/version edit.
- Do not silently keep an App-backed compatibility path.

## Handoff

Return one exact commit, workflow event/permission/concurrency matrix, validation
logs, and any installer/legacy references W2-P2/P3 must remove.

