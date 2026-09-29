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
| `linktrend-promote-main.yml` | v3 `main` promotion check, published as the legacy-named `Linktrend Receipt Gate` context: a `promote/main/*` head must have the tree of a green `development` commit (`scripts/orchestrator/promotion_check.py`; runbook `docs/runbooks/orchestrator-delivery.md`) |

The v2 packager, integrator-merge, Review Ready publisher, receipt promotion and repair-observer templates were retired in v3 (IDE-22); see the v3 plan.

`linktrend-promote-main.yml` runs `scripts/orchestrator/promotion_check.py` from the target repo's `development` branch and requires `Verify IDE Development` on the matching commit; a consumer needs both before it relies on this check.

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
