# Lane E disposition — Issue #72 (PLAN ONLY)

**Repo:** `linktrend/IDE-Development`
**Captured:** 2026-08-02T05:06:20Z
**Mode:** PLAN ONLY — `applyAuthorized: false`
**Prior plan:** `docs/archive/evidence/wp02/lane-c/cleanup-plan-post-wp03.md`
**Machine JSON:** `docs/evidence/issue-72/lane-e/disposition.json`

## Post-WP03 refresh

| Fact | Value |
|------|-------|
| Merged | #69 (WP02→development), #70 (dev→staging), #71 (staging→main) |
| `development` | `e6301fc920a4bf841f6bb4d27c15dc4e1f655ef2` |
| `staging` | `8ac0afdc55fe6762587c0226040300ac7cbc7dd6` |
| `main` | `0faed7420e314942d4d48222d39f2afb15d8e40a` |
| Equal tree | `43b1333ae21f43a34c3bdcccb2aac96f3d6e007f` |
| Preserve export | `preserveResolutionOk=true`; issues 43/44/51; PR 49 |

### What changed vs prior cleanup-plan

| Item | Prior (pre-WP03 plan) | Now (Lane E) |
|------|----------------------|--------------|
| WP03 apply window | Deferred until integration | Integration done; apply still blocked pending Codex+Principal |
| Promote leftovers | `promote/main/f7829…`, `promote/staging/991abc…` | **Same + NEW** `promote/main/8ac0afdc55fe`, `promote/staging/e6301fc920a4` |
| `issue/68-*` | KEEP active WP02 | PR #69 **MERGED**; WT still attached → KEEP-OPEN until Lisa remove |
| Issue #72 | N/A | **KEEP-ACTIVE** local branch+WT (not on origin) |
| Open PR set | #36/#37/#49/#52/#54/#56/#58/#60/#62/#65 | **Unchanged** |
| Historical WOULD_DELETE | GITOPS-01 / bugbot / lisa-option-a / old promotes | **Still present** |
| Remote dry-run | Assumed runnable | **EXIT 1** dirty caller checkout |

---

## DO-NOT-TOUCH (hard)

| Object | Why |
|--------|-----|
| **PR #36, #37, #49** | Principal preserve; #49 in `cleanup_preserve.defaults.json` |
| **Issue #72 branch + worktree** | Active work for this issue |
| **`main` / `staging` / `development`** | Protected permanent |
| **`stash@{0}`** | Must not drop/apply/modify |
| Credentials / Bugbot / rulesets / branch protection | Out of scope forever for this lane |

---

## A. Open PRs

| PR | Head tip | Class | Proposed action |
|----|----------|-------|-----------------|
| **#36** | `7eb41b2` CONFLICTING | **DO-NOT-TOUCH** | `none` |
| **#37** | `8ac8fb4` MERGEABLE | **DO-NOT-TOUCH** | `none` |
| **#49** | `0868c00` CONFLICTING | **DO-NOT-TOUCH** / KEEP-FROZEN | `none` |
| #52 | `ccdefcd` CONFLICTING | SUPERSEDED | `close-pr-after-codex-verify` |
| #54 | `1e8823b` CONFLICTING | SUPERSEDED | `close-pr-after-codex-verify` |
| #56 | `9120ecb` CONFLICTING | SUPERSEDED | `close-pr-after-codex-verify` |
| #58 | `c2a24e1` CONFLICTING | SUPERSEDED | `close-pr-after-codex-verify` |
| #60 | `1b828ca` CONFLICTING | SUPERSEDED | `close-pr-after-codex-verify` |
| #62 | `c596aac` CONFLICTING | SUPERSEDED | `close-pr-after-codex-verify` |
| #65 | `44a26f0` CONFLICTING | DEFER | `none` (WP01 ledger) |

---

## B. Remote branches — WOULD_DELETE-CANDIDATE (dry-run)

| Branch | Tip | Notes |
|--------|-----|-------|
| `issue/GITOPS-01-review-packager-pipeline` | `04904b7…` | Prior candidate; still MERGED evidence |
| `issue/ide-bugbot-integrator-merge-fix` | `e97e383…` | Prior candidate |
| `issue/ide-lisa-option-a-doctrine` | `689dd14…` | Prior candidate |
| `promote/main/f7829436751b` | `2a511a9…` | Prior leftover |
| `promote/staging/991abc319782` | `b867600…` | Prior leftover |
| **`promote/main/8ac0afdc55fe`** | `4e9770d…` | **NEW** post-#71 |
| **`promote/staging/e6301fc920a4`** | `d8ec514…` | **NEW** post-#70 |

