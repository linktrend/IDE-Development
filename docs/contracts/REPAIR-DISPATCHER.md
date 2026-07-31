# Repair Dispatcher Contract

**Status:** Active
**Date:** 2026-07-30
**Schema owner:** IDE Development
**Dispatch owner:** Lisa (OpenClaw ACP)

## Separation of duties

| Actor | Owns | Must not |
|---|---|---|
| IDE Development | Repair task schema + GitHub recording helpers (`scripts/gitops/repair_task.py`; `conflict_task.py` shim) | Spawn Cursor agents |
| GitHub Actions / Issues | Durable failure records (idempotent upsert) | Call Cursor APIs / spawn agents |
| Lisa ACP Repair Dispatcher | Read tasks → `dispatch-attempt` → Cursor ACP repair agents | Invent schema; prefer-incoming merges |
| Cursor ACP repair agent | Minimal fix on the named branch | Merge; promote; exceed 3 attempts |

**GitHub never spawns Cursor.**

## Schema fields (v2)

| Field | Notes |
|---|---|
| `failureId` | Stable hash of `repo\|type\|pr\|workflow\|check\|branch` (**not** headSha) |
| `repository` | `owner/repo` |
| `failureType` | See types below |
| `prNumber` / `workflowName` / `checkName` | Optional GitHub identifiers |
| `branch` | Work or promote branch |
| `headSha` / `baseSha` | Exact SHAs (updated on re-observation; not identity) |
| `severity` | `ordinary` \| `immediate` |
| `attemptCount` / `maxAttempts` | Default max **3**; increment **only** on `dispatch-attempt` |
| `repairStatus` | e.g. `recorded`, `dispatched`, `escalated_issues`, `immediate_no_auto_repair`, `resolved` |
| `evidence` | Object / notes |
| `nextAction` | Operator/Lisa guidance |
| `lisaDispatchState` | `pending` \| `dispatched` \| `exhausted` \| `do_not_dispatch` |
| `resolutionState` | `open` \| `resolved` \| `Issues` |

### failureTypes

**Ordinary** (`lisaDispatchState=pending`):

- `ci_failure`, `bugbot_failure`, `merge_conflict`, `promotion_conflict`

**Immediate** (`lisaDispatchState=do_not_dispatch`):

- `automation_credentials_blocked`, `usage_limit`, `packager_author_blocked`
- `immediate_security`, `immediate_destructive`, `immediate_approval_required`, `immediate_product_decision`

Promotion conflicts also keep compat fields (`stage`, `sourceBranch`, `targetBranch`, `status=conflict_blocked`, …).
`conflict_task.py` is a thin shim that delegates to `repair_task`.

## Behavior

1. **Idempotent upsert** by `failureId` (same identity updates one record; new headSha overwrites field).
2. **Re-observation does not increment** `attemptCount`.
3. **`dispatch-attempt`** increments `attemptCount` and sets `repairStatus=dispatched`.
4. After **3** unsuccessful attempts → `resolutionState=Issues`, `lisaDispatchState=exhausted` (cannot dispatch).
5. **`--resolve --head-sha=X`** closes when the repaired SHA is recorded.
6. **Immediate** types: durable record only; never auto-repair.
7. **No prefer-incoming** on conflicts.
8. Labels: `linktrend-repair` + type-specific. Titles: `[repair:<type>] repo#pr check`.

## CLI

```bash
python3 scripts/gitops/repair_task.py upsert \
  --repo owner/repo \
  --failure-type ci_failure \
  --pr 23 \
  --workflow CI \
  --check "Verify IDE Development" \
  --branch issue/23-example \
  --head-sha <sha>

python3 scripts/gitops/repair_task.py dispatch-attempt --repo owner/repo --id <failureId>
python3 scripts/gitops/repair_task.py resolve --repo owner/repo --id <failureId> --head-sha <repaired>
python3 scripts/gitops/repair_task.py show --repo owner/repo --id <failureId>
python3 scripts/gitops/repair_task.py list --repo owner/repo
```

File backend (tests): `LINKTREND_REPAIR_BACKEND=file` + `LINKTREND_REPAIR_DIR=...`
(also accepts legacy `LINKTREND_CONFLICT_BACKEND` / `LINKTREND_CONFLICT_DIR`).

## Observer

Managed workflow `linktrend-repair-observer.yml` upserts `ci_failure` / `bugbot_failure` on
workflow_run / check_run failures using read-only checkout of the default branch and the
LiNKtrend GitOps GitHub App (`AUTOMATION_TOKEN` via `resolve_automation_token.sh`).

- Ordinary workflow token: not used for Issue upsert/resolve (job grants `contents: read` only).
- App unavailable: write local `automation_credentials_blocked` outcome / step summary and fail the workflow; no GitHub mutations.
- `repair_observer.py` proves current PR/branch head before resolving.
