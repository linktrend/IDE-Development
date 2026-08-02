# WP02 Lane B — Lineage construction plan

**Lane:** B (deterministic lineage + conflict analysis)
**Worktree:** `issue-68-work-packet-02-integration-lineage-stale-cleanup`
**Analysis UTC:** 2026-08-02T03:13:39Z
**Branch tip analyzed:** `9cd3fec75075c6910b5a3bbb09b582e4cb3c94e4`
**Authority:** Lead alone executes merges; this lane writes evidence only.

## Immutable inputs (verified)

| Role | SHA | Verified |
|------|-----|----------|
| `origin/development` base | `991abc319782008ef93af95002be0d7f3d5a937c` | commit object exists |
| WP01 checkpoint | `89956878c54ff45e4aef1ff42883d209221b7a30` | DEV ancestor **YES** |
| Cleanup tip (#63 lineage) | `5cf099155d9f7b5d95e094f74b288af7aec766af` | DEV ancestor **YES** |
| Frozen PR #49 tip | `0868c0034620c4ccb255457484f0342a12a0c833` | ancestor of WP01 **YES**; ancestor of DEV **NO** |
| WP02 branch tip (startup) | `9cd3fec75075c6910b5a3bbb09b582e4cb3c94e4` | DEV ancestor **YES**; docs-only on top of DEV |

Additional verified facts:

- WP01 and cleanup are **not** ancestors of each other.
- `merge-base(WP01, cleanup) == development` (`991abc3…`).
- DEV→WP01: **19** commits / **277** paths; DEV→cleanup: **11** commits / **12** paths.
- Path overlap (both changed vs DEV): **exactly 1** — `docs/OPEN-ISSUES.md` (blobs differ).
- Frozen #49 commits not in WP01: **0** (fully contained; do **not** merge #49 separately).

## Recommended merge order (smallest ordinary history)

**Order A (recommended): merge WP01, then cleanup.**

Justification:

1. From DEV, both tips are fast-forward reachable; the WP02 tip only adds WP02 evidence docs on DEV.
2. WP01 is the large production-readiness / RC / installer / managed-core surface — land it first so the resulting tip preserves WP01 behavior intact.
3. Cleanup is a small additive GitOps/stale-cleanup delta on the same DEV base (11 unique paths besides the shared OPEN-ISSUES edit). After WP01 is present, cleanup auto-merges all cleanup-only paths; only OPEN-ISSUES conflicts.
4. Order B (cleanup then WP01) yields the **same single conflict** (`merge-tree` exit 1 on `docs/OPEN-ISSUES.md` either way). Prefer A so the final integration commit for stale-cleanup sits atop the WP01 RC tip (matches WP02 purpose).

**Do not** add frozen #49, #23 tip, or #28 tip as merge parents in the default construction (see deferred section).

## Exact ordered git steps for lead

Work only on `issue/68-work-packet-02-integration-lineage-stale-cleanup`. Do not force-push. Do not alter frozen PR heads.

```bash
# 0) Preconditions (read-only checks)
cd "/Users/linktrend/Projects/IDE Development/.git/linktrend-worktrees/issue-68-work-packet-02-integration-lineage-stale-cleanup"
git fetch origin
git rev-parse HEAD   # expect 9cd3fec… or later docs-only tip still based on 991abc3…
git merge-base --is-ancestor 991abc319782008ef93af95002be0d7f3d5a937c HEAD
git merge-base --is-ancestor 991abc319782008ef93af95002be0d7f3d5a937c 89956878c54ff45e4aef1ff42883d209221b7a30
git merge-base --is-ancestor 991abc319782008ef93af95002be0d7f3d5a937c 5cf099155d9f7b5d95e094f74b288af7aec766af

# 1) Merge exact WP01 checkpoint (expect clean)
git merge --no-ff --no-edit 89956878c54ff45e4aef1ff42883d209221b7a30 \
  -m "$(cat <<'EOF'
merge(wp02): integrate WP01 production-readiness checkpoint

Exact tip 89956878c54ff45e4aef1ff42883d209221b7a30 onto WP02 lineage branch.
EOF
)"

# 2) Merge exact cleanup tip (expect ONE content conflict: docs/OPEN-ISSUES.md)
git merge --no-ff --no-commit 5cf099155d9f7b5d95e094f74b288af7aec766af

# 3) Resolve docs/OPEN-ISSUES.md WITHOUT wholesale side selection
#    Append-only doctrine (file header): keep BOTH section-14 payloads.
#    Chronological numbering:
#      ## 14. Reconcile approved stale … (from cleanup; dated 2026-08-01)
#      ## 15. Work Packet 1 … (from WP01; dated 2026-08-02)
#    Shared preamble through ## 13 is identical on both sides — leave untouched.
#    Authority: docs/OPEN-ISSUES.md append-only rule; WP01 RC docs; STALE-CLEANUP-CONTROLS.md

# 4) Stage resolution and finish merge
git add docs/OPEN-ISSUES.md
git commit -m "$(cat <<'EOF'
merge(wp02): integrate stale-cleanup tip with OPEN-ISSUES append resolution

Exact tip 5cf099155d9f7b5d95e094f74b288af7aec766af. Conflict resolved by
retaining both WP01 and cleanup section entries (renumber WP01 to ## 15).
EOF
)"

# 5) Post-merge verification (lead / Lane C coordination)
#    - scripts/tests/test-stale-cleanup-controls.sh
#    - scripts/tests/test-gitops-behavioral.sh
#    - WP01 installer/RC suites as already evidenced on WP01 tip
git status -sb
git log --oneline -5
```

Optional dry-run preview (no branch mutation) already validated by Lane B:

```bash
git merge-tree --write-tree --messages --name-only \
  89956878c54ff45e4aef1ff42883d209221b7a30 \
  5cf099155d9f7b5d95e094f74b288af7aec766af
# → exit 1; only docs/OPEN-ISSUES.md
```

## Alternative order (not preferred)

Merge cleanup first, then WP01. Same conflict set. Use only if lead needs cleanup tip reachable before WP01 for a specific verification harness; otherwise use Order A.

## #23 / #28 / #49 — include or defer

| Source | Tip | Action | Reason |
|--------|-----|--------|--------|
| Frozen #49 | `0868c00…` | **Omit** as merge parent | Already ancestor of WP01 (0 commits not in WP01). |
| #23 branch | `7eb41b2…` | **Do not merge tip** | Substance already on DEV via PR #24 squash `3ea6eba…` (**same tree** as #23 tip). Post-merge DEV/WP01 blobs for `completion_gate.py` / `AGENT-COMPLETION.md` have **evolved past** #23 tip — merging #23 would regress GitOps. |
| #28 branch | `8ac8fb4…` | **Deferred for lead** | Unique file only: `docs/handoff/2026-07-30-gitops-bootstrap-activation-smoke.md` (absent on DEV/WP01/cleanup). Docs-only smoke record; not required for cleanup/WP01 code integration. Optional later cherry-pick if lead wants historical smoke evidence in-tree. |

## Post-construction expectations

- Cleanup-only paths land automatically from cleanup tip (no conflict):
  `STALE-CLEANUP-CONTROLS.md`, `cleanup_controls.py`, `cleanup_stale_records.py`, `cleanup_preserve.defaults.json`, `test-stale-cleanup-controls.sh`, handoff `2026-08-01-issue-63-cleanup-repo-scope.md`, plus updated `LISA-LOCAL-CLEANUP-HANDOFF.md`, `REPAIR-DISPATCHER.md`, `cleanup-merged-branches.sh`, `repair_task.py`, `test-gitops-behavioral.sh`.
- WP01-only paths (276) land from WP01 with no cleanup interference.
- WP01 does **not** modify `docs/contracts/AGENT-COMPLETION.md` or `scripts/gitops/completion_gate.py` vs DEV — credential-boundary / completion behavior preserved at DEV+WP01 level; cleanup does not touch those paths either.

## Hard stops for lead

- Never wholesale `-X ours` / `-X theirs` on OPEN-ISSUES.
- Never merge #23 tip to “recover” unique blobs — they are stale relative to DEV.
- Never rewrite / force-push frozen #49 / #36 / #37 heads.
- Lane B does not commit these merges; evidence only under `docs/evidence/wp02/lane-b/**`.
