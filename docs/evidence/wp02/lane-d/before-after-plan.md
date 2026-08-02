# WP02 Lane D — Before/After Plan (deterministic, union-preserving)

**Captured:** 2026-08-02T03:12:13Z
**Repo:** `linktrend/IDE-Development`
**Source SHA (WP02 worktree HEAD):** `9cd3fec75075c6910b5a3bbb09b582e4cb3c94e4`
**Audit tooling SHA (WP01 tip):** `89956878c54ff45e4aef1ff42883d209221b7a30`
**Live audit:** read-only (`external_state_audit.py report|plan|verify --live`)
**Mutations in this lane:** none
**Apply:** blocked (see `apply-decision.md`)

Contracts referenced (WP01 tip via `git show`):
`EXTERNAL-STATE-AUDIT.md`, `GITHUB-APP-GITOPS-CREDENTIALS.md`, `BUGBOT-MENTION-ONLY.md`, `REPOSITORY-PROTECTION.md`.

Rollback / before refs:
- Packet before-state: `docs/evidence/wp02/before-state-2026-08-02T030943Z/`
- Live protection rollback snapshot: `docs/evidence/wp02/lane-d/notes/repository-protection-plan-live.redacted.json` → `rollback.snapshot`

---

## Authority / credential posture (before → desired)

| Surface | Before (live observed) | Desired after | Planned action |
|--------|-------------------------|---------------|----------------|
| `LINKTREND_GITOPS_APP_ID` variable | present, numeric (value not echoed) | present, numeric | **noop** |
| `LINKTREND_GITOPS_APP_PRIVATE_KEY` secret **name** | listed | listed | **noop** (never read/rotate here) |
| GitHub App installation on repo | **blocked** (`GET …/installation` → 401 JWT decode; user OAuth cannot prove install) | installation present + non-secret authority metadata readable via App JWT path | **observe / BLOCKER** — no ambient-token mutation |
| App permission matrix | **unknown** | narrowly scoped; privileged automation App-backed only | **observe / BLOCKER** until App-auth GET available |
| Privileged automation token provenance | contract: `resolve_automation_token.sh` fail-closed; **no `GITHUB_TOKEN` fallback**; process env ambient secrets **absent** | `AUTOMATION_TOKEN_SOURCE=github_app` only | **noop** for settings; enforce via workflow path |
| Session `gh` identity | keyring OAuth `linktrend` scopes `admin:repo_hook,gist,read:org,repo,workflow` | not an authorized mutation credential | **do not use for apply** |
| `LINKTREND_BUGBOT_USER_TOKEN` secret **name** | listed | listed | **noop** |
| Carlos restricted user-token boundary | **unknown** via API | allowed: Packager feature-PR create + Bugbot `@cursor review` comment only; forbidden: status publish / merge / promote / repair / admin / secrets | **observe / operator confirm** |
| Bugbot `manualTriggerOnly` | **unknown** (Cursor dashboard; not GitHub API) | `manualTriggerOnly=true` (mention-only / Manual-Only) | **verification-only**; no change without approved non-exposure route |
| Bugbot check name | default `Cursor Bugbot` | `Cursor Bugbot` | **noop** |
| Status context | `Linktrend Review Ready` | App-backed publisher only | **noop** |

---

## Repository protections (union-preserving)

Mechanism capability: **rulesets** available.

### `development` — ruleset `development-autonomous-merge`

| Field | Before | After (desired) | Action |
|------|--------|-----------------|--------|
| Exists / id | yes / `19728531` | unchanged | **noop** |
| Enforcement | `active` | `active` | noop |
| Required checks | `Cursor Bugbot`, `Verify IDE Development`, `Enforce allowed PR source branches` | same managed baseline; `preserved=[]` | noop |
| Non-check rules | `required_status_checks` only observed | preserve all non-check rules if later present | preserve |
| Bypass actors | `[]` | preserve | preserve |

**Also present (classic branch protection):** required checks match the same three contexts. Any future apply **must preserve** classic unrelated fields (`required_pull_request_reviews`, restrictions, force-push flags, etc.) and must not wipe classic protection solely because rulesets are preferred.

### `staging` — ruleset `staging-autonomous-promote`

