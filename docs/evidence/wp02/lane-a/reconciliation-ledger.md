# WP02 Lane A — reconciliation ledger (human)

Machine-readable source: `reconciliation-ledger.json`
Before-state: `docs/evidence/wp02/before-state-2026-08-02T030943Z/`
Immutable inputs: DEV `991abc3` · WP01 `8995687` · CLEAN `5cf0991` · PR49 `0868c00`

## Lineage map

```
origin/development (991abc3)
├── WP01 sibling (8995687) … +19 commits
│   ├── includes merge of frozen PR #49 (0868c00)
│   ├── includes #64 (44a26f0) and #66 (76d2aae)
│   └── WP1 production-readiness lanes
└── CLEAN sibling (5cf0991) … +11 commits
    └── #51 → #53 → #55 → #57 → #59 → #61 → #63 tip
```

WP02 issue `#68` currently sits on `991abc3` + docs snapshot (`9cd3fec`) and is the canonical integration target.

## Frozen PR #49 / Issue #43

| Proof | Result |
|-------|--------|
| Ancestor of WP01 | `git merge-base --is-ancestor 0868c00 8995687` → YES |
| Tip frozen | `origin/issue/43-…` == `0868c00` |
| Content represented | 128/166 P49-touched paths identical blob in WP01; 0 missing; 38 evolved in WP01 descendant (hardening/WP1) |
| Classification | `ancestor_of_wp01_checkpoint` |
| WP03 | Keep tip unchanged; close PR/issue/branch/worktree only after WP03 |

## Issues #23 / PR #36 and #28 / PR #37

### #23 / PR #36 (`7eb41b2`) — semantically_superseded

- Squash merge PR #24 (`3ea6eba`) has **identical tree** `965ef30` to tip `7eb41b2`.
- DEV then advanced with #31/#32, #35/#39, #45 (App-backed Review Ready).
- 71 tip paths vs DEV: 35 EQ, 36 DIFF, **0 ABSENT**.
- Diff tip→DEV is regressive (~6984 deletions of App-backed publisher/audit surfaces).
- `@cursor review` / genuine Bugbot counting already on DEV `packager_logic.py`.
- **Do not incorporate tip.** Close after WP03 with repair #40.

### #28 / PR #37 (`8ac8fb4`) — uniquely_required

- Single docs file `docs/handoff/2026-07-30-gitops-bootstrap-activation-smoke.md`.
- ABSENT from DEV, WP01, and CLEAN.
- Documentation-only smoke facts; recommend ordinary add into WP02 lineage.

## Sibling overlap (WP01 vs CLEAN)

| Surface | Finding |
|---------|---------|
| Ancestry | Siblings from DEV; 19 vs 11 exclusive commits |
| `docs/OPEN-ISSUES.md` | DIFFERS (WP01 §14 = Issue #67 WP1; CLEAN §14 = Issue #51 cleanup) |
| CLEAN-only | `cleanup_controls.py`, `cleanup_stale_records.py`, `cleanup_preserve.defaults.json`, `test-stale-cleanup-controls.sh`, `STALE-CLEANUP-CONTROLS.md`, issue-63 handoff |
| Shared DIFFERS | `repair_task.py`, `test-gitops-behavioral.sh`, `LISA-LOCAL-CLEANUP-HANDOFF.md`, `REPAIR-DISPATCHER.md`, `cleanup-merged-branches.sh` |
| WP01-only | managed-core / portable-v2 / WP1 evidence (~261 paths absent on CLEAN) |

Both lineages are `uniquely_required_incorporated_into_new_lineage`. Lane B must three-way merge overlaps — no prefer-incoming.

## Per-entity summary

| ID | Tip | Classification | WP03 disposition |
|----|-----|----------------|------------------|
| origin/development | 991abc3 | already_present_in_origin_development | retain |
| WP01 / #67 | 8995687 | uniquely_required… | incorporate then close sources after WP03 |
| CLEAN / #63 | 5cf0991 | uniquely_required… | incorporate then close after WP03 |
| PR #49 / #43 | 0868c00 | ancestor_of_wp01_checkpoint | freeze tip; close after WP03 |
| PR #36 / #23 | 7eb41b2 | semantically_superseded | close after WP03 (do not merge tip) |
| PR #37 / #28 | 8ac8fb4 | uniquely_required… | incorporate handoff; close after WP03 |
| #44 branch | 98568c3 | already_present_in_origin_development | close after WP03 (content via #45) |
| PR #52/#54/#56/#58/#60/#62 (#51–#61) | … | ancestor_of_cleanup_tip_5cf0991 | close after CLEAN incorporated |
| PR #65 / #64 | 44a26f0 | ancestor_of_wp01_checkpoint | close after WP01 incorporated |
| #66 | 76d2aae | ancestor_of_wp01_checkpoint | close after WP01 incorporated |
| #68 WP02 | 9cd3fec | uniquely_required… | active WP02 target |
| #31, #35 | on DEV | already_present_in_origin_development | close if still open after WP03 |
| repair #40 | — | semantically_superseded | close with PR #36 |
| repair #46, #50 | — | intentionally_deferred | usage_limit; no tip mutation |
| main worktree | bba98ba | intentionally_deferred | retain primary checkout |
| mirror worktrees | (various) | safe_to_close_clean_only_after_wp03 | remove when owning ref closed |

## Open PRs covered

#36, #37, #49, #52, #54, #56, #58, #60, #62, #65 (all from before-state `open-prs.json`).

## Blockers

None for ledger authority. No live closes/deletes in WP02.

## Append — WP02 completion (2026-08-02)

Canonical lineage incorporated on Issue #68. Accepted partial tip `712675614014abdf6e180915e07aa21e1a983324`; external configuration closed (`EXTERNAL-CONFIGURATION-CLOSURE.md`). WP02 **COMPLETE** for stated scope. WP03 dispositions in the table above remain deferred (close/clean only after WP03). Not production-accepted; not consumer-rollout-authorized.
