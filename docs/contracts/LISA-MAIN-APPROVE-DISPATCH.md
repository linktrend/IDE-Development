# Lisa Main Approve — `workflow_dispatch` contract

**Status:** Follow-up interface (Lisa dispatches; workflow lives in managed templates)  
**Date:** 2026-07-28  
**Timezone:** Asia/Taipei  
**Workflow file:** `.github/workflows/linktrend-staging-to-main.yml` (synced from `core/github/managed-workflows/linktrend-staging-to-main.yml`)

**SOT:** `docs/AUTONOMOUS-GIT-OPERATIONS.md` · `docs/adr/0003-autonomous-ship-pull-promote.md` · `core/github/CI-GATE-CONTRACTS.md`

---

## Calendar context

| Event | Time (Asia/Taipei) | Behavior |
|---|---|---|
| Main package | Mon **08:00** | Schedule or `action=package` opens/refreshes `staging` → `main` PR — **no merge** |
| Morning digest | Mon **08:30** | Lisa reports `Main ready (Mon): Clear\|Issues`; asks Principal to Approve on Telegram when Clear |
| Main Approve | Mon **08:30** (Telegram reply) | Principal says Approve → Lisa dispatches `action=approve-merge` |

Lisa must **not** merge `staging`→`main` without Principal Approve in the Telegram conversation or an explicit standing order.

---

## `workflow_dispatch` interface

**Workflow name (GitHub UI):** `LiNKtrend Staging To Main`  
**File:** `linktrend-staging-to-main.yml`

### Inputs

| Input | Type | Required | Default | Purpose |
|---|---|---|---|---|
| `action` | choice | yes (on dispatch) | `package` | `package` = open/refresh promote PR; `approve-merge` = merge after Principal Approve |
| `expected_sha` | string | no | empty | Optional exact `staging` tip SHA for idempotent approve |

### `action=package`

- Fetches `origin/staging` and `origin/main`.
- If `staging` is already contained in `main`, skips (nothing to package).
- Otherwise opens or refreshes an open PR `staging` → `main` with package SHA in body.
- **Does not merge.**

Triggered by:

- Schedule: Mon 08:00 Asia/Taipei (`0 0 * * 1` UTC)
- Manual: `workflow_dispatch` with `action=package`

### `action=approve-merge`

Runs **only** on `workflow_dispatch` with `action=approve-merge`.

Merge path requirements (all must pass):

1. `origin/staging` tip SHA resolved.
2. If `expected_sha` is non-empty and **≠** staging tip → **refuse** (idempotency guard).
3. If staging already in `main` → success, nothing to merge.
4. Dry-run merge `staging` into `main` — on conflict → **fail** (`conflict_blocked`); no force, no prefer-incoming.
5. **release-gate:** every check in `LINKTREND_RELEASE_GATE_CHECKS` (repo variable) or default `Verify IDE Development` must be **`success`** on the **exact staging tip SHA**. Missing ≠ success.
6. If open PR `staging`→`main` exists: PR `headRefOid` must equal staging tip; merge PR with `--merge`. If PR head drifted → **fail**.
7. Fallback: direct merge push of exact SHA only when no open PR (same conflict and gate rules).

**No Bugbot re-review** on main promote.

---

## Failure modes

| Failure | Symptom | Lisa / operator action |
|---|---|---|
| `expected_sha` mismatch | Log: `expected_sha … != staging tip … — refusing merge` | Re-read package SHA from Mon PR body or `gh api`; dispatch again with correct SHA or omit `expected_sha` only if Carlos accepts non-idempotent merge |
| `conflict_blocked` | Merge dry-run fails | Do not force-merge; escalate `Main ready (Mon): Issues`; repair on branch per conflict recovery in SOT |
| `release-gate` missing | Check name not `success` on staging tip | Wait for CI on staging tip or fix CI; do not merge |
| `release-gate` fail | Check conclusion `failure` / `neutral` | Fix staging; re-run gates; re-package Monday or after fix |
| PR head drift | Open PR head ≠ staging tip | Refresh package (`action=package`) then Approve with fresh SHA |
| Staging empty / already in main | Workflow exits 0 early | No merge needed; report Clear |

---

## Example `gh` commands

**Package only (operator or Lisa after Mon 08:00 schedule):**

```bash
gh workflow run linktrend-staging-to-main.yml \
  --repo linktrend/IDE-Development \
  -f action=package
```

**Approve merge (after Principal Telegram Approve, with idempotent SHA):**

```bash
STG_SHA="$(gh api repos/linktrend/IDE-Development/git/ref/heads/staging --jq .object.sha)"

gh workflow run linktrend-staging-to-main.yml \
  --repo linktrend/IDE-Development \
  -f action=approve-merge \
  -f expected_sha="${STG_SHA}"
```

**Approve merge (all in-scope repos — Lisa Monday procedure):**

```bash
for REPO in IDE-Development openclaw_prime LiNKplatform LiNKskills LiNKbrain LiNKsites LiNKdeveloper LiNKlibraries LiNKautowork; do
  STG_SHA="$(gh api "repos/linktrend/${REPO}/git/ref/heads/staging" --jq .object.sha 2>/dev/null || echo "")"
  if [ -z "${STG_SHA}" ]; then continue; fi
  gh workflow run linktrend-staging-to-main.yml \
    --repo "linktrend/${REPO}" \
    -f action=approve-merge \
    -f expected_sha="${STG_SHA}"
done
```

Adjust repo slug for GitHub names (`IDE Development` on disk → `IDE-Development` on GitHub).

**Inspect run:**

```bash
gh run list --repo linktrend/IDE-Development --workflow linktrend-staging-to-main.yml --limit 3
gh run view <run-id> --repo linktrend/IDE-Development --log-failed
```

---

## Lisa integration (openclaw_prime follow-up)

On Monday **08:30** morning digest, when `Main ready date` equals today and `Main ready (Mon): Clear`:

1. Include Approve ask in email + Telegram (notify-only on email).
2. On Carlos Telegram **Approve / yes**: record `Main approve decision date`; dispatch `approve-merge` per repo with `expected_sha` from staging tip.
3. On deny/defer: leave PR open; no dispatch.

Full digest procedure: openclaw_prime `agents/pipeline-status.md` and `agents/morning-digest.md` (to be updated in follow-up PR).

---

## Related configuration

| Item | Location |
|---|---|
| release-gate check names | Repo variable `LINKTREND_RELEASE_GATE_CHECKS` (comma-separated) or workflow default |
| Gate contract | `core/github/CI-GATE-CONTRACTS.md` (`release-gate` section) |
| Managed template | `core/github/managed-workflows/linktrend-staging-to-main.yml` |
