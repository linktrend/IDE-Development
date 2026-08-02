# WP02 Lane B — Commands and results

**Worktree cwd:** `/Users/linktrend/Projects/IDE Development/.git/linktrend-worktrees/issue-68-work-packet-02-integration-lineage-stale-cleanup`
**Branch (unchanged by Lane B merges):** `issue/68-work-packet-02-integration-lineage-stale-cleanup` @ `9cd3fec75075c6910b5a3bbb09b582e4cb3c94e4`
**Write scope:** `docs/evidence/wp02/lane-b/**` only
**No commit / push / freeze-head mutation performed.**

Immutable SHAs:

```
DEV   = 991abc319782008ef93af95002be0d7f3d5a937c
WP01  = 89956878c54ff45e4aef1ff42883d209221b7a30
CLEAN = 5cf099155d9f7b5d95e094f74b288af7aec766af
F49   = 0868c0034620c4ccb255457484f0342a12a0c833
TIP   = 9cd3fec75075c6910b5a3bbb09b582e4cb3c94e4
B23   = 7eb41b2494faf6a7dc683b37d2b7334ddd517bee
B28   = 8ac8fb4a5c7e39086a4f1f02e4a45b3b17939e6c
```

---

## 1. Object existence + ancestry

```bash
for sha in $DEV $WP01 $CLEAN $F49 $TIP; do git cat-file -t "$sha"; done
git merge-base --is-ancestor $DEV $WP01; echo $?
git merge-base --is-ancestor $DEV $CLEAN; echo $?
git merge-base --is-ancestor $F49 $WP01; echo $?
git merge-base --is-ancestor $F49 $DEV; echo $?
git merge-base --is-ancestor $WP01 $CLEAN; echo $?
git merge-base --is-ancestor $CLEAN $WP01; echo $?
```

**Results:** all SHAs are commits. Ancestor checks: DEV⊂WP01 YES; DEV⊂CLEAN YES; F49⊂WP01 YES; F49⊂DEV NO; WP01⊂CLEAN NO; CLEAN⊂WP01 NO.

```bash
git merge-base $WP01 $CLEAN
# → 991abc319782008ef93af95002be0d7f3d5a937c

git rev-list --count $DEV..$WP01   # 19
git rev-list --count $DEV..$CLEAN  # 11
git rev-list --count $WP01..$F49   # 0
```

---

## 2. Path inventories

```bash
git diff --name-only $DEV...$WP01 | wc -l    # 277
git diff --name-only $DEV...$CLEAN | wc -l   # 12
comm -12 <(git diff --name-only $DEV...$WP01 | sort) \
         <(git diff --name-only $DEV...$CLEAN | sort)
# → docs/OPEN-ISSUES.md only
```

**Cleanup-only (11):**
`docs/contracts/LISA-LOCAL-CLEANUP-HANDOFF.md`, `REPAIR-DISPATCHER.md`, `STALE-CLEANUP-CONTROLS.md`, `docs/handoff/2026-08-01-issue-63-cleanup-repo-scope.md`, `scripts/cleanup-merged-branches.sh`, `scripts/gitops/cleanup_controls.py`, `cleanup_preserve.defaults.json`, `cleanup_stale_records.py`, `repair_task.py`, `scripts/tests/test-gitops-behavioral.sh`, `test-stale-cleanup-controls.sh`.

**OPEN-ISSUES blobs:**

```
DEV   5fa41f15471972a8eaf18c2439254dd5233dd9a2
WP01  1df05be0095408689aab529bdbc926eb4a56ee34
CLEAN 2de99957d3a63f367e3f757b488a644837aa938c
```

---

## 3. merge-tree simulations (no worktree mutation)

```bash
git merge-tree --write-tree --messages --name-only $WP01 $CLEAN
# exit=1
# f72d42291e39fbc568dcc072f1400b66e18dddb5
# docs/OPEN-ISSUES.md
# Auto-merging docs/OPEN-ISSUES.md
# CONFLICT (content): Merge conflict in docs/OPEN-ISSUES.md

git merge-tree --write-tree --messages --name-only $CLEAN $WP01
# exit=1
# 2b0846437fcc7d77a578a8942cd1f9ef60ae57b7
# docs/OPEN-ISSUES.md
# CONFLICT (content): Merge conflict in docs/OPEN-ISSUES.md

git merge-tree --write-tree --messages --name-only $TIP $WP01
# exit=0 → tree f6ddf51071493a4396512389a1228b4277486cf5

git merge-tree --write-tree --messages --name-only $TIP $CLEAN
# exit=0 → tree 8cde4d88e8e2c16e4bec74024a8cd4f1e1ee76bd
```

Synthetic tip+WP01 then cleanup (dangling commits, **not** on any branch, **not** pushed):

