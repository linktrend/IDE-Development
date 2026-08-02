# Handoff — 2026-07-30 (issue #31 Carlos user identity for Packager)

## Why

Smoke PR #30 was authored by `linktrend-gitops[bot]`. Cursor Bugbot does not
reliably run for App-authored PRs / App-authored `@cursor review` comments.

Repository secret `LINKTREND_BUGBOT_USER_TOKEN` now exists for a narrowly scoped
Carlos user identity.

## Change (this branch)

Dual credentials in Review Packager only:

| Token | Operations |
|-------|------------|
| `BUGBOT_USER_TOKEN` (`LINKTREND_BUGBOT_USER_TOKEN`) | Feature PR **create**; single `@cursor review` + SHA marker |
| GitHub App (`AUTOMATION_TOKEN`) | Everything else (reads, undraft, freeze, checks, merge, promote, repair, cleanup) |

Fail closed: `bugbot_user_credentials_blocked` when user token missing or equal to App/GITHUB_TOKEN.

## PR #30 disposition

Superseded: App-authored; cannot prove Bugbot. Closed with evidence preserved.
Recreate the docs-only smoke **after** this correction is on default `main`
(Codex verify → bootstrap promote). Do not merge #30.

## Bootstrap remaining (after Codex)

1. Promote this tip through development → staging → main (ordinary gates).
2. Packager smoke on main with Carlos-authored draft PR + Carlos `@cursor review`.
3. Confirm real `Cursor Bugbot` check; Integrator merge; staging promote.
4. Stop for Carlos Main Approve on the smoke tip (do not self-approve main).
