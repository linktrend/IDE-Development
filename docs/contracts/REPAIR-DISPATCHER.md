# Repair Dispatcher Contract

**Status:** Active  
**Date:** 2026-07-30  
**Schema owner:** IDE Development  
**Dispatch owner:** Lisa (OpenClaw ACP)  

## Separation of duties

| Actor | Owns | Must not |
|---|---|---|
| IDE Development | Repair task schema + GitHub recording helpers (`scripts/gitops/repair_task.py`, `conflict_task.py`) | Spawn Cursor agents |
| GitHub Actions / Issues | Durable failure records (idempotent upsert) | Call Cursor APIs / spawn agents |
| Lisa ACP Repair Dispatcher | Read tasks → dispatch Cursor ACP repair agents | Invent schema; prefer-incoming merges |
| Cursor ACP repair agent | Minimal fix on the named branch | Merge; promote; exceed 3 attempts |

**GitHub never spawns Cursor.**

## Schema fields (v2)

| Field | Notes |
|---|---|
| `failureId` | Stable hash identity (also stored as `id` for conflict_task compat) |
| `repository` | `owner/repo` |
| `failureType` | `ci_failure` \| `merge_conflict` \| `promotion_conflict` \| `immediate_*` |
| `pr` / `workflowId` / `checkId` | Optional GitHub identifiers |
| `branch` | Work or promote branch |
| `headSha` / `baseSha` | Exact SHAs |
| `severity` | `ordinary` \| `immediate` |
| `attemptCount` / `maxAttempts` | Default max **3** |
| `repairStatus` | e.g. `recorded`, `dispatched`, `escalated_issues`, `immediate_no_auto_repair` |
| `evidence` | Object / notes |
| `nextAction` | Operator/Lisa guidance |
| `lisaDispatchState` | `pending` \| `dispatched` \| `exhausted` \| `do_not_dispatch` |
| `resolutionState` | `open` \| `resolved` \| `Issues` |

Promotion conflicts also keep `conflict_task` fields (`stage`, `sourceBranch`, `targetBranch`, `status=conflict_blocked`, …) so `promote_*.sh` keep working.

## Behavior

1. **Idempotent upsert** by `failureId` (same identity updates one record).
2. **Ordinary** failures: Lisa may dispatch Cursor ACP; increment attempt on each dispatch/repair cycle.
3. After **3** attempts → escalate to `Issues` (no more auto-dispatch).
4. **Immediate** (`immediate_*`): durable record only; **do not auto-repair**; `lisaDispatchState=do_not_dispatch`.
5. **No prefer-incoming** on conflicts.

## Helper

```bash
python3 scripts/gitops/repair_task.py upsert \
  --repo owner/repo \
  --failure-type ci_failure \
  --branch issue/23-example \
  --head-sha <sha> \
  --increment-attempt
```

Promotion path may continue to call `conflict_task.py` (compatible) or `repair_task.py --failure-type promotion_conflict`.
