# Managed GitHub Workflows

Templates synced into consumer repos (and IDE Development itself) by:

```bash
./scripts/sync-managed-workflows.sh <repo-path>
```

## Synced files (Layer B)

| File | Purpose |
|---|---|
| `branch-source-policy.yml` | Allowed work branches into development; `promote/*` into staging/main |
| `linktrend-review-packager.yml` | Discover (Tue/Fri 08:00) + evaluate (`pull_request_target` / `workflow_run` CI / external `check_run`) |
| `linktrend-development-to-staging.yml` | Build (Tue/Fri 10:00) + exact-candidate reevaluate |
| `linktrend-staging-to-main.yml` | Package / approve-merge (bound SHAs) / observe |
| `linktrend-integrator-merge.yml` | Merge to development when fast-gate + Bugbot + reviewed SHA |
| `linktrend-cleanup-merged.yml` | Weekly remote cleanup of merged/abandoned branches (no local worktrees) |

## Trust boundary (all privileged workflows)

- Checkout **default branch only** (`persist-credentials: false`)
- Never run PR head/merge scripts with write credentials
- Autonomous mutation requires GitHub App token (`docs/contracts/GITHUB-APP-GITOPS-CREDENTIALS.md`)
- Honest outcomes via `gitops-outcome.json` / result checks (green job ≠ packaged)

## Contracts

- `core/github/CI-GATE-CONTRACTS.md` (includes consumer `workflow_run` name mapping)
- `core/github/REVIEW-READY.md` (commit status, not a file in the diff)
- `docs/contracts/BUGBOT-MENTION-ONLY.md`
- `docs/contracts/GITHUB-APP-GITOPS-CREDENTIALS.md`

## Never synced

- `ci.yml` (unprivileged PR testing; `contents: read`)
