# WP02 Lane D — Apply Decision

**Decision:** `blocked`  
**Captured:** 2026-08-02T03:12:13Z  
**Repo:** `linktrend/IDE-Development`  
**Source SHA:** `9cd3fec75075c6910b5a3bbb09b582e4cb3c94e4`

## Verdict

Live APPLY was **not** executed. External settings were left unchanged. Deterministic create plan exists for missing `staging` / `main` rulesets, but authorization gates failed closed.

## Decision matrix

| Criterion | Required | Observed | Pass? |
|-----------|----------|----------|-------|
| (a) Change within approved repository standard/contracts | Staging/main rulesets + source-policy required by `REPOSITORY-PROTECTION.md` / external-state checklist | Drift confirmed: staging/main rulesets **missing**; development already matched | Partial (plan valid; apply not unlocked solely by drift) |
| (b) Authorized GitHub App path only (not ambient `GH_TOKEN`/`GITHUB_TOKEN`, not Carlos restricted user token, not keyring OAuth admin) | Minted App installation token / App JWT for privileged writes | Process env ambient tokens **absent**; `gh` uses keyring OAuth `linktrend` with broad scopes; `GET …/installation` → **401** JWT decode; org/user installation list unavailable to this identity | **FAIL** |
| (c) Restorable before-state snapshot exists | Snapshot before mutate | Packet snapshot `before-state-2026-08-02T030943Z/` exists; live protection `rollback.snapshot` captured under `lane-d/notes/` | Pass for planned protection creates |
| Tooling apply surface | Explicit apply only | `external_state_audit.py apply` **refused** (exit 5); repository protection apply not invoked | Pass (refused) |
| Bugbot Manual-Only | Verification-only unless approved route without credential exposure | `manualTriggerOnly` **unknown** via GitHub API; no approved Cursor dashboard mutation route demonstrated | Pass (no change attempted) |
| Zero ambient-token fallback for privileged mutations | Fail closed | `resolve_automation_token.sh` contract: no `GITHUB_TOKEN` fallback; session did not mint App token | Pass (no privileged mutation attempted) |

## Concrete blockers preventing apply

1. **App installation / authority unproven:** installation probe blocked (401 JWT). Cannot prove App install or permission matrix via authorized App path from this session.  
2. **No App-backed mutation credential available:** only readable path is ambient `gh` keyring OAuth — forbidden for privileged settings writes under WP02 / credential contracts.  
3. **Must not fall back** to ambient `GH_TOKEN`/`GITHUB_TOKEN` or Carlos `LINKTREND_BUGBOT_USER_TOKEN` for ruleset create.  
4. **Bugbot Manual-Only** remains operator-confirm only; no apply route demonstrated without credential exposure.  
5. **Carlos user-token boundary** remains API-unreadable (`unknown`); not used for apply.

## What would unlock apply later (operator / Principal)

1. Mint GitHub App installation token via approved workflow/`actions/create-github-app-token` using `LINKTREND_GITOPS_APP_ID` + `LINKTREND_GITOPS_APP_PRIVATE_KEY` (values never printed).  
2. Re-run live verify with App JWT so `github_app.installation` and authority metadata become observable.  
3. Confirm Bugbot Manual-Only in Cursor dashboard (evidence note only).  
4. Confirm Carlos PAT scope boundary matches Packager PR + Bugbot mention only.  
5. Explicit Principal/lead authorization to run `manage-repository-protections.sh apply --apply` (or equivalent) **with App token**, using the captured rollback snapshot.  
6. Post-apply `verify` must pass; rollback available from snapshot.

## Mutations performed this lane

**None.** `mutations: []` on all audit modes; protection apply not called.
