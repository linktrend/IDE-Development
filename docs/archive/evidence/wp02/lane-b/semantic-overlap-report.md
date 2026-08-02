# WP02 Lane B — Semantic overlap report

**Generated:** 2026-08-02T03:13:39Z
**Method:** path inventory vs `991abc3…` + `git merge-tree` + per-file blob compare + contract/test citation
**Merge-tree conflict count:** **1** (`docs/OPEN-ISSUES.md`)

## How to read this report

- **True conflict** = both WP01 and cleanup changed the path vs development → appears in `merge-tree`.
- **Semantic overlap (non-conflict)** = cleanup changed a path that WP01 left at development; auto-merges to cleanup, but still needs contract/test authority before lead trusts the result.
- Resolutions cite contracts/tests — **never** wholesale ours/theirs.

---

## 1. True three-way conflict

### `docs/OPEN-ISSUES.md`

| Side | Blob | Section 14 payload |
|------|------|--------------------|
| development | `5fa41f1…` | ends at ## 13 (App-backed Review Ready) |
| WP01 | `1df05be…` | ## 14 Work Packet 1 / Issue #67 (2026-08-02) |
| cleanup | `2de9995…` | ## 14 Reconcile stale PRs / Issue #51 (2026-08-01) |

**Conflict shape:** shared identical body through ## 13; competing new ## 14 appendices.

**Authority:**

