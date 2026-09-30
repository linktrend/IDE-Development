# Managed GitHub Workflows

Templates synced into consumer repos (and IDE Development itself) by:

```bash
./scripts/sync-managed-workflows.sh <repo-path>
```

## Synced files (Layer B)

| File | Purpose |
|---|---|
| `branch-source-policy.yml` | Allowed work branches into development; only `promote/main/*` into main |
| `linktrend-cleanup-merged.yml` | Explicit manual remote cleanup of merged/abandoned branches (no local worktrees) |
| `linktrend-promote-main.yml` | v3 `main` promotion check, published as the unique `Linktrend Main Receipt Gate` context to avoid collision with the old staging workflow: a `promote/main/*` head must match a development merge tree whose exact Phase PR head has a reusable Full inventory (`scripts/orchestrator/promotion_check.py`; runbook `docs/runbooks/orchestrator-delivery.md`) |

## Synced only with a deploy target

| File | Purpose |
|---|---|
| `linktrend-deploy.yml` | `Linktrend Deploy`: on push to `main` (and manual dispatch) calls `linktrend/LiNKops/.github/workflows/deploy.yml@v1` with `target-file: deploy/target.json`, `sha: ${{ github.sha }}` and the explicit `TS_OAUTH_CLIENT_ID` / `TS_OAUTH_SECRET` secrets; `contents: read` only. Synced only when the target repo has `deploy/target.json`, and removed (if unmodified) when that file goes away. Interface: `docs/contracts/DEPLOY-CALLER.md` |

IDE Development itself declares no deploy target and has no live copy.

## Retired in v3

All other v2 workflow templates were retired in v3 (IDE-22); the orchestrator (`scripts/orchestrator/`) now packages, merges and promotes. The sync removes these v2 copies from a consumer's `.github/workflows/` only while they still equal a published v2 rendering for that consumer (`scripts/ide_development/retired_workflows.py`, known bytes under `core/managed-core/migrations/known-bytes/retired-workflow-*`); a locally edited copy is kept and reported as a conflict (exit 11). `ide-development.py update` applies the same hash-guarded removal inside its transaction, so `rollback` restores them.

`linktrend-development-to-staging.yml`, `linktrend-integrator-merge.yml`, `linktrend-repair-observer.yml`, `linktrend-review-gate.yml`, `linktrend-review-packager.yml`, `linktrend-review-ready-publisher.yml`, `linktrend-staging-to-main.yml`. After removal, branch protection must stop requiring their check contexts (`docs/runbooks/v3-upgrade.md`).

`linktrend-promote-main.yml` runs `scripts/orchestrator/promotion_check.py` from the target repo's `development` branch and validates the exact Phase Verify run's Full inventory; a consumer needs both before it relies on this check.

## Trust boundary (all privileged workflows)

- Checkout **default branch only** (`persist-credentials: false`)
- Never run PR head/merge scripts with write credentials
- Read-only event/candidate resolution may use the ordinary workflow token (`github.token`) with read scopes only
- Approved explicit mutation jobs use scoped built-in `github.token` permissions only; custom App/PAT automation is retired.
- Write permissions are granted only to the exact job that needs them, with immutable SHA/receipt guards before mutation.
- Honest outcomes via `gitops-outcome.json` / result checks (green job ≠ packaged)

## Contracts

- `core/github/CI-GATE-CONTRACTS.md` (v3 jobs, required check names, local fast command, and the `main` promotion check)
- `docs/contracts/BUGBOT-MENTION-ONLY.md`
- `docs/contracts/GITHUB-APP-GITOPS-CREDENTIALS.md`

## Never synced

- `ci.yml` (unprivileged PR testing; `contents: read`)

## Runner routing

- `runnerType` is optional in `.github/linktrend-gitops-consumer.json` and defaults to `github-hosted`.
- `fastWorkflowName` and `ciWorkflowName` are required exact workflow display names. Both must execute successfully on the actual Phase rollout PR head before Full can issue a receipt.
- Private and public repositories use the same `github-hosted` ARM64 profile; retired self-hosted runner profiles are rejected.
- Candidate CI is consumer-owned and must use a separately isolated runner; managed sync never overwrites `ci.yml`.
