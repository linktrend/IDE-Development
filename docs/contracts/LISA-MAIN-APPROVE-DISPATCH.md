# Main Approve package / store interface (authoritative)

**Status:** Authoritative — IDE Development issue #23 delivers this interface for Lisa
**Date:** 2026-07-30
**Timezone:** Asia/Taipei
**Workflow file:** `.github/workflows/linktrend-development-to-main.yml`
(synced from `core/github/managed-workflows/linktrend-development-to-main.yml`)
**Discover CLI:** `scripts/gitops/main_approve_package_discover.py`
**Reuse validator:** `scripts/gitops/main_approve_package_reuse.py` (used by `promote_main.sh`)

**SOT:** `docs/AUTONOMOUS-GIT-OPERATIONS.md` · `docs/adr/0003-autonomous-ship-pull-promote.md` · `core/github/CI-GATE-CONTRACTS.md` · `scripts/gitops/promote_main.sh`

This document is the **Main Approve package store** Lisa must consume. It unblocks Lisa’s fail-closed `MAIN_APPROVE_RUNTIME_STORE` / `blocked_no_store` path.

Lisa package type (OpenClaw `MainApprovePackage`) is produced under `package` without requiring Lisa to invent authoritative fields:

| Field | Meaning |
|---|---|
| `packageId` | Stable id: `main-approve-<mondayDate>-<digest16>` (or `...-empty`) |
| `mondayDate` | Asia/Taipei Monday date (`YYYY-MM-DD`) for the claim window |
| `createdAt` | Time this approval package payload was **discovered/sealed** (UTC `Z`). Not the promote PR `createdAt`. |
| `claimExpiresAt` | Explicit expiry timestamp (see Expiry policy) |
| `items[]` | Numbered `MainApproveItem` rows |

---

## Package store (authoritative location)

**Store kind:** GitHub PR metadata only. **`available: true`** means this interface exists (even when `itemCount=0`).

| Rule | Requirement |
|---|---|
| Location | Open PR `promote/main/<12-char development prefix>` → base `main` |
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
3. Marker present with `schemaVersion=1`, `stage=main`, `sourceBranch=development`, `targetBranch=main`.
4. `sourceSha`, `targetSha`, `candidateHead` are exact **lowercase 40-char** Git object IDs.
5. Marker `promoteBranch` equals live head branch; live `headRefOid` equals `candidateHead`.

**Ambiguity:** two or more valid packages for one repository → reject **all** for that repo (`ambiguous_duplicate_packages`); do not choose arbitrarily.

---

## Freshness (reject stale before asking Carlos)

Before sealing an item / approve-merge inputs, verify:

| Marker field | Must equal |
|---|---|
| `sourceSha` | current remote **`development`** tip |
| `targetSha` | current remote **`main`** tip |
| `candidateHead` | live PR head OID |

Any mismatch → omit/block the item with `requiresRepackage=true` and a precise reason (`development_tip_drift`, `main_tip_drift`, `candidate_head_drift`, or `*_on_reread`).

**Final live reread** (immediately before sealing dispatch inputs) also re-validates: PR still open, base `main`, allowed `promote/main/*` head, same-repo/fork trust, marker still matches, tips/head still match, and **re-queries the exact configured release gates** on the current promotion head. If gates are pending/failed, the sealed item is `Issues` (never sealed as `Clear`).

---

## Release gates

Configured check names (in order):

1. Explicit `--release-gate-checks` / env `LINKTREND_RELEASE_GATE_CHECKS` / `RELEASE_GATE_CHECKS`, else
2. GitHub Actions variable `LINKTREND_RELEASE_GATE_CHECKS` via `gh api`, else
3. Default: `Verify IDE Development,Linktrend Branch Source Policy`

**Variable resolution fail-closed:** defaults are used **only** when the repository variable is positively confirmed absent (`404` / Not Found) or empty. Authentication, rate-limit, network, permission, malformed-response, or other API failures **stop** package discovery with `available: false` and `error=release_gate_config_failed:…`.

Rules:

- Live discovery **never** returns `Unknown` as a usable `gateResult`.
- `gateResult = Clear` **only** when every required named check is **SUCCESS** on the exact promotion head.
- Missing, pending, neutral, cancelled, or failed required checks → `Issues`.
- `gh pr checks` exit `0` (pass), `8` (pending), or other nonzero (fail/mixed) are **informational** when stdout is valid JSON — classify into Clear/Issues. Fail closed only for auth, rate-limit, malformed JSON, or unavailable data (`gate_query_failed`).
- Items include machine-readable `gateEvidence` (`requiredChecks`, per-check state, status/detail).
- Fixture mode may pass `--checks-json`; **production live mode must query GitHub** (`gh pr checks`).
- Final live reread re-queries the same named gates on the current promotion head; pending/failed updates the item to `Issues` (does not seal `Clear`).

---

## Expiry policy

- `mondayDate` = Asia/Taipei calendar Monday for `now`.
- `claimExpiresAt` = that Monday **23:59:59 Asia/Taipei** (ISO offset, e.g. `2026-07-28T23:59:59+08:00`).
- After `claimExpiresAt`, discover omits items (`package.expired=true`, reason `package_expired`) and Lisa must treat the claim as `expired_claim` / re-discover.

