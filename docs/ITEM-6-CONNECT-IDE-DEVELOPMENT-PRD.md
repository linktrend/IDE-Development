# Item 6 — Connect IDE Development as a five-provider consumer (PRD)

**Status:** Documentation only; implementation is not authorized by this document
**Orchestrator item:** Item 6
**Issue:** [#311](https://github.com/linktrend/IDE-Development/issues/311)
**Branch:** `issue/311-item-6-connect-ide-development-five-provider-con`
**Worktree:** `/Users/linktrend/Projects/IDE Development/.git/linktrend-worktrees/issue-311-item-6-connect-ide-development-five-provider-con`
**Start commit:** `741e58922e7413c1097f4a58ea25e94a934af903` (`origin/development` at packet start)
**Start tree:** `1affbab9035df799fdb7d723d8518e54fa6a1c00`
**Installed line:** managed-core `v2.3.8` (`VERSION` / `core/managed-core/VERSION`)
**Date:** 2026-08-17 (Asia/Taipei)
**Companion plan:** [`ITEM-6-CONNECT-IDE-DEVELOPMENT-IMPLEMENTATION-PLAN.md`](./ITEM-6-CONNECT-IDE-DEVELOPMENT-IMPLEMENTATION-PLAN.md)

This PRD defines the consumer-side connection of **IDE Development** to five LiNK providers. It does not implement connectors, change managed IDE files, mutate provider repositories, open a PR, merge, promote, deploy, or run Full.

The supervising Codex agent remains responsible for acceptance of this documentation packet.

## 1. Objective

Make IDE Development a **fail-closed consumer** of exactly these five providers:

| Provider | Consumer use in IDE Development |
|---|---|
| **LiNKplatform** | Identity, permissions, and capabilities required at the transport/authorization boundary |
| **LiNKlibraries** | Discovery and retrieval of verified library entries (revision-2 immutable references) |
| **LiNKbrain** | Knowledge and coordination projections that remain advisory |
| **LiNKskills** | Discovery, validation, and execution addressing of immutable skill releases |
| **LiNKautowork** | Requests, status, handoffs, and receipts |

Replace obsolete consumer pins and references. Prove **positive**, **denied**, **unavailable**, and **fail-closed** behaviour for each provider. Fix only genuine IDE Development consumer defects. Do not change provider repositories.

IDE Development remains the **system source and internal self-verification target**. It must never receive a nested `.ide-development/` install of itself.

Item 6 is **not** a numbered `v2.4.0` update. It must stay disjoint from active `v2.4.0` packets **WP-U03** and **WP-U08**, and must not compete for managed-core, workflow, packager, or controller surfaces until `v2.4.0` has rolled out. Pre-rollout source work may proceed only on disjoint non-managed paths. Final integration, installer materialization, hosted CI, and any PR into `development` wait for that rollout.

## 2. Authority and related documents

| Document | Role for Item 6 |
|---|---|
| This PRD | Product definition and acceptance IDs `AC-I6-*` |
| Companion implementation plan | Work packets, path ownership, ordering, tests, rollback |
| Root [`AGENTS.md`](../AGENTS.md) | System source ≠ consumer install; no nested `.ide-development/` |
| [`contracts/MANAGED-CORE-V2.md`](./contracts/MANAGED-CORE-V2.md) | Same self-verification rule; consumer install layout applies to the nine consumers, not this repo |
| [`GITOPS-CONSUMER-ROLLOUT.md`](./GITOPS-CONSUMER-ROLLOUT.md) | Locked nine-consumer install order; IDE Development is absent on purpose |
| [`IDE-DEVELOPMENT-TECHNICAL-PRD.md`](./IDE-DEVELOPMENT-TECHNICAL-PRD.md) | As-built v2 reference (Wave-1 library client only). Not rewritten by this PRD |
| [`adr/0002-shared-component-template-asset-library.md`](./adr/0002-shared-component-template-asset-library.md) | Canonical LiNKlibraries remote and cache rules |
| Accepted `v2.4.0` next-release set on `issue/307-create-living-next-ide-development-release-updat` at `3a5d15231d65b8549d64971960b2aeb617b58838` (tree `6b9f73f1e78ae4abda3b78b939adc190b6d0842a`) | Frozen specification, PRD, and plan. **Not present on `origin/development` at Item 6 start.** Cite by that branch/SHA; do not copy those files into this packet |

`v2.4.0` freeze identities recorded by Issue 307 (do not restamp here):

- Numbered-update freeze: commit `09a37b3ae4d6b05db85d0173d7c8dcf17cac2b59` / tree `4a628bd3966abd4bffca0be210b4cbd7470501bb`
- Accepted amendment A1: commit `472c7cc6ff5a6660dc99cfb56c4d529855e3a8f8` / tree `e1195f2571d7fac571fd00cf6d328f61a6dadc0b`

Item 6 does not add, remove, or weaken numbered Updates 1–10.

## 3. Current verified state versus assumptions

Inspection was performed from this packet's start commit/tree against `origin/development`, the Issue 307 living documents, Issue 244 provenance, local sibling clones, and GitHub `development` tips. Facts below are verified. Anything not in this section is an assumption and must be re-verified before implementation pins are frozen.

### 3.1 Verified — IDE Development (`origin/development`)

| Fact | Evidence |
|---|---|
| Tip SHA / tree | `741e58922e7413c1097f4a58ea25e94a934af903` / `1affbab9035df799fdb7d723d8518e54fa6a1c00` |
| Package identity | `v2.3.8` |
| Nested `.ide-development/` | Absent at repo root (correct) |
| `core/link-integrations/` | Absent |
| Library surface | `core/library/library-client.mjs` + `library-contract.json` (Wave-1 catalog/entry sparse-fetch). Dual-homed into `core/managed-core/platforms/library/` and `MANIFEST.json` destinations `.cursor/library/` and `.ide-development/library/` |
| Five-provider pin table | Absent on this line |
| Next-release `v2.4.0` docs | Absent on this line |
| Tests covering five-provider consumer outcomes | Absent on this line |
| `docs/CURRENT-STATUS.md` | Still dated 2026-08-03 and describes portable `v2.1.0` / WP04 pending. Historical operator surface; this PRD does not rewrite it |

### 3.2 Verified — accepted `v2.4.0` and active packets

| Fact | Evidence |
|---|---|
| Living next-release docs | `docs/NEXT-IDE-DEVELOPMENT-RELEASE-SPECIFICATION.md`, `...-PRD.md`, `...-IMPLEMENTATION-PLAN.md` on Issue 307 branch tip `3a5d15231d65b8549d64971960b2aeb617b58838` |
| WP-U03 ownership | Packager/coordinator: `scripts/gitops/packager_*.py`, phase records, managed Fast trigger templates. Parallel with WP-U08; integrate before WP-U09 |
| WP-U08 ownership | Controller state directory, PR/branch inventory, reconciliation report. Same wave as WP-U03 |
| WP-U04 in flight | Issue 308 already differs from `origin/development` on managed workflows, `core/managed-core/MANIFEST.json`, gitops publisher scripts, and doctrine copies |
| WP-U03 / WP-U08 issue branches | Issue 309 and Issue 310 exist and currently match `origin/development` (no novel commits at inspection) |
| Safe parallelism rule | Only WP-U03 and WP-U08 are authorized concurrent **core** implementation packets. Item 6 may run concurrently **only** if it writes disjoint non-managed paths and does not open a `development` PR |

### 3.3 Verified — prior five-provider attempt (Issue 244 / PR 245)

Branch `issue/244-add-ide-development-five-provider-consumer-conne` (tip `248d30b`) and open PR [#245](https://github.com/linktrend/IDE-Development/pull/245) add `core/link-integrations/consumer-contracts.mjs`, tests, a revision-2 library client, and **managed-core MANIFEST / `platforms/providers/` materialization**.

That branch is **not** based on current `v2.3.8`. It must not be merged as the Item 6 delivery. Treat it as provenance only.

Issue 244 frozen pins (obsolete versus current provider `development` tips):

| Provider | Issue 244 commit / tree | Current `origin/development` commit / tree (2026-08-19) |
|---|---|---|
| LiNKplatform | `6a7114674c23fc6b9ba9ae2b3277b8aec7a3fb15` / `91d565a988150da39a13b66c4bcd51f7bc47c9be` | `adbabf7d399cbfe5c1056d275c3d98eb480397cc` / `b76993f458b6dbed5d2c3e09c2c5e8ad87c6a45d` |
| LiNKlibraries | `b2d2bbb035c6e6a3f859480ce57f12e0882dd3f0` / `2701e6a190468f437102946425a64e890eed6690` | `4cbe7fb174aba4b159d6c37ba1ef65fd3221510f` / `60e582fbd1ce988538b650c99878e700c6cfa0d2` |
| LiNKbrain | `43887ffc3b51ef2e54c30820d41cab67f54d5d0f` / `40c7acfcd7b204f19a1278e6801033c4ee64b369` | `9042e668dd0c7cef232cb427ffc9c76f06a7a446` / `303a15936932fb5a54b208c934a6d511045cc8e4` |
| LiNKskills | `93ec4b9df2ebe2a9d9b412fb8b3bcde2aa8e97f3` / `1845b996a7ec4d217a57e6f66574d6c5d676bb67` | `e3d80fd22a05a4f68207e130c50b772b5acffda4` / `69a131b46a73a4ef724694bfe240b1a11652bcc9` |
| LiNKautowork | `10f75a8d840160a10d131371e94a338dfd1ebb4a` / `c433907818f2cd4adbfdd61549f9f91396e31819` | `79ee98eb3bd1ae0cce9d34872e90fe7101a9f353` / `deb37e4f3a29339b35613ee799d461c74bb7b585` |

Issue 244 also materializes the consumer module into `.ide-development/providers/` for **other** repositories. That destination is valid for the nine consumers after an authorized install. It is **not** a license to install `.ide-development/` into IDE Development.

### 3.4 Verified — current provider contract shapes (read-only)

These shapes were observed in sibling provider checkouts / GitHub `development` tips. They are **shape facts**, not Item 6 pin freezes. Implementation must re-read the named provider commit/tree before freezing consumer pins.

| Provider | Observed contract facts | Consumer implication |
|---|---|---|
| LiNKplatform | AuthClaims `platform.auth-claims/1.1.0`; envelope `platform.auth-token-envelope/0.1.0` | Validate claims/capability/audience/org; do not mint identity; do not store secrets |
| LiNKlibraries | Revision-2 schemas and materialization receipts; canonical remote `https://github.com/linktrend/LiNKlibraries.git` | Consume immutable commit/tree/digest references; Wave-1 `indexes/catalog.json` client remains the installed dual-homed client until a later managed migration |
| LiNKbrain | `contractVersion` `2.0.0`; `authority: advisory`; MCP `2026-07-28` sessionless | Advisory projections only; no execution authority; session `initialize` forbidden at the modern boundary |
| LiNKskills | Provider v0.2 / `skills.api.v0.2`; MCP `2026-07-28`; immutable release URIs; restricted tools; `skills_run_*` not on v0.2 | Discover/validate/address exact releases; requesting agent executes; no local full catalogue/pack |
| LiNKautowork | Deterministic provider plane present on `origin/development` `79ee98eb3bd1ae0cce9d34872e90fe7101a9f353` | Consume request/status/handoff/receipt objects; no provider-side mutation from this repo |

Local sibling clones for LiNKlibraries, LiNKbrain, and LiNKautowork were **ahead of** their `origin/development` at inspection. Item 6 pins **GitHub `development` tips**, not unpushed local HEADs.

### 3.5 Assumptions (must not be treated as facts)

| ID | Assumption | Required verification before implementation freeze |
|---|---|---|
| A-01 | Issue 244 validator field sets still match current provider schemas | Diff each provider contract at the chosen pin SHA against `consumer-contracts.mjs` provenance |
| A-02 | `provider-contract/v1` remains the Autowork receipt contract id | Confirm on LiNKautowork `79ee98eb…` (or newer `development` tip at freeze time) |
| A-03 | OKF `0.2` remains optional mapping, never a second source of truth | Confirm against current LiNKskills and LiNKbrain docs at pin time |
| A-04 | Wave-1 `library-client.mjs` can coexist with a revision-2 reference validator under `core/link-integrations/` until post-`v2.4.0` managed migration | Confirm no MANIFEST destination collision and no dual-authority catalog behaviour |
| A-05 | PR 245 can remain open as frozen provenance without being merged | Codex/founder disposition; this PRD recommends do-not-merge |
| A-06 | No live stage/E2E/production provider endpoints are required for Item 6 source tests | Hold: tests use fixtures and recorded pins only |

## 4. Provider versus consumer ownership

| Owner | Owns | Must not do |
|---|---|---|
| **LiNKplatform** | Identity issuance, AuthClaims, capability grants, token envelope | IDE Development must not mint claims, store signing keys, or patch Platform |
| **LiNKlibraries** | Catalog, entries, Librarian merge, revision-2 schemas | IDE Development must not push `development`, invent catalog rows, or change Librarian |
| **LiNKbrain** | Knowledge/coordination projections, advisory authority | IDE Development must not treat Brain as an executor or copy transcripts/raw content |
| **LiNKskills** | Skill releases, qualification, fragment addressing | IDE Development must not keep a local full pack or add `skills_run_*` on the v0.2 surface |
| **LiNKautowork** | Request/status/handoff/receipt provider plane | IDE Development must not implement Autowork internals or close Autowork work as itself |
| **IDE Development (this repo)** | Consumer validators, pins, fail-closed tests, later managed materialization **for other repos** | Must not install nested `.ide-development/`; must not change the five provider repos; must not open implementer PRs |
| **Nine GitOps consumers** | Their application code and installed managed core after authorized rollout | Out of Item 6 source scope |
| **Founder / Principal** | Production activation, consumer mutation, `v2.4.0` publication, unique-work keep/delete | Not delegated to this packet |

IDE Development is a **consumer of the five providers** and a **producer of managed core for nine other repositories**. Those two roles must not be collapsed.

## 5. Functional requirements

### FR-I6-REL — Release-wide consumer guarantees

1. Connect only the five providers named in §1.
2. Pin each provider by exact GitHub repository, commit SHA, and tree SHA. Live `HEAD` or `latest` is not a pin.
3. Fail closed on missing, stale, forged, wrong-audience, expired, unqualified, or unpublished provider material.
4. Keep Brain advisory (`authority=advisory`, `executionAuthority=none`).
5. Require Platform-issued identity at any transport boundary; the consumer module itself has no credentials, network client, or secret store.
6. Address skills by immutable release + progressive fragments; do not retain a local skill catalogue or full remote pack.
7. Treat Autowork results as bounded receipts (`accepted` / `completed` / `failed` / `unavailable`); never as a license to mutate Git, Ledger, or Gates.
8. Consume LiNKlibraries through immutable revision-2 references (source commit/tree, release digests, receipt type). Do not execute library payloads from this module.
9. Replace obsolete Issue 244 pins and any remaining “IDE Development is a consumer install target” language that this work introduces. Do not rewrite historical/navigation documents in this documentation packet.
10. Never create, install, or verify a nested `.ide-development/` tree inside `linktrend/IDE-Development`.

### FR-I6-PLATFORM — LiNKplatform

The consumer must validate a bounded AuthClaims `1.1.0` object (and, when present, refuse unsigned/forged envelope misuse) for actor, audience, service scope, capability, organization, and expiry. Wrong audience, missing capability, expired claim, unknown fields, and sensitive keys fail closed.

### FR-I6-LIBRARIES — LiNKlibraries

The consumer must accept only revision-2 references whose source commit/tree match the frozen LiNKlibraries pin, whose digests are well-formed, and whose receipt type is `verified_cache` or `consumption`. Metadata-only, quarantined, superseded, unknown-field, and unpinned source identities fail closed. Wave-1 `library-client.mjs` stays the installed dual-homed client until a post-`v2.4.0` managed migration packet; Item 6 source work must not replace it in `MANIFEST.json`.

### FR-I6-BRAIN — LiNKbrain

The consumer must accept only advisory, metadata-first projections (`contractVersion` `2.0.0`). Transcripts, prompts, raw conversation, execution authority, and unknown fields fail closed. Coordination handoff refs are opaque identifiers only.

### FR-I6-SKILLS — LiNKskills

The consumer must accept only published + qualified + available immutable releases with `sha256:` digests and fragment level in range. Unqualified, unpublished, unavailable, `latest` aliases, and out-of-range fragments fail closed. Telemetry/use reports are bounded (`completed_use`, score 0–10, opaque refs). The requesting agent executes; this module does not run skills.

### FR-I6-AUTOWORK — LiNKautowork

The consumer must validate request identity, idempotency key, status, and bounded result/handoff payloads. Sensitive keys, unknown fields, and malformed ids fail closed. `unavailable` is a first-class status, not success.

### FR-I6-MCP — Shared modern MCP boundary

Where a provider advertises MCP `2026-07-28` sessionless semantics, the consumer must refuse legacy/session `initialize` negotiation and refuse silent downgrade. This is a consumer fail-closed check, not a new MCP server in IDE Development.

## 6. Non-functional requirements

| ID | Requirement |
|---|---|
| NFR-I6-01 | Consumer module has no network, Git write, credential, Ledger, or Gate mutation capability |
| NFR-I6-02 | Payloads are bounded (depth, size, key denylist). Sensitive names fail closed |
| NFR-I6-03 | Tests are fixture-based and pin-based. No live production provider calls |
| NFR-I6-04 | Agent- and model-agnostic. No Cursor/Codex/Terra-only API |
| NFR-I6-05 | Pre-rollout source files stay off `core/managed-core/`, `core/github/managed-workflows/`, installer, and `MANIFEST.json` |
| NFR-I6-06 | Checkpoints do not start managed Fast/Full and do not open PRs |
| NFR-I6-07 | Logs and evidence sanitize secrets, tokens, transcripts, and raw provider bodies |
| NFR-I6-08 | Idempotent validators: same input → same accept/reject code |
| NFR-I6-09 | Focused tests only until post-`v2.4.0` hosted integration |

## 7. Security requirements

| ID | Requirement |
|---|---|
| SEC-I6-01 | No secrets, tokens, private keys, or customer data in pins, fixtures, evidence, or docs |
| SEC-I6-02 | Platform identity is verified, never minted, by this consumer |
| SEC-I6-03 | Deny unknown fields; deny keys matching secret/password/token/authorization/private-key/prompt/transcript/raw/full-content/body |
| SEC-I6-04 | Path containment: no writes outside declared disposable cache locations (libraries retrieval later); this source module starts with in-memory validation only |
| SEC-I6-05 | Do not embed provider private schemas that are not already published as consumer-facing contracts |
| SEC-I6-06 | Fixture secret-scan: synthetic tokens used in negative tests must follow the `v2.4.0` Update 10 exact-declaration rule **when that update is installed**. Until then, do not add realistic live-looking tokens |

## 8. Failure requirements

Every provider surface must distinguish these four outcomes. Missing distinction is a failed acceptance criterion.

| Outcome | Meaning | Consumer action |
|---|---|---|
| **positive** | Pin matches; contract version matches; required fields valid; capability/qualification/receipt allowed | Return a frozen bounded projection/reference |
| **denied** | Identity, capability, audience, org, qualification, or policy forbids the operation | Throw a stable typed error; do not retry as infrastructure |
| **unavailable** | Provider explicitly reports unavailability, or required pin/material cannot be proven present, without implying success | Record `unavailable`; do not treat as positive; do not invent data |
| **fail-closed** | Malformed, expired, stale pin, unknown field, sensitive field, wrong contract version, legacy MCP, or ambiguous result | Throw; never coerce to positive or denied-success |

Infrastructure retries are not in this consumer module (it has no transport). If a later transport adapter is added after `v2.4.0`, it inherits the `v2.4.0` two-attempt infrastructure bound and must not retry policy/identity failures.

## 9. Acceptance criteria

Every criterion is **unmet** until a separately authorized implementation packet proves it. This documentation packet satisfies only `AC-I6-DOC-*`.

### AC-I6-DOC — this documentation packet

| ID | Criterion |
|---|---|
| AC-I6-DOC-01 | This PRD and the companion plan exist on Issue 311 from start SHA `741e58922e7413c1097f4a58ea25e94a934af903` |
| AC-I6-DOC-02 | Documents record issue/branch/worktree/start SHA/tree and the `v2.4.0` / WP-U03 / WP-U08 disjoint rule |
| AC-I6-DOC-03 | Documents do not implement product code, modify workflows/managed IDE files, change providers, open a PR, or run Full |
| AC-I6-DOC-04 | Relative markdown links in the two primary documents resolve on this branch; `git diff --check` is clean |
| AC-I6-DOC-05 | Issue branch is committed and pushed; local HEAD equals `origin/<issue-branch>` |

### AC-I6-REL — consumer boundary

| ID | Criterion |
|---|---|
| AC-I6-REL-01 | Exactly five provider pins exist (platform, libraries, brain, skills, autowork), each with commit SHA and tree SHA taken from that provider's GitHub `development` at freeze time |
| AC-I6-REL-02 | Issue 244 pins are not used |
| AC-I6-REL-03 | Consumer module has no transport, credentials, Git write, Ledger, or Gate mutation APIs |
| AC-I6-REL-04 | IDE Development checkout still has no nested `.ide-development/` after source work |
| AC-I6-REL-05 | Pre-rollout source files are only under the owned non-managed paths in the plan |
| AC-I6-REL-06 | No implementer PR into `development` is opened before `v2.4.0` source promote |
| AC-I6-REL-07 | Provider repositories are unmodified by Item 6 |

### AC-I6-POS / DEN / UNA / FC — per provider

For each provider `P` in `{platform, libraries, brain, skills, autowork}`:

| ID pattern | Criterion |
|---|---|
| AC-I6-POS-P | A fixture that matches the frozen pin and current consumer-facing contract is accepted and returns a frozen bounded object |
| AC-I6-DEN-P | A fixture that is well-formed but lacks permission, qualification, audience, selectable state, or equivalent policy is rejected with a stable denied/not-permitted/unavailable-for-use code (not coerced to success) |
| AC-I6-UNA-P | A fixture that represents provider unavailability or missing pinned material is classified `unavailable` (or the provider-specific equivalent) and is not treated as success |
| AC-I6-FC-P | Expired, unknown-field, sensitive-field, wrong-version, unpinned source, stale pin, and (where advertised) legacy MCP cases throw fail-closed |

Concrete IDs: `AC-I6-POS-platform` … `AC-I6-FC-autowork` (20 IDs). The plan maps each to a focused test.

### AC-I6-X — cross-cutting

| ID | Criterion |
|---|---|
| AC-I6-X-01 | Shared MCP `2026-07-28` modern / `legacy` negotiation fails closed on mismatch |
| AC-I6-X-02 | OKF mapping, when present, is optional and cannot override provider authority |
| AC-I6-X-03 | Obsolete consumer references introduced by Issue 244 (pins, “execute” receipt types, nested self-install instructions) are absent from Item 6 source files |
| AC-I6-X-04 | Genuine consumer defects only: no provider-repo “fixes”, no drive-by managed-core refactors, no CURRENT-STATUS/README rewrite in source packets |
| AC-I6-X-05 | Post-`v2.4.0` managed materialization, if authorized, targets consumer destinations under `.ide-development/providers/` for the nine consumers and still forbids installing that tree into IDE Development |
| AC-I6-X-06 | Hosted Fast/Full and Packager PR occur only in the deferred integration packets |

## 10. Explicit exclusions

This PRD does **not** authorize:

- product, CI, workflow, script, managed-core, installer, or runtime change in Issue 311
- merging or continuing PR 245 / Issue 244 onto `development`
- changing LiNKplatform, LiNKlibraries, LiNKbrain, LiNKskills, or LiNKautowork
- nested `.ide-development/` self-install, even as a test in this repository
- opening an implementer PR, self-merge, self-review, prefer-incoming, or staging/main promotion
- running Full, changing GitHub protections, or live provider/stage/production calls
- WP04 / `v2.4.0` nine-consumer installs
- rewriting [`IDE-DEVELOPMENT-TECHNICAL-PRD.md`](./IDE-DEVELOPMENT-TECHNICAL-PRD.md), [`CURRENT-STATUS.md`](./CURRENT-STATUS.md), [`README.md`](../README.md), [`OPEN-ISSUES.md`](./OPEN-ISSUES.md), or [`ARCHIVE-INDEX.md`](./ARCHIVE-INDEX.md) in this packet
- adding Item 6 as a numbered `v2.4.0` update
- touching WP-U03 or WP-U08 owned paths (`scripts/gitops/packager_*.py`, phase records, managed Fast triggers, controller state directory, managed PR/branch cleanup)
- touching WP-U04 in-flight paths (Review Ready publisher workflow/scripts/`MANIFEST.json`) until that packet is integrated
- production activation of any provider endpoint
- Claude Code platform support
- restoring the former custom GitHub App or Mac Mini runners

## 11. Dependencies

| Dependency | Relationship |
|---|---|
| Frozen provider contracts at pin time | Item 6 consumes them; does not author them |
| Platform AuthClaims 1.1.0 | Required for transport-boundary identity once a transport adapter exists; validators can be proven with fixtures first |
| LiNKlibraries revision 2 | Required for reference validation; Wave-1 client remains installed until managed migration |
| Accepted `v2.4.0` spec/PRD/plan | Scheduling and disjoint-path constraint. Item 6 source may proceed in parallel; Item 6 integration waits for `v2.4.0` source promote |
| WP-U03 / WP-U08 | Must remain path-disjoint. Item 6 must not start Packager/controller work |
| WP-U04 | Already mutating `MANIFEST.json` and managed workflows. Item 6 must not edit those files until after `v2.4.0` serial integration |
| Issue 244 / PR 245 | Provenance only; obsolete pins; managed-surface collision |
| Founder authorization | Required before any implementation packet after this documentation checkpoint |

## 12. No-production boundary

Item 6 is **not production**:

- No live provider traffic.
- No customer data.
- No billing, CRM, email, invoice, or deploy side effects.
- No GitHub protection changes.
- No consumer repository installs.
- No Git tag or GitHub Release.
- No claim that IDE Development is “connected in production” when only fixtures pass.

“Connected” for Item 6 source means: **pinned, validated, fail-closed consumer contracts exist and are tested**. Hosted and installed connection is a later packet after `v2.4.0` rollout and separate authorization.

## 13. Architecture decisions (documentation freeze)

| Decision | Choice | Alternative rejected |
|---|---|---|
| D1 | New non-managed module `core/link-integrations/` plus `tests/link-integrations/` for pre-rollout source | Extending `core/managed-core/platforms/` now — collides with WP-U04/`v2.4.0` MANIFEST work |
| D2 | Keep Wave-1 `library-client.mjs` installed; add revision-2 reference validation beside it | Replacing the managed library client in this item — managed surface and dual-home risk |
| D3 | Do not merge PR 245 | Rebase-and-merge Issue 244 — obsolete pins, wrong base, managed-core collision, implementer PR |
| D4 | Pin GitHub `development` tips at implementation freeze, not local sibling HEADs | Pinning local ahead-of-origin clones |
| D5 | Deferred Packager PR / hosted CI until after `v2.4.0` source promote | Opening a parallel Phase PR now — violates Issue 307 delivery policy and WP-U03 ownership |

## 14. Change log

| Date | Change | Actor |
|---|---|---|
| 2026-08-17 | Author Item 6 five-provider consumer PRD from `origin/development` `741e58922e7413c1097f4a58ea25e94a934af903` | Issue 311 documentation agent (Cursor Grok 4.6 High) |
