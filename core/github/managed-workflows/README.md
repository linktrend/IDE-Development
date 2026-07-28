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
| `branch-source-policy.yml` | Enforce allowed PR sources into `development` |
| `linktrend-review-packager.yml` | Tue/Fri **08:00** Asia/Taipei — discover review-ready → open PR → request Bugbot once |
| `linktrend-development-to-staging.yml` | Tue/Fri **10:00** Asia/Taipei auto promote (`development` → `staging`) |
| `linktrend-staging-to-main.yml` | Mon 08:00 package; merge only on Principal Approve dispatch |
| `linktrend-integrator-merge.yml` | Auto-merge PRs into `development` when fast-gate + Bugbot pass |

**Promotion window:** Review Packager runs at 08:00 so Pull 07, review, CI, integration, and repair finish before Staging promote at **10:00**. See `docs/AUTONOMOUS-GIT-OPERATIONS.md`.

## Never synced by this pack

- `ci.yml` — product/repo-specific verification (keep local)
- Any other repo-only workflows

## Contracts (read before changing workflows)

| Document | Purpose |
|---|---|
| `core/github/CI-GATE-CONTRACTS.md` | Named gates: `fast-gate`, `staging-gate`, `release-gate` — never “wait for every check” |
| `core/github/REVIEW-READY.md` | Branch-local `.linktrend/review-ready.json`; Packager validity (`commitSha == HEAD`) |

Review Packager and Integrator use `fast-gate` check names (repo variable or IDE Development default `Verify IDE Development`). Missing required checks ≠ success.

## Bugbot

Workflows do not enable Bugbot by themselves. Complete `core/checklists/BUGBOT-INHERITANCE.md` after wire/backfill.

**Pass signal:** GitHub check `Cursor Bugbot` conclusion/state `success` (no open findings). `neutral` means findings remain — Integrator must not merge.

**Ruleset:** after syncing workflows, run `scripts/apply-development-merge-ruleset.sh [owner/repo] [check names...]` so `development` requires Bugbot + CI before merge.

**Integrator CI names:** set repository variable `LINKTREND_INTEGRATOR_REQUIRED_CHECKS` (comma-separated job display names). See Bugbot checklist step 7.

## Related

- SOT: `docs/AUTONOMOUS-GIT-OPERATIONS.md`
- Consumer rollout: `docs/GITOPS-CONSUMER-ROLLOUT.md`
- Lisa follow-up: `docs/contracts/LISA-OPENCLAW-FOLLOW-UP.md`
- Main Approve dispatch: `docs/contracts/LISA-MAIN-APPROVE-DISPATCH.md`
