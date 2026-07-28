# Managed GitHub Workflows

Templates synced into consumer repos (and IDE Development itself) by:

```bash
./scripts/sync-managed-workflows.sh <repo-path>
```

## Synced files (Layer B)

| File | Purpose |
|---|---|
| `branch-source-policy.yml` | Allowed work branches into development; `promote/*` into staging/main |
| `linktrend-review-packager.yml` | Discover (Tue/Fri 08:00) + evaluate (PR/check) |
| `linktrend-development-to-staging.yml` | Build (Tue/Fri 10:00) + reevaluate (no rebuild) |
| `linktrend-staging-to-main.yml` | Package / approve-merge / observe |
| `linktrend-integrator-merge.yml` | Merge to development when fast-gate + Bugbot + reviewed SHA |

## Contracts

- `core/github/CI-GATE-CONTRACTS.md`
- `core/github/REVIEW-READY.md` (commit status, not a file in the diff)
- `docs/contracts/BUGBOT-MENTION-ONLY.md`

## Never synced

- `ci.yml`
