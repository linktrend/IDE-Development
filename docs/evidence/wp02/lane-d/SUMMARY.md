# WP02 Lane D — SUMMARY (live external GitHub-state readiness)

**Repo:** `linktrend/IDE-Development`
**Bound:** `2026-08-02T03:12:13Z` @ source SHA `9cd3fec75075c6910b5a3bbb09b582e4cb3c94e4`
**Tooling:** WP01 `89956878c54ff45e4aef1ff42883d209221b7a30` `external_state_audit.py` / `repository_protection.py` (extracted under `/tmp`)

## Readiness status

**NOT READY** (`verify` exit 3; `summary.ready=false`; 8/19 required checks unresolved).

## Apply decision

**`blocked`** — no live mutations. Ambient/keyring OAuth is insufficient for privileged settings writes; App installation probe is blocked; Bugbot Manual-Only left verification-only.

## What is already OK

- App ID variable present (numeric; value not echoed) + App private-key **secret name** listed
- Bugbot user-token **secret name** listed; default check name `Cursor Bugbot`
- `development-autonomous-merge` active with Bugbot + Verify + source-policy; classic development protection aligned
- `allow_auto_merge=true`
- Nine required GitOps workflows present and `active`; latest conclusions recorded for 8/9
- Process env: zero ambient privileged token values; automation resolver contract has **no `GITHUB_TOKEN` fallback**
- `Linktrend Review Ready` remains App-backed status context constant
- Audit/tooling apply surface refused (`exit 5`)

## Concrete blockers

1. **`github_app.installation=blocked`** — `GET …/installation` 401 (JWT); cannot prove App install with session OAuth.
2. **`github_app.authority_scope=unknown`** — permission matrix not observable without App-auth path.
3. **`protection.staging_ruleset=missing`** — no `staging-autonomous-promote` (classic also unprotected).
4. **`protection.main_ruleset=missing`** — no `main-autonomous-release` (classic also unprotected).
5. **`protection.promotion_source_policy=drift`** — source-policy required check missing on staging + main.
6. **`bugbot.manual_trigger_only=unknown`** — Cursor dashboard only; Manual-Only not API-provable here.
7. **`carlos.user_token_boundary=unknown`** — PAT allowlist (Packager PR + Bugbot mention only) not API-readable.
8. **`workflows.permissions_posture=unknown`** — workflow `permissions:` not exposed by Actions list API.
9. **Apply authority gap** — no GitHub App installation token in session; must not use keyring OAuth / ambient tokens / Carlos token for ruleset create.

## Planned (not applied)

Create staging + main managed rulesets (union-preserving; no Bugbot on promote branches); leave development + `allow_auto_merge` noop. Full plan: `before-after-plan.md`.

## Deliverables

1. `external-state-audit-live.json`
2. `before-after-plan.md`
3. `apply-decision.md`
4. `commands-and-results.md`
5. `SUMMARY.md` (this file)
