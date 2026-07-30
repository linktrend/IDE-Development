# Main Approve package / store interface (authoritative)

**Status:** Authoritative — IDE Development issue #23 delivers this interface for Lisa
**Date:** 2026-07-30
**Timezone:** Asia/Taipei
**Workflow file:** `.github/workflows/linktrend-staging-to-main.yml`
(synced from `core/github/managed-workflows/linktrend-staging-to-main.yml`)
**Discover CLI:** `scripts/gitops/main_approve_package_discover.py`
**Reuse validator:** `scripts/gitops/main_approve_package_reuse.py` (used by `promote_main.sh`)

**SOT:** `docs/AUTONOMOUS-GIT-OPERATIONS.md` · `docs/adr/0003-autonomous-ship-pull-promote.md` · `core/github/CI-GATE-CONTRACTS.md` · `scripts/gitops/promote_main.sh`

This document is the **Main Approve package store** Lisa must consume. It unblocks Lisa’s fail-closed `MAIN_APPROVE_RUNTIME_STORE` / `blocked_no_store` path.

Lisa package type (OpenClaw `MainApprovePackage`) is produced under `package` without requiring Lisa to invent authoritative fields:

| Field | Meaning |
|---|---|
| `packageId` | Stable id: `main-approve-<mondayDate>-<digest16>` (or `...-empty`) |
| `mondayDate` | Asia/Taipei Monday date (`YYYY-MM-DD`) for the claim window |
| `claimExpiresAt` | Explicit expiry timestamp (see Expiry policy) |
| `createdAt` | Package creation time (UTC `Z`) |
| `items[]` | Numbered `MainApproveItem` rows |

---

## Package store (authoritative location)

**Store kind:** GitHub PR metadata only. **`available: true`** means this interface exists (even when `itemCount=0`).

| Rule | Requirement |
|---|---|
| Location | Open PR `promote/main/<12-char staging prefix>` → base `main` |
| Writer | Mon **08:00** schedule or `workflow_dispatch` `action=package` via `promote_main.sh` |
| Machine record | HTML comment marker in PR body (below) |
| Human bindings | Three SHA lines in the same PR body |
| Not a store | OpenClaw JSON/Markdown sidecars, local files under `~/.openclaw*`, ad-hoc gist notes |

**No JSON/Markdown OpenClaw sidecar state.** Lisa adapters must read GitHub (this contract + discover CLI) or a future OpenClaw **task binding** that copies these same fields — never invent a parallel file store.

---

## Trust boundary (accept / reject)

Discover and package reuse accept **only** candidates that satisfy all of:

1. PR **open**, base **`main`**, same-repository head (reject fork / `isCrossRepository` / head repo mismatch).
2. Head branch exactly `promote/main/<12-char hex>` and suffix **equals** `sourceSha[:12]`.
3. Marker present with `schemaVersion=1`, `stage=main`, `sourceBranch=staging`, `targetBranch=main`.
4. `sourceSha`, `targetSha`, `candidateHead` are exact **lowercase 40-char** Git object IDs.
5. Marker `promoteBranch` equals live head branch; live `headRefOid` equals `candidateHead`.

**Ambiguity:** two or more valid packages for one repository → reject **all** for that repo (`ambiguous_duplicate_packages`); do not choose arbitrarily.

---

## Freshness (reject stale before asking Carlos)

Before sealing an item / approve-merge inputs, verify:

| Marker field | Must equal |
|---|---|
| `sourceSha` | current remote **`staging`** tip |
| `targetSha` | current remote **`main`** tip |
| `candidateHead` | live PR head OID |

Any mismatch → omit/block the item with `requiresRepackage=true` and a precise reason (`staging_tip_drift`, `main_tip_drift`, `candidate_head_drift`, or `*_on_reread`). Discover **re-reads** tips/head again before emitting `workflowInputs`.

---

## Release gates

Configured check names (in order):

1. `LINKTREND_RELEASE_GATE_CHECKS` / `RELEASE_GATE_CHECKS` env, else
2. GitHub Actions variable `LINKTREND_RELEASE_GATE_CHECKS`, else
3. Default: `Verify IDE Development,Enforce allowed PR source branches`

Rules:

- Live discovery **never** returns `Unknown` as a usable `gateResult`.
- `gateResult = Clear` **only** when every required named check is **SUCCESS** on the exact promotion head.
- Missing, pending, neutral, cancelled, or failed required checks → `Issues`.
- Items include machine-readable `gateEvidence` (`requiredChecks`, per-check state, status/detail).
- Fixture mode may pass `--checks-json`; **production live mode must query GitHub** (`gh pr checks`).