**DEFER (unchanged):** `issue/cleanup-orchestrator-ship-hour-labels`, `issue/ide-lisa-ship05-digest-830` (head mismatch), `issue/ide-pull-wave-test`, `codex-rollout`, `cursor/*`, `dev/minicursor/*`.

**KEEP (open PR / preserve / WT):** all `issue/{23,28,43,44,51,53,55,57,59,61,63,64,66,67,68}-*` as inventoried in JSON.

---

## C. Worktrees (Lisa-local only)

| Worktree | Class | Notes |
|----------|-------|-------|
| `…/issue-72-…` | **KEEP-ACTIVE** | This session — do not remove |
| `…/issue-43-…` @ `0868c00` | KEEP-FROZEN | PR #49 |
| `…/issue-44-…`, `…/issue-51-…` | KEEP-FROZEN | preserve defaults |
| `…/issue-{28,53,55,57,59,61,64,66,67}-…` | KEEP-OPEN | Open PR or active packet |
| `…/issue-63-…`, `…/issue-68-…` | KEEP-OPEN → later remove | Content superseded; WT blocks remote delete |
| `/private/tmp/issue-23-…` | KEEP-OPEN (prunable metadata) | Do not prune while #36 open |
| Primary `/Users/…/IDE Development` on `main` | DO-NOT-TOUCH | |

---

## D. Stash

| Entry | Class | Action |
|-------|-------|--------|
| `stash@{0}` on `issue/ide-pull-wave-test` | **DO-NOT-TOUCH** | Inventory only — never drop/apply/modify |

---

## E. Repair records (dry-run)

`cleanup_stale_records.py`: KEEP #50 (PR49/issue43), #46 (issue44), #40 (PR36). Candidates empty. GitHub close deferred.

---

## F. Later apply command sequence (commented / dry-run first)

```bash
# === BLOCKERS: Codex verify + Principal OK; clean caller checkout; applyAuthorized ===
# Never run --apply from dirty issue/72 worktree.

# 0) Confirm preserve
# python3 scripts/gitops/cleanup_controls.py export-preserve --repo linktrend/IDE-Development

# 1) Remote dry-run (must EXIT 0 and print expected WOULD_DELETE set)
# bash scripts/cleanup-merged-branches.sh --remote --repo linktrend/IDE-Development

# 2) Tip re-verify for each candidate (example)
# git ls-remote origin refs/heads/promote/main/8ac0afdc55fe
# git ls-remote origin refs/heads/promote/staging/e6301fc920a4
# git ls-remote origin refs/heads/issue/GITOPS-01-review-packager-pipeline
# git ls-remote origin refs/heads/issue/ide-bugbot-integrator-merge-fix
# git ls-remote origin refs/heads/issue/ide-lisa-option-a-doctrine
# git ls-remote origin refs/heads/promote/main/f7829436751b
# git ls-remote origin refs/heads/promote/staging/991abc319782

# 3) ONLY after Codex+Principal — remote apply (still exact tip match + no WT + preserve OK)
# bash scripts/cleanup-merged-branches.sh --remote --repo linktrend/IDE-Development --apply

# 4) Lisa-local dry-run then apply (never from GitHub Actions)
# bash scripts/cleanup-merged-branches.sh --local --repo linktrend/IDE-Development
# bash scripts/cleanup-merged-branches.sh --local --repo linktrend/IDE-Development --apply

# 5) Superseded PR closes (manual / Principal) — NEVER #36/#37/#49
# # gh pr close 52 --repo linktrend/IDE-Development --comment "Superseded by WP03 #69; Codex-verified"
# # … similarly 54 56 58 60 62 after ledger proof

# 6) Stash — DO NOT TOUCH
# # git stash drop   # FORBIDDEN
```

## Apply blockers (always)

1. Awaits **Codex verify + Principal** authorization
2. `applyAuthorized: false` on every object in this plan
3. Remote dry-run **EXIT 1** until caller checkout is clean
4. Do not close/delete while open-PR / preserve / active-WT / Issue #72 constraints hold
