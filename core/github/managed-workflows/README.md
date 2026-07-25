# Managed GitHub Workflows

Templates synced into consumer repos (and IDE Development itself) by:

```bash
./scripts/sync-managed-workflows.sh <repo-path>
# or via
./scripts/wire-repo.sh <consumer-repo-path>
```

## Synced files (Layer B)

| File | Purpose |
|---|---|
| `branch-source-policy.yml` | Enforce allowed PR sources |
| `linktrend-development-to-staging.yml` | Tue/Fri 08:00 Asia/Taipei auto promote |
| `linktrend-staging-to-main.yml` | Mon 08:00 package; merge only on Approve dispatch |
| `linktrend-integrator-merge.yml` | Auto-merge PRs into `development` when ready |

## Never synced by this pack

- `ci.yml` — product/repo-specific verification (keep local)
- Any other repo-only workflows

## Bugbot

Workflows do not enable Bugbot by themselves. Complete `core/checklists/BUGBOT-INHERITANCE.md` after wire/backfill.

**Pass signal:** GitHub check `Cursor Bugbot` conclusion/state `success` (no open findings). `neutral` means findings remain — Integrator must not merge.

**Ruleset:** after syncing workflows, run `scripts/apply-development-merge-ruleset.sh [owner/repo] [check names...]` so `development` requires Bugbot + CI before merge.
