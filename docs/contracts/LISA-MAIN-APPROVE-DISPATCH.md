# Lisa Main Approve — `workflow_dispatch` contract

**Status:** Follow-up interface (Lisa dispatches; workflow lives in managed templates)
**Date:** 2026-07-28 (corrected: temporary promote branches; no direct push)
**Timezone:** Asia/Taipei
**Workflow file:** `.github/workflows/linktrend-staging-to-main.yml` (synced from `core/github/managed-workflows/linktrend-staging-to-main.yml`)

**SOT:** `docs/AUTONOMOUS-GIT-OPERATIONS.md` · `docs/adr/0003-autonomous-ship-pull-promote.md` · `core/github/CI-GATE-CONTRACTS.md`

---

## Calendar context

| Event | Time (Asia/Taipei) | Behavior |
|---|---|---|
| Main package | Mon **08:00** | Schedule or `action=package` builds `promote/main/<sha>` from main tip, merges staging, opens PR into main — **no merge** |
| Morning digest | Mon **08:30** | Lisa reports `Main ready (Mon): Clear\|Issues`; asks Principal to Approve on Telegram when Clear |
| Main Approve | Mon **08:30** (Telegram reply) | Principal says Approve → Lisa dispatches `action=approve-merge` with **both** SHA bindings |

Lisa must **not** merge `staging`→`main` without Principal Approve in the Telegram conversation or an explicit standing order.

---

## `workflow_dispatch` interface

**Workflow name (GitHub UI):** `LiNKtrend Staging To Main`
**File:** `linktrend-staging-to-main.yml`

### Inputs

| Input | Type | Required | Default | Purpose |
|---|---|---|---|---|
| `action` | choice | yes (on dispatch) | `package` | `package` = open/refresh promote PR; `approve-merge` = merge after Principal Approve |
| `expected_sha` | string | no | empty | Exact **staging tip** SHA required for approve-merge |
| `expected_promote_head` | string | no | empty | Exact **promote PR head** SHA required for approve-merge |

### `action=package`

- Builds temporary branch `promote/main/<stagingShortSha>` from `origin/main`.
- Merges `origin/staging` into that branch (conflict → `conflict_blocked` durable task; protected branches unchanged).
- Opens/refreshes PR `promote/main/*` → `main`.
- **Does not merge. Never direct-pushes `main`.**

### `action=approve-merge`

Runs **only** on `workflow_dispatch` with `action=approve-merge`.

Merge path requirements (all must pass):

1. Resolve `origin/staging` tip.
2. If `expected_sha` is non-empty and **≠** staging tip → **refuse**.
3. Locate open PR from `promote/main/*` for that staging SHA.
4. If `expected_promote_head` is non-empty and **≠** PR head → **refuse**.
5. **release-gate** must be **success on the promote PR head** (combined candidate). Missing ≠ success. Prior staging-only greens are not proof.
6. Merge **only that PR**. No direct push to `main`.

**No Bugbot re-review** on main promote.

---

## Failure modes

| Failure | Symptom | Lisa / operator action |
|---|---|---|
| `expected_sha` mismatch | staging tip drifted | Re-package; ask Carlos to Approve new SHAs |
| `expected_promote_head` mismatch | promote PR head drifted | Re-package; bind new head |
| `conflict_blocked` | merge into promote branch failed | Repair on promote branch; durable task attempt count; max 3 → Issues |
| `release-gate` missing/fail | named checks not success on promote head | Wait/fix CI on promote PR; do not merge |
| No open promote PR | package not run | Run `action=package` first |

---

## Example `gh` commands

```bash
# Package
gh workflow run linktrend-staging-to-main.yml \
  --repo linktrend/IDE-Development \
  -f action=package

# Approve-merge (bind both SHAs from package PR body)
gh workflow run linktrend-staging-to-main.yml \
  --repo linktrend/IDE-Development \
  -f action=approve-merge \
  -f expected_sha=<stagingSha> \
  -f expected_promote_head=<promotePrHeadSha>
```

---

## Honest boundary

This contract does **not** claim GitHub can spawn Cursor agents. Repair agents are external; workflows only create durable conflict tasks and reevaluate on PR/check/`workflow_dispatch` events.