- File doctrine: append-only engineering build log (`docs/OPEN-ISSUES.md` header — “Append-only”).
- WP01 release-candidate / operator docs: `docs/work-packets/2026-08-02-work-packet-1-production-readiness.md`, `docs/BUILD-LOG.md`, `docs/runbooks/release-candidate.md`.
- Cleanup contract: `docs/contracts/STALE-CLEANUP-CONTROLS.md` (Issues #51/#57/#59/#61/#63).

**Resolution recommendation:** keep **both** entries; chronological numbers:

1. `## 14. Reconcile approved stale IDE Development PRs / worktrees — 2026-08-01` (cleanup text, unchanged)
2. `## 15. Work Packet 1 — production-readiness proof and release candidate (Issue #67) — 2026-08-02` (WP01 text, renumbered)

**Reject:** `-X ours`, `-X theirs`, or dropping either section.

---

## 2. Packet “overlap” paths that are cleanup-only (auto-merge)

These were called out as differing between WP01 and cleanup trees. Verified: **WP01 blob == development** for each; cleanup alone modifies. After Order A (WP01 then cleanup), git takes cleanup without conflict.

### `docs/contracts/LISA-LOCAL-CLEANUP-HANDOFF.md`

- **Change:** date → 2026-08-01; adds `--repo OWNER/NAME` precedence handoff; links `STALE-CLEANUP-CONTROLS.md`.
- **Authority:** `docs/contracts/STALE-CLEANUP-CONTROLS.md` (repo-scope / `--repo` fail-closed); Lisa handoff remains IDE-owned contract.
- **Recommendation:** **take cleanup**. No WP01 semantic claim on this file.

### `docs/contracts/REPAIR-DISPATCHER.md`

- **Change:** documents `plan-cleanup-completed`, `cleanup_stale_records.py`, Issue #63 repo-scope for linked-PR evidence; clarifies file-backend-only apply deletes; GitHub bulk close refused.
- **Authority:** same file as repair control plane contract; cross-link `STALE-CLEANUP-CONTROLS.md`; implementation `scripts/gitops/repair_task.py` + `cleanup_controls.py`.
- **Tests:** `scripts/tests/test-stale-cleanup-controls.sh` (cleanup tip); behavioral suite still seeds gitops scripts.
- **Recommendation:** **take cleanup**. Additive to existing dispatcher; does not rewrite dispatch-attempt/resolve semantics beyond cleanup inventory.

### `scripts/cleanup-merged-branches.sh`

- **Change:** large additive update (+192/−14) for preserve policy / repo scope / fail-closed apply gates (paired with cleanup_controls).
- **Authority:** `STALE-CLEANUP-CONTROLS.md` authority table (remote via workflow; local via Lisa only).
- **Tests:** `scripts/tests/test-stale-cleanup-controls.sh`.
- **Recommendation:** **take cleanup**. WP01 does not own this script delta.

### `scripts/gitops/repair_task.py`

- **Change:** adds `plan-cleanup-completed` CLI; imports `cleanup_controls.normalize_caller_repo` / `plan_completed_repair_cleanup`; refuses GitHub backend bulk delete; requires valid `--repo`.
- **Authority:** `REPAIR-DISPATCHER.md` + `STALE-CLEANUP-CONTROLS.md`.
- **Preserve WP01/GitOps:** WP01 does not modify this file vs DEV; `completion_gate.py` / `AGENT-COMPLETION.md` untouched by both WP01 and cleanup vs DEV.
- **Recommendation:** **take cleanup**. Lead/Lane C must run stale-cleanup + gitops behavioral tests after merge.

### `scripts/tests/test-gitops-behavioral.sh`

- **Change:** one line — also copy `scripts/gitops/*.json` into seed fixture (for `cleanup_preserve.defaults.json`).
- **Authority:** supports cleanup preserve defaults; does not alter completion-gate assertions by itself.
- **Recommendation:** **take cleanup**.

---

## 3. Cleanup-only additions (no WP01 counterpart)

| Path | Role | Authority / test |
|------|------|------------------|
| `docs/contracts/STALE-CLEANUP-CONTROLS.md` | Primary cleanup contract | Self-authoritative; preserve list includes #43/#44/#51 and PR #49 |
| `scripts/gitops/cleanup_controls.py` | Shared KEEP / plan helpers | Contract above; exercised by `test-stale-cleanup-controls.sh` |
| `scripts/gitops/cleanup_stale_records.py` | Completed-repair inventory | Contract; live GitHub close deferred |
| `scripts/gitops/cleanup_preserve.defaults.json` | Committed preserve defaults | Contract “Preserve always” |
| `scripts/tests/test-stale-cleanup-controls.sh` | Large behavioral suite | Primary test authority for cleanup |
| `docs/handoff/2026-08-01-issue-63-cleanup-repo-scope.md` | Issue #63 handoff evidence | Docs; supports repo-scope narrative |

**Recommendation:** accept entire set from cleanup tip (automatic on merge).

---

## 4. WP01-only surface (preserve; cleanup must not clobber)

276 paths including managed-core v2, installer (`scripts/ide-development.py`, `scripts/ide_development/`), native Codex (`.agents/`, `AGENTS.md`), Cursor platforms under `core/managed-core/platforms/cursor/`, RC schemas/tests, cleanroom/security/platform matrices, WP1 evidence under `docs/validation/wp1-evidence/`.

**Authority samples:**

- `docs/contracts/MANAGED-CORE-V2.md` (WP01 only vs DEV)
- `docs/runbooks/release-candidate.md`, `docs/acceptance/acceptance-matrix.md`
- Tests: `scripts/ide_development_tests/*`, `tests/cleanroom_acceptance/run_tests.py`, `tests/security_acceptance/*`, `tests/platform_matrix/*`

**Recommendation:** merge WP01 first so this tree is the base; cleanup cannot overwrite these paths (no cleanup edits there).

**Credential / completion boundary check:**
`docs/contracts/AGENT-COMPLETION.md` and `scripts/gitops/completion_gate.py` — **identical** on DEV, WP01, and cleanup. Integration does not disturb App-backed Review Ready / fail-closed completion gate.

---

## 5. Frozen #49 / #23 / #28

### Frozen PR #49 (`0868c00…`)

- Fully contained in WP01 (0 commits on #49 not in WP01).
- **Recommendation:** no separate merge. Preserve-list in `STALE-CLEANUP-CONTROLS.md` still protects PR #49 from cleanup apply.

### Issue #23 tip (`7eb41b2…`)

- PR #24 merge `3ea6eba…` is on development and has the **same tree** as #23 tip (squash-style landing).
- Tip blobs for `completion_gate.py` / `AGENT-COMPLETION.md` are **behind** current DEV/WP01 — merging the tip would regress GitOps.
- **Recommendation:** **do not merge #23 tip**. Mark unique stale blobs as historical, not still-required.

### Issue #28 tip (`8ac8fb4…`)

- Only unique path: `docs/handoff/2026-07-30-gitops-bootstrap-activation-smoke.md` (absent on DEV/WP01/cleanup).
- Docs-only activation smoke facts after #23/#24 promote.
- **Recommendation:** **deferred for lead** — optional cherry-pick if historical smoke evidence is desired; **not** required to combine WP01 + cleanup code/contracts.

---

## 6. Integration recommendation (pre-merge)

| Question | Answer |
|----------|--------|
| Safe to integrate WP01 + cleanup on ordinary history? | **Yes**, with one documented content resolve |
| Recommended order | **WP01 then cleanup** |
| Conflict count | **1** |
| Blockers | Manual OPEN-ISSUES append; optional #28 decision; post-merge test run by lead/Lane C |

Do **not** recommend integration until lead applies the OPEN-ISSUES append resolution (this report’s §1) — wholesale side selection would drop either WP01 RC status pointer or stale-cleanup contract pointer.