| Field | Before | After (desired) | Action |
|------|--------|-----------------|--------|
| Ruleset | **missing** | create active ruleset targeting `refs/heads/staging` | **create** (blocked until App-authorized apply) |
| Classic protection | **not protected** (404) | not required if ruleset created; do not invent classic wipe | create ruleset preferred |
| Required checks | none | `Verify IDE Development`, `Enforce allowed PR source branches` (**no** `Cursor Bugbot`) | create |
| Unrelated rules | n/a | none to preserve yet | — |

### `main` — ruleset `main-autonomous-release`

| Field | Before | After (desired) | Action |
|------|--------|-----------------|--------|
| Ruleset | **missing** | create active ruleset targeting `refs/heads/main` | **create** (blocked until App-authorized apply) |
| Classic protection | **not protected** (404) | ruleset preferred | create |
| Required checks | none | `Verify IDE Development`, `Enforce allowed PR source branches` (**no** `Cursor Bugbot`) | create |
| Main Approve compatibility | — | do not invent extra human-review rules conflicting with Lisa Main Approve; preserve bypass actors on update | preserve policy |

### Repo setting

| Setting | Before | After | Action |
|---------|--------|-------|--------|
| `allow_auto_merge` | `true` | `true` | **noop** |

### Source-policy coverage

| Branch | `Enforce allowed PR source branches` required? | Before | Desired |
|--------|-----------------------------------------------|--------|---------|
| development | yes | yes (ruleset + classic) | keep |
| staging | yes | **missing** | add via staging ruleset |
| main | yes | **missing** | add via main ruleset |

**Preservation rule:** union managed baselines with any future repo-specific required checks; never delete unrelated ruleset rule types or classic review/restriction fields.

---

## Required workflows / variables

### Variables (names)

Observed: `LINKTREND_BUGBOT_REVIEW_COMMAND`, `LINKTREND_GITOPS_APP_ID`, `LINKTREND_INTEGRATOR_REQUIRED_CHECKS` → **noop**.

### Secrets (names only)

Observed: `LINKTREND_BUGBOT_USER_TOKEN`, `LINKTREND_GITOPS_APP_PRIVATE_KEY` → **noop** (no create/rotate/read).

### Workflows (all `state=active`)

| Workflow file | Latest conclusion (id/status only) | Action |
|---------------|------------------------------------|--------|
| `branch-source-policy.yml` | success (`30691192168`) | noop |
| `ci.yml` | success (`30691192240`) | noop |
| `linktrend-review-ready-publisher.yml` | success (`30688136681`) | noop |
| `linktrend-review-packager.yml` | skipped (`30691214552`) | noop |
| `linktrend-integrator-merge.yml` | skipped (`30691214539`) | noop |
| `linktrend-development-to-staging.yml` | skipped (`30691214550`) | noop |
| `linktrend-staging-to-main.yml` | skipped (`30691214537`) | noop |
| `linktrend-repair-observer.yml` | skipped (`30691214513`) | noop |
| `linktrend-cleanup-merged.yml` | no runs recorded (`unknown`) | noop / observe |

Workflow YAML `permissions:` posture: **unknown** via Actions list API → record only; do not mutate workflow files in this lane.

---

## Planned mutation set (authorized apply only — currently blocked)

If and only if Principal authorizes **and** all of (a)(b)(c) hold:

1. Create ruleset `staging-autonomous-promote` with managed staging checks (union-preserving).
2. Create ruleset `main-autonomous-release` with managed main checks (union-preserving).
3. Leave `development-autonomous-merge` and `allow_auto_merge` untouched (noop).
4. Do **not** change Bugbot dashboard / Manual-Only unless a separate approved non-credential-exposure route exists.
5. Do **not** use Carlos restricted user token, ambient `GH_TOKEN`/`GITHUB_TOKEN`, or keyring OAuth for these writes.

**Restorable before-state:** live `rollback.snapshot` in `notes/repository-protection-plan-live.redacted.json` (development ruleset body + `allow_auto_merge=true`; staging/main `exists=false`).

---

## Explicit non-goals

- No consumer repository changes
- No PR/issue/branch/worktree mutations
- No review-ready / Packager / Bugbot trigger / promote
- No secret value retrieval or printing
