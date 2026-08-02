# Conflict-resolution notes — WP01 vs cleanup tip

**Lane:** C  
**Three-way bases:** development `991abc3` · WP01 `8995687` · cleanup `5cf0991`  
**Diff dumps:** `docs/evidence/wp02/lane-c/notes/diff-wp01-vs-cleanup-*.diff`

## Summary

For five of six named conflict paths, **WP01 ≡ development**. Cleanup is a pure additive delta on those files. Take **cleanup** content, then preserve any WP01-only documentation elsewhere.

Only **`docs/OPEN-ISSUES.md`** is a true three-way documentation conflict: WP01 and cleanup both inserted a different “§14”.

| File | DEV==WP01 | DEV==CLEANUP | Resolution |
|------|-----------|--------------|------------|
| `scripts/gitops/repair_task.py` | YES | NO | **Take cleanup** (adds `plan-cleanup-completed` + `--repo` fail-closed). WP01 did not change this file. |
| `scripts/tests/test-gitops-behavioral.sh` | YES | NO | **Take cleanup** (seeds `*.json` preserve defaults into test fixtures). |
| `scripts/cleanup-merged-branches.sh` | YES | NO | **Take cleanup** (full `--repo` / preserveResolutionOk / scoped PR evidence). |
| `docs/contracts/LISA-LOCAL-CLEANUP-HANDOFF.md` | YES | NO | **Take cleanup** (Issue #63 `--repo` handoff + STALE contract link). |
| `docs/contracts/REPAIR-DISPATCHER.md` | YES | NO | **Take cleanup** (`plan-cleanup-completed` + Issue #63 repo scope). Does not remove WP01 portable doctrine (lives elsewhere). |
| `docs/OPEN-ISSUES.md` | NO | NO | **Merge both §14 topics** (see below). |

Cleanup-only files (no WP01 counterpart) — **add from tip / proposed/**:

- `scripts/gitops/cleanup_controls.py`
- `scripts/gitops/cleanup_stale_records.py`
- `scripts/gitops/cleanup_preserve.defaults.json`
- `scripts/tests/test-stale-cleanup-controls.sh`
- `docs/contracts/STALE-CLEANUP-CONTROLS.md`
- `docs/handoff/2026-08-01-issue-63-cleanup-repo-scope.md`
- workflow copies under `.github/workflows/` and `core/github/managed-workflows/` (already present on both sides historically; tip versions match cleanup hardening)

## Per-file guidance

### `scripts/gitops/repair_task.py`

- **Keep cleanup** CLI/docstring additions and `plan-cleanup-completed` path.
- Imports `normalize_caller_repo` / `plan_completed_repair_cleanup` from `cleanup_controls` — requires cleanup modules present.
- WP01 portable behavior does not live in this file; no WP01 hunks to re-apply.
- After merge: run `test-stale-cleanup-controls.sh` sections 14c–14f and coexistence suite section 6.

### `scripts/tests/test-gitops-behavioral.sh`

- Single cleanup hunk: `cp .../*.json` when seeding gitops scripts so `cleanup_preserve.defaults.json` is available in behavioral fixtures.
- Keep that line; do not drop WP01-unrelated behavioral coverage (unchanged by WP01).

### `scripts/cleanup-merged-branches.sh`

- Prefer cleanup wholesale (+192/−14 vs WP01/DEV).
- Preserves: fail-closed `--repo`, ambiguous origin+upstream, preserve PR head resolution (OPEN/CLOSED/MERGED), worktree KEEP, no delete-by-name.
- No WP01 portable installer logic in this script — no dual-merge needed inside the file.

### `docs/contracts/LISA-LOCAL-CLEANUP-HANDOFF.md` / `REPAIR-DISPATCHER.md`

- Take cleanup dated 2026-08-01 text.
- Cross-link `STALE-CLEANUP-CONTROLS.md` must remain.
- Portable WP01 contracts (`MANAGED-CORE-V2`, RC runbooks, security acceptance) are separate paths — leave intact from WP01 merge.

### `docs/OPEN-ISSUES.md` (true conflict)

**WP01 §14:** Work Packet 1 production-readiness (Issue #67) status pointer.  
**Cleanup §14:** Reconcile approved stale IDE Development PRs/worktrees (Issue #51) + STALE contract pointer.

**Recommended merged shape:**

1. Keep WP01 §14 (Issue #67 / WP01) verbatim.  
2. Renumber cleanup block to **§15** (or append after WP01 §14): Issue #51 stale-cleanup controls + link to `STALE-CLEANUP-CONTROLS.md`.  
3. Also retain cleanup’s shortened consumer-rollout bullet under GITOPS deferred notes if still accurate; prefer WP01’s more precise “IDE Development is system source only — not a consumer wire target” wording where both edited the same bullet (WP01 kept longer form; cleanup shortened — **prefer WP01 wording** for that single bullet if still present on the WP01 side of the three-way).

Do **not** drop either packet pointer; WP02/WP03 operators need both.

## Behavioral coexistence (non-file)

| Concern | Keep from WP01 | Keep from cleanup |
|---------|----------------|-------------------|
| Repo scope evidence | `validate_repository`, wrong-repo fixture, security_acceptance | `--repo` on all PR evidence; no implicit `gh` under ambiguity |
| Portable installer / RC | `tests/test-portable-v2-integration.sh`, managed-core package | Unaffected; cleanup must not rewrite managed-core |
| Repair tasks | Existing upsert/dispatch/resolve | `plan-cleanup-completed` + file-backend-only apply |
| Frozen PR #49 | WP01 “does not touch frozen PR #49” | `preservePrNumbers: [49]` + CLOSED head retention |

## Lead integrate checklist

1. Merge WP01 into issue/68 lineage.  
2. Merge cleanup tip; for the six paths above, apply this table (no prefer-incoming).  
3. Copy Lane C `proposed/` trees **except** skip re-copying `wrong-repo-evidence.json` if WP01 already has identical blob.  
4. Add new coexistence tests from proposed.  
5. Reconcile `OPEN-ISSUES.md` as §14 WP01 + §15 cleanup.  
6. Run validation command set in `integration-test-design.md`.
