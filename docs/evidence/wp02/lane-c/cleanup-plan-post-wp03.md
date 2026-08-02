# Cleanup plan (post-WP03 only) — no apply in WP02

**Status:** PLAN ONLY  
**Lane:** C  
**Captured context:** 2026-08-02 (before-state + live `gh`/`worktree`/`ls-remote` read)  
**Repo:** `linktrend/IDE-Development`  
**Authority:** Execute only after WP03 integrates the canonical lineage into `development`; never during WP02.

## Hard rules (carry into WP03 apply)

1. Default dry-run. Apply only with explicit Principal/Codex authorization and exact evidence.
2. Pass `--repo linktrend/IDE-Development` on every cleanup invocation (Issue #63).
3. Never delete by branch name alone; require MERGED/abandoned evidence + tip SHA match + no OPEN PR + no attached worktree + preserveResolutionOk.
4. Never close open PRs automatically (including #36, #37, #49).
5. Never remove local worktrees from GitHub Actions; Lisa-local only per `LISA-LOCAL-CLEANUP-HANDOFF.md`.
6. Preserve permanent branches: `main`, `staging`, `development`.
7. Preserve list from `cleanup_preserve.defaults.json` until Principal removes entries: issues **43, 44, 51**; PR **49**.

## Disposition classes

| Class | Meaning | WP03 action |
|-------|---------|-------------|
| **KEEP-FROZEN** | Frozen reviewed head / active preserve | Do not delete branch; do not close PR; do not remove worktree |
| **KEEP-OPEN** | Open PR and/or active worktree | Keep until PR closes / worktree removed deliberately |
| **SUPERSEDED-AFTER-WP03** | Content represented in canonical lineage; PR/branch only historical | After WP03 merge to `development`, dry-run then optional remote delete if gates pass; close PR only with Principal decision |
| **WOULD_DELETE-CANDIDATE** | Contract snapshot / merged promote leftovers | Dry-run first; apply remote delete only if exact tip match + no worktree |
| **DEFER** | Needs Principal/Codex judgment | Inventory only |

---

## A. Open PRs (do not auto-close)

| PR | Head branch | Class | Notes |
|----|-------------|-------|-------|
| **#49** | `issue/43-build-portable-ide-development-v2-managed-core-i` @ `0868c00` | **KEEP-FROZEN** | Frozen portable lineage; preservePrNumbers=[49]; never alter head |
| **#36** | `issue/23-gitops-lifecycle-repair-control` | **KEEP-OPEN** / **DEFER** | Conflicting; open-PR no abandoned label → no auto-close |
| **#37** | `issue/28-gitops-bootstrap-activation-smoke-record-issue-2` | **KEEP-OPEN** / **DEFER** | Same |
| **#52** | `issue/51-reconcile-approved-stale-ide-development-prs-wor` | **SUPERSEDED-AFTER-WP03** | Cleanup lineage tip absorbed via `5cf0991`; close PR after WP03 only if ledger proves equivalence |
| **#54** | `issue/53-repair-bugbot-findings-on-stale-cleanup-controls` | **SUPERSEDED-AFTER-WP03** | Ancestor of cleanup tip |
| **#56** | `issue/55-repair-remaining-bugbot-cleanup-policy-parity-fi` | **SUPERSEDED-AFTER-WP03** | Ancestor of cleanup tip |
| **#58** | `issue/57-repair-bugbot-fail-closed-preservation-when-pres` | **SUPERSEDED-AFTER-WP03** | Ancestor of cleanup tip |
| **#60** | `issue/59-repair-bugbot-ambiguous-remote-fail-closed-prese` | **SUPERSEDED-AFTER-WP03** | Ancestor of cleanup tip |
| **#62** | `issue/61-repair-bugbot-repository-scoped-pr-evidence-for` | **SUPERSEDED-AFTER-WP03** | Ancestor of cleanup tip |
| **#65** | `issue/64-production-hardening-portable-installer-safety-m` | **DEFER** | WP01-adjacent; Lane A ledger decides keep vs superseded |

**WP03 PR procedure:** inventory with `gh pr list --repo linktrend/IDE-Development --state open`; close superseded review PRs only after ledger proof + Principal OK; never close #36/#37/#49 in the automated cleanup path.

---

## B. Remote branches

### B1. Preserve / active (KEEP)

| Branch | Class | Reason |
|--------|-------|--------|
| `issue/43-*` | KEEP-FROZEN | Preserve issue 43 + PR #49 |
| `issue/44-*` | KEEP | Preserve issue 44 + worktree |
| `issue/51-*` … `issue/63-*` | KEEP until superseded closed | Cleanup lineage owners; tip `issue/63-*` @ `5cf0991` |
| `issue/67-*` | KEEP until WP01 integrated & ledger OK | WP01 checkpoint |
| `issue/68-*` | KEEP | Current WP02 work branch |
| `main` / `staging` / `development` | KEEP | Protected |

### B2. Historical merged candidates (from STALE contract snapshot — re-verify)

Still present on origin at plan time:

| Branch | Class | Proposed WP03 step |
|--------|-------|--------------------|
| `issue/GITOPS-01-review-packager-pipeline` | WOULD_DELETE-CANDIDATE | Dry-run `--remote --repo linktrend/IDE-Development`; apply only if MERGED + tip match + no WT |
| `issue/ide-bugbot-integrator-merge-fix` | WOULD_DELETE-CANDIDATE | Same |
| `issue/ide-lisa-option-a-doctrine` | WOULD_DELETE-CANDIDATE | Same |
| `promote/main/f7829436751b` | WOULD_DELETE-CANDIDATE | Same (promote leftover) |
| `promote/staging/991abc319782` | WOULD_DELETE-CANDIDATE | Same |
| `issue/cleanup-orchestrator-ship-hour-labels` | DEFER | Re-classify via Lane A ledger |
| `issue/ide-lisa-ship05-digest-830` | DEFER | Same |
| `issue/ide-pull-wave-test` | DEFER | Same |

### B3. Issue branches with open PRs

All `issue/{23,28,43,51,53,55,57,59,61,64,…}` heads backing open PRs → **KEEP-OPEN** until PR disposition completes. Cleanup must not delete while OPEN evidence exists.

---

## C. Local worktrees (Lisa-only)

Observed attached worktrees (operator Mini) — **KEEP** while attached:

| Worktree path (abbrev) | Branch | Class |
|------------------------|--------|-------|
| `…/issue-23-…` (prunable) | `issue/23-…` | KEEP-OPEN; prune only if `git worktree prune` safe after branch gone |
| `…/issue-28-…` | `issue/28-…` | KEEP-OPEN |
| `…/issue-43-…` @ `0868c00` | `issue/43-…` | KEEP-FROZEN |
| `…/issue-44-…` | `issue/44-…` | KEEP (preserve) |
| `…/issue-51` … `issue-63` | cleanup chain | KEEP until superseded PRs closed + no ownership |
| `…/issue-64` / `issue-66` / `issue-67` | portable hardening / WP01 | KEEP until ledger says removable |
| `…/issue-68-…` | WP02 | KEEP (active) |

**WP03 local apply:** Lisa runs `cleanup-merged-branches.sh --local --repo linktrend/IDE-Development` dry-run first. Never `git worktree remove` for dirty/active agent checkouts. After remote branch delete + PR close, prune prunable worktrees deliberately.

---

## D. Repair inventory (dry-run only)

Re-run:

```bash
python3 scripts/gitops/cleanup_stale_records.py --repo linktrend/IDE-Development --json
LINKTREND_REPAIR_BACKEND=file python3 scripts/gitops/repair_task.py plan-cleanup-completed --repo linktrend/IDE-Development
```

Contract snapshot KEEP: repair #46 (usage_limit / issue 44), #40 (PR #36 open), #50 (PR #49 / issue 43).  
Live GitHub issue close remains deferred (`--apply --i-understand-close-repairs` refused).

---

## E. Suggested WP03 command sequence (still dry-run first)

```bash
# 1) Preserve export must succeed
python3 scripts/gitops/cleanup_controls.py export-preserve --repo linktrend/IDE-Development

# 2) Remote dry-run
bash scripts/cleanup-merged-branches.sh --remote --repo linktrend/IDE-Development

# 3) Local dry-run (Lisa Mini only)
bash scripts/cleanup-merged-branches.sh --local --repo linktrend/IDE-Development

# 4) Only after Principal authorization + exact tip verification:
# bash scripts/cleanup-merged-branches.sh --remote --repo linktrend/IDE-Development --apply
# (local --apply separately, Lisa-only)
```

## Explicit non-goals for this plan file

- No WP02 deletions, PR closes, or worktree removals  
- No consumer-repo cleanup  
- No credential / protection changes
