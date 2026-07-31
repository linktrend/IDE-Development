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

### Dual credentials (Packager identity boundary)

Cursor Bugbot requires a **human user** PR author and a **human user** `@cursor review` comment. The GitHub App alone cannot satisfy that trigger path.

| Kind | Name | Allowed operations only |
|------|------|-------------------------|
| Repository secret | `LINKTREND_BUGBOT_USER_TOKEN` | (1) Review Packager **feature PR create** into `development`; (2) the single `@cursor review` + exact-SHA marker comment |

Resolved in-job as `BUGBOT_USER_TOKEN` by `scripts/gitops/resolve_bugbot_user_token.sh` / `bugbot_user_credentials.py`.

**Hard rules:**

1. Fail closed when the user token is missing for either permitted operation (`bugbot_user_credentials_blocked`).
2. Never silently substitute `AUTOMATION_TOKEN`, `LINKTREND_APP_TOKEN`, or `GITHUB_TOKEN`.
3. Never use the user token for merge, promote, repair, status/check writes, cleanup, or branch pushes.
4. Never print, artifact, summarize, or cross-job-output the user token value.
5. All other Packager/Integrator/promote mutations continue to use the GitHub App installation token.

### Token minting contract (same job only)

1. Only the official mint step receives the private key:
   `actions/create-github-app-token@fee1f7d63c2ff003460e3d139729b119787bc349` (v2.2.2)
2. Subsequent shell/Python steps receive **only**:
   - `LINKTREND_GITOPS_APP_ID` (non-secret)
   - `LINKTREND_APP_TOKEN` = `${{ steps.app.outputs.token }}` (minted installation token)
3. Consuming steps must **not** receive `LINKTREND_GITOPS_APP_PRIVATE_KEY`
4. Mint and consume in the **same job**. Do not put the token in job outputs, artifacts, summaries, or repository files (GitHub does not transmit secret job outputs; the action revokes the token when its job ends)
5. Do not use `skip-token-revoke` to work around cross-job transport

`scripts/gitops/resolve_automation_token.sh` accepts a non-empty minted token + App ID and rejects private-key leakage into consumer steps.

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

If App ID or minted token are unavailable:

1. Outcome status is **`automation_credentials_blocked`**
2. Workflows must **not** silently fall back to `GITHUB_TOKEN` and claim autonomy
3. Diagnostics may print `AUTOMATION_TOKEN_SOURCE` / `AUTOMATION_CREDENTIALS_STATUS` only (never key or token material)

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
5. Store a narrowly scoped Carlos user PAT as repository secret `LINKTREND_BUGBOT_USER_TOKEN` (PR write + issue comment only; no admin)
6. Re-run a Packager `workflow_dispatch` smoke after this change is on the **default branch**
7. Confirm logs show `AUTOMATION_TOKEN_SOURCE=github_app`, `BUGBOT_USER_TOKEN_SOURCE=user_secret`, a draft PR **authored by `linktrend`**, and exactly one `@cursor review` comment also authored by `linktrend`

## Rollout gate

Consumer rollout remains blocked until:

1. This corrected system is on the default branch and smoke-tested
2. Bugbot `manualTriggerOnly` is confirmed per repo
3. This App token path is configured (`automation_credentials_blocked` must not be the steady state)

## Agent prohibition

Agents must **not** create or configure credentials, GitHub Apps, secrets, or repository settings in this workstream.
