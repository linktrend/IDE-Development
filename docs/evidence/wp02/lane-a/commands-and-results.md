# WP02 Lane A — commands and results

Worktree: `/Users/linktrend/Projects/IDE Development/.git/linktrend-worktrees/issue-68-work-packet-02-integration-lineage-stale-cleanup`
Generated (UTC): 2026-08-02T03:16:08Z
Read-only git/gh evidence; writes only under docs/evidence/wp02/lane-a/

## 1. Verify immutable input SHAs

```bash
git rev-parse --verify 991abc319782008ef93af95002be0d7f3d5a937c^{commit}
git rev-parse --verify 89956878c54ff45e4aef1ff42883d209221b7a30^{commit}
git rev-parse --verify 5cf099155d9f7b5d95e094f74b288af7aec766af^{commit}
git rev-parse --verify 0868c0034620c4ccb255457484f0342a12a0c833^{commit}
```

Output:
```
991abc319782008ef93af95002be0d7f3d5a937c
89956878c54ff45e4aef1ff42883d209221b7a30
5cf099155d9f7b5d95e094f74b288af7aec766af
0868c0034620c4ccb255457484f0342a12a0c833
```

## 2. PR #49 ancestor of WP01 + frozen tip

```bash
git merge-base --is-ancestor 0868c0034620c4ccb255457484f0342a12a0c833 89956878c54ff45e4aef1ff42883d209221b7a30; echo exit:$?
git rev-parse origin/issue/43-build-portable-ide-development-v2-managed-core-i
```

Output:
```
exit:0
0868c0034620c4ccb255457484f0342a12a0c833
```

## 3. Sibling proof WP01 vs CLEAN vs DEV

```bash
git merge-base 991abc319782008ef93af95002be0d7f3d5a937c 89956878c54ff45e4aef1ff42883d209221b7a30
git merge-base 991abc319782008ef93af95002be0d7f3d5a937c 5cf099155d9f7b5d95e094f74b288af7aec766af
git merge-base 89956878c54ff45e4aef1ff42883d209221b7a30 5cf099155d9f7b5d95e094f74b288af7aec766af
git rev-list --count 991abc319782008ef93af95002be0d7f3d5a937c..89956878c54ff45e4aef1ff42883d209221b7a30
git rev-list --count 991abc319782008ef93af95002be0d7f3d5a937c..5cf099155d9f7b5d95e094f74b288af7aec766af
git merge-base --is-ancestor 89956878c54ff45e4aef1ff42883d209221b7a30 5cf099155d9f7b5d95e094f74b288af7aec766af; echo wp01_of_clean:$?
git merge-base --is-ancestor 5cf099155d9f7b5d95e094f74b288af7aec766af 89956878c54ff45e4aef1ff42883d209221b7a30; echo clean_of_wp01:$?
```

Output:
```
MB(DEV,WP01)=991abc319782008ef93af95002be0d7f3d5a937c
MB(DEV,CLEAN)=991abc319782008ef93af95002be0d7f3d5a937c
MB(WP01,CLEAN)=991abc319782008ef93af95002be0d7f3d5a937c
commits DEV..WP01=19
commits DEV..CLEAN=11
wp01_of_clean:1
clean_of_wp01:1
```

## 4. #23 squash tree equivalence with PR #24

```bash
git rev-parse 3ea6eba^{tree}
git rev-parse 7eb41b2494faf6a7dc683b37d2b7334ddd517bee^{tree}
```

Output:
```
3ea6eba^{tree}=965ef30de915b1bfcdd568ac885eac4a4f79eff9
P36^{tree}=965ef30de915b1bfcdd568ac885eac4a4f79eff9
```

## 5. #23 blob census vs DEV (summary)

```bash
# for each path in git diff --name-only DEV...P36: compare blobs
```

Output (recount):
```
eq_dev=35 diff_dev=36 abs_dev=0 paths=71
```

## 6. #28 unique file absence

```bash
git cat-file -e SHA:docs/handoff/2026-07-30-gitops-bootstrap-activation-smoke.md
```

Output:
```
DEV ABSENT
WP01 ABSENT
CLEAN ABSENT
P37 PRESENT 19912a6c7cae
```

## 7. #44 content equivalence on DEV

```bash
# blob compare all files in DEV...I44
```

Output:
```
eq=42 diff=0 abs=0
I44_ancestor_of_DEV:1
```

## 8. P49-touched path blob identity in WP01

```bash
MB49=$(git merge-base 991abc319782008ef93af95002be0d7f3d5a937c 0868c0034620c4ccb255457484f0342a12a0c833)
git diff --name-only $MB49 $P49 | while read f; do compare blobs; done
```

Output:
```
MB49=edbcb86cacbf99f65aed76063a3a188117bfcf86 same=128 differ=38 missing_in_wp01=0 touched=166
```

## 9. OPEN-ISSUES.md blob IDs (sibling DIFFERS)

```bash
git rev-parse DEV|WP01|CLEAN:docs/OPEN-ISSUES.md
```

Output:
```
DEV=5fa41f15471972a8eaf18c2439254dd5233dd9a2
WP01=1df05be0095408689aab529bdbc926eb4a56ee34
CLEAN=2de99957d3a63f367e3f757b488a644837aa938c
```

## 10. Cleanup-chain ancestry matrix (tips → CLEAN)

```bash
for tip in ccdefcd 1e8823b 9120ecb c2a24e1 1b828ca c596aac 5cf0991; do git merge-base --is-ancestor $tip CLEAN; done
```

Output:
```
YES ccdefcd ancestor_of_CLEAN
YES 1e8823b ancestor_of_CLEAN
YES 9120ecb ancestor_of_CLEAN
YES c2a24e1 ancestor_of_CLEAN
YES 1b828ca ancestor_of_CLEAN
YES c596aac ancestor_of_CLEAN
YES 5cf0991 ancestor_of_CLEAN
```

## 11. WP01 ancestors #64 / #66 / #49

Output:
```
YES 44a26f0 ancestor_of_WP01
YES 76d2aae ancestor_of_WP01
YES 0868c00 ancestor_of_WP01
```

## 12. Inputs consulted (no mutation)

- docs/work-packets/2026-08-02-work-packet-02-integration-lineage-and-live-readiness.md
- docs/evidence/wp02/before-state-2026-08-02T030943Z/{open-prs,open-issues,worktrees,frozen-prs,local-git}*
- docs/evidence/wp02/lane-ownership.md

## Prohibited actions (confirmed not done)

- commit/push: no
- open/close PR or issue: no
- alter frozen heads: no
- writes outside docs/evidence/wp02/lane-a/: no