---

## Expiry policy

- `mondayDate` = Asia/Taipei calendar Monday for `now`.
- `claimExpiresAt` = that Monday **23:59:59 Asia/Taipei** (ISO offset, e.g. `2026-07-28T23:59:59+08:00`).
- After `claimExpiresAt`, discover omits items (`package.expired=true`, reason `package_expired`) and Lisa must treat the claim as `expired_claim` / re-discover.

---

## Marker schema (`schemaVersion: 1`)

Exact HTML comment written by `promote_main.sh` package:

```html
<!-- linktrend-promote: {"schemaVersion":1,"stage":"main","sourceBranch":"staging","targetBranch":"main","sourceSha":"<stagingTip>","targetSha":"<priorMainTip>","candidateHead":"<promotePrHead>","promoteBranch":"promote/main/<short>"} -->
```

| Field | Meaning | Lisa / dispatch binding |
|---|---|---|
| `schemaVersion` | Must be `1` | reject unknown |
| `stage` | Always `"main"` | filter |
| `sourceBranch` | `"staging"` | required |
| `targetBranch` | `"main"` | required |
| `sourceSha` | Staging tip at package time | `stagingSha` / `expected_sha` |
| `targetSha` | Prior main tip at package time | `priorMainSha` / `expected_main_sha` |
| `candidateHead` | Promote PR head SHA | `promotionHeadSha` / `expected_promote_head` |
| `promoteBranch` | `promote/main/<short>` | must match head |

Human-readable lines in the same body (must match marker):

- `expected_sha (staging source) = <sourceSha>`
- `expected_main_sha (prior main target) = <targetSha>`
- `expected_promote_head = <candidateHead>`

---

## Lisa binding map (`MainApproveItem`)

| Lisa field | Store field |
|---|---|
| `index` | 1-based package order |
| `repository` | `owner/repo` |
| `promotionPrNumber` | open promote PR number |
| `stagingSha` | marker `sourceSha` |
| `priorMainSha` | marker `targetSha` |
| `promotionHeadSha` | marker `candidateHead` (must equal live PR `headRefOid`) |
| `gateResult` | `Clear` \| `Issues` only |
| `plainDescription` | Carlos-facing text **without SHAs** |

Carlos Telegram/email must never include commit SHAs. Lisa keeps SHAs only in internal bindings.

Fixture schema: `docs/contracts/fixtures/lisa-main-approve-package.schema.json`

---

## Producer reuse (`promote_main.sh` package)

Before reporting an existing package as valid:

1. Locate open PRs into `main`.
2. Run `main_approve_package_reuse.py` — **not** source/target-only matching.
3. Reuse only when open + same-repo + base main + expected `promote/main/<prefix>` + marker valid + live head == `candidateHead`.
4. If source/target match but trust/freshness fails → **fail closed** (`blocked` + durable repair/repackage). Do **not** silently reuse or arbitrarily overwrite.

---

## Discovery procedure (Lisa / operator)

```bash
python3 scripts/gitops/main_approve_package_discover.py \
  --repo linktrend/IDE-Development
```

Stdout JSON includes `available`, `store=github_promote_pr_marker`, `package` (Lisa shape), full `items` (with `workflowInputs` / `gateEvidence`), and `rejected`.

Fixture / offline:

```bash
python3 scripts/gitops/main_approve_package_discover.py \
  --from-body-file /path/to/pr-body.md \
  --repository linktrend/Example \
  --pr-number 42 \
  --head-sha <candidateHead> \
  --staging-tip <sourceSha> \
  --main-tip <targetSha> \
  --checks-json /path/to/checks.json \
  --now 2026-07-28T10:00:00+08:00
```

---

## Calendar context

| Event | Time (Asia/Taipei) | Behavior |
|---|---|---|
| Main package | Mon **08:00** | `action=package` builds `promote/main/<sha>`, merges staging, opens PR into main — **no merge** |
| Morning digest | Mon **08:30** | Lisa reports `Main ready (Mon): Clear\|Issues`; asks Principal to Approve on Telegram when Clear **and** store available **and** claim not expired |
| Main Approve | Mon **08:30** (Telegram reply) | Principal says Approve → Lisa dispatches `action=approve-merge` with **all three** SHA bindings |

