# GitHub App credentials for autonomous GitOps (setup contract)

**Status:** Required external gate — agents must not create Apps, secrets, or credentials  
**Date:** 2026-07-28  
**Audience:** Carlos (one-time setup)

## Why not `GITHUB_TOKEN` alone

GitHub documents that pull requests **created or updated with `GITHUB_TOKEN`** do not create `pull_request` workflow runs that satisfy the usual automation loop without **manual approval** of workflows from that PR. Autonomous Packager/promotion therefore cannot honestly claim hands-free operation if it only uses `GITHUB_TOKEN` to open promote/draft PRs.

A **broad personal access token** is not preferred: it is user-scoped, hard to rotate narrowly, over-privileged by default, and couples automation to a human identity.

## Preferred design

A dedicated **GitHub App** installed on the org/repos, used only by managed GitOps workflows via:

| Kind | Name | Notes |
|------|------|--------|
| Repository/org variable | `LINKTREND_GITOPS_APP_ID` | Numeric App ID (non-secret) |
| Repository/org secret | `LINKTREND_GITOPS_APP_PRIVATE_KEY` | PEM private key — **never** commit |

Workflows mint a short-lived installation token (e.g. `actions/create-github-app-token`) and set `LINKTREND_APP_TOKEN` for scripts.

## Minimum App permissions

Grant only what autonomy needs:

| Permission | Access | Why |
|------------|--------|-----|
| Contents | Read & write | Push temporary `promote/*` branches |
| Pull requests | Read & write | Open/update/merge promotion and review draft PRs |
| Checks | Read & write | Read gates; post honest result check runs |
| Statuses | Read & write | Read/write `Linktrend Review Ready` (agents may also use user tokens) |
| Issues | Read & write | Durable conflict repair issues |
| Metadata | Read | Required baseline |
| Actions | Read | Inspect workflow_run / gate workflow identity |

Do **not** grant admin, members, or secrets management.

## Workflow fail-closed contract

If App ID/private key/token are unavailable:

1. Outcome status is **`automation_credentials_blocked`**
2. Workflows must **not** silently fall back to `GITHUB_TOKEN` and claim autonomy
3. Diagnostics may print `AUTOMATION_TOKEN_SOURCE` / `AUTOMATION_CREDENTIALS_STATUS` only (never key material)

`scripts/gitops/resolve_automation_token.sh` enforces this when `REQUIRE_APP_TOKEN=1`.

## One-time setup steps (Carlos)

1. GitHub → Settings → Developer settings → **GitHub Apps** → New GitHub App  
   - Name e.g. `LiNKtrend GitOps`  
   - Webhook: disabled  
   - Permissions: table above  
   - Where can this App be installed: Only on this account / org
2. Create private key; store PEM in org or repo secret `LINKTREND_GITOPS_APP_PRIVATE_KEY`
3. Note App ID → variable `LINKTREND_GITOPS_APP_ID`
4. Install the App on `IDE-Development` (later each consumer)
5. Re-run a Packager `workflow_dispatch` smoke after this change is on the **default branch**
6. Confirm logs show `AUTOMATION_TOKEN_SOURCE=github_app` and a draft PR whose subsequent CI runs without manual workflow approval

## Rollout gate

Consumer rollout remains blocked until:

1. This corrected system is on the default branch and smoke-tested  
2. Bugbot `manualTriggerOnly` is confirmed per repo  
3. This App token path is configured (`automation_credentials_blocked` must not be the steady state)

## Agent prohibition

Agents must **not** create or configure credentials, GitHub Apps, secrets, or repository settings in this workstream.
