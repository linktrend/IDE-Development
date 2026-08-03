# Stale Cleanup Controls

**Status:** Contract (IDE-owned) — Issues #51 / #57 / #59 / #61 / #63
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

- Any issue, PR, or branch named by the current preserve policy
- Protected branches **`main`**, **`staging`**, **`development`**
- Consumer repos (out of scope for this IDE-only contract)
- Credentials / GitHub App / Bugbot / branch protections (out of scope)

Committed defaults: `scripts/gitops/cleanup_preserve.defaults.json`. The list is intentionally empty after the 2026-08-03 reconciliation; add entries only for active, intentionally protected work and remove them when that work closes.
Optional overlays: `LINKTREND_CLEANUP_PRESERVE_FILE`, `.linktrend/cleanup-preserve.json`, `LINKTREND_CLEANUP_PRESERVE` (comma-separated branch names).

## Apply gates (fail-closed)

**Default: dry-run.** Apply (delete/remove) only when **all** of the following hold:

1. Merged or abandoned evidence exists for the candidate
2. Exact tip SHA match (no guessing on moved tips)
3. No open PR on the branch (OPEN evidence wins over historical MERGED)
4. No attached worktree (local and remote paths)
5. Not on the preserve list above

If any gate fails → **KEEP** (list in report; do not apply).

### preservePrNumbers + PR evidence repo scope (Issues #57 / #59 / #61 / #63)

`preservePrNumbers` resolution is **fail-closed**. If `gh` cannot resolve a preserved PR's `headRefName` (gh unavailable, error, empty head, or repo ambiguity), cleanup must **not** delete candidate branches.

Shell (`cleanup-merged-branches.sh`) accepts explicit `--repo OWNER/NAME` and loads preserve policy via `cleanup_controls.py export-preserve` with a **deterministic repo**. Precedence (Issues #59 / #63):

1. Explicit CLI `--repo` (**highest**; Issue #63)
2. `GITHUB_REPOSITORY`
3. `GH_REPO`
4. Only if unambiguous: `gh repo view` / `origin`

**Explicit `--repo` fail-closed (Issue #63):** when the caller passes `--repo`, that value is authoritative over env, remotes, and implicit `gh`. Empty or invalid explicit `--repo` (not a valid `OWNER/NAME` slug) **fails closed immediately** — exit non-zero; **no fallthrough** to `GITHUB_REPOSITORY` / `GH_REPO` / remotes / implicit `gh`; no PR evidence queries; no `WOULD_DELETE` / `DELETED`.

**Ambiguous remotes (Issue #59):** when neither `--repo` nor env is set **and** both `origin` and `upstream` remotes exist → **fail closed**. Do not guess `origin` or implicit `gh` context. Export must leave preserve PR heads unresolved (`preserveResolutionOk=false`, numbers in `unresolvedPrNumbers`) → cleanup **KEEP**; `WOULD_DELETE` / `DELETED` blocked.

Valid explicit `--repo` / env remain authoritative even when both remotes exist. Any unresolved PR ⇒ **KEEP** / no apply deletes.

**Repository-scoped PR evidence (Issue #61):** whenever shell cleanup has resolved a nonempty `CLEANUP_REPO`, every PR evidence query (`gh pr list` used to classify OPEN / MERGED / ABANDONED / NONE for delete eligibility) **MUST** pass `--repo CLEANUP_REPO`. If `CLEANUP_REPO` is empty because repository context is ambiguous or unresolved → **fail closed**: do not query implicit `gh` for PR evidence; no candidate delete (no `WOULD_DELETE` / `DELETED` from implicit context). Issue #59 precedence and ambiguity controls above remain authoritative; Issue #63 empty/invalid explicit `--repo` is a stronger hard fail (exit before evidence).

**Completed-repair linked-PR scope (Issue #63):** `repair_task.py plan-cleanup-completed` and `cleanup_stale_records.py` (file-backend path) **MUST** propagate the caller's `--repo` into `cleanup_controls.plan_completed_repair_cleanup(..., repo=...)`. Linked PR state used to authorize file deletes is therefore repository-scoped; wrong implicit `gh` / remote context must not authorize apply deletes. File-backend remains **local resolved JSON only**; `githubMutation` stays `none` (no GitHub Issue close/delete from this control).

Default remains dry-run (no live delete by default). Scope: IDE cleanup policy/runtime only — no consumer changes. Also out of scope: credentials, App/Bugbot config, production branch-protection edits.

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

## Historical operational snapshot (2026-08-01) — reconciled

The candidates below were the evidence basis for the cleanup plan. They were reconciled and removed or closed on 2026-08-03. This is historical context, not a live delete or preserve list.

### Remote WOULD_DELETE (merged evidence)

- `issue/GITOPS-01-review-packager-pipeline`
- `issue/ide-bugbot-integrator-merge-fix`
- `issue/ide-lisa-option-a-doctrine`
- `promote/main/f7829436751b`
- `promote/staging/991abc319782`

### KEEP at snapshot time

- `issue/43-*`
- `issue/44-*` (worktree)
- `issue/51-*`
- PR **#49**
- `issue/23-*` (open PR **#36** + worktree)
- `issue/28-*` (open PR **#37**)

### Stale OPEN PRs deferred at snapshot time

- PR **#36**
- PR **#37**

### Repair inventory

| Record | Note | Action |
|--------|------|--------|
| **#46** | `usage_limit` on `issue/44-*` (PR **#45** merged) | **KEEP at snapshot time**; reconciled after #44 closed |
| **#40** | PR **#36** still open | **KEEP** |
| **#50** | PR **#49** / issue **#43** | **KEEP** |

## Related

- `docs/contracts/LISA-LOCAL-CLEANUP-HANDOFF.md` — local worktree/branch cleanup; Actions never removes Mini worktrees; Lisa passes explicit `--repo`
- `docs/contracts/REPAIR-DISPATCHER.md` — durable repair tasks; inventory close policy defers here; Issue #63 `--repo` propagation into plan-cleanup
- `scripts/cleanup-merged-branches.sh` (`--repo OWNER/NAME` highest precedence) / `.github/workflows/linktrend-cleanup-merged.yml`
- `scripts/gitops/cleanup_controls.py` / `scripts/gitops/cleanup_stale_records.py` / `scripts/gitops/repair_task.py`
