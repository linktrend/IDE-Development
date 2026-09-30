# Deploy caller interface (IDE Development ↔ LiNKops)

**Status:** Proposed; LiNKops confirms it in its Wave 2.3.
**Owner of the deploy standard:** the LiNKops repository (`linktrend/LiNKops`), which also owns the `deploy/target.json` schema.
**Owner of the caller:** IDE Development (`core/github/managed-workflows/linktrend-deploy.yml`, synced by `scripts/sync-managed-workflows.sh`).

IDE Development ships only a thin caller. It does not define how a deploy runs, where it runs, or what a target looks like. Those belong to LiNKops.

## When a repository gets the caller

| Repository state | Caller installed? | Deploy after `main` |
|---|---|---|
| Has `deploy/target.json` | Yes — `.github/workflows/linktrend-deploy.yml` | Automatic on every push to `main` |
| No `deploy/target.json` | No (removed, if unmodified, when the file goes away) | Automatic only when the repository has its own deploy with a health check **and** a rollback; otherwise the orchestrator waits for Carlos |

A reusable-workflow reference to a missing target would fail every push to `main`, so the caller is never installed without `deploy/target.json`. IDE Development itself declares no target and has no live copy.

## Interface IDE Development expects from LiNKops

| Item | Expected value |
|---|---|
| Reusable workflow | `linktrend/LiNKops/.github/workflows/deploy.yml` |
| Ref | `@v1` — a moving major tag that LiNKops keeps backward compatible; breaking changes ship as `@v2` and a new caller |
| Trigger | `on: workflow_call` |
| Input `target-file` | string, required; repo-relative path to the target declaration (always `deploy/target.json`) |
| Input `sha` | string, required; the exact 40-character commit to deploy (`${{ github.sha }}` of the push to `main`) |
| Secret `TS_OAUTH_CLIENT_ID` | required; Tailscale OAuth client ID used to reach the deploy host |
| Secret `TS_OAUTH_SECRET` | required; Tailscale OAuth client secret |
| Outputs | `deployed-sha` (the commit now live), `health` (`pass` or `fail`), `rolled-back` (`true` or `false`) |
| Rollback | If the post-deploy health check fails, the workflow restores the previously deployed release, re-checks health, reports `rolled-back: true`, and fails the job |
| Idempotence | Re-running for the same `sha` is safe; runs for one repository are serialized by the caller's `concurrency` group and are never cancelled mid-deploy |

Secrets are passed explicitly by name. The caller never uses `secrets: inherit`.

## Caller permissions

The caller grants `contents: read` only. Tailscale access uses OAuth client secrets, not GitHub OIDC, so it does not need `id-token: write`. If LiNKops moves the interface to OIDC, the caller adds `id-token: write` in the same change that bumps the interface.

## Not owned here

- The `deploy/target.json` schema, deploy hosts, runtimes, health checks, and rollback mechanics (LiNKops).
- Deploy secrets: stored per repository (or organization) as GitHub Actions secrets; the values come from the approved secret store and are never committed.
