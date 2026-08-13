# W2-P3 — Thin GitHub Fallback and Receipt-Based Promotion

## Assignment

Remove high-churn workflow cascades in local-coordinator mode and implement exact-receipt staging/main promotion. Terra supplies verified `B1`. This packet may run with W2-P1 and W2-P2.

## Dependencies and reading

All Wave 1 packets must be integrated. Read the implementation plan, frozen interfaces, `core/github/CI-GATE-CONTRACTS.md`, `docs/contracts/ACTIONS-COST-CONTROLS.md`, managed workflow templates, sync script, and promotion scripts.

## Owned paths

- `core/github/managed-workflows/**`
- corresponding `.github/workflows/linktrend-*.yml`
- `scripts/sync-managed-workflows.sh`
- `scripts/gitops/promote_staging.sh`
- `scripts/gitops/promote_main.sh`
- new `scripts/gitops/promotion_receipt_gate.py`
- new `scripts/gitops/ruleset_plan.py`
- new `scripts/tests/test_local_coordinator_workflow_profile.sh`
- new `scripts/tests/test_promotion_receipt_gate.py`
- `docs/evidence/streamlined-delivery/W2-P3/**`

## Required implementation

1. Render explicit `local-coordinator` and `github-actions` profiles.
2. Local profile removes schedule/check-run/workflow-run/pull-request-target cascades from Packager, Integrator, repair, and promotion; retain bounded manual recovery where appropriate.
3. GitHub Actions profile preserves supported behavior.
4. Local profile uses frozen status contexts.
5. Promotion verifies receipt before mutation.
6. Development requires exact seal, Fast Gate, Cursor Bugbot, Full Suite passed/not-required, and unchanged head.
7. Staging automatically creates/reuses one candidate, runs release checks, and never reruns full suite for matching identity.
8. Main supports principal-approval and automatic modes; principal approval defaults.
9. Main approval binds source, base, PR head, and receipt.
10. Detect/reuse correct promotion PR and prevent duplicates.
11. Cancel obsolete GitHub runs without waiting where supported.
12. Produce reversible dry-run ruleset and rollback plans.
13. Use normal GitHub credentials; remove former custom-App dependency from active owned paths.

## Tests and negative probes

- Local profile contains no prohibited automatic cascade and retains manual recovery.
- Compatibility profile passes existing render tests.
- Wrong/missing/failed receipt blocks.
- Different commit with identical content passes.
- One-byte/dependency change blocks.
- Full suite never runs in staging/main path.
- Duplicate promotion handled deterministically.
- Stale main approval rejected.
- Automatic main still requires gates.
- Ruleset plan is dry-run/reversible and only expected contexts.
- External actions remain pinned and actionlint passes.

## Prohibited

No live dispatch, PR, merge, ruleset apply, promotion, host coordinator implementation, W2-P2 Packager/Integrator Python edits, or version/manifest/package regeneration.

## Acceptance commands

```bash
bash scripts/tests/test_local_coordinator_workflow_profile.sh
python3 -m unittest scripts.tests.test_promotion_receipt_gate
bash scripts/tests/test-managed-runner-routing.sh
bash scripts/tests/test-gitops-lifecycle.sh
actionlint .github/workflows/*.yml
git diff --check
```

## Handoff

Commit/push and report B1, exact SHA, files, profile comparison, tests, negative probes, ruleset dry-run evidence, clean state, and blocker or `none`. No live mutation and no PR.

