# Lane E commands and results — Issue #72 (read-only)

**Repo:** `linktrend/IDE-Development`
**Worktree:** `…/issue-72-pre-launch-ide-development-codebase-cleanup-arch`
**Branch:** `issue/72-pre-launch-ide-development-codebase-cleanup-arch` @ `e6301fc920a4bf841f6bb4d27c15dc4e1f655ef2`
**Captured:** 2026-08-02T05:06:20Z
**Secrets:** none captured (no tokens printed)

All commands below are inventory / dry-run only. No `--apply`, no PR/issue close, no branch delete, no worktree remove, no stash modify, no push/commit.

---

## 1. Caller identity

```bash
pwd && git rev-parse --abbrev-ref HEAD && git rev-parse HEAD && git status -sb
```

**EXIT:** 0

**Key output:**
- cwd = issue-72 worktree
- branch = `issue/72-pre-launch-ide-development-codebase-cleanup-arch`
- HEAD = `e6301fc920a4bf841f6bb4d27c15dc4e1f655ef2`
- dirty: `M README.md`; untracked `docs/CURRENT-STATUS.md`, `docs/evidence/issue-72/`, `docs/work-packets/2026-08-02-work-packet-04-consumer-rollout.md`

---

## 2. Open PRs

```bash
gh pr list --repo linktrend/IDE-Development --state open --limit 100 --json number,title,headRefName,headRefOid,baseRefName,isDraft,mergeable,url
```

**EXIT:** 0

**Key output:** open PRs **#65, #62, #60, #58, #56, #54, #52, #49, #37, #36** (10 total).

---

## 3. Recently merged PRs

```bash
gh pr list --repo linktrend/IDE-Development --state merged --limit 30 --json number,title,headRefName,mergedAt,mergeCommit
```

**EXIT:** 0

**Key output (WP03):**
- #69 merged → `e6301fc…` (issue/68)
- #70 merged → `8ac0afdc…` (promote/staging/e6301fc920a4)
- #71 merged → `0faed742…` (promote/main/8ac0afdc55fe)

---

## 4. Open issues

```bash
gh issue list --repo linktrend/IDE-Development --state open --limit 100 --json number,title,labels,state,updatedAt
```

**EXIT:** 0

**Key output:** open includes **#72** (active), #68, #67, #66, #64, #63…#51, repairs #50/#46/#40, #44/#43, #35/#31/#28/#23.

---

## 5. Worktrees / stash / local branches

```bash
git worktree list -v
git stash list
git branch -vv
```

**EXIT:** 0 (each)

**Key output:**
- 17 worktrees listed including issue-72 (active) and prunable `/private/tmp/issue-23-…`
- `stash@{0}`: On `issue/ide-pull-wave-test` (Cursor cloud-agent move) — **not modified**
- Local `issue/72-…` tracks `origin/development`; no remote `issue/72-*`

---

## 6. Remote heads

```bash
git ls-remote --heads origin
```

**EXIT:** 0

**Key output:** 33 heads. Includes permanent `main`/`staging`/`development`, open-PR heads, promote leftovers (old + new WP03), historical candidates. **No** `issue/72-*`.

---

## 7. Tree equality check

```bash
git rev-parse origin/development^{tree} origin/staging^{tree} origin/main^{tree}
```

**EXIT:** 0

**Key output:** all three = `43b1333ae21f43a34c3bdcccb2aac96f3d6e007f`

---

## 8. Preserve export

```bash
python3 scripts/gitops/cleanup_controls.py export-preserve --repo linktrend/IDE-Development
```

**EXIT:** 0

**Key output:** `preserveResolutionOk: true`; issues `[43,44,51]`; PR `[49]`; branch `issue/43-…`.

---

## 9. Remote cleanup dry-run (no --apply)

```bash
bash scripts/cleanup-merged-branches.sh --remote --repo linktrend/IDE-Development
```

**EXIT:** 1

**Key WOULD_DELETE_REMOTE:**
- `issue/GITOPS-01-review-packager-pipeline`
- `issue/ide-bugbot-integrator-merge-fix`
- `issue/ide-lisa-option-a-doctrine`
- `promote/main/8ac0afdc55fe` *(new)*
- `promote/main/f7829436751b`
- `promote/staging/991abc319782`
- `promote/staging/e6301fc920a4` *(new)*

**FAIL line:** `FAIL: caller checkout changed during cleanup`
(Interpretation: dirty/untracked changes on caller worktree during scan — apply blocked until clean re-run.)

---

## 10. Local cleanup dry-run (no --apply)

```bash
bash scripts/cleanup-merged-branches.sh --local --repo linktrend/IDE-Development
```

**EXIT:** 0

**Key WOULD_DELETE_LOCAL:**
- `issue/31-…`, `issue/35-…`
- `issue/GITOPS-01-…`, `issue/ide-bugbot-…`, `issue/ide-lisa-option-a-…`
- `promote/main/a1c3444a8447`, `promote/staging/0ac31136b8c`

**KEEP:** `issue/72-…` — caller checkout.

---

## 11. Stale repair inventory (dry-run)

```bash
python3 scripts/gitops/cleanup_stale_records.py --repo linktrend/IDE-Development --json
```

**EXIT:** 0

**Key output:** keeps #50/#46/#40; `candidates: []`; `applyRefused: github_issue_close_deferred_to_codex`.

---

## 12. File-backend repair plan (dry-run)

```bash
LINKTREND_REPAIR_BACKEND=file python3 scripts/gitops/repair_task.py plan-cleanup-completed --repo linktrend/IDE-Development
```

**EXIT:** 0

**Key output:** `completedCount: 0`; `actions: []`; `githubMutation: none`.

---

## 13. Candidate tip re-verify

```bash
# for each prior/new WOULD_DELETE + DEFER + issue/68:
git ls-remote origin refs/heads/<branch>
git merge-base --is-ancestor <tip> origin/development
gh pr list --repo linktrend/IDE-Development --head <branch> --state open --json number,state
```

**EXIT:** 0 (overall)

**Notes:**
- All listed WOULD_DELETE tips still on origin; no open PRs on those heads
- Squash merge of #69 ⇒ tip `2a1edb1` is **not** first-parent ancestor of `development` (expected); MERGED evidence still via PR #69
- `issue/ide-pull-wave-test` tip **is** ancestor of development; dry-run still KEEP (no MERGED/abandoned PR evidence form)

---

## 14. PR detail spot-check (#36/#37/#49 + superseded)

```bash
gh pr view <n> --repo linktrend/IDE-Development --json number,state,mergeable,headRefName,headRefOid,isDraft,labels,title
```

**EXIT:** 0

**Key:** #36 CONFLICTING; #37 MERGEABLE; #49 CONFLICTING; superseded chain #52–#62 CONFLICTING; #65 CONFLICTING.

---

## Explicit non-actions this session

- No `gh pr close` / `gh issue close`
- No `git push` / `git commit`
- No `cleanup-merged-branches.sh --apply`
- No `git worktree remove` / `git worktree prune`
- No `git stash drop` / `git stash apply`
- No credential / Bugbot / ruleset / protection changes
