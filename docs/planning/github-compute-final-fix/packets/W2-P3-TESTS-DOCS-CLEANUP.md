# W2-P3 — Regression Tests, Operator Documentation, and Cleanup Tooling

## Objective

Provide complete verification and safe cleanup tooling for the permanent design.
Remove stale active doctrine that could instruct future agents to use the Mac Mini,
self-hosted runners, or former custom App.

## Dependencies and base

- Wave 1 combined PASS and exact Phase SHA.
- Consume frozen interfaces and agreed W2-P1/W2-P2 file lists.

## Owned paths

- `scripts/tests/*` not assigned to other packets
- `docs/contracts/*`, `docs/runbooks/*`, active operations/status docs assigned by
  Terra
- `core/managed-core/content/doctrine/*` mirrored active doctrine
- host/external cleanup scripts specifically assigned by Terra
- test fixtures and evidence templates

Do not edit workflow implementation, installer/manifest, or product runtime code.

## Required implementation

1. Replace obsolete local-coordinator/self-hosted/App expectations in active tests
   and doctrine with the approved hosted-ARM64 behavior.
2. Add end-to-end deterministic fixtures for no-checkpoint CI, correct concurrency
   scope, obsolete cancellation, exact sealing, Bugbot-final-only signal, full-suite
   once, two-attempt stop, two-candidate stop, receipt reuse, changed-tree reject,
   and promotion without full-suite rerun.
3. Add least-privilege workflow permission and forbidden-legacy static tests.
4. Add disposable fresh-install, upgrade, idempotence, and rollback runbook/tests.
5. Build safe external cleanup tooling with plan/dry-run default, explicit `--apply`,
   before-state capture, ownership validation, secret-name-only output, and
   protection verification. Separate repository App/runner cleanup from Mac host/
   Docker cleanup.
6. Host cleanup may target only recorded IDE-owned launchd services and Docker
   resources. It must refuse broad globs/unknown resources.
7. Document billing alerts with no spending cap and a monthly usage report.
8. Document emergency authority, normal post-release flow, consumer rollout, and
   LiNKdeveloper boundary.
9. Archive or mark superseded older Streamlined Delivery planning so agents cannot
   mistake Mac coordination for current authority. Preserve history; do not erase
   unrelated evidence.

## Acceptance criteria

- New tests fail against an old-profile fixture and pass against the new profile.
- Cleanup dry-run makes zero external changes.
- Apply fixture deletes only owned mock resources and preserves lookalikes.
- Secret values never appear in logs/evidence.
- Active-doc scan contains no instruction to require the former custom App or Mac
  runner; historical archive references are clearly non-authoritative.
- Operator runbook explains commit-to-main flow in plain English.
- Usage alert documentation explicitly says no stop limit.

## Validation

Run all new suites plus the complete repository verification:

```bash
bash scripts/verify-ide-development.sh
```

Run shellcheck/actionlint/document-link checks available in the repository.

## Prohibited

- No live cleanup, GitHub mutation, host service change, Docker deletion, PR,
  merge, promotion, consumer edit, version/tag/release, or billing change.
- Do not delete archive evidence or unrelated docs.

## Handoff

Return one exact commit, test matrix/results, dry-run/apply fixture evidence, active
documentation scan, and explicit external operations Terra must perform in W3.