---

## Marker schema (`schemaVersion: 1`)

Exact HTML comment written by `promote_main.sh` package:

```html
<!-- linktrend-promote: {"schemaVersion":1,"stage":"main","sourceBranch":"development","targetBranch":"main","sourceSha":"<developmentTip>","targetSha":"<priorMainTip>","candidateHead":"<promotePrHead>","promoteBranch":"promote/main/<short>"} -->
```

| Field | Meaning | Lisa / dispatch binding |
|---|---|---|
| `schemaVersion` | Must be `1` | reject unknown |
| `stage` | Always `"main"` | filter |
| `sourceBranch` | `"development"` | required |
| `targetBranch` | `"main"` | required |
| `sourceSha` | Development tip at package time | `developmentSha` / `expected_sha` |
| `targetSha` | Prior main tip at package time | `priorMainSha` / `expected_main_sha` |
| `candidateHead` | Promote PR head SHA | `promotionHeadSha` / `expected_promote_head` |
| `promoteBranch` | `promote/main/<short>` | must match head |

Human-readable lines in the same body (must match marker):

- `expected_sha (development source) = <sourceSha>`
- `expected_main_sha (prior main target) = <targetSha>`
- `expected_promote_head = <candidateHead>`

---

## Lisa binding map (`MainApproveItem`)

| Lisa field | Store field |
|---|---|
| `index` | 1-based package order |
| `repository` | `owner/repo` |
| `promotionPrNumber` | open promote PR number |
| `developmentSha` | marker `sourceSha` |
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
  --development-tip <sourceSha> \
  --main-tip <targetSha> \
  --checks-json /path/to/checks.json \
  --now 2026-07-28T10:00:00+08:00
```

---

## Approval window and supported controller route

Existing Monday package/approval windows and expiry remain unchanged. Discovery is read-only. Lisa presents the current clear package without technical identifiers in Principal-facing prose, records the explicit approval, and re-reads exact Development/main/PR identities before the designated lead acts. This source update does not create a schedule or dispatch an action.

Package preparation uses the normal `delivery_controller.py prepare-main` (or the paired `promote_main.sh` operator route). The temporary promote/main ref preserves the exact accepted Development commit. It does not create a synthetic candidate merge commit. Main must be an ancestor of that accepted source for the shell packaging path; otherwise normal source integration and new exact evidence are required.

After explicit Principal approval, normal `complete-main` consumes all bound values:

| Controller input | Meaning |
|---|---|
| `source_sha` | Exact current Development source commit |
| `base_sha` | Exact prior main target commit |
| `expected_head` | Exact promote PR head, equal to Development source |
| `pr_number` | Exact open same-repository non-draft promote/main PR |
| `role` | `program-lead`; operational writer lease, not a separate credential |

The exact approval JSON additionally binds these SHAs and the retained receipt digest. Missing or inferred approval, stale tips, wrong source/head/marker, receipt mismatch, and protected check failures stop the operation. Existing protected Source Policy and Receipt Gate remain required. Main merge uses normal GitHub protection, never admin bypass or direct push. No paid Bugbot review or Full rerun is introduced.

```bash
# Read-only discovery, no Actions dispatch.
python3 scripts/gitops/main_approve_package_discover.py --repo linktrend/IDE-Development

# Only after an exact Principal approval and repository-specific operation window:
python3 scripts/gitops/delivery_controller.py complete-main \
  --repository <owner/repo> --role program-lead \
  --pr-number <promotionPrNumber> --source-sha <developmentSha> \
  --base-sha <priorMainSha> --expected-head <promotionHeadSha> \
  --approval-json <exact-Principal-approval.json> --receipt <retained-full-receipt.json>
```

The retained `linktrend-staging-to-main.yml` filename is the receipt-only protected PR workflow, not a manual merge-dispatch interface. It checks trusted code against inert candidate/transition data and does not execute candidate code. Never dispatch it as a merge command.

---

## Failure modes

| Failure | Symptom | Lisa / operator action |
|---|---|---|
| Store unavailable / contract missing | Lisa `blocked_no_store` | Land IDE #23; point adapter at this contract + discover CLI |
| `expected_sha` / development tip mismatch | development tip drifted | Re-package; ask Carlos to Approve new package |
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


## Direct-main controller dispatch migration

Current output uses `developmentSha` and `controllerInputs`; the old `stagingSha` / `workflowInputs` consumer contract is retired. Inputs name `complete-main`, `program-lead`, `source_sha`, `base_sha`, `expected_head`, and `pr_number`. Lisa re-reads the current Development/main tips and exact promote PR head before presenting the bound approval. After Principal approval, the designated Program lead invokes the normal `delivery_controller.py complete-main` with the exact approval JSON and retained Full receipt. No GitHub Actions dispatch is needed to consume approval; never invoke the retained receipt-only workflow as a manual merge command. Older callers must fail closed until they consume this paired contract; do not relabel a staging package as Development.

The main receipt workflow remains an actual required protected PR check. It consumes the existing successful Full receipt plus its exact protected Development transition, never a fabricated success or a Full rerun. This source change neither dispatches that workflow nor authorizes paid checks or a live main operation.
