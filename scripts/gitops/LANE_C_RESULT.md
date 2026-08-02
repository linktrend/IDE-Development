# Lane C Result — External GitHub state plan/verify (WP1)

**Issue:** #67 Work Packet 1
**Lane:** C (external GitHub state plan and verification)
**Model:** cursor-grok-4.5-high
**Date:** 2026-08-02
**Scope:** Read-only plan/verify only. No commit/push/PR/Bugbot/review-ready/merge/promote. No credentials created or shown. No live GitHub setting changes. No apply executed.

---

## Deliverables (owned paths)

| Path | Action |
|------|--------|
| `scripts/gitops/external_state_audit.py` | Enhanced: `plan` / `verify` / `report`; expanded checklist; refuse `apply` |
| `scripts/gitops/external_state_plan.py` | NEW thin plan entrypoint |
| `scripts/gitops/external_state_verify.py` | NEW thin verify entrypoint |
| `scripts/gitops/repository_protection.py` | Enhanced: `FixtureClient(read_only=True)` refuses mutating ops |
| `core/managed-core/schemas/external-state-plan.schema.json` | NEW |
| `core/managed-core/schemas/external-state-verify.schema.json` | NEW |
| `core/managed-core/schemas/external-state-fixture.schema.json` | NEW |
| `scripts/tests/fixtures/external-state-wp1/**` | NEW fixture matrix + live summary |
| `scripts/tests/fixtures/repository-protection/read-only-plan/**` | NEW read-only plan fixture |
| `scripts/tests/test-external-state-wp1.sh` | NEW |
| `scripts/tests/test-external-state-audit.sh` | Updated for WP1 surface |
| `scripts/tests/test-repository-protection.sh` | Extended read-only assertion |

---

## Commands run

```bash
# Fixture matrix (WP1)
bash scripts/tests/test-external-state-wp1.sh

# Legacy audit contract suite (updated)
bash scripts/tests/test-external-state-audit.sh

# Protection suite (includes WP1 read_only)
bash scripts/tests/test-repository-protection.sh

# Apply refusal
python3 scripts/gitops/external_state_audit.py apply --repo linktrend/Fixture
# → exit 5, mutations=[]

# Matched plan/verify
python3 scripts/gitops/external_state_plan.py \
  --repo linktrend/Fixture \
  --fixture-dir scripts/tests/fixtures/external-state-wp1/matched
python3 scripts/gitops/external_state_verify.py \
  --repo linktrend/Fixture \
  --fixture-dir scripts/tests/fixtures/external-state-wp1/matched

# Optional live read-only plan (identifiers/settings posture/conclusions only)
python3 scripts/gitops/external_state_audit.py plan \
  --repo linktrend/IDE-Development --live --human
```

---

## Fixture matrix results

| Case | Fixture | Expected | Result |
|------|---------|----------|--------|
| matched | `external-state-wp1/matched` | verify exit 0, all ok/matched | PASS |
| drifted | `external-state-wp1/drifted` | verify exit 3 | PASS |
| forbidden | `external-state-wp1/forbidden` | authority/Carlos/workflow permissions `forbidden` | PASS |
| unavailable | `external-state-wp1/unavailable` | verify exit 4 | PASS |
| malformed | `external-state-wp1/malformed` | refuse exit 1 | PASS |
| credential-missing | `external-state-wp1/credential-missing` | `credential-missing` on secret names | PASS |
| dry-run | (no fixture) | unproven/unchecked; never ready | PASS |
| apply refused | CLI `apply` | exit 5 | PASS |
| protection read_only | `repository-protection/read-only-plan` | plan/verify ok; mutate exit 5 | PASS |

All three test scripts: **PASS**.

---

## Live read-only audit (`linktrend/IDE-Development`)

**Status:** Completed (read-only GETs). **NOT READY** — several items `unknown`/`blocked`/`missing` (never assumed compliant).
**Evidence:** `scripts/tests/fixtures/external-state-wp1/live-plan-summary.json` (posture only; no secret values).
**Mutations:** `[]`. **applyRefused:** `true`.

| Check | Live status |
|-------|-------------|
| `github_app.app_id_variable` | ok (numeric; value not echoed) |
| `github_app.private_key_secret` | ok (name present; value not read) |
| `github_app.installation` | **blocked** (installation API 401/JWT for this identity) |
| `github_app.authority_scope` | **unknown** (permission matrix not observable) |
| `bugbot.user_token_secret` | ok (name present) |
| `bugbot.manual_trigger_only` | **unknown** (Cursor dashboard not on GitHub API) |
| `bugbot.check_name` | ok (default `Cursor Bugbot`) |
| `carlos.user_token_boundary` | **unknown** (PAT scopes not readable via repo API) |
| `protection.development_ruleset` | ok |
| `protection.staging_ruleset` | **missing** |
| `protection.main_ruleset` | **missing** |
| `protection.promotion_source_policy` | **drift** (staging/main lack source-policy) |
| `protection.repo_specific_checks_preserved` | matched |
| `protection.allow_auto_merge` | ok (`true`) |
| `workflows.required_presence` | matched (9 workflows) |
| `workflows.enabled_state` | matched (active) |
| `workflows.permissions_posture` | **unknown** (list API lacks permissions map) |
| `workflows.latest_conclusions` | matched (recorded conclusions; no secrets) |
| `completion.status_context` | ok (`Linktrend Review Ready`) |

Embedded protection plan (read-only): `development:noop`, `staging:create`, `main:create` — verify not matched. **No apply performed.**

---

## Confirmation: no apply occurred

- `external_state_audit.py` / `plan` / `verify` always set `mutations=[]`, `dryRun=true`, `applyRefused=true`.
- CLI mode `apply` and `ReadOnlyGitHubClient.mutate` / `.apply` raise exit 5.
- `repository_protection.FixtureClient(read_only=True)` refuses create/update/delete/patch.
- Live session used GET-only `gh api --method GET` paths; no POST/PUT/PATCH/DELETE.
- No secrets, PEMs, or token values printed, stored, packaged, or hashed.

---

## Blockers / follow-ups (operator; out of Lane C apply scope)

1. Live installation probe blocked for current `gh` identity → needs App-aware or admin-capable read identity (still read-only).
2. Bugbot `manualTriggerOnly` and Carlos PAT boundary remain **unknown** without dashboard/fixture confirmation.
3. Staging/main managed rulesets are **missing** on `linktrend/IDE-Development` (plan shows create intent only; apply is a separate operator gate — not this packet).
4. Workflow permissions posture unknown from GitHub workflows list API alone.

Lane C implementation and fixture proof are complete; production readiness of live external state is **not** claimed.
