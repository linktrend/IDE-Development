# WP02 Lane F — SECURITY/GITOPS Review (#2)

| Field | Value |
|-------|-------|
| **Verdict** | **PASS** |
| **Reviewer** | WP02 Lane F reviewer #2 (SECURITY/GITOPS) |
| **Model** | cursor-grok-4.5-high |
| **Worktree** | `…/issue-68-work-packet-02-integration-lineage-stale-cleanup` |
| **Tip audited** | `3c21bb8493a795aa6e46e0eb8a31b2fcd6c15a96` (verified `git rev-parse HEAD`) |
| **Scope** | Read-only audit of cleanup fail-closed behavior, credential provenance, GitHub App authority, zero unauthorized mutation |
| **Write surface** | This file only (`docs/evidence/wp02/lane-f/security-gitops-review.md`) |
| **Commit/push** | None |

## Sources reviewed

| Source | Role |
|--------|------|
| `docs/evidence/wp02/lane-c/SUMMARY.md` | Cleanup hardening posture / non-actions |
| `docs/evidence/wp02/lane-c/cleanup-plan-post-wp03.md` | Plan-only WP03 apply sequence |
| `docs/evidence/wp02/lane-d/SUMMARY.md` | Live external-state readiness |
| `docs/evidence/wp02/lane-d/apply-decision.md` | Apply blocked decision matrix |
| `docs/evidence/wp02/lane-d/external-state-audit-live.json` | Machine evidence (mutations, auth probe, secret names) |
| `docs/evidence/wp02/lane-d/commands-and-results.md` | Command transcript / apply refused |
| `scripts/gitops/cleanup_controls.py` | Preserve export + repo resolution fail-closed |
| `scripts/cleanup-merged-branches.sh` | Delete gates (dry-run default) |
| `docs/contracts/STALE-CLEANUP-CONTROLS.md` | Cleanup authority contract |
| `docs/contracts/GITHUB-APP-GITOPS-CREDENTIALS.md` | App token / no ambient fallback |
| `docs/contracts/EXTERNAL-STATE-AUDIT.md` | Audit/apply boundary |

---

## Checklist confirmation

| Requirement | Result | Evidence |
|-------------|--------|----------|
| No cleanup apply in WP02 | **PASS** | Lane C: PLAN ONLY / B3 / Non-actions (no live branch/worktree/PR deletion). Plan file comments `--apply` only for post-WP03 + Principal auth. |
| Lane D apply blocked without ambient-token fallback | **PASS** | `apply-decision.md` → `blocked`. `external-state-audit-live.json`: `mutations: []`, `applyRefused: true`, ambient process tokens all `absent`, `automationTokenContract.ambientFallback` = none / no `GITHUB_TOKEN` fallback. `apply` exit 5. Keyring OAuth noted as **forbidden** for privileged writes. |
| Preserve open **and** closed PR heads | **PASS** | `cleanup_controls._pr_head_ref` / `export_preserve_for_shell`: heads for OPEN, CLOSED, or MERGED. Shell: OPEN evidence → KEEP; preserve unresolved → KEEP all candidates. |
| No delete-by-name-alone | **PASS** | `maybe_delete_remote`/`local` require: candidate form + not protected + not preserve + preserveResolutionOk + MERGED/ABANDONED evidence (CLOSED without abandoned ≠ delete) + tip mismatch KEEP when both OIDs present + no worktree + not caller checkout. `NONE` / empty `CLEANUP_REPO` → no implicit `gh` delete path. |
| Secrets not exposed in evidence | **PASS** | Lane D: secret **names** only; APP_ID “numeric; value not echoed”; no `ghp_/gho_/ghs_/github_pat_/PEM` in `lane-d/**` primary evidence. Ambient token values absent. Synthetic `ghs_*` strings appear only inside Lane C **proposed test fixtures** asserting tokens must not print — not live credentials. |
| GitHub App authority for privileged mutation | **PASS (fail-closed)** | Installation probe `GET …/installation` → 401 JWT; `github_app.installation=blocked`; `authority_scope=unknown`. Session correctly refused App-unproven apply. |
| Zero unauthorized mutation | **PASS** | Lane D: `mutations: []` on report/verify/plan; protection apply not invoked; Bugbot Manual-Only left verification-only. Lane C: inventory/plan only. |

---

## Concrete findings

### F1 — PASS: WP02 performed no cleanup apply

Lane C documents status **PLAN ONLY**, blocker B3 (“No live apply allowed in WP02”), and explicit non-actions: no live branch/worktree/PR deletion. `cleanup-plan-post-wp03.md` defers apply to WP03 after Principal authorization and exact tip verification; suggested `--apply` lines remain commented.

### F2 — PASS: Lane D external-state apply blocked; no ambient fallback

