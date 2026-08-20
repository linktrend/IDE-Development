# Managed GitHub Workflows

Templates synced into consumer repos (and IDE Development itself) by:

```bash
./scripts/sync-managed-workflows.sh <repo-path>
```

## Synced files (Layer B)

| File | Purpose |
|---|---|
| `branch-source-policy.yml` | Allowed work branches into development; `promote/*` into staging/main |
| `linktrend-review-packager.yml` | Discover (Tue/Fri 08:00) + evaluate (`workflow_run` CI / external `check_run` / explicit dispatch) |
| `linktrend-review-ready-publisher.yml` | Legacy `Linktrend Review Ready` publisher/withdrawer. **v2.5:** non-canonical; outcomes are `WAIVED_LEGACY_GATE`, never PASS, and never Issue-checkpoint or Phase-delivery proof |
| `linktrend-development-to-staging.yml` | Build (Tue/Fri 10:00) + exact-candidate reevaluate |
| `linktrend-staging-to-main.yml` | Package / approve-merge (bound SHAs) / observe |
| `linktrend-integrator-merge.yml` | Merge to development when fast-gate + Bugbot + reviewed SHA |
| `linktrend-cleanup-merged.yml` | Explicit manual remote cleanup of merged/abandoned branches (no local worktrees) |
| `linktrend-repair-observer.yml` | Bounded repair evidence observer using the scoped built-in workflow token |

## Trust boundary (all privileged workflows)

- Checkout **default branch only** (`persist-credentials: false`)
- Never run PR head/merge scripts with write credentials
- Read-only event/candidate resolution may use the ordinary workflow token (`github.token`) with read scopes only
- Approved explicit mutation jobs use scoped built-in `github.token` permissions only; custom App/PAT automation is retired.
- Write permissions are granted only to the exact job that needs them, with immutable SHA/receipt guards before mutation.
- Honest outcomes via `gitops-outcome.json` / result checks (green job ≠ packaged)

## Contracts

- `core/github/CI-GATE-CONTRACTS.md` (includes consumer `workflow_run` name mapping)
- `core/github/REVIEW-READY.md` (commit status, not a file in the diff)
- `docs/contracts/BUGBOT-MENTION-ONLY.md`
- `docs/contracts/GITHUB-APP-GITOPS-CREDENTIALS.md`

## Never synced

- `ci.yml` (unprivileged PR testing; `contents: read`)

## Runner routing

- `runnerType` is optional in `.github/linktrend-gitops-consumer.json` and defaults to `github-hosted`.
- `fastWorkflowName` and `ciWorkflowName` are required exact workflow display names. Both must execute successfully on the actual Phase rollout PR head before Full can issue a receipt.
- Private and public repositories use the same `github-hosted` ARM64 profile; retired self-hosted runner profiles are rejected.
- Candidate CI is consumer-owned and must use a separately isolated runner; managed sync never overwrites `ci.yml`.
