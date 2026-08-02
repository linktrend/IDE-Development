# WP02 Lane C — commands and results

**Worktree:** `…/issue-68-work-packet-02-integration-lineage-stale-cleanup`  
**Lane write root:** `docs/evidence/wp02/lane-c/**`  
**No commit / no push / no cleanup apply**

## Environment

```text
pwd → …/issue-68-work-packet-02-integration-lineage-stale-cleanup
HEAD → 9cd3fec75075c6910b5a3bbb09b582e4cb3c94e4
branch → issue/68-work-packet-02-integration-lineage-stale-cleanup
```

## Immutable SHA verification

```bash
git cat-file -t 5cf099155d9f7b5d95e094f74b288af7aec766af   # → commit
git cat-file -t 89956878c54ff45e4aef1ff42883d209221b7a30   # → commit
git cat-file -t 991abc319782008ef93af95002be0d7f3d5a937c   # → commit
```

## Inventory (cleanup tip vs WP01)

```bash
git ls-tree -r --name-only 5cf0991 | rg -i 'cleanup|stale|preserve|…'
# Confirmed cleanup-only: cleanup_controls.py, cleanup_stale_records.py,
#   cleanup_preserve.defaults.json, test-stale-cleanup-controls.sh,
#   STALE-CLEANUP-CONTROLS.md, handoff issue-63
# WP01 missing those; WP01 has portable security fixtures / tests
```

## Extract from cleanup tip → proposed/

```bash
for f in \
  scripts/tests/test-stale-cleanup-controls.sh \
  scripts/gitops/cleanup_controls.py \
  scripts/gitops/cleanup_stale_records.py \
  scripts/gitops/cleanup_preserve.defaults.json \
  scripts/cleanup-merged-branches.sh \
  docs/contracts/STALE-CLEANUP-CONTROLS.md \
  docs/contracts/LISA-LOCAL-CLEANUP-HANDOFF.md \
  docs/contracts/REPAIR-DISPATCHER.md \
  docs/OPEN-ISSUES.md \
  docs/handoff/2026-08-01-issue-63-cleanup-repo-scope.md \
  scripts/gitops/repair_task.py \
  scripts/tests/test-gitops-behavioral.sh \
  .github/workflows/linktrend-cleanup-merged.yml \
  core/github/managed-workflows/linktrend-cleanup-merged.yml
do
  git show 5cf0991:"$f" > docs/evidence/wp02/lane-c/proposed/"$f"
done
```

### Blob verify (all OK)

| Path | Match tip blob |
|------|----------------|
| `scripts/tests/test-stale-cleanup-controls.sh` | OK (1891 lines) |
| `scripts/gitops/cleanup_controls.py` | OK |
| `scripts/gitops/cleanup_stale_records.py` | OK |
| `scripts/gitops/cleanup_preserve.defaults.json` | OK |
| `scripts/cleanup-merged-branches.sh` | OK |
| `docs/contracts/STALE-CLEANUP-CONTROLS.md` | OK |
| `docs/contracts/LISA-LOCAL-CLEANUP-HANDOFF.md` | OK |
| `docs/contracts/REPAIR-DISPATCHER.md` | OK |
| `docs/handoff/2026-08-01-issue-63-cleanup-repo-scope.md` | OK |
| `docs/OPEN-ISSUES.md` | OK (tip; reconcile with WP01 at integrate) |
| `scripts/gitops/repair_task.py` | OK |
| `scripts/tests/test-gitops-behavioral.sh` | OK |
| workflow yml ×2 | OK |

## Three-way conflict stats

```bash
git diff --stat 8995687 5cf0991 -- \
  scripts/gitops/repair_task.py \
  scripts/tests/test-gitops-behavioral.sh \
  scripts/cleanup-merged-branches.sh \
  docs/contracts/LISA-LOCAL-CLEANUP-HANDOFF.md \
  docs/contracts/REPAIR-DISPATCHER.md \
  docs/OPEN-ISSUES.md
```

Results: repair_task +91/−1; behavioral +1; cleanup-merged-branches +192/−14; Lisa handoff +5/−2; REPAIR-DISPATCHER +11/−3; OPEN-ISSUES +5/−12.

`DEV==WP01` for all except `OPEN-ISSUES.md` (WP01 added §14 WP1).

## Live read-only inventory (cleanup plan inputs)

```bash
gh pr list --repo linktrend/IDE-Development --state open --limit 30 --json number,title,headRefName,isDraft,mergeable
git worktree list
git ls-remote --heads origin 'issue/GITOPS-01-review-packager-pipeline' # EXISTS
# … also EXISTS: ide-bugbot-integrator-merge-fix, ide-lisa-option-a-doctrine,
#    promote/main/f7829436751b, promote/staging/991abc319782
```

Open PRs observed: #65, #62, #60, #58, #56, #54, #52, #49, #37, #36.

## New artifacts authored (not from tip)

- `proposed/scripts/tests/test-cleanup-wp01-lineage-coexistence.sh` (`bash -n` → syntax OK)
- `proposed/tests/security_acceptance/test_cleanup_wp01_coexistence.py`
- `proposed/scripts/ide_development_tests/fixtures/security/cleanup/wrong-repo-evidence.json` (copy of WP01 blob; PROVENANCE.txt; skip if WP01 already present)
- `integration-test-design.md`, `cleanup-plan-post-wp03.md`, `conflict-resolution-notes.md`, `SUMMARY.md`, this file
- `notes/diff-wp01-vs-cleanup-*.diff`

## Explicitly not run

- `cleanup-merged-branches.sh --apply` (any scope)
- `git worktree remove` / remote branch delete / PR close
- `completion_gate.py review-ready` / commit / push
- Full `test-stale-cleanup-controls.sh` against this worktree (cleanup sources not yet at real `scripts/` — only under `proposed/`; lead runs after integrate)
