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
| `linktrend-review-ready-publisher.yml` | Normal-token `workflow_dispatch` publisher/withdrawer for `Linktrend Review Ready` (`action=publish|withdraw`; default-branch scripts; tip is data only) |
| `linktrend-development-to-staging.yml` | Build (Tue/Fri 10:00) + exact-candidate reevaluate |
| `linktrend-staging-to-main.yml` | Package / approve-merge (bound SHAs) / observe |
| `linktrend-integrator-merge.yml` | Merge to development when fast-gate + Bugbot + reviewed SHA |
| `linktrend-cleanup-merged.yml` | Weekly remote cleanup of merged/abandoned branches (no local worktrees) |
| `linktrend-repair-observer.yml` | Upsert/resolve repair tasks on CI/Bugbot lifecycle (normal `AUTOMATION_TOKEN` only) |

## Trust boundary (all privileged workflows)

- Checkout **default branch only** (`persist-credentials: false`)
- Never run PR head/merge scripts with write credentials
- Read-only event/candidate resolution may use the ordinary workflow token (`github.token`) with read scopes only
- Durable repair and all other autonomous mutations require `LINKTREND_AUTOMATION_TOKEN` (`docs/contracts/GITHUB-APP-GITOPS-CREDENTIALS.md`)
- Automation token unavailable → local `automation_credentials_blocked` outcome / step summary and failed workflow only
- Mutation jobs must not grant write permissions to the ordinary workflow token (`issues`/`checks`/`pull-requests`/`contents`/`statuses` write)
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
- Approved private repositories use `linktrend-private-macos-arm64`, which renders trusted managed jobs onto `[self-hosted, macOS, ARM64, linktrend-privileged]`.
- Candidate CI is consumer-owned and must use a separately isolated runner; managed sync never overwrites `ci.yml`.