Decision matrix criterion (b) **FAIL** on App path → overall apply **`blocked`**. Observed:

- Process env: `GH_TOKEN`, `GITHUB_TOKEN`, `LINKTREND_GITOPS_APP_PRIVATE_KEY`, `LINKTREND_BUGBOT_USER_TOKEN`, `LINKTREND_APP_TOKEN`, `AUTOMATION_TOKEN`, `BUGBOT_USER_TOKEN` all **absent**.
- `gh` identity: keyring OAuth user `linktrend` with broad scopes — documented as **not** an App installation token and **must not** be used for privileged settings writes.
- Tooling: `external_state_audit.py apply` **refused** (exit 5); repository protection apply not called.
- Contract alignment: `GITHUB-APP-GITOPS-CREDENTIALS.md` / `resolve_automation_token.sh` — no silent `GITHUB_TOKEN` autonomy fallback.

This is correct fail-closed behavior under `EXTERNAL-STATE-AUDIT.md` (WP02 may apply only via authorized App path + rollback; unproven → do not mutate).

### F3 — PASS: Preserve OPEN/CLOSED heads; OPEN wins; no name-only delete

Spot-check of tip scripts vs `STALE-CLEANUP-CONTROLS.md`:

1. **Repo resolution fail-closed** (`resolve_cleanup_repo`): invalid/empty explicit `--repo` → fail; ambiguous `origin`+`upstream` without authoritative CLI/env → `preserveResolutionOk=false` / unresolved PR numbers → shell KEEP (no `WOULD_DELETE`/`DELETED`).
2. **PR evidence scoped** (`gh pr list --repo CLEANUP_REPO`); empty `CLEANUP_REPO` returns `NONE` without implicit context.
3. **Preserve PR heads** include CLOSED (and OPEN/MERGED) via export-preserve; unresolved preserve PRs block deletes.
4. **OPEN evidence** short-circuits to KEEP before any delete eligibility.
5. **CLOSED without `abandoned` label** is not delete evidence (only MERGED / abandoned CLOSED).
6. **Dry-run default**; `--apply` only after gates; `--apply` deletes branches only — never closes PRs/issues (matches contract + Lane C plan: do not auto-close #36/#37/#49).

### F4 — PASS: Credential provenance / secret hygiene in evidence

`external-state-audit-live.json` binding records:

- `actionsInventory.secretNamesOnly`: `LINKTREND_BUGBOT_USER_TOKEN`, `LINKTREND_GITOPS_APP_PRIVATE_KEY`
- Variable names listed; APP_ID value intentionally not echoed
- `authProbe` documents absence of ambient privileged token **values**
- `mutations: []`, `dryRun: true`, `applyRefused: true`

No real PAT/PEM material found under `docs/evidence/wp02/lane-d/**`.

### F5 — ADVISORY (non-blocking): tip-SHA gate soft when OID empty

`cleanup-merged-branches.sh` tip check:

```bash
if [ -n "$head_oid" ] && [ -n "$tip" ] && [ "$head_oid" != "$tip" ]; then
  KEEP  # mismatch only
fi
```

If `headRefOid` **or** branch tip is empty, the exact-SHA gate does not KEEP — a candidate with MERGED/ABANDONED evidence could still reach `WOULD_DELETE_*` / `--apply` DELETE. Contract text requires “Exact tip SHA match (no guessing on moved tips).”

**Impact on this review:** does **not** flip WP02 to FAIL — WP02 did not apply cleanup, and other fail-closed gates (repo scope, preserve resolution, OPEN, evidence class) still hold. **Remediation for WP03:** fail closed (KEEP) when either OID is empty before authorizing delete.

---

## Residual risks (informational; not WP02 FAIL)

1. External state remains **NOT READY** (`ready=false`; staging/main rulesets missing; App install/authority unproven via this session). Correct response was block-apply, not invent readiness.
2. Session OAuth scopes (`admin:repo_hook`, `repo`, `workflow`) are capable of privileged writes; operators must continue to treat keyring OAuth as read-only for WP02/WP03 protection apply.
3. Lane C proposed tree is evidence-only until lead integrates; coexistence tests not executed on this HEAD (blocker B1) — out of scope for mutation safety of WP02 itself.

---

## Verdict rationale

All mandatory confirmations for this SECURITY/GITOPS lane pass: **no WP02 cleanup apply**, **Lane D apply blocked without ambient-token fallback**, **OPEN/CLOSED preserve + evidence-based delete gates**, **no secret values in primary evidence**, and **zero unauthorized GitHub mutations** in Lane C/D packets. One advisory hardening gap (empty tip/OID soft gate) is recorded for WP03; it does not constitute unauthorized WP02 mutation.

**PASS**
