# Item 6 — Connect IDE Development as a five-provider consumer (Implementation Plan)

**Status:** Documentation only; implementation is not authorized by this document
**Orchestrator item:** Item 6
**PRD:** [`ITEM-6-CONNECT-IDE-DEVELOPMENT-PRD.md`](./ITEM-6-CONNECT-IDE-DEVELOPMENT-PRD.md)
**Issue:** [#311](https://github.com/linktrend/IDE-Development/issues/311)
**Branch:** `issue/311-item-6-connect-ide-development-five-provider-con`
**Worktree:** `/Users/linktrend/Projects/IDE Development/.git/linktrend-worktrees/issue-311-item-6-connect-ide-development-five-provider-con`
**Start commit:** `741e58922e7413c1097f4a58ea25e94a934af903`
**Start tree:** `1affbab9035df799fdb7d723d8518e54fa6a1c00`
**Date:** 2026-08-17 (Asia/Taipei)

This plan maps every `AC-I6-*` criterion to bounded work packets. It does not implement connectors, modify managed IDE files, change provider repositories, open a PR, merge, promote, deploy, or run Full.

**For later authorized implementers:** copy the [packet template](#9-reusable-packet-template) at execution. Fill identities from live `git rev-parse`. Do not copy historical Terra/Luna dispatch files under `docs/planning/`.

Accepted `v2.4.0` next-release documents live on `issue/307-create-living-next-ide-development-release-updat` at `3a5d15231d65b8549d64971960b2aeb617b58838` and are **not** on this branch. Item 6 follows that delivery policy: issue checkpoints only; one later Phase/Packager PR after `v2.4.0` source promote.

## 1. Objective

Deliver a pinned, fail-closed IDE Development **consumer** boundary for LiNKplatform, LiNKlibraries, LiNKbrain, LiNKskills, and LiNKautowork, with positive/denied/unavailable/fail-closed tests, without nesting `.ide-development/` into this repository and without colliding with WP-U03, WP-U08, or other `v2.4.0` managed surfaces.

## 2. Architecture

Pre-rollout source lives in a new non-managed module:

```text
core/link-integrations/
  README.md
  pins.mjs
  errors.mjs
  platform.mjs
  libraries.mjs
  brain.mjs
  skills.mjs
  autowork.mjs
  mcp.mjs
  index.mjs
tests/link-integrations/
  test-pins.mjs
  test-platform.mjs
  test-libraries.mjs
  test-brain.mjs
  test-skills.mjs
  test-autowork.mjs
  test-mcp.mjs
  fixtures/
```

Issue 244 `consumer-contracts.mjs` is provenance, not the file to merge. Re-read provider contracts at freeze time and rewrite against current pins.

Managed materialization (`core/managed-core/MANIFEST.json`, `core/managed-core/platforms/providers/`, installer destinations `.ide-development/providers/` for **other** repos) waits until after `v2.4.0` rollout.

## 3. Global constraints

- Repository: `linktrend/IDE-Development` only.
- Branching: `python3 scripts/gitops/create_issue_branch.py` / agentsetup. One `issue/<n>-<slug>` per packet.
- Ship = commit + push. No implementer PR. No Bugbot. No managed Fast/Full on checkpoints.
- No nested `.ide-development/` in this repo.
- No provider-repo edits.
- No `MANIFEST.json`, managed workflows, packager, or controller-state edits in pre-rollout packets.
- Cursor model for authorized implementation: `cursor-grok-4.6-high`.
- Continue bounded repair/review while findings remain actionable, in scope, and each cycle makes measurable progress. Stop only for repeated unresolved findings, no progress across consecutive cycles, a redesign or new-authority requirement, infrastructure retry exhaustion, or an explicit resource limit. The separate two-attempt infrastructure retry limit remains mandatory.
- Fail closed on identity, pin, policy, and malformed input. No prefer-incoming.

## 4. Two calendars (must not be mixed)

```text
PRE-ROLLOUT (safe now, after founder/Codex authorization of implementation)
  WP-I6-DOCS     this documentation checkpoint (Issue 311)
  WP-I6-S0       pin freeze + inventory (serial)
  WP-I6-S1..S5   five provider validators (parallel after S0)
  WP-I6-S6       obsolete-reference sweep + cross-cutting MCP/OKF tests
  STOP. Checkpoint only. No PR. No MANIFEST. No hosted CI.

WAIT FOR v2.4.0
  WP-U04 (in flight, Issue 308) → WP-U03 + WP-U08 → remaining Updates →
  WP-COMBINED Full → WP-RELEASE source promote of exact v2.4.0

POST-ROLLOUT (only after v2.4.0 is on IDE Development protected lines)
  WP-I6-MANIFEST   managed-core materialization for nine consumers
  WP-I6-INTEGRATE  Packager/Phase PR of Item 6 novel commits
  WP-I6-HOSTED     Fast on Phase PR; reuse the single final-combined exact-tree Full
```

Do not create `phase/next-ide-development-v2.4.0` from Item 6. That branch belongs to WP-U03.

## 5. Path ownership and collision map

### 5.1 Item 6 pre-rollout (writable)

| Path | Owner packet |
|---|---|
| `docs/ITEM-6-CONNECT-IDE-DEVELOPMENT-PRD.md` | WP-I6-DOCS only |
| `docs/ITEM-6-CONNECT-IDE-DEVELOPMENT-IMPLEMENTATION-PLAN.md` | WP-I6-DOCS only |
| `core/link-integrations/pins.mjs` | WP-I6-S0 |
| `core/link-integrations/errors.mjs` | WP-I6-S0 |
| `core/link-integrations/README.md` | WP-I6-S0 (created), WP-I6-S6 (reference sweep) |
| `core/link-integrations/platform.mjs` | WP-I6-S1 |
| `core/link-integrations/libraries.mjs` | WP-I6-S2 |
| `core/link-integrations/brain.mjs` | WP-I6-S3 |
| `core/link-integrations/skills.mjs` | WP-I6-S4 |
| `core/link-integrations/autowork.mjs` | WP-I6-S5 |
| `core/link-integrations/mcp.mjs` | WP-I6-S6 |
| `core/link-integrations/index.mjs` | WP-I6-S6 (barrel after S1–S5 exist) |
| `tests/link-integrations/test-<name>.mjs` | matching S0–S6 |
| `tests/link-integrations/fixtures/` | S0 creates layout; each S1–S5 owns its subdirectory |

### 5.2 Forbidden until post-`v2.4.0` (Item 6 must not write)

| Path | Current owner |
|---|---|
| `scripts/gitops/packager_*.py`, phase record schemas, managed Fast trigger templates | WP-U03 (Issue 309) |
| Controller state directory, managed PR/branch inventory/cleanup | WP-U08 (Issue 310) |
| `core/github/managed-workflows/linktrend-review-ready-publisher.yml`, `scripts/gitops/readiness_status.py`, `scripts/gitops/review_ready_dispatch.py`, related tests | WP-U04 (Issue 308, already dirty vs `origin/development`) |
| `core/managed-core/MANIFEST.json` | WP-U04 now; later WP-I6-MANIFEST only |
| `core/managed-core/platforms/**` | `v2.4.0` managed packets; later WP-I6-MANIFEST |
| `core/github/managed-workflows/**` except as above | `v2.4.0` Updates 1/3/5/7 |
| `scripts/ide-development.py` / installer tests | `v2.4.0` installer packets; later WP-I6-MANIFEST |
| `core/library/library-client.mjs` and `core/managed-core/platforms/library/**` | Installed Wave-1 dual-home; not an Item 6 pre-rollout write |
| Any path under LiNKplatform / LiNKlibraries / LiNKbrain / LiNKskills / LiNKautowork | Provider owners |

### 5.3 Read-only inputs

- Provider GitHub `development` tips at freeze time (gh/git fetch; no commit in those repos).
- Issue 244 files as provenance (`core/link-integrations/consumer-contracts.mjs` at `248d30b`).
- Issue 307 next-release docs at `3a5d15231d65b8549d64971960b2aeb617b58838`.

## 6. Work-packet matrix (every AC mapped)

| Packet | Calendar | Depends on | PRD acceptance | Parallel? | Full? |
|---|---|---|---|---|---|
| WP-I6-DOCS | Pre-rollout docs | none | `AC-I6-DOC-01`–`05` | No | No |
| WP-I6-S0 | Pre-rollout source | Founder/Codex authorization after docs acceptance | `AC-I6-REL-01`, `AC-I6-REL-02`, `AC-I6-REL-03` (module skeleton), `AC-I6-REL-07` | Serial first | No |
| WP-I6-S1 | Pre-rollout source | WP-I6-S0 | `AC-I6-POS-platform`, `AC-I6-DEN-platform`, `AC-I6-UNA-platform`, `AC-I6-FC-platform` | Parallel with S2–S5 | No |
| WP-I6-S2 | Pre-rollout source | WP-I6-S0 | `AC-I6-POS-libraries`, `AC-I6-DEN-libraries`, `AC-I6-UNA-libraries`, `AC-I6-FC-libraries` | Parallel with S1, S3–S5 | No |
| WP-I6-S3 | Pre-rollout source | WP-I6-S0 | `AC-I6-POS-brain`, `AC-I6-DEN-brain`, `AC-I6-UNA-brain`, `AC-I6-FC-brain` | Parallel with S1–S2, S4–S5 | No |
| WP-I6-S4 | Pre-rollout source | WP-I6-S0 | `AC-I6-POS-skills`, `AC-I6-DEN-skills`, `AC-I6-UNA-skills`, `AC-I6-FC-skills` | Parallel with S1–S3, S5 | No |
| WP-I6-S5 | Pre-rollout source | WP-I6-S0 | `AC-I6-POS-autowork`, `AC-I6-DEN-autowork`, `AC-I6-UNA-autowork`, `AC-I6-FC-autowork` | Parallel with S1–S4 | No |
| WP-I6-S6 | Pre-rollout source | WP-I6-S1 through S5 | `AC-I6-X-01`, `AC-I6-X-02`, `AC-I6-X-03`, `AC-I6-X-04`, `AC-I6-REL-04`, `AC-I6-REL-05` | Serial after S1–S5 | No |
| WP-I6-MANIFEST | Post-`v2.4.0` | `v2.4.0` on protected lines; WP-I6-S6 | `AC-I6-X-05` | No | No |
| WP-I6-INTEGRATE | Post-`v2.4.0` | WP-I6-S6 novel commits + Packager of that era | `AC-I6-REL-06`, `AC-I6-X-06` (PR half) | No | No |
| WP-I6-HOSTED | Post-`v2.4.0` | WP-I6-INTEGRATE Phase PR | `AC-I6-X-06` (hosted half) | No | Reuse the single final-combined exact-tree Full; no standalone Item 6 Full |

Trace: `AC-I6-DOC-*` (5), `AC-I6-REL-*` (7), twenty POS/DEN/UNA/FC IDs, `AC-I6-X-*` (6) = 38 IDs, each named in exactly one owning packet.

## 7. Work packages

### WP-I6-DOCS — this documentation checkpoint

| Field | Value |
|---|---|
| Repository | `linktrend/IDE-Development` |
| Issue / branch / worktree | 311 / `issue/311-item-6-connect-ide-development-five-provider-con` / path in header |
| Start commit / tree | `741e58922e7413c1097f4a58ea25e94a934af903` / `1affbab9035df799fdb7d723d8518e54fa6a1c00` |
| Owned paths | the two `docs/ITEM-6-*.md` files only |
| Focused tests | relative link resolution; `git diff --check` |
| Fast / Full | Forbidden |
| Acceptance | `AC-I6-DOC-01`–`05` |
| Rollback | Leave issue branch unmerged |
| Stop | After commit + push with clean remote equality. Do not call `review-ready`. Do not open a PR |

### WP-I6-S0 — freeze current provider pins

| Field | Value |
|---|---|
| Depends on | Codex acceptance of this PRD/plan and founder authorization to implement |
| Owned paths | `core/link-integrations/{pins,errors,README}.mjs/md`; `tests/link-integrations/test-pins.mjs`; `tests/link-integrations/fixtures/README.md` |
| Required work | Read each provider GitHub `development` tip; record repository/commit/tree; refuse Issue 244 SHAs; export `FROZEN_PROVIDERS`; document that local sibling HEADs are not pins; create `ConsumerContractError` with stable `code` |
| Focused tests | `test-pins.mjs`: five keys; each SHA matches `^[a-f0-9]{40}$`; none equal Issue 244 table; pins object frozen |
| Acceptance | `AC-I6-REL-01`, `AC-I6-REL-02`, `AC-I6-REL-03` (no transport APIs in skeleton), `AC-I6-REL-07` |
| Rollback | Delete the new directory on the issue branch; do not revert `development` |
| Stop | If a provider `development` tip cannot be read, or if a pin would equal Issue 244, call `blocked` |

Pin freeze command (read-only):

```bash
gh api repos/linktrend/<Provider>/commits/development --jq '{sha:.sha,tree:.commit.tree.sha}'
```

Do not `git push` inside provider clones.

### WP-I6-S1 — LiNKplatform identity / permissions / capabilities

| Field | Value |
|---|---|
| Files | Create `core/link-integrations/platform.mjs`; `tests/link-integrations/test-platform.mjs`; `tests/link-integrations/fixtures/platform/` |
| Consumes | `FROZEN_PROVIDERS.platform`, `ConsumerContractError` |
| Produces | `validatePlatformIdentity(claim, context) → frozen { actorId, runtimeBindingId, orgId }` |
| Positive | AuthClaims `platform.auth-claims/1.1.0` with matching audience, service scope, capability, org, future `expiresAt` |
| Denied | Missing capability, wrong audience, wrong org, `internal`/`actorKind` illegal combination |
| Unavailable | Fixture where required claim material is absent / provider reports identity service unavailable — stable `identity_unavailable` (not success) |
| Fail-closed | expired; unknown field; sensitive key; wrong `claimContractVersion`; non-object |
| Command | `node --test tests/link-integrations/test-platform.mjs` |
| Do not | Call Platform HTTP, mint JWTs, edit LiNKplatform |

### WP-I6-S2 — LiNKlibraries discovery / retrieval references

| Field | Value |
|---|---|
| Files | Create `core/link-integrations/libraries.mjs`; `tests/link-integrations/test-libraries.mjs`; `tests/link-integrations/fixtures/libraries/` |
| Consumes | `FROZEN_PROVIDERS.libraries` |
| Produces | `validateLibraryReference(facts) → frozen facts` |
| Positive | Source commit/tree equal the freeze pin; git SHAs well-formed; sha256 digests well-formed; `receiptType` `verified_cache` or `consumption` |
| Denied | Selectable policy fail: metadata-only / quarantined / superseded encoded as denied (`library_not_selectable`) |
| Unavailable | Pin present in module but fixture source does not match pin (`library_reference_not_frozen` or `library_unavailable`) |
| Fail-closed | unknown field `closureDigest`; `receiptType: execute`; unpinned SHA; invalid digest; sensitive key |
| Do not | Modify `core/library/library-client.mjs` or managed `platforms/library/`; do not git-fetch LiNKlibraries in tests |

### WP-I6-S3 — LiNKbrain knowledge / coordination

| Field | Value |
|---|---|
| Files | Create `core/link-integrations/brain.mjs`; `tests/link-integrations/test-brain.mjs`; `tests/link-integrations/fixtures/brain/` |
| Produces | `validateBrainProjection(value) → frozen { projectionRef, handoffRef? }` |
| Positive | `contractVersion` `2.0.0`, `authority` `advisory`, `executionAuthority` `none`, bounded summary |
| Denied | Projection well-formed but `authority` not advisory or execution authority not `none` |
| Unavailable | Missing `projectionRef` classified unavailable/missing, not success |
| Fail-closed | `transcript` / `prompt` / unknown field; wrong contract version |
| Do not | Execute Brain tools; copy raw conversation |

### WP-I6-S4 — LiNKskills discovery / validation / execution addressing

| Field | Value |
|---|---|
| Files | Create `core/link-integrations/skills.mjs`; `tests/link-integrations/test-skills.mjs`; `tests/link-integrations/fixtures/skills/` |
| Produces | `validateSkillsRelease`, `validateSkillsTelemetry` |
| Positive | published + qualified + available; `sha256:` digests; fragmentLevel 0–6; telemetry score 10 without issue |
| Denied | `qualification` not `qualified`, or lifecycle not `published` |
| Unavailable | `availability !== available` → `skills_release_unavailable` |
| Fail-closed | fragmentLevel 7; `latest` ids; sensitive fields; score 10 with issue object |
| Do not | Add a local catalogue; invoke `skills_run_*`; edit LiNKskills |

Execution in Item 6 means **addressing an immutable release for the requesting agent to run**, not running the skill inside IDE Development.

### WP-I6-S5 — LiNKautowork requests / status / handoffs / receipts

| Field | Value |
|---|---|
| Files | Create `core/link-integrations/autowork.mjs`; `tests/link-integrations/test-autowork.mjs`; `tests/link-integrations/fixtures/autowork/` |
| Produces | `validateAutoworkReceipt` (and request/handoff validators if the pin-time contract splits them) |
| Positive | `accepted` / `completed` with opaque ids and bounded result |
| Denied | Well-formed request that the receipt marks `failed` for policy (not coerced to completed) |
| Unavailable | `status: unavailable` accepted as that status, not as success |
| Fail-closed | unknown field; `secret` in result; malformed opaque id; unknown status string |
| Do not | Open Autowork jobs against production; edit LiNKautowork |

Re-verify the receipt `contractVersion` string against LiNKautowork `9caab9aa33de5f96e33d67d880f2934dc6fd9fef` (or newer `development` at S0 freeze). Do not copy Issue 244's `provider-contract/v1` unless that file still says so.

### WP-I6-S6 — obsolete references, MCP/OKF, barrel, self-install guard

| Field | Value |
|---|---|
| Files | Create `mcp.mjs`, `index.mjs`; update README; `tests/link-integrations/test-mcp.mjs`; `tests/link-integrations/test-self-install-guard.mjs` |
| Work | `negotiateMcp('2026-07-28','modern')` passes; legacy/session fails closed; OKF optional mapping cannot grant Brain execution; grep Item 6 source for Issue 244 SHAs and `.ide-development/` install instructions targeting this repo; assert repo root has no `.ide-development/` |
| Acceptance | `AC-I6-X-01`–`04`, `AC-I6-REL-04`, `AC-I6-REL-05` |
| Do not | Rewrite `CURRENT-STATUS.md` / Technical PRD; do not add MANIFEST entries |

Self-install guard test:

```bash
node --test tests/link-integrations/test-self-install-guard.mjs
# asserts: !existsSync('.ide-development') at repo root
# asserts: index.mjs has no install-self helper
```

After S6, run all `tests/link-integrations/*.mjs`, `git diff --check`, and `git status` (owned paths only). Checkpoint + push. **Do not** `completion_gate.py review-ready` until post-`v2.4.0` integration is authorized. Ordinary pre-rollout completion is `checkpoint` only.

### WP-I6-MANIFEST — managed materialization (WAIT)

| Field | Value |
|---|---|
| When | After exact `v2.4.0` is on IDE Development `development` (and as required staging/main) |
| Files | `core/managed-core/platforms/providers/**`, `core/managed-core/MANIFEST.json` destinations `.ide-development/providers/` and `.cursor/` only as declared for **consumers**; installer tests on **disposable** repos |
| Forbidden | `python3 scripts/ide-development.py install --repo` pointing at this repository |
| Acceptance | `AC-I6-X-05` |
| Collision note | Rebase/layer onto post-`v2.4.0` `MANIFEST.json` (WP-U04 will have changed it). Deliberate conflict repair. Never prefer-incoming |

### WP-I6-INTEGRATE — Packager PR (WAIT)

| Field | Value |
|---|---|
| When | After WP-I6-S6 (and WP-I6-MANIFEST if that is in the same Phase) and after `v2.4.0` Packager exists |
| Work | `write-evidence` + `review-ready` on the issue branch; independent Packager opens draft PR. Implementer does not open the PR |
| Acceptance | `AC-I6-REL-06`, PR half of `AC-I6-X-06` |
| Stop | If Packager is still the v2.3.8 `packager_discover.py` path, do not treat it as Update 3; wait for WP-U03 |

### WP-I6-HOSTED — Fast / Full (WAIT)

| Field | Value |
|---|---|
| Fast | Only on the Packager Phase/review PR |
| Full | Do not run a separate Item 6 Full. Reuse the single final-combined exact-tree Full unless Carlos later authorizes a specific exception |
| Acceptance | Hosted half of `AC-I6-X-06` |

## 8. Safe parallelism and ordering

```text
WP-I6-DOCS
    |
    |  (Codex acceptance + founder implementation authorization)
    v
WP-I6-S0          SERIAL
    |
    +--> WP-I6-S1 Platform
    +--> WP-I6-S2 Libraries     parallel; separate worktrees; owned files only
    +--> WP-I6-S3 Brain
    +--> WP-I6-S4 Skills
    +--> WP-I6-S5 Autowork
    |
    v
WP-I6-S6          SERIAL
    |
    X  STOP until v2.4.0 source promote
    |
WP-I6-MANIFEST → WP-I6-INTEGRATE → WP-I6-HOSTED
```

Parallel S1–S5 rules:

- Separate issue branches/worktrees from the **same** S0 tip.
- No writes outside the owned file list.
- Do not edit `pins.mjs` after S0 freeze except via a new S0 repair issue.
- Integrate S1–S5 serially onto one follow-up branch before S6, or have S6 live on a branch that layers the five exact novel commit ranges. Never prefer-incoming on overlap.

Item 6 pre-rollout may run **at the same time as WP-U03 and WP-U08** because paths are disjoint. It must not integrate onto `phase/next-ide-development-v2.4.0`.

## 9. Reusable packet template

Copy into the packet issue's working notes at execution. Fill SHA/tree fields only from live git.

```markdown
# Packet <WP-I6-*> — <title>

## Identity (fill at execution only)

| Field | Value |
|---|---|
| Packet ID | WP-I6-DOCS / WP-I6-S0 … S6 / WP-I6-MANIFEST / WP-I6-INTEGRATE / WP-I6-HOSTED |
| PRD acceptance | AC-I6-… (copy the matrix row; do not drop IDs) |
| Calendar | pre-rollout source OR post-v2.4.0 integration |
| Depends on | packet IDs from the matrix |
| Repository | `linktrend/IDE-Development` |
| Issue | created via `python3 scripts/gitops/create_issue_branch.py` |
| Branch | `issue/<n>-<slug>` |
| Worktree | `git rev-parse --show-toplevel` |
| Cursor model | `cursor-grok-4.6-high` |
| Parallel lane | `<lane id or serial>` |
| Start commit | `<git rev-parse origin/development>` |
| Start tree | `<git rev-parse <start-commit>^{tree}>` |
| Accepted prerequisite commits | `<exact ordered commits, or none>` |
| Novel packet commit range | `<fill at handoff>` |
| Exact HEAD after packet | `<git rev-parse HEAD>` |
| Exact tree after packet | `<git rev-parse HEAD^{tree}>` |
| Remote equality | `<git rev-parse HEAD>` == `<git rev-parse origin/<branch>>` |

## Assignment

Implement only owned paths. Checkpoint = commit + push. No PR, no Bugbot, no managed Fast/Full. Pre-rollout packets stop at checkpoint. Post-v2.4.0 packets use `completion_gate.py write-evidence` then `review-ready` (or `blocked`).

## Owned paths

Copy from the matching work-package section. Do not expand into `core/managed-core/`, `core/github/managed-workflows/`, `scripts/gitops/packager_*`, controller state, installer, or provider repositories unless this is WP-I6-MANIFEST after v2.4.0.

## Required implementation

Trace every required-behaviour item and every POS/DEN/UNA/FC test from the named PRD IDs. Re-read provider contracts at the S0 pin SHAs. Do not copy Issue 244 pins. Do not add a numbered v2.4.0 update.

## Focused tests

Run only packet-owned `node --test tests/link-integrations/test-*.mjs` plus `git diff --check`. Do not run Full. Do not call live providers.

## Fast / Full

- Pre-rollout: forbidden.
- Fast: WP-I6-HOSTED after Packager PR.
- Full: forbidden in WP-I6-S* and WP-I6-DOCS. WP-I6-HOSTED reuses the single final-combined exact-tree Full; it does not start a standalone Item 6 Full without a later explicit founder exception.

## Prohibited

- Nested `.ide-development/` in `linktrend/IDE-Development`
- Provider-repo commits
- Implementer-opened delivery PRs, self-merge, self-review, prefer-incoming
- Staging/main promotion
- Merging PR 245
- Editing WP-U03 / WP-U08 / WP-U04 owned paths
- Production provider traffic
- Filling another packet's start SHA in this plan file

## Acceptance

All PRD IDs in the matrix row. Fail closed on pin, identity, policy, and malformed input.

## Rollback

Leave the issue branch unmerged. Preserve unique work. Do not revert protected branches.

## Stop conditions

Stop and run `python3 scripts/gitops/completion_gate.py blocked` when:

- a provider pin cannot be proven from GitHub `development`
- a required POS/DEN/UNA/FC test cannot be expressed without live production calls
- path ownership collides with an in-flight v2.4.0 packet
- actionable findings repeat without resolution, consecutive cycles make no measurable progress, repair requires redesign or new authority, infrastructure retries are exhausted, or an explicit resource limit is reached
- nested `.ide-development/` would be required for the test to pass

## Handoff

Commit and push. Report start commit/tree, novel range, final local/remote SHA and tree, changed files, commands and exit codes, negative probes, clean status, and blocker or `none`. Pre-rollout: no PR. Post-v2.4.0: Packager consumes Review Ready.
```

## 10. Review, repair, evidence, rollback, stop

| Gate | Rule |
|---|---|
| Review | Codex supervises this documentation packet. Every source checkpoint receives an independent exact-head review before acceptance; post-rollout Packager review remains separate |
| Repair | ≤3 ordinary cycles on the same issue branch; then `blocked`. No prefer-incoming |
| Evidence | Pre-rollout: commands, exit codes, pin SHAs in the packet handoff. Post-v2.4.0: `completion_gate.py write-evidence` bound to exact HEAD |
| Rollback | Unmerged issue branch is the rollback. Do not force-push protected lines. Do not delete unique work |
| Stop | See template stop conditions. Also stop if asked to install this repo as a consumer of itself |

## 11. Focused test inventory (source packets)

Run from repo root after each source packet:

```bash
node --test tests/link-integrations/test-pins.mjs
node --test tests/link-integrations/test-platform.mjs
node --test tests/link-integrations/test-libraries.mjs
node --test tests/link-integrations/test-brain.mjs
node --test tests/link-integrations/test-skills.mjs
node --test tests/link-integrations/test-autowork.mjs
node --test tests/link-integrations/test-mcp.mjs
node --test tests/link-integrations/test-self-install-guard.mjs
git diff --check
```

Expected for this **documentation** packet: the `tests/link-integrations/` directory does not exist yet. Do not create it here.

## 12. Explicit exclusions (plan-level)

- Opening or merging a PR from Issue 311
- Implementing any validator in Issue 311
- Running Full for this documentation package
- Touching other repositories
- Using Issue 244 as the merge source
- Rewriting historical or navigation documents
- Freezing future implementation-packet start SHAs in this plan (S0 freeze happens at S0 execution)
- Executing S0–S6 from this documentation branch. The founder has separately authorized those source packets through bounded Cursor/Grok issue branches

## 13. Definition of done

### This documentation task (Issue 311)

- PRD and this plan exist with complete `AC-I6-*` traceability
- Packet template present; future start SHA/tree remain execution-time except Issue 311's own start identity
- No product/CI/workflow/script/managed-core/runtime change
- Documentation link check and `git diff --check` pass
- Branch committed and pushed; no PR opened

### Item 6 product outcome (later packets)

All `AC-I6-*` IDs met: five current pins, four-outcome tests each, no nested self-install, no provider mutation, managed materialization only after `v2.4.0`, Packager—not implementer—opens the PR.

## 14. Change log

| Date | Change | Actor |
|---|---|---|
| 2026-08-17 | Author Item 6 implementation plan from start `741e58922e7413c1097f4a58ea25e94a934af903` | Issue 311 documentation agent (Cursor Grok 4.6 High) |
