# Bugbot mention-only (cost control)

**Status:** Required before consumer rollout (WP04) — mention-only still a per-repo gate; WP04 prepared / not executed
**Date:** 2026-07-28

Code alone **cannot** enforce mention-only. Cursor Bugbot runs from Cursor’s GitHub App settings. PR #19 observed automatic usage-limit comments on pushes even without a new `cursor review` comment — proof that automatic mode is still active for this installation.

## Required setting

For each repository (starting with `linktrend/IDE-Development`):

`manualTriggerOnly: true` (API) / **Only run when mentioned** (dashboard)

Manual triggers remain: comment exactly `@cursor review` or `bugbot run`.

### Packager authorship (Carlos user token)

GitHub App–authored PRs / comments do **not** reliably wake Bugbot. The Review Packager therefore uses repository secret `LINKTREND_BUGBOT_USER_TOKEN` for **only**:

1. Creating the feature draft PR into `development` (author must be `linktrend`)
2. Posting the single `@cursor review` + `<!-- linktrend-bugbot-requested: <sha> -->` comment (author must be `linktrend`)

Freeze comments, undraft, readiness, merges, promotion, and repair stay on the GitHub App. Missing user token → `bugbot_user_credentials_blocked` (fail closed; no App substitution).

### Request accounting (packager 2-request limit)

A comment counts toward the normal max of **2** Bugbot requests per PR only when it contains **both**:

1. An **executable** trigger line: `@cursor review` or `bugbot run`
2. The idempotency marker: `<!-- linktrend-bugbot-requested: <sha> -->`

Bare historical `cursor review` (no `@`) plus the marker does **not** consume the limit.

## API (team Admin API key)

```bash
curl -X POST https://api.cursor.com/bugbot/repo/update \
  -H "Authorization: Bearer $CURSOR_ADMIN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "repoUrl": "https://github.com/linktrend/IDE-Development",
    "enabled": true,
    "manualTriggerOnly": true
  }'
```

List: `GET https://api.cursor.com/bugbot/repos`

## Dashboard steps (Carlos)

1. Open https://cursor.com/dashboard/bugbot
2. Find `IDE-Development` (and each consumer before wire)
3. Enable Bugbot if needed
4. Set **Only run when mentioned** / repository `manualTriggerOnly` equivalent
5. Optional team setting: **Run only once per PR** (reduces spend if auto mode cannot be cleared)
6. Verify: push a trivial commit to a draft test PR **without** commenting `@cursor review` — Bugbot must **not** start a billable review
7. Verify mention path: comment `@cursor review` once — Bugbot runs

## Rollout gate

Consumer rollout is **blocked** until mention-only is confirmed per repository. Do not purchase funds or raise spending limits as part of this GitOps work.

## Historical note (PR #19 spend-limit period)

Agents must not post additional `@cursor review` comments on PR #19 while the spending limit is active. Integrator correctly blocks on SHA/marker mismatch; bootstrap merge (if any) is a documented one-time admin exception outside the product workflow. For current rollout gates, see `docs/CURRENT-STATUS.md` and WP04 (`docs/work-packets/2026-08-02-work-packet-04-consumer-rollout.md`).