```bash
T1=$(git merge-tree --write-tree $TIP $WP01 | head -1)
C1=$(git commit-tree $T1 -p $TIP -p $WP01 -m "tmp: synthetic TIP+WP01 for lane-b analysis")
# C1=76ac03178fe6b91f4b6e5585947fbfb944301c6b
git merge-tree --write-tree --messages --name-only $C1 $CLEAN
# exit=1; conflict docs/OPEN-ISSUES.md

T2=$(git merge-tree --write-tree $TIP $CLEAN | head -1)
C2=$(git commit-tree $T2 -p $TIP -p $CLEAN -m "tmp: synthetic TIP+CLEAN for lane-b analysis")
# C2=535f0bac4b8e3a082a16528a2fe5de01351172f4
git merge-tree --write-tree --messages --name-only $C2 $WP01
# exit=1; conflict docs/OPEN-ISSUES.md
```

**Note:** `C1`/`C2` are unreferenced analysis objects in the object database only.

---

## 4. OPEN-ISSUES three-way file merge (temp files under `/tmp`)

```bash
mkdir -p /tmp/wp02-lane-b-merge
git show $DEV:docs/OPEN-ISSUES.md  > /tmp/wp02-lane-b-merge/OPEN-ISSUES.base.md
git show $WP01:docs/OPEN-ISSUES.md > /tmp/wp02-lane-b-merge/OPEN-ISSUES.wp01.md
git show $CLEAN:docs/OPEN-ISSUES.md > /tmp/wp02-lane-b-merge/OPEN-ISSUES.clean.md
git merge-file -p \
  /tmp/wp02-lane-b-merge/OPEN-ISSUES.wp01.md \
  /tmp/wp02-lane-b-merge/OPEN-ISSUES.base.md \
  /tmp/wp02-lane-b-merge/OPEN-ISSUES.clean.md \
  > /tmp/wp02-lane-b-merge/OPEN-ISSUES.conflict.md
# exit=1; single conflict hunk at competing ## 14 sections
```

Section headings confirmed:

```bash
git show $CLEAN:docs/OPEN-ISSUES.md | rg -n '^## 1[0-9]\.'
# … ## 14. Reconcile approved stale … — 2026-08-01

git show $WP01:docs/OPEN-ISSUES.md | rg -n '^## 1[0-9]\.'
# … ## 14. Work Packet 1 … — 2026-08-02
```

---

## 5. #23 / #28 / #49 probes

```bash
git rev-parse origin/issue/23-gitops-lifecycle-repair-control
# 7eb41b2494faf6a7dc683b37d2b7334ddd517bee

git rev-parse origin/issue/28-gitops-bootstrap-activation-smoke-record-issue-2
# 8ac8fb4a5c7e39086a4f1f02e4a45b3b17939e6c

# PR #24 merge on development
git merge-base --is-ancestor 3ea6ebadf46d2640f8035bbe7fc8a93e48881638 $DEV  # YES
test "$(git rev-parse $B23^{tree})" = "$(git rev-parse 3ea6ebadf46d2640f8035bbe7fc8a93e48881638^{tree})"
# SAME_TREE

# Regression if #23 tip merged:
git rev-parse $B23:scripts/gitops/completion_gate.py
# a2a8293…  ≠  DEV/WP01/CLEAN 9c7d509…

git rev-parse $B23:docs/contracts/AGENT-COMPLETION.md
# 0fca89c…  ≠  DEV/WP01/CLEAN f5858e8…

# #28 unique path
git cat-file -e $WP01:docs/handoff/2026-07-30-gitops-bootstrap-activation-smoke.md; echo $?  # absent
git cat-file -e $CLEAN:docs/handoff/2026-07-30-gitops-bootstrap-activation-smoke.md; echo $? # absent
git cat-file -e $DEV:docs/handoff/2026-07-30-gitops-bootstrap-activation-smoke.md; echo $?   # absent

git log --oneline $DEV..$F49
# 0868c00 fix(portable-v2): harden Wave 1 install integrity and protection fail-closed
# c726a73 fix(portable-v2): repair Wave 1 PYTHONPATH and trailing whitespace
# db89069 feat(managed-core): integrate portable IDE Development v2 Wave 1
```

---

## 6. Cleanup semantic diff samples (read-only)

```bash
git diff --stat $DEV..$CLEAN
# 12 files changed, 3601 insertions(+), 20 deletions(-)

git diff --stat $DEV..$WP01
# 277 files changed, 31083 insertions(+), 649 deletions(-)

git diff --stat $DEV..$WP01 -- docs/contracts/AGENT-COMPLETION.md scripts/gitops/completion_gate.py
# (empty — WP01 does not change these vs DEV)

git diff --stat $DEV..$CLEAN -- docs/contracts/AGENT-COMPLETION.md scripts/gitops/completion_gate.py
# (empty — cleanup does not change these vs DEV)
```

---

## 7. Branch status after Lane B evidence write

Lane B only creates/updates files under `docs/evidence/wp02/lane-b/**`. Lead owns any commit of evidence. No `git merge` was executed on the WP02 branch.
