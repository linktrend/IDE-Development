# Stale Cleanup Controls

**Status:** Contract (IDE-owned) — Issue #51
**Date:** 2026-08-01
**Owner:** IDE Development

## Purpose

Safe, deterministic cleanup controls for stale **IDE Development** PR / worktree / branch / completed-repair records. Cleanup must be evidence-based, fail-closed by default, and never touch protected or preserve-listed work.

## Authority

| Surface | Script / workflow | Scope |
|---------|-------------------|--------|
| Remote branch cleanup | `scripts/cleanup-merged-branches.sh` via `linktrend-cleanup-merged.yml` | Remote refs only |
| Local branch/worktree cleanup | Same script (`--local`) via **Lisa** on operator Mini | Local only; never GitHub Actions |
| Preserve policy helper | `scripts/gitops/cleanup_controls.py` + `cleanup_preserve.defaults.json` | Shared KEEP decisions |
| Completed repair inventory | `scripts/gitops/cleanup_stale_records.py` | Dry-run inventory; live close deferred |
| File-backend resolved JSON | `repair_task.py plan-cleanup-completed` (optional) | Local files only; never GitHub |

Do not invent alternate cleanup entrypoints. Do not edit credentials, App, Bugbot, or branch-protection surfaces under this contract.

## Preserve always

Never delete, close, or auto-resolve:

- Issues **#43**, **#44**, **#51**
- PR **#49**
- Protected branches **`main`**, **`staging`**, **`development`**
- Consumer repos (out of scope for this IDE-only contract)
- Credentials / GitHub App / Bugbot / branch protections (out of scope)

Committed defaults: `scripts/gitops/cleanup_preserve.defaults.json`
Optional overlays: `LINKTREND_CLEANUP_PRESERVE_FILE`, `.linktrend/cleanup-preserve.json`, `LINKTREND_CLEANUP_PRESERVE` (comma-separated branch names).

## Apply gates (fail-closed)

**Default: dry-run.** Apply (delete/remove) only when **all** of the following hold:

1. Merged or abandoned evidence exists for the candidate
2. Exact tip SHA match (no guessing on moved tips)
3. No open PR on the branch (OPEN evidence wins over historical MERGED)
4. No attached worktree (local and remote paths)
5. Not on the preserve list above

If any gate fails → **KEEP** (list in report; do not apply).

### preservePrNumbers resolution (Issue #57)

`preservePrNumbers` resolution is **fail-closed**. If `gh` cannot resolve a preserved PR's `headRefName` (gh unavailable, error, empty head, or repo ambiguity), cleanup must **not** delete candidate branches.

Shell loads preserve policy via `cleanup_controls.py export-preserve` with a **deterministic repo** (`--repo` / `GITHUB_REPOSITORY` / `GH_REPO` / `gh repo view` / `origin`). Export payload surfaces `unresolvedPrNumbers` and `preserveResolutionOk`; any unresolved PR ⇒ **KEEP** / no apply deletes.

Default remains dry-run (no live delete). Out of scope: consumers, credentials, App/Bugbot config, production branch-protection edits.

## Local worktrees

- GitHub Actions **never** removes local worktrees.
- Local cleanup is **Lisa-only** on the operator machine (see `docs/contracts/LISA-LOCAL-CLEANUP-HANDOFF.md`).
- Keep **active** worktrees (any attached checkout — clean or dirty). Local apply must not `git worktree remove`.

## Open PRs (no abandoned label)

Open PRs **without** an abandoned label are **not** auto-closed.

List them as **Codex / Principal candidates** for manual decision. Cleanup scripts may report them; they must not close them.

## Completed repair records

- `cleanup_stale_records.py` runs as **inventory dry-run**.
- `--apply --i-understand-close-repairs` is **refused** (deferred to Codex/Principal).
- Prefer reporting candidates over mutating repair inventory.

```bash
python3 scripts/gitops/cleanup_stale_records.py --repo linktrend/IDE-Development --json
```

## Operational snapshot (2026-08-01) — Codex reference

Known candidates as of this date. Re-verify before apply; this snapshot is not a live delete list.

### Remote WOULD_DELETE (merged evidence)

- `issue/GITOPS-01-review-packager-pipeline`
- `issue/ide-bugbot-integrator-merge-fix`
- `issue/ide-lisa-option-a-doctrine`
- `promote/main/f7829436751b`
- `promote/staging/991abc319782`

### KEEP (active / preserve)

- `issue/43-*`
- `issue/44-*` (worktree)
- `issue/51-*`
- PR **#49**
- `issue/23-*` (open PR **#36** + worktree)
- `issue/28-*` (open PR **#37**)

### Stale OPEN PRs deferred (do not auto-close)

- PR **#36**
- PR **#37**

### Repair inventory

| Record | Note | Action |
|--------|------|--------|
| **#46** | `usage_limit` on `issue/44-*` (PR **#45** merged) | **KEEP** while issue/44 preserve is active; re-inventory after #44 closes |
| **#40** | PR **#36** still open | **KEEP** |
| **#50** | PR **#49** / issue **#43** | **KEEP** |

## Related

- `docs/contracts/LISA-LOCAL-CLEANUP-HANDOFF.md` — local worktree/branch cleanup; Actions never removes Mini worktrees
- `docs/contracts/REPAIR-DISPATCHER.md` — durable repair tasks; inventory close policy defers here
- `scripts/cleanup-merged-branches.sh` / `.github/workflows/linktrend-cleanup-merged.yml`
- `scripts/gitops/cleanup_controls.py` / `scripts/gitops/cleanup_stale_records.py`
