# W3-P1 — Integrate, Package, Canary, Promote, and Release

## Assignment

Complete the feature from verified Wave 2 integration, reconcile the concurrent feature, generate the managed package, prove the live canary, and release IDE Development through development, staging, and main.

Terra supplies verified `B2`. This is the only Wave 3 packet. Luna implements repository changes. Terra independently verifies and owns live installation, rulesets, PRs, merges, promotion, tag, release, rollback, and cleanup.

## Required reading

- every document in `docs/planning/streamlined-delivery/`
- all Wave 1 and Wave 2 evidence
- `scripts/verify-ide-development.sh`
- `scripts/ide_development/build_manifest.py`
- `docs/runbooks/release-candidate.md`
- `docs/contracts/REPOSITORY-PROTECTION.md`

## Owned scope

- Combined integration corrections.
- Test aggregators and fixtures required to prove this feature.
- Active contracts, ADRs, operator documentation, README references, and managed doctrine copies.
- Managed runtime file manifest.
- Root and managed `VERSION`.
- `core/managed-core/INDEX.yaml` and `MANIFEST.json`.
- Dedicated streamlined-delivery release candidate/checksum/evidence paths.

Do not modify application code outside IDE Development. Do not touch the unrelated feature except deliberate conflict reconciliation performed with Terra.

## Luna repository sequence

1. Confirm clean B2 worktree and exact ancestry.
2. Fetch current `origin/development` and inventory concurrent-feature commits/paths.
3. With Terra, merge latest development into the Phase branch and preserve both feature sets.
4. Run affected focused tests before additional edits.
5. Fix integration defects only; do not redesign frozen interfaces.
6. Update active contracts/ADR/runbook for coordinator, Phase PR, attempts, receipts, profiles, promotion, rollback, and operator commands.
7. Add authored runtime files to managed source lists.
8. Regenerate managed doctrine and manifest with official tooling.
9. Determine the next semantic version from repository release rules only after final content is stable.
10. Build release-candidate evidence after final content stabilizes.

## Required combined tests

```bash
python3 -m unittest discover -s scripts/ide_development_tests
python3 -m unittest discover -s scripts/tests -p 'test_*streamlined*'
python3 -m unittest discover -s scripts/tests -p 'test_*receipt*'
python3 -m unittest discover -s host/coordinator/tests
bash scripts/tests/test-gitops-phase-delivery.sh
bash scripts/tests/test-gitops-review-packager.sh
bash scripts/tests/test-integrator-bugbot-gate.sh
bash scripts/tests/test-gitops-lifecycle.sh
bash scripts/tests/test-managed-runner-routing.sh
bash tests/test-portable-v2-integration.sh
env PYTHONPATH=scripts python3 -m ide_development.build_manifest --verify
actionlint .github/workflows/*.yml
bash scripts/verify-ide-development.sh
git diff --check
```

If a discovery command finds zero tests, correct the invocation or add an explicit aggregator. An empty discovery is not proof.

## Disposable consumer proof

Install into a temporary Git repository and verify:

- v2 config accepted;
- local and Actions profiles render deterministically;
- system repository never receives a nested installation;
- package contains no host-specific absolute source path;
- fast/full/release commands remain consumer-owned;
- install/sync is idempotent;
- rollback restores the previous managed package.

## Terra-only live canary

Luna must not perform these mutations. Terra performs them after repository verification:

1. Snapshot installed runners, launchd services, configuration, rulesets, checks, containers, and rollback version.
2. Install the exact candidate coordinator in canary mode.
3. Register IDE Development only.
4. Prove protected-default policy loading and no PR-head execution on host.
5. Measure one fast run; target at most 300 seconds.
6. Prove one-heavy/two-fast admission and host-pressure pause.
7. Prove obsolete queued/running cancellation and cleanup.
8. Prove restart recovery.
9. Prove attempts 1 and 2 failure create one stop/alert and no third dispatch.
10. Prove completed containers and temporary worktrees disappear.
11. Prove stable normal GitHub statuses and absence of custom App credentials.
12. Roll back immediately on any trust, cleanup, state, or protection failure.

## Terra-only PR and release sequence

1. Apply a short protected-branch release lock.
2. Seal and push exact Phase candidate.
3. Open one Phase PR to development with normal authentication.
4. Require Fast Gate, Cursor Bugbot, and Full Suite/not-required on exact identity.
5. Permit at most one corrected seal.
6. Merge to development.
7. Apply and verify replacement development status rules.
8. Create/verify/merge staging using receipt plus short release checks.
9. Create main promotion and satisfy configured approval.
10. Verify receipt plus short release checks and merge main.
11. Prove the released feature content across branches using tree/content equality rather than identical merge commit IDs.
12. Tag and publish from verified main.
13. Verify all protections active.
14. Remove only streamlined-delivery packet/Phase branches and worktrees proven safe.
15. Leave concurrent-feature resources untouched and end release lock.

## Temporary-rule exception

Terra may use the approved override only when an obsolete status context is the sole blocker and all replacement evidence is green. Snapshot, narrowly disable, merge exact candidate, immediately install/verify replacement protection. Never bypass tests, Bugbot, conflicts, missing evidence, or identity mismatch.

## Completion evidence

Include B0/B1/B2; packet Issue/branch/attempt/executor/final SHA; Terra takeovers; tests and negative probes; disposable consumer; canary timing/resources/restart/cancellation/stop/cleanup; service install and rollback; rulesets before/after; concurrent-feature preservation; Phase/staging/main PRs and merges; final trees; version/tag/release; and unresolved issue or `none`.