Lisa must **not** merge `staging`→`main` without Principal Approve in the Telegram conversation or an explicit standing order.

---

## `workflow_dispatch` interface

**Workflow name (GitHub UI):** `LiNKtrend Staging To Main`
**File:** `linktrend-staging-to-main.yml`

### Inputs

| Input | Type | Required on approve-merge | Purpose |
|---|---|---|---|
| `action` | choice | yes | `package` \| `approve-merge` \| `reevaluate` |
| `expected_sha` | string | **yes** | Exact **staging** source SHA (`sourceSha`) |
| `expected_main_sha` | string | **yes** | Exact **prior main** target SHA (`targetSha`) |
| `expected_promote_head` | string | **yes** | Exact **promote PR head** SHA (`candidateHead`) |
| `promote_pr_number` | string | no | Exact promote PR number (else locate by marker) |

Empty SHA inputs on `approve-merge` → **fail closed** (runtime matches `promote_main.sh`).

### `action=package`

- Builds temporary branch `promote/main/<stagingShortSha>` from `origin/main`.
- Merges `origin/staging` into that branch (conflict → `promotion_conflict` durable task; protected branches unchanged).
- Opens/refreshes PR `promote/main/*` → `main` with marker + three binding lines.
- Reuses an existing PR only after full trust/freshness validation (see Producer reuse).
- **Does not merge. Never direct-pushes `main`.**

### `action=approve-merge`

Runs **only** on `workflow_dispatch` with `action=approve-merge`.

All must pass:

1. Resolve `origin/staging` and `origin/main` tips.
2. `expected_sha` **must equal** staging tip (required, non-empty).
3. `expected_main_sha` **must equal** main tip (required, non-empty).
4. Locate open PR (by `promote_pr_number` or marker matching source+target).
5. `expected_promote_head` **must equal** PR head and marker `candidateHead`.
6. Marker must parse and match all three SHAs.
7. **release-gate** success on the promote PR head. Missing ≠ success.
8. Merge **only that PR**. No direct push to `main`.

**No Bugbot re-review** on main promote.

---

## Example `gh` commands

```bash
# Package (store write)
gh workflow run linktrend-staging-to-main.yml \
  --repo linktrend/IDE-Development \
  -f action=package

# Discover packages (store read)
python3 scripts/gitops/main_approve_package_discover.py \
  --repo linktrend/IDE-Development

# Approve-merge (bind all three SHAs from package PR / discover output)
gh workflow run linktrend-staging-to-main.yml \
  --repo linktrend/IDE-Development \
  -f action=approve-merge \
  -f expected_sha=<stagingSha> \
  -f expected_main_sha=<priorMainSha> \
  -f expected_promote_head=<promotePrHeadSha>
```

---

## Failure modes

| Failure | Symptom | Lisa / operator action |
|---|---|---|
| Store unavailable / contract missing | Lisa `blocked_no_store` | Land IDE #23; point adapter at this contract + discover CLI |
| `expected_sha` / staging tip mismatch | staging tip drifted | Re-package; ask Carlos to Approve new package |
| `expected_main_sha` / main tip mismatch | main tip advanced | Re-package against new main tip |
| `expected_promote_head` mismatch | promote PR head drifted | Re-package; bind new head |
| Fork / cross-repo head | trust reject | Close invalid PR; re-package same-repo |
| Ambiguous duplicates | multiple valid packages | Close extras; re-package one |
| Expired claim | `now` > `claimExpiresAt` | Re-discover / re-package on current Monday window |
| Missing marker | PR body incomplete | Re-package; do not invent SHAs |
| Invalid existing-package reuse | producer `blocked` | Repair/repackage; do not overwrite |
| `conflict_blocked` | merge into promote branch failed | Repair on promote branch; durable task; max 3 → Issues |
| `release-gate` missing/fail | named checks not success on promote head | Wait/fix CI on promote PR; do not merge |
| No open promote PR | package not run | Run `action=package` first |

---

## Honest boundary

- This contract does **not** claim GitHub can spawn Cursor agents.
- Repair agents are external; workflows only create durable conflict tasks and reevaluate on PR/check/`workflow_dispatch` events.
- Lisa OpenClaw code changes that flip `MAIN_APPROVE_RUNTIME_STORE.available` happen in `openclaw_prime` **after** this interface exists on the consumer’s managed runtime — not in this IDE change set.
