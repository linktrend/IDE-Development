# IDE Development v2.5.0 — Product Requirements, Roadmap, and End-to-End Implementation Plan

**Document status:** Canonical implementation specification  
**Implementation status:** Not started; this document authorizes no code, GitHub, provider, consumer, deployment, or production mutation by itself  
**Planning issue:** IDE Development #339  
**Target release:** `v2.5.0`  
**Prepared:** 2026-08-19 (Asia/Taipei)  
**System repository:** `linktrend/IDE-Development`  
**System-source rule:** IDE Development authors `core/managed-core/`; it must never receive a nested `.ide-development/` installation of itself  

## 1. How to use this document

This document is the complete product definition and execution plan for IDE Development v2.5.0. One executing agent can use it to create issues, run or delegate bounded work packets, obtain independent reviews, verify results, integrate the exact release tree, publish the package, and roll it out after receiving the required execution and promotion approvals.

No task history, chat transcript, prior PRD, or unstated decision is required to understand the intended result. Repository files named below are implementation surfaces to inspect and change; they are not external sources of missing requirements. When a current file conflicts with this document for the v2.5 implementation, this document defines the target state, while repository safety instructions and explicit founder approvals continue to govern whether a live action may occur.

The executor must:

1. Read the root `AGENTS.md` and any narrower repository instructions before changing files.
2. Use `agentsetup` for every new repository-scoped implementation packet.
3. Keep each packet on a short-lived `issue/*` branch or isolated worktree.
4. Treat this document as requirements, not as blanket authorization to merge, publish, change GitHub settings, mutate providers, deploy services, or roll out consumers.
5. Request explicit authorization at the gates identified in §19 when it was not already supplied by the execution task.
6. Preserve independent implementer/reviewer separation and exact-head/tree evidence.
7. Never claim that configuration, fixtures, source code, package presence, health endpoints, or version files prove live application functionality.

### 1.1 Sole-specification execution contract

This document is designed to be the sole **technical and product specification** supplied to one executing agent. The instruction may be only: **“Implement IDE Development v2.5.0 end to end using this document.”** It does not need to repeat architecture, requirements, repository names, sequencing, tests, rollout order, exclusions, or completion criteria.

The executing agent may be **Luna High, Grok 4.5 Medium, Grok 4.6 Medium, or an equivalently capable agent**. It owns the whole program from intake through closure. Where this document requires implementer/reviewer separation, the executing agent creates and coordinates separate bounded agent sessions with distinct identities; the founder does not need to provide separate prompts or technical context to those sessions.

Before doing any mutation, the executing agent must prove it can:

1. read this entire document and the applicable repository instructions;
2. maintain the requirement, packet, repository, branch, commit, tree, review, test, and approval ledgers defined here;
3. use isolated branches/worktrees without disturbing unrelated work;
4. distinguish read-only discovery from GitHub, provider, application, runtime, or repository mutation;
5. stop at an authorization gate instead of treating this specification as permission;
6. preserve implementer/reviewer separation; and
7. emit exact machine-readable evidence rather than narrative-only claims.

If any capability is unavailable, the executing agent must replace that internal lane with a capable session or record a blocked result. It must not simplify or reinterpret requirements to fit the model, and it must not ask the founder to restate information already contained here.

### 1.2 What “no other information” does and does not mean

No additional design decision, chat history, task transcript, architectural explanation, repository list, rollout order, testing policy, or product requirement should be requested from the founder. The executor discovers current technical state through the repositories and authenticated read APIs, using the deterministic rules in this document.

The following are **external authority or access**, not missing specification information:

- authenticated access to the named repositories and selected Codex/Cursor environments;
- protected GitHub App/private-key bindings and provider/runtime credentials already approved for the operation;
- permission to mutate another repository, GitHub rulesets/secrets/settings, a live provider, a runtime/VPS, or protected branches;
- explicit founder approval for a reserved main/publish/deploy gate when not already recorded for the exact operation.

The agent must not ask the founder to redesign the solution when one of those is absent. It must complete every safe authorized predecessor, emit one exact blocked-gate record identifying the missing authority/access by name without exposing a secret, and stop only the dependent path. A later authorization resumes from the recorded exact state; it does not require a new technical brief.

### 1.3 Default decision rules

When implementation details admit more than one reasonable choice, apply these defaults in order:

1. preserve the provider/consumer ownership table in §7;
2. reuse a current repository abstraction only when it meets the v2.5 target and has tests;
3. prefer one canonical generator/schema/controller over duplicated implementations;
4. prefer transactional, idempotent, reversible changes over direct mutation;
5. prefer GitHub-hosted compute for hosted validation and Cursor Cloud for newly delegated Cursor work when both are authorized and suitable;
6. never use local application state as a substitute for a required Cloud/API or real-application proof;
7. use the smallest test profile that proves the changed risk, and never omit a declared required test merely to meet a runtime target;
8. stop and create a narrow design finding when a choice would change ownership, public contracts, security boundaries, production behavior, or an acceptance criterion.

Routine file naming, internal function decomposition, and test fixture organization do not require founder input when they follow existing repository conventions and the path ownership ledger.

## 2. Executive outcome

IDE Development v2.5.0 must deliver two changes as one coherent product:

1. **A functioning agent development environment.** Codex and Cursor, when working in an upgraded consumer repository, can use the approved LiNK providers through installed IDE Development adapters. They can resolve Platform identity/capabilities, retrieve only qualified IDE workflow skills from LiNKskills, read advisory Brain material, perform bounded Brain handoffs, consume verified Libraries material, and use approved Autowork request/status/receipt surfaces.
2. **A simple, reliable delivery system.** An issue checkpoint produces no expensive CI. Accepted issue commits are assembled into one Phase PR. One bounded Fast gate, one independent review outcome, and at most one final exact-tree Full receipt govern development integration. Staging and main reuse that evidence and do not rerun equivalent suites. Credentials, workflows, required checks, rulesets, and delivery components are bootstrapped and verified before work depends on them.

The release is not done until both changes are installed and proven together in one real consumer repository, then rolled out safely to the remaining eight repositories.

## 3. Current v2.4.0 baseline

The executor begins from the current protected `development` line and re-verifies all identities before implementation. The as-built baseline on 2026-08-19 is:

- Root product identity: `VERSION` = `v2.4.0`.
- Managed package identity: `core/managed-core/VERSION` = `2.4.0`.
- Manifest: `core/managed-core/MANIFEST.json`, schema version 1, package `ide-development-managed-core`, 319 managed file entries.
- Manifest platform distribution: 143 `all`, 44 `codex`, 64 `cursor`, and 68 `github` entries.
- Skill duplication: 43 workflow/domain skills are copied into each of `.ide-development/skills`, `.cursor/skills`, and `.agents/skills` in consumers.
- Installer: `scripts/ide-development.py` and `scripts/ide_development/`, supporting `plan`, `install`, `update`, `drift`, `verify`, `version`, `rollback`, and `release-candidate`.
- Provider validators: `core/link-integrations/` validates frozen provider facts but has no live transport, credentials, application tool registration, or installed consumer materialization.
- Managed workflows are authored under `core/github/managed-workflows/` and mirrored into consumer `.github/workflows/` destinations.
- Current system workflows include separate Fast, Full, Review Gate, Review Ready publisher, repair observer, development receipt, main receipt, cleanup, branch-source, and release publication responsibilities.
- Current protected application CI also runs from `.github/workflows/ci.yml` on pushes and PRs to `development`, `staging`, and `main`, which can repeat source validation during promotion.
- Cross-platform installer evidence uses `.github/workflows/ide-development-cross-platform.yml` for Ubuntu, macOS, and Windows.
- The nine installed consumers are:
  1. `linktrend/openclaw_prime`
  2. `linktrend/LiNKplatform`
  3. `linktrend/LiNKskills`
  4. `linktrend/LiNKbrain`
  5. `linktrend/LiNKsites`
  6. `linktrend/LiNKdeveloper`
  7. `linktrend/LiNKlibraries`
  8. `linktrend/LiNKautowork`
  9. `linktrend/LiNKtrading-codebase`

The baseline contains valuable transactional installation, hash verification, rollback, exact-tree receipts, source-policy, and fail-closed behavior. v2.5 must preserve those protections while removing duplicate mechanisms and incomplete product surfaces.

### 3.1 Repository and execution-environment registry

The executing agent must use this registry as the starting scope. It must verify each `origin` before mutation and may discover a relocated local checkout by exact remote URL. It must not create a second clone merely because the preferred local path is absent. All repositories have protected `development`, `staging`, and `main` branches as of the prepared baseline; WP25-00 must reverify them.

| Role | GitHub repository | Preferred local checkout | Cursor environment | v2.5 scope |
|---|---|---|---|---|
| System source | `linktrend/IDE-Development` | `/Users/linktrend/Projects/IDE Development` | `LiNKdevelopment IDE` | Complete v2.5 implementation, release, publication |
| Consumer/provider | `linktrend/openclaw_prime` | `/Users/linktrend/Projects/openclaw_prime` | `LiNKdevelopment IDE` | IDE rollout and canaries; no unrelated Lisa/runtime deployment |
| First real canary/provider | `linktrend/LiNKplatform` | `/Users/linktrend/Projects/LiNKplatform` | `LiNKdevelopment IDE` | Provider compatibility plus first consumer rollout |
| Provider/consumer | `linktrend/LiNKskills` | `/Users/linktrend/Projects/LiNKskills` | `LiNKdevelopment IDE` | Qualified IDE skill releases plus consumer rollout |
| Provider/consumer | `linktrend/LiNKbrain` | `/Users/linktrend/Projects/LiNKbrain` | `LiNKdevelopment IDE` | Provider compatibility plus consumer rollout |
| Consumer | `linktrend/LiNKsites` | `/Users/linktrend/Projects/LiNKsites` | `LiNKdevelopment IDE` | IDE rollout and canaries; no unrelated product change |
| Consumer | `linktrend/LiNKdeveloper` | `/Users/linktrend/Projects/LiNKdeveloper` | `LiNKdevelopment IDE` | IDE rollout and canaries; no unrelated product change |
| Provider/consumer | `linktrend/LiNKlibraries` | `/Users/linktrend/Projects/LiNKlibraries` | `LiNKdevelopment IDE` | Provider compatibility plus consumer rollout; no runtime deployment implied |
| Provider/consumer | `linktrend/LiNKautowork` | `/Users/linktrend/Projects/LiNKautowork` | `LiNKdevelopment IDE` | Provider compatibility plus consumer rollout; no VPS deployment implied |
| IDE-only consumer | `linktrend/LiNKtrading-codebase` | `/Users/linktrend/Projects/LiNKtrading-codebase` | `LiNKtrading-codebase` | IDE v2.5 rollout only; never merge unrelated trading work |

Repository discovery algorithm:

1. Test the preferred path with `git -C <path> remote get-url origin`.
2. Normalize HTTPS and SSH GitHub forms and require the expected `linktrend/<repository>` identity.
3. If absent/mismatched, search only approved workspace roots for a checkout with that exact origin.
4. If multiple matches exist, select a clean checkout or create an isolated worktree from the verified repository; never guess between dirty copies.
5. Fetch read-only remote references and record the protected branch commits/trees before creating work.
6. Treat any unrelated repository, agent, task, or Cursor environment as out of scope.

## 4. Problems v2.5 must solve

### 4.1 Incomplete provider deployment

v2.4 shipped offline validators but did not install a provider transport or expose callable LiNKbrain/LiNKskills tools to Codex and Cursor. All nine repositories report v2.4.0 installed, yet installed IDE Development alone does not let either application perform Brain, Skills, or handoff operations.

### 4.2 Packaged skill duplication and unclear authority

The same skills are physically copied into multiple discovery locations. This creates drift, stale copies, ambiguous selection, and package size. v2.5 must make LiNKskills the only workflow-skill authority. IDE Development must contain no workflow skill implementation.

### 4.3 Over-engineered delivery

Multiple workflows, publishers, variables, raw check names, rulesets, markers, and controller paths can disagree. Valid candidates have been blocked by obsolete check names, unavailable external review services, missing publisher credentials, malformed receipt markers, optional cache failures, and delivery components that did not actually perform their namesake operation.

### 4.4 Redundant and misleading validation

Fast, Full, consumer CI, promotion CI, copied consumer tests, optional cache post-jobs, and stage/main checks can repeat the same work. A green test can omit newly added required tests; a copied test can fail because it references source-only files; a passing fixture can be incorrectly presented as live interoperability.

### 4.5 Operational fragility

Observed failures include stale agents consuming capacity, unsupported model identifiers, linked-worktree permission failures, hard-coded dates expiring, shell incompatibility, macOS path aliases, accidental workflow dispatch during inspection, and automated tools mutating thousands of files.

## 5. Product goals and measurable success

| ID | Goal | Success measure |
|---|---|---|
| G-01 | Real provider access | Codex and Cursor complete live Platform, Brain, Skills, and handoff canaries from the first upgraded consumer |
| G-02 | LiNKskills-only workflow skills | No workflow `SKILL.md` is packaged by IDE Development; both apps retrieve exact qualified releases only from the approved LiNKskills namespace |
| G-03 | One ordinary delivery path | One Phase PR reaches `development` through one authoritative delivery gate |
| G-04 | Fast feedback | Normal Fast completes in under five minutes on GitHub-hosted compute |
| G-05 | No redundant Full | Full runs once on the final exact release tree when the risk classifier requires it; promotions reuse the receipt |
| G-06 | Durable authentication | Bootstrap provisions and proves the GitHub App route before implementation depends on Review Ready or delivery automation |
| G-07 | Atomic check/protection contract | Installed workflows can produce every managed required check, with no obsolete or impossible contexts |
| G-08 | Safe rollout | One real canary repository passes first; the remaining eight then upgrade with per-repository rollback evidence |
| G-09 | Truthful evidence | Source, package, installed, application, hosted, and live proof remain explicitly distinguished |
| G-10 | Bounded recovery | Stalls, infrastructure failures, token expiry, rate limits, and host pressure stop or recover within declared bounds without losing work |

## 6. Non-goals

v2.5 does not:

- add Claude Code as a supported IDE platform;
- grant LiNKbrain execution authority;
- make IDE Development the owner of provider contracts or provider runtime internals;
- deploy LiNKlibraries or LiNKautowork runtime services when those deployments are not separately authorized;
- deploy or change OpenClaw/Lisa product behavior unrelated to IDE provider canaries;
- merge unrelated LiNKtrading product work;
- put secret values, private keys, customer data, transcripts, prompts, or raw provider bodies in Git;
- remove repository-owned technical tests or checks merely to reduce runtime;
- weaken protection by treating skipped, missing, cancelled, unavailable, or stale evidence as passed;
- require a separate disposable rollout repository when one of the real nine can serve as the controlled canary.

## 7. Roles and authority

| Role | Owns | Must not own |
|---|---|---|
| IDE Development | Installer, managed package, provider client/adapters, app discovery, delivery controller, release/rollout harness | Provider truth, Brain execution, skill qualification, application product code |
| LiNKplatform | Identity, organization, permissions, capabilities, token/claim contracts | IDE delivery state or skill content |
| LiNKskills | Qualified immutable skill releases, fragments, availability, qualification, use telemetry | Consumer execution or Git delivery authority |
| LiNKbrain | Advisory knowledge/coordination and bounded handoff contracts | Code execution or deployment decisions |
| LiNKlibraries | Verified reusable artifacts, catalogues, immutable release/receipt contracts | Consumer composition/runtime decisions |
| LiNKautowork | Authorized request/status/handoff/receipt provider plane | Repository merge, Ledger, Gate, or deployment authority |
| Consumer repository | Product code, repository-specific technical instructions, selected test commands | Managed IDE lifecycle internals |
| Implementer | Bounded issue changes and focused evidence | Self-review, self-merge, protected promotion |
| Independent reviewer | Exact-head technical review and findings | Implementer identity for the reviewed packet |
| Packager | Serial integration of accepted issue commits into one Phase candidate | Product implementation |
| Delivery controller | Protected merge/promotion after exact gates | Fabricating or weakening evidence |
| Founder/Principal | Reserved production/main approvals, exceptional scope/waivers, first-time external authorization | Routine recoverable automation mechanics |

## 8. Target product architecture

### 8.1 Layer model

v2.5 has six layers:

1. **Transactional package layer** — manifest, installer, installed-state, transactions, backup, drift, verify, rollback.
2. **Provider contract and transport layer** — one canonical provider registry and bounded adapters for Platform, Brain, Skills, Libraries, and Autowork.
3. **Application adapter layer** — Codex and Cursor discovery/tool registration with equivalent capabilities and errors.
4. **LiNKskills loader layer** — minimal infrastructure that retrieves exact IDE workflow-skill releases; no workflow skill content in IDE Development.
5. **Delivery layer** — one versioned delivery contract, Packager, Delivery Controller, GitHub App authentication, Fast/Review/conditional Full, promotion receipt reuse.
6. **Acceptance and rollout layer** — permanent app canary harness, release candidate creation, first-repository canary, remaining rollout, rollback and cleanup.

### 8.2 Canonical source and installed paths

The implementation must converge on these paths unless a packet proves an existing equivalent is safer. Any deviation must be documented in the packet's technical design before coding.

| Concern | Canonical system source | Consumer destination |
|---|---|---|
| Provider registry/contracts | `core/link-integrations/` | `.ide-development/providers/` |
| Platform adapter | `core/link-integrations/platform.mjs` plus transport module | `.ide-development/providers/platform/` |
| Brain adapter/handoffs | `core/link-integrations/brain.mjs` plus transport module | `.ide-development/providers/brain/` |
| Skills adapter/loader | `core/link-integrations/skills.mjs` plus loader | `.ide-development/providers/skills/` |
| Libraries adapter | `core/link-integrations/libraries.mjs` plus retrieval module | `.ide-development/providers/libraries/` |
| Autowork adapter | `core/link-integrations/autowork.mjs` plus transport module | `.ide-development/providers/autowork/` |
| Codex adapter | `core/managed-core/platforms/codex/` | managed `AGENTS.md` block and non-skill provider discovery/configuration |
| Cursor adapter | `core/managed-core/platforms/cursor/` | `.cursor/rules/` and provider/MCP configuration owned by managed markers or exact managed files |
| Delivery contract | `core/managed-core/config/delivery.json` and schema | `.ide-development/config/delivery.json` |
| Provider/app config | new schema and template under `core/managed-core/config/` | `.ide-development/config/providers.json` without secrets |
| Managed workflows | `core/github/managed-workflows/` | `.github/workflows/` |
| Runtime scripts | `scripts/gitops/` and manifest declarations | `scripts/gitops/` where consumer execution is required |
| App canary harness | new modules under `scripts/ide_development/` | invoked from release/rollout package; sanitized evidence under `.ide-development/evidence/` only when committed evidence is required |
| Git-local cache/backups | installer/runtime-generated only | `.git/ide-development/` and never committed |

### 8.3 One provider registry

Add a machine-readable registry schema and configuration containing only non-secret facts:

- provider identifier and owner repository;
- supported contract and MCP versions;
- transport type and endpoint reference name;
- Platform capability required for each tool;
- read/write classification;
- exact tool allowlist for Codex, Cursor, and canaries;
- timeout and bounded retry class;
- redaction policy;
- live/staged/source-only availability state;
- immutable provider commit/tree/contract digest used by the release.

No adapter may maintain an independent contradictory provider list.

### 8.4 Identity and credentials

Provider calls use LiNKplatform identity/capabilities at the authorization boundary. IDE Development does not mint identity or embed credentials. Runtime configuration resolves protected values from approved application/host secret stores.

GitHub delivery uses one GitHub App identity. The App's durable private credential remains in an approved secret manager or GitHub protected secret, while each operation mints a short-lived repository-scoped installation token. Tokens are never committed, logged, cached across jobs, assumed to have a fixed length, or reused after expiry.

### 8.5 No packaged workflow skills

All current `core/skills/*/SKILL.md` workflow/domain skills and their managed mirrors must be inventoried and migrated to LiNKskills as immutable qualified releases in the namespace `ide-development/<skill-id>`. IDE Development must not package those `SKILL.md` files into `.ide-development`, `.agents`, or `.cursor`.

The remaining bootstrap surface is infrastructure, not a skill:

1. managed Codex/Cursor instructions call the LiNKskills provider adapter;
2. the adapter identifies the exact v2.5 skill-set lock;
3. it retrieves the requested qualified fragment/release;
4. it verifies identifier, version, digest, qualification, publication, availability, and provider pin;
5. the requesting application consumes it for the current session;
6. any cache is Git-local, digest-bound, disposable, and not an alternative authority.

If LiNKskills is unavailable, IDE workflow execution stops with `skills_provider_unavailable`; it must not silently use a repository-local, global, marketplace, model-invented, stale, or similarly named skill.

After the replacement releases and loader are accepted, the v2.5 system-source tree must also remove IDE-owned workflow skill implementations from `core/skills/` and `.agents/skills/`, not merely stop packaging their mirrors. The minimal loader must not be named `SKILL.md` or placed in a skill-discovery directory. The IDE Development repository itself must use the same LiNKskills provider route as consumers. Historical copies may exist only in Git history or a clearly non-active archive excluded from manifests and discovery.

### 8.6 Simplified workflow topology

The consumer-managed required workflow topology is limited to:

1. **Linktrend Delivery Gate** — Phase PR to `development`; validates source branch, change/risk classification, selected Fast profile, independent review result, and conditional Full receipt.
2. **Linktrend Promotion Gate** — temporary promotion PRs to `staging` or `main`; verifies allowed source, exact accepted tree, receipt binding, target base, and required approval. It runs no equivalent application suite.
3. **Linktrend Maintenance** — non-required manual/scheduled cleanup, stalled-run observation, and evidence retention. It cannot merge or declare acceptance.

IDE Development system source additionally retains one **Managed-Core Release Publisher** for immutable tag/release publication after protected main approval.

Consumer-owned CI remains consumer-owned. The delivery configuration selects which consumer command/check represents required product validation and ensures it executes once on the Phase candidate. It is not rerun merely because the identical tree moves to staging or main.

Externally visible managed required contexts are capped at:

- `Linktrend Delivery Gate` on `development`;
- `Linktrend Promotion Gate` on `staging` and `main`.

Optional informational jobs may exist inside those workflows but must not become independent stale required contexts.

### 8.7 Delivery state machine

```text
issue checkpoint
  -> accepted_issue
  -> phase_candidate
  -> fast_passed
  -> review_passed | review_unavailable_with_independent_fallback
  -> full_not_required | full_receipt_sealed
  -> development_merged
  -> staging_promoted
  -> founder_main_approved
  -> main_promoted
  -> release_published (IDE system only)
  -> canary_installed
  -> canary_accepted
  -> rollout_complete
```

Every transition records repository, branch, commit, tree, dependency/profile identity, workflow identity, actor, timestamp, and prior state. Invalid, missing, ambiguous, stale, or mismatched evidence fails closed.

## 9. Functional requirements

### 9.1 Package and installer

| ID | Requirement |
|---|---|
| FR-PKG-01 | Set root and managed package identities to `v2.5.0` / `2.5.0` only during final integration, after manifests and migrations are complete |
| FR-PKG-02 | Extend manifest/schema for provider adapters, provider configuration, delivery contract, app harness, and skill supersessions |
| FR-PKG-03 | Remove all packaged workflow skills only through exact manifest/supersession identities; modified consumer-owned files fail closed and are preserved |
| FR-PKG-04 | Install/update remains transactional, idempotent, physical-file based, cross-platform, recoverable, and incapable of following paths outside the consumer root |
| FR-PKG-05 | `verify` proves hashes, modes, installed state, adapter presence, configuration schema, and absence of obsolete managed files; it does not claim live provider success |
| FR-PKG-06 | `rollback` restores prior managed files, markers, app adapters, workflow set, configuration, and installed state byte-for-byte |
| FR-PKG-07 | Release archives are reproducible, contain no credentials/host paths/Git metadata, and install without access to the system checkout |
| FR-PKG-08 | IDE Development system source refuses nested self-install at all CLI entrypoints |

### 9.2 LiNKplatform

| ID | Requirement |
|---|---|
| FR-PLAT-01 | Resolve actor, runtime binding, organization, audience, service scope, required capability, and expiry through the supported Platform adapter |
| FR-PLAT-02 | Refuse forged, expired, wrong-audience, wrong-organization, unknown-field, or insufficient-capability claims |
| FR-PLAT-03 | Do not use a direct developer Supabase connection as the production IDE authorization path |
| FR-PLAT-04 | Expose a bounded read-only capability canary to Codex and Cursor |

### 9.3 LiNKbrain and handoffs

| ID | Requirement |
|---|---|
| FR-BRAIN-01 | Search/read bounded advisory projections without exposing raw prompts, transcripts, or full conversation content |
| FR-BRAIN-02 | Create, read, accept, and inspect status of handoffs in authorized namespaces |
| FR-BRAIN-03 | Keep `authority=advisory` and `executionAuthority=none`; Brain output cannot authorize code, Git, deployment, or production actions |
| FR-BRAIN-04 | Distinguish denied, unavailable, malformed, incompatible, and empty-success results |
| FR-BRAIN-05 | Handoff canaries use an isolated test namespace and leave a deterministic closed/cleaned result |

### 9.4 LiNKskills

| ID | Requirement |
|---|---|
| FR-SKILL-01 | Migrate every current IDE Development skill to an immutable qualified LiNKskills release or explicitly retire it with replacement/justification |
| FR-SKILL-02 | Publish one v2.5 skill-set lock containing exact skill identifiers, versions, release digests, fragments, and provider pin |
| FR-SKILL-03 | Codex and Cursor discover IDE workflow skills only through that lock and approved namespace |
| FR-SKILL-04 | Retrieve progressive-disclosure fragments; do not download or persist the full catalogue when unnecessary |
| FR-SKILL-05 | The requesting app executes the retrieved instructions locally; IDE Development and LiNKskills do not gain application execution authority |
| FR-SKILL-06 | Report bounded use telemetry when required, without prompts, transcripts, credentials, or private source bodies |
| FR-SKILL-07 | Refuse `latest`, unpublished, unqualified, unavailable, incompatible, digest-mismatched, or non-allowlisted skills |
| FR-SKILL-08 | Remove v2.4 physical skill copies only after both applications prove retrieval of the replacement set; rollback restores v2.4 atomically |
| FR-SKILL-09 | Remove active IDE-owned workflow skill implementations from the system repository as well as consumer package destinations; retain only a non-skill provider loader |

### 9.5 LiNKlibraries

| ID | Requirement |
|---|---|
| FR-LIB-01 | Discover and retrieve only selectable verified revision-2 entries by exact provider source, release source, artifact tree, digests, and receipt |
| FR-LIB-02 | Keep provider source tree, release source tree, artifact tree, payload identity, and receipt identity distinct |
| FR-LIB-03 | Refuse metadata-only, quarantined, superseded, unsafe-path, unknown-field, mutable, unpinned, or digest-mismatched material |
| FR-LIB-04 | Support component, starter-kit, and website-template profiles where the provider contract permits them |
| FR-LIB-05 | Retrieval does not itself authorize payload execution or mutation of LiNKlibraries |

### 9.6 LiNKautowork

| ID | Requirement |
|---|---|
| FR-AUTO-01 | Submit only bounded capability-authorized requests with idempotency identity |
| FR-AUTO-02 | Read accepted/completed/failed/denied/unavailable status, handoffs, results, and receipts without coercing failure/unavailability to success |
| FR-AUTO-03 | Enforce callback ordering, receipt expiry, contract negotiation, unknown-field rejection, and secret-field redaction |
| FR-AUTO-04 | Autowork receipts never grant Git, Gate, Ledger, deployment, or production authority |
| FR-AUTO-05 | If no live Autowork runtime exists at acceptance time, source/staged conformance is recorded as a live-runtime hold rather than production PASS |

### 9.7 Codex and Cursor parity

| ID | Requirement |
|---|---|
| FR-APP-01 | Both applications expose the same provider capability names, intent, inputs, bounded outputs, error classes, timeouts, and redaction policy |
| FR-APP-02 | App-specific technical differences are isolated behind adapters; provider/domain logic is shared |
| FR-APP-03 | Application discovery works from any directory inside the consumer repository without external symlinks |
| FR-APP-04 | A missing connector/tool is a failed application acceptance criterion, not an inferred pass from configuration presence |
| FR-APP-05 | Normal use employs narrow per-tool approval; blanket Cursor `--force` or equivalent unrestricted permission is forbidden |
| FR-APP-06 | The managed instructions prevent selection of non-allowlisted IDE workflow skills |

### 9.8 GitHub authentication and bootstrap

| ID | Requirement |
|---|---|
| FR-AUTH-01 | Add one bootstrap command family with `plan`, `apply`, `verify`, and `rollback`; `plan` and `verify` are read-only |
| FR-AUTH-02 | Bootstrap inventories every operation currently performed by automation and verifies GitHub App permission parity before cutover |
| FR-AUTH-03 | Bootstrap installs/verifies the App on IDE Development and authorized consumers and records repository selection without secret values |
| FR-AUTH-04 | IDE-owned credentials/bindings are provisioned, repaired, rotated, or restored where the authenticated operator/App has authority; detection alone is not steady-state success |
| FR-AUTH-05 | One genuinely external first-time authorization may be requested once with exact reason/scope; routine releases must not repeatedly request it |
| FR-AUTH-06 | Short-lived tokens refresh before expiry and retry once after an authentication-expiry response; policy/permission denial is not retried as infrastructure |
| FR-AUTH-07 | Rate limits use bounded backoff and request consolidation; retry storms are forbidden |
| FR-AUTH-08 | App removal, suspension, permission drift, repository removal, key rotation, GitHub outage, and token-format changes have explicit diagnostics and rollback |
| FR-AUTH-09 | Bootstrap proves Review Ready/delivery publication using a harmless canary before implementation work depends on it |
| FR-AUTH-10 | Old authentication remains recoverable through the canary cutover, then is revoked and removed after App acceptance so two routes cannot compete |

### 9.9 Packager, review, delivery, and promotion

| ID | Requirement |
|---|---|
| FR-DEL-01 | Checkpoint means commit + push + focused evidence; checkpoint pushes start no managed expensive CI |
| FR-DEL-02 | Packager discovers accepted issue SHAs, validates evidence/remote equality, integrates serially into one `phase/*` candidate, and opens/updates one draft Phase PR |
| FR-DEL-03 | Packager, Integrator, Controller, Review, and Promoter names are reserved for components that perform those operations; validation-only files are renamed or removed |
| FR-DEL-04 | One `Linktrend Delivery Gate` is the authoritative managed required check on the Phase PR |
| FR-DEL-05 | Independent review binds the exact candidate head/tree; any source repair invalidates the review and requires one new exact-head review |
| FR-DEL-06 | External reviewer states are `passed`, `failed`, or `unavailable`; unavailable may use the approved independent-review fallback without being reported as passed |
| FR-DEL-07 | Risk classifier selects focused/Fast/Full profile from changed paths, contract impact, dependencies, workflow/config changes, and release scope |
| FR-DEL-08 | Full runs once only on the final sealed tree when required; its receipt binds repository, tree, dependencies, profile, workflow identity, and run |
| FR-DEL-09 | Delivery Controller rereads PR head/base/checks/review/receipt immediately before normal protected merge |
| FR-DEL-10 | Promotion marker is generated and schema-validated; hand-written JSON, placeholders, quoted JSON, or manually copied receipt coordinates are forbidden |
| FR-DEL-11 | Staging/main promotion compares Git trees when merge/squash commit identities differ and reuses exact evidence |
| FR-DEL-12 | Main waits for explicit founder approval unless the execution task already contains that exact approval |
| FR-DEL-13 | Inspection APIs cannot dispatch workflows; read-only status/probe code and mutation/dispatch code are separate entrypoints |

### 9.10 Tests and evidence

| ID | Requirement |
|---|---|
| FR-TEST-01 | Focused tests run during implementation/repair; Fast runs once per Phase candidate; Full runs once per final exact tree when required; promotions run receipt/policy checks only |
| FR-TEST-02 | Fast includes changed-path formatting/static validation, fixture-aware secret scan, manifest/workflow integrity, affected unit/contracts, and selected consumer command; target under five minutes |
| FR-TEST-03 | Canonical Full inventory is machine-readable and fails if a declared required test package is omitted |
| FR-TEST-04 | Identical tree/dependency/profile/workflow identities reuse signed evidence; changed identity invalidates reuse |
| FR-TEST-05 | Optional caches, analytics, uploads, and post-job cleanup are advisory and cannot overturn required application proof |
| FR-TEST-06 | Time-sensitive fixtures use a controlled clock or relative values; tests simulate dates to prove validity/expiry behavior |
| FR-TEST-07 | Derived fixture digests/caches are regenerated from canonical inputs; generated mirrors/manifests use one deterministic generator |
| FR-TEST-08 | Installed consumer tests are self-contained and never reference files present only in IDE Development source |
| FR-TEST-09 | Evidence labels source/static, package, installed, hosted, application, stage, VPS, E2E, and production proof separately |
| FR-TEST-10 | `skipped`, `queued`, `cancelled`, `missing`, `unavailable`, `failed`, and `passed` remain distinct states |

### 9.11 Agent and automation safety

| ID | Requirement |
|---|---|
| FR-OPS-01 | Dispatch preflight verifies exact model identifier, reasoning level, cloud/local location, Fast setting, approval mode, sandbox compatibility, workspace, and write access |
| FR-OPS-02 | Worktree preflight proves Git metadata operations before implementation |
| FR-OPS-03 | Agents heartbeat with material states and last progress; no-progress timeout cancels/replaces a run within bounds |
| FR-OPS-04 | Completed, failed, cancelled, and abandoned sessions are closed and cannot consume capacity |
| FR-OPS-05 | Coordinator limits heavy jobs by host memory/CPU; unrelated processes are never killed |
| FR-OPS-06 | Mutating tools declare scope and run first on an isolated canary; unexpected mass mutation aborts and rolls back |
| FR-OPS-07 | Shell/interpreter and filesystem/path behavior is preflighted on target OS/host |

### 9.12 Release and rollout

| ID | Requirement |
|---|---|
| FR-ROL-01 | Publish artifact binds version, main source commit/tree, manifest, archive digests, skill-set lock, provider pins, workflow contract, and rollback identity |
| FR-ROL-02 | Published bytes are the same bytes validated before publication |
| FR-ROL-03 | LiNKplatform is the first real canary consumer unless preflight proves it cannot safely serve; fallback requires a recorded reason and selects the next lowest-risk consumer, not a disposable substitute |
| FR-ROL-04 | Canary upgrades through a normal rollout PR, then proves install, drift, app discovery, provider calls, handoffs, failure modes, delivery dry run, and rollback |
| FR-ROL-05 | Remaining order after LiNKplatform canary: openclaw_prime, LiNKskills, LiNKbrain, LiNKsites, LiNKdeveloper, LiNKlibraries, LiNKautowork, LiNKtrading-codebase |
| FR-ROL-06 | LiNKtrading receives IDE v2.5 only; no unrelated product PR/merge is included |
| FR-ROL-07 | Each consumer gets a repository-scoped report and rollback commit/package identity; failure pauses only that repository unless it proves a systemic package defect |
| FR-ROL-08 | Systemic defect stops remaining rollout and triggers package rollback/replacement; repository-specific defect does not mutate other consumers |
| FR-ROL-09 | Cleanup closes rollout PRs, removes temporary Phase/promotion/rollout branches and worktrees, and closes stale sessions after permanent branches are verified |

## 10. Non-functional requirements

### 10.1 Performance

| ID | Requirement |
|---|---|
| NFR-PERF-01 | Fast target: under 5 minutes under normal GitHub capacity |
| NFR-PERF-02 | Provider read canary target: under 60 seconds per provider/app after authentication |
| NFR-PERF-03 | Package plan/drift target: under 60 seconds per normal repository |
| NFR-PERF-04 | Installer update target: under 3 minutes excluding Git/network operations |
| NFR-PERF-05 | Promotion gate target: under 2 minutes because it verifies evidence and policy only |
| NFR-PERF-06 | No unbounded polling; all waits have a timeout and progressive, non-spam status |

### 10.2 Security and privacy

| ID | Requirement |
|---|---|
| NFR-SEC-01 | Deny unknown provider fields at trust boundaries unless the published contract explicitly allows extensions |
| NFR-SEC-02 | Bound payload depth, key count, string length, result count, and total response size |
| NFR-SEC-03 | Reject/log-redact keys matching credential, token, authorization, password, private key, prompt, transcript, raw body, or full content categories |
| NFR-SEC-04 | Use least-privilege per-operation tool allowlists |
| NFR-SEC-05 | Do not expose protected credentials to untrusted fork events or candidate code |
| NFR-SEC-06 | Pin third-party GitHub Actions by immutable commit |
| NFR-SEC-07 | Do not execute candidate-controlled code in a privileged workflow context |

### 10.3 Reliability

| ID | Requirement |
|---|---|
| NFR-REL-01 | Deterministic/idempotent plan and verify operations |
| NFR-REL-02 | Atomic installation and external-state migration with before-state archive |
| NFR-REL-03 | At most two infrastructure retries per exact candidate |
| NFR-REL-04 | At most three ordinary source repair cycles per packet |
| NFR-REL-05 | No silent fallback from live provider to fixtures, cache, or local copies |
| NFR-REL-06 | No silent fallback from App authentication to a human token |

### 10.4 Portability

| ID | Requirement |
|---|---|
| NFR-PORT-01 | Python 3.11+ stdlib installer remains the portable mutation engine unless explicitly approved otherwise |
| NFR-PORT-02 | Installer unit/migration coverage runs on Ubuntu, macOS, and Windows |
| NFR-PORT-03 | Shell workflows explicitly invoke Bash where Bash semantics are required |
| NFR-PORT-04 | Normalize legitimate macOS aliases such as `/var` and `/private/var` without weakening traversal checks |
| NFR-PORT-05 | No external checkout symlinks for Codex/Cursor discovery |

### 10.5 Maintainability

| ID | Requirement |
|---|---|
| NFR-MAINT-01 | One canonical source exists for generated mirrors, manifest entries, workflow/check contract, provider registry, and skill-set lock |
| NFR-MAINT-02 | Every generated file carries provenance or is reproducibly regenerable |
| NFR-MAINT-03 | Retired v2.4 components are removed or clearly archived; they do not remain active alongside replacements |
| NFR-MAINT-04 | User/operator messages are plain English first, with exact evidence available underneath |

## 11. Required schemas and durable records

The implementation must add or revise machine-readable schemas for:

1. `provider-registry` — providers, versions, capabilities, endpoints, tools, retries, redaction.
2. `provider-runtime-config` — consumer-specific non-secret endpoint/binding references.
3. `ide-skill-set-lock` — exact LiNKskills releases and digests.
4. `delivery-contract` — workflow names, required external context, profiles, risk rules, branch sources.
5. `delivery-state` — state machine and exact identities.
6. `promotion-package` — source/target/head/tree/receipt/approval.
7. `bootstrap-plan` and `bootstrap-result` — App installation, permissions, credentials/bindings, workflows, rulesets, rollback.
8. `application-canary-result` — app/provider/tool, sanitized input class, result state, latency, exact package/provider identity.
9. `rollout-record` — consumer before/after, package, PRs, permanent branches, canaries, rollback.
10. `test-inventory` — required test components and profile membership.

Each schema requires positive, negative, unknown-field, version-mismatch, and round-trip tests.

### 11.1 Program-control and evidence layout

The executing agent creates one sanitized program ledger and updates it after every state transition. This prevents a long-running implementation from depending on conversational memory.

| Record | Required path in IDE Development | Required contents |
|---|---|---|
| Program ledger | `docs/evidence/v2.5/program-ledger.json` | schema version, program state, active packet, repositories, exact protected refs, packet states, approvals by reference, blockers, next dependency |
| Requirement trace | `docs/evidence/v2.5/requirement-trace.json` | every `G-*`, `FR-*`, `NFR-*`, and `AC-*`; owning packet/component/test/evidence; current state |
| Collision ledger | `docs/evidence/v2.5/path-ownership.json` | repository, path/pattern, exclusive packet owner, generated/manual classification, release point |
| Packet evidence | `docs/evidence/v2.5/packets/WP25-XX.json` | issue, branch, implementer identity, commits/trees, changed paths, commands/results, review identity/result, remote equality, residual holds |
| External-state inventory | `docs/evidence/v2.5/external-state.json` | GitHub App installation/permission names, workflow/check/ruleset names, provider pins, app/environment identifiers; never secret values |
| Release record | `docs/evidence/v2.5/release.json` | exact candidate/main/tag/artifact identities, Fast/Full/review receipts, approvals, publication checksums |
| Consumer rollout records | `docs/evidence/v2.5/rollout/<repository>.json` | before/after branches/trees, installed manifest, PRs, checks, app canaries, rollback/re-update, cleanup |

The ledger files are generated or schema-validated, deterministic, free of credentials/private bodies, and committed only when they are intended release evidence. Volatile logs and sensitive API responses remain under `.git/ide-development/v2.5-program/` and are summarized safely. If a repository convention supplies a stricter evidence location, the packet may use it but must record the resolved path in the program ledger.

### 11.2 Required packet state and output contract

Every WP25 packet uses exactly these states:

```text
not_started -> preflighted -> implementing -> checkpointed -> review_pending
-> accepted | repair_required | blocked | superseded
```

`accepted` requires all of the following:

- named issue and correct short-lived branch/worktree;
- exact base/head commit and tree;
- bounded changed-path list matching collision ownership;
- required focused commands with exit status and evidence path;
- clean Git status and pushed remote equality;
- independent exact-head review when required;
- no unresolved in-scope finding;
- next dependency identified.

`superseded` requires the replacement packet/commit and proof that no unique accepted work is being deleted. `blocked` requires the exact failed gate, evidence, attempted bounded recovery, owner, and resume action. Narrative statements such as “done,” “looks good,” or “tests passed” without these fields do not transition state.

### 11.3 Minimum schema field contracts

The packet implementing each schema may add fields but must not omit these minimums or weaken their meanings:

| Schema | Minimum required fields and constraints |
|---|---|
| `provider-registry` | `schemaVersion`, `providers[]`; each provider has immutable `id`, `ownerRepository`, `contractId`, `contractVersion`, `providerCommit`, `providerTree`, `capabilities[]`, `tools[]`, `transport`, `timeouts`, `retryPolicy`, `redactionPolicy`; no secret value or mutable `latest` |
| `provider-runtime-config` | `schemaVersion`, `consumerRepository`, `environment`, `providers`; each binding has provider `id`, non-secret endpoint/binding reference, credential reference name, enabled capabilities; secret values forbidden |
| `ide-skill-set-lock` | `schemaVersion`, IDE version, LiNKskills commit/tree, namespace, `skills[]`; each skill has exact identifier/version/release digest/fragments/qualification/publication/availability; no alias |
| `delivery-contract` | `schemaVersion`, contract version, supported branches/source patterns, one development context, one promotion context, profiles, path-risk rules, consumer product command mapping, review policy, repair/retry limits |
| `delivery-state` | repository, issue/Phase PR, base/head commits/trees, dependency/profile/workflow identities, current state, prior state, actor/identity, timestamp, review/check/receipt references, reason |
| `promotion-package` | repository, source branch, target branch, exact source/head/tree, accepted receipt and workflow identity, approval reference, marker schema/version, creation/expiry, rollback reference |
| `bootstrap-plan/result` | repository, before-state digest, desired App installation/permissions/repository scope, secret/variable/check/workflow/ruleset names, operations, canary plan/results, rollback operations, after-state digest; no credential value |
| `application-canary-result` | repository/tree, installed IDE version/manifest digest, app/id/version/session, profile, allowlisted tools, provider contract/pin, sanitized request class/result state, latency, cleanup result, evidence digest, timestamps |
| `rollout-record` | repository, before refs/trees/installed state, rollout issue/branch/PR, package/tag/archive/manifest identity, check/review receipts, after refs/trees, app canaries, rollback/re-update identities, cleanup, exclusions |
| `test-inventory` | schema/profile version, components[] with stable ID/owner/command/working directory/platform/risk paths/timeout/required flag/evidence parser; execution records exact selected and completed IDs |

Global schema rules:

- reject unknown top-level or trust-boundary fields unless the schema version explicitly marks an extension point;
- use explicit enums for states and proof levels;
- use UTC ISO-8601 timestamps and full 40-character Git commits/trees;
- store digests with named algorithm (minimum SHA-256 for file/archive payloads);
- distinguish absent, unavailable, denied, failed, empty-success, and passed;
- validate paths as repository-relative where committed and reject traversal/absolute consumer destinations;
- redact credential/prompt/transcript/private-body classes before persistence;
- provide one canonical generator/validator and checked fixtures for every schema.

## 12. Permanent Codex/Cursor application-canary harness

### 12.1 Purpose

The harness proves that a human using Codex or Cursor in an upgraded repository can actually reach and use the intended provider capabilities. It is permanent product acceptance tooling, not disposable release test code.

### 12.2 Proposed CLI

Extend `scripts/ide-development.py` with:

```text
canary plan    --repo <path> --app codex|cursor --profile <name> --json
canary run     --repo <path> --app codex|cursor --profile <name> --json
canary verify  --result <path> --json
canary cleanup --result <path> --json
```

Profiles:

- `provider-read`: Platform capability, Brain search, Skills search/exact retrieval.
- `brain-handoff`: isolated create/read/accept/close or deterministic cleanup.
- `libraries-read`: exact verified catalogue/release retrieval.
- `autowork-read`: status/receipt read when live runtime exists.
- `release-acceptance`: all required available profiles for one app.

### 12.3 Operation

For each app, the harness:

1. verifies the repository and installed package identity;
2. verifies provider configuration without printing secret values;
3. starts an isolated non-interactive app session in that repository;
4. grants only the profile's named tools;
5. invokes a small real operation;
6. captures sanitized tool/result evidence;
7. distinguishes empty-success from unavailable/failure;
8. closes the session and cleans isolated test state;
9. emits a signed/hash-bound result tied to package/provider/app versions.

It must not use screen coordinates, depend on window focus, or substitute a direct provider call outside the application. Cursor's ordinary production harness must not require blanket `--force`; Codex must likewise receive only profile-specific tools.

### 12.4 Example

```text
Repository: LiNKplatform
Application: Cursor
Allowed tools: platform project discovery and read-only SQL/capability read
Request: report whether Platform capabilities and organizations are accessible
Forbidden: file writes, shell, database writes, unrelated MCP tools
Expected: live Platform response, sanitized evidence, PASS, session closed
```

The 2026-08-19 baseline proved Cursor CLI can access `linkplatform-prod` when explicitly authorized, but its normal MCP approval rejected the read tool while blanket `--force` allowed it. v2.5 must replace that broad permission with the profile allowlist.

## 13. Test strategy and authoritative commands

### 13.1 Profiles

| Profile | Runs when | Contents | Must not contain |
|---|---|---|---|
| Focused | During each packet/repair | Changed module unit/contracts, schema negatives, diff/syntax | Unaffected workspace-wide suites |
| Fast | Once per Phase candidate | Formatting/static, secret scan, manifest/workflow checks, affected tests, selected consumer product command | Full E2E, repeated cross-platform matrix, unrelated packages |
| Full | Final sealed release-risk tree only | Machine-readable complete required inventory, integration, installer, security, release candidate, selected E2E | Optional cache as authority, repeated promotion execution |
| Promotion | Staging/main PR | Source policy, exact tree, receipt, target base, approval | Application build/test reruns |
| App canary | Release/canary rollout/provider change | Real Codex/Cursor provider calls | Source-only fixture substitution |
| Cross-platform | Installer/package changes | Ubuntu/macOS/Windows installer matrix | Provider production calls |

### 13.2 Existing commands to preserve or rationalize

The implementation must keep equivalent coverage for these current authoritative commands, while the new test inventory decides which profile owns each command:

```bash
PYTHONPATH=scripts python3 -m unittest discover -s scripts/ide_development_tests -v
python3 -m pytest tests/adapters -q
bash scripts/tests/test-gitops-behavioral.sh
bash scripts/tests/test-gitops-lifecycle.sh
bash scripts/tests/test-gitops-phase-delivery.sh
bash tests/test-portable-v2-integration.sh
bash scripts/verify-ide-development.sh
bash scripts/verify-pipeline-states.sh
node --test tests/link-integrations/test-*.mjs
python3 scripts/run_cross_platform_matrix.py
python3 scripts/ide-development.py release-candidate create
python3 scripts/ide-development.py release-candidate verify --archive <archive>
```

The executor must first inventory the exact current commands and remove duplicates by coverage, not by filename. If two commands prove the same assertion, retain one canonical owner and replace the other with receipt reuse or a lightweight reference check.

### 13.3 Full test inventory

Add a committed inventory assigning every required test component:

- identifier;
- command;
- owning profile;
- changed-path/risk selectors;
- dependencies;
- expected artifacts/receipt;
- maximum duration;
- platform applicability;
- required/optional status.

Full fails before execution if the inventory is malformed or a required declared package has no command. After execution it fails if any required component did not run to PASS.

### 13.4 Required negative simulations

At minimum prove:

- missing/wrong/expired App token;
- App removed from one repository;
- permission denied versus infrastructure unavailable;
- GitHub rate limit and transient outage;
- stale/obsolete required check name;
- external reviewer unavailable, including Bugbot quota/service unavailability, with the approved independent-review fallback exercised and the external service never misreported as passed;
- malformed promotion marker;
- changed tree with stale receipt;
- optional cache failure;
- skipped/missing required test;
- time-expired fixture;
- stale generated digest;
- unsupported model slug;
- unwritable linked-worktree metadata;
- stalled agent/no heartbeat;
- host memory below threshold;
- macOS path alias;
- unsupported remote shell option;
- automated mutation exceeding path/line limits;
- provider unavailable, denied, incompatible, malformed, and empty-success;
- unapproved local/global skill presented instead of LiNKskills release.

### 13.5 Deterministic WP25-00 command recipe

The executing agent adapts quoting only; it does not substitute narrative inspection for these facts.

For every repository in §3.1:

```bash
git -C "<repo-path>" remote get-url origin
git -C "<repo-path>" status --short --branch
git -C "<repo-path>" worktree list --porcelain
git -C "<repo-path>" fetch origin --prune
git -C "<repo-path>" rev-parse origin/development origin/development^{tree}
git -C "<repo-path>" rev-parse origin/staging origin/staging^{tree}
git -C "<repo-path>" rev-parse origin/main origin/main^{tree}
git -C "<repo-path>" branch -vv
```

For every GitHub repository, using authenticated `gh` or the equivalent connected GitHub API:

```bash
gh repo view linktrend/<repository> --json nameWithOwner,defaultBranchRef
gh pr list --repo linktrend/<repository> --state open --limit 100 --json number,headRefName,baseRefName,headRefOid,isDraft,url
gh workflow list --repo linktrend/<repository> --all
gh api repos/linktrend/<repository>/rulesets
gh api repos/linktrend/<repository>/branches/development/protection
gh api repos/linktrend/<repository>/branches/staging/protection
gh api repos/linktrend/<repository>/branches/main/protection
gh variable list --repo linktrend/<repository>
gh secret list --repo linktrend/<repository>
```

An unavailable ruleset/protection endpoint is recorded with HTTP status and plan/permission diagnosis; it is not interpreted as no protection. Secret listing records names and update timestamps only, never values.

Application/provider preflight:

1. enumerate the selected `LiNKdevelopment IDE` Cursor Cloud environment and close only completed/abandoned runs belonging to this program;
2. enumerate `LiNKtrading-codebase` separately and never touch unrelated trading work;
3. verify Codex and Cursor non-interactive entrypoints/version/help without starting a mutating session;
4. enumerate configured provider tools/bindings and credential reference names without calling a write tool;
5. check live provider health only through an approved read-only operation and do not infer application integration from health;
6. record exact command/API response class and timestamp in external-state evidence.

### 13.6 Command-result rules

- Every command records working directory, exact command, start/end time, exit status, and bounded output/evidence path.
- Pipelines use pipe-failure behavior; an earlier failed command cannot be hidden by a later successful formatter.
- `skipped`, missing executable, unavailable service, timeout, killed process, or partial output is not PASS.
- Do not rerun an unchanged expensive command. Diagnose first; rerun only after identity change or an authorized bounded infrastructure retry.
- A command discovered to be obsolete is replaced in the test inventory with documented equivalent coverage before removal.
- Hosted GitHub proof is tied to repository, run ID/attempt, workflow commit, head commit/tree, and conclusion.
- Local proof is tied to repository/worktree, head commit/tree, dependency lock, command, and platform identity.

## 14. Migration design

### 14.1 Skill migration

1. Inventory all current 43 skills and all three installed copies.
2. Classify each as migrate, merge, or retire.
3. In LiNKskills, create/update exact releases under the approved IDE namespace.
4. Qualify and publish through LiNKskills governance.
5. Produce the v2.5 skill-set lock.
6. Implement provider retrieval in IDE Development.
7. Prove Codex and Cursor retrieval/execution in an isolated consumer fixture.
8. Add exact supersession records for packaged v2.4 skill files.
9. Update a consumer transactionally; verify old copies are removed only when hashes/ownership match.
10. Prove rollback restores v2.4 copies and v2.5 update re-removes them.

### 14.2 Workflow/check migration

1. Inventory active workflows, job names, repository variables, rulesets/protection, labels, and required contexts.
2. Generate a before-state archive without secret values.
3. Install the new Delivery, Promotion, and Maintenance workflows.
4. Prove they can publish their contexts on a harmless canary branch/PR.
5. Atomically replace managed required contexts on `development`, `staging`, and `main` while preserving legitimate repository-owned contexts.
6. Disable/remove superseded managed workflows, variables, labels, and contexts.
7. Verify no protected branch requires an obsolete or impossible context.
8. Roll back all applied branches/settings if any branch fails migration.

### 14.3 GitHub App migration

1. Inventory current credential operations and required permissions.
2. Verify/install App access for the canary repository.
3. Verify protected secret/private-key availability without exposing the value.
4. Mint a least-privilege short-lived token and run harmless read/write/delete canaries.
5. Prove Review Ready/delivery state publication, Phase PR update, checks, normal protected merge on a harmless test candidate, and promotion package generation.
6. Simulate expiry/refresh, rate limit, removal, and permission denial.
7. Retain the former route until acceptance.
8. Cut over atomically, revoke the old credential, remove old references, and verify only one route is active.

### 14.4 Provider integration migration

1. Re-freeze provider contracts/pins from protected provider lines.
2. Retain and extend existing validators; do not discard fail-closed contract coverage.
3. Add transport and application tool registration behind validators.
4. Add provider configuration schema and secret references.
5. Materialize adapters into managed core/manifest.
6. Prove positive, denied, unavailable, incompatible, malformed, and redacted behavior.
7. Prove live calls where the provider is deployed; record explicit live holds elsewhere.

## 15. Roadmap, waves, and dependencies

### Wave 0 — freeze and baseline

Goal: create an exact, auditable starting point and prevent concurrent v2.5 surface collisions.

- WP25-00: baseline/freeze and collision map.
- WP25-01: schemas, identifiers, architecture decisions, and acceptance traceability.

Gate W0: accepted baseline commit/tree, current external-state inventory, packet path ownership, and no unresolved requirements ambiguity.

### Wave 1 — foundations (parallel after W0)

- WP25-02: GitHub App bootstrap/authentication foundation.
- WP25-03: consolidated delivery/check contract and test inventory.
- WP25-04: provider registry/transport foundation and Platform adapter.
- WP25-05: LiNKskills provider-side migration and skill-set lock.
- WP25-06: installer/manifest/supersession schema preparation.

Gate W1: each foundation has focused tests and independent design/code review; no managed package version bump yet.

### Wave 2 — provider and app capabilities

- WP25-07: Brain read and handoffs.
- WP25-08: Skills loader/discovery/telemetry in IDE Development.
- WP25-09: Libraries and Autowork adapters.
- WP25-10: Codex application adapter.
- WP25-11: Cursor application adapter.
- WP25-12: permanent application-canary harness.

Dependencies:

- 07/08/09 depend on 04; 08 also depends on 05.
- 10/11 depend on provider APIs from 04 and at least interfaces from 07–09.
- 12 depends on 10/11 and the provider profiles.

Gate W2: source/contract tests pass; both applications prove provider discovery in an isolated package fixture; live mutation remains unauthorized.

### Wave 3 — delivery simplification and package integration

- WP25-13: Packager/Delivery Controller simplification.
- WP25-14: workflow consolidation and atomic protection migration.
- WP25-15: test selection/evidence reuse and Full inventory.
- WP25-16: managed-core materialization, skill removal, migrations, installer/update/rollback.
- WP25-17: documentation/operator interface and stale component removal.

Gate W3: generated package is internally consistent; old/new active mechanisms do not coexist; cross-platform and rollback proofs pass.

### Wave 4 — final integration and release candidate

- WP25-18: serial Phase integration and exact-tree repair.
- WP25-19: independent combined exact-head review.
- WP25-20: Fast and one final combined Full on the sealed exact tree.
- WP25-21: protected IDE Development promotion, immutable publication, and release evidence.

Gate W4: protected `development`, `staging`, and approved `main` contain the accepted tree; published `v2.5.0` artifact exactly matches validated bytes.

### Wave 5 — real canary and rollout

- WP25-22: LiNKplatform canary install, migration, provider/app acceptance, delivery dry run, rollback proof.
- WP25-23: remaining eight repository-scoped rollout packets, parallelized only after the canary proves the package.
- WP25-24: global rollout reconciliation, cleanup, and closure.

Gate W5: nine consumers have verified v2.5 installs; repository-specific evidence/rollback exists; no stale managed workflows/checks/branches/worktrees/agents remain.

## 16. Detailed work packets

Every packet follows the same completion rule: focused validation, exact diff review, commit, push, clean status, remote equality, machine-readable evidence, and independent review where identified. Implementers do not open/merge their own delivery PRs.

### 16.1 One-agent end-to-end operating loop

The single executing agent performs this loop without waiting for the founder to supply packet prompts:

1. **Intake:** read this document completely; locate/verify repositories using §3.1; read applicable `AGENTS.md`; create the §11.1 ledgers.
2. **Preflight:** run WP25-00 read-only; verify protected refs, current branches/worktrees/agents/PRs, GitHub/provider/application access, credentials by name only, and approvals already present in the execution task or durable evidence.
3. **Freeze:** record exact commits/trees/contracts/pins and assign collision ownership. If the live baseline differs, update only the inventory/technical approach needed to reach the unchanged requirements; do not silently change a requirement.
4. **Issue setup:** for each packet, use the repository's `agentsetup` entrypoint to create/reuse an issue and `issue/*` worktree from current `development`. Record issue/branch/base.
5. **Implement:** execute only owned paths and requirements. Run focused tests, repair ordinary source failures within the declared limit, commit, push, verify clean status/remote equality, and write packet evidence.
6. **Review:** create a separate agent session with a distinct identity and read-only exact-head review prompt. The reviewer inspects scope, requirements, code, generated outputs, security, tests, and truthful evidence. It does not implement the reviewed packet.
7. **Repair:** send each accepted finding to the original implementation lane or a new repair lane; change only the narrow cause; rerun affected focused tests; push; invalidate the old review; obtain one new exact-head review.
8. **Integrate:** after dependency gates, Packager serially integrates accepted packet commits into one Phase tree. The executing agent resolves conflicts deliberately from ownership/requirements, never with blanket incoming/ours selection.
9. **Validate/release:** run the single Phase Fast, independent combined review, and one exact-tree Full when required; then use the protected delivery/promotion/publication sequence and approvals in §§18–19.
10. **Canary/rollout:** upgrade LiNKplatform first, prove rollback/re-update and both real app paths, then process the remaining eight in the declared order/parallelism without introducing systemic fixes in consumer branches.
11. **Close:** reconcile all permanent refs, PRs, temporary branches/worktrees/sessions, credentials/routes, managed files, canaries, and evidence; complete every checklist item and publish one consolidated report.

At every loop boundary the executing agent persists the program ledger. Context loss, task restart, or agent replacement therefore resumes from repository/evidence truth rather than requiring a founder briefing.

### 16.2 Internal packet and review prompts

When the executing agent delegates a packet, it generates the prompt below from this document and the live ledger. The founder does not prepare it.

```text
Implement WP25-XX from docs/IDE-DEVELOPMENT-V2.5-PRD-ROADMAP-IMPLEMENTATION-PLAN.md.
Repository: <exact repository and verified worktree>
Base: development <commit> / tree <tree>
Issue/branch: <issue> / <issue branch>
Owned paths: <collision-ledger paths only>
Requirements/acceptance: <exact G/FR/NFR/AC IDs and packet acceptance>
Dependencies: <accepted packet commits/trees/provider pins>
Required focused commands: <commands from inventory>
Exclusions: <repository and packet exclusions>
Finish at: commit + push + clean remote-equal checkpoint + packet evidence. Do not open/merge/promote/publish/deploy. Stop on an ownership, authorization, or contract conflict.
```

Independent review prompt:

```text
Independently review WP25-XX at exact commit <sha> / tree <tree> against the complete v2.5 document and packet evidence. You are not the implementer. Verify scope, owned paths, requirement coverage, code/generated parity, security/privacy, tests, failure states, and evidence truthfulness. Return PASS only when there are no actionable findings; otherwise return numbered findings with severity, exact path/line, violated requirement, and required correction. Make no source changes.
```

### 16.3 Exclusive source ownership before WP25-18

WP25-00 refines this table to exact files after live inventory. Until then these patterns prevent parallel collision:

| Packet | Exclusive implementation surface |
|---|---|
| WP25-01 | new schemas/examples and schema-test harness |
| WP25-02 | GitHub App authentication/bootstrap modules and their focused tests |
| WP25-03 | delivery contract, test inventory, risk/state definitions |
| WP25-04 | provider registry, shared transport, Platform client/tests |
| WP25-05 | LiNKskills provider issues/releases; IDE skill inventory and lock generator only |
| WP25-06 | installer manifest/state/transaction/migration engine, not generated managed-core output |
| WP25-07 | Brain and handoff client modules/tests |
| WP25-08 | Skills client/loader/cache/telemetry modules/tests |
| WP25-09 | Libraries and Autowork client modules/tests |
| WP25-10 | Codex application adapter/tests |
| WP25-11 | Cursor application adapter/tests |
| WP25-12 | application-canary CLI/runner/evidence/cleanup tests |
| WP25-13 | Packager, Delivery Controller, completion/evidence interaction |
| WP25-14 | managed workflow sources and external workflow/check/ruleset migration tooling |
| WP25-15 | risk selection, Fast/Full inventory execution, evidence reuse/cache policy |
| WP25-16 | generated `core/managed-core/`, manifest, combined migrations, installer integration |
| WP25-17 | active operator/product docs, CLI help, archive/retirement map |

Generated files are changed only by their owning generator packet or WP25-16 final generation. Cross-cutting changes that touch another packet's exclusive path wait for that owner or become a recorded narrow dependency; two agents never edit the same path concurrently.

### 16.4 Packet dependency and independent-review matrix

| Packet | Must wait for | May run with | Required independent acceptance |
|---|---|---|---|
| 00 | none | none | executing-agent baseline audit; no implementation review |
| 01 | 00 | 02, 03, 05 inventory, 06 design | architecture/schema review |
| 02 | 00 | 01, 03, 05 inventory, 06 design | security/authentication review plus harmless authenticated canary |
| 03 | 00 | 01, 02, 05 inventory, 06 design | delivery/test-contract review |
| 04 | 01 | 05 provider work, 06 | provider-boundary/security review |
| 05 | 00 and provider instructions; lock waits for 01 | 01–04, 06 | LiNKskills provider review and IDE lock review by identities other than implementers |
| 06 | 01 design | 02–05 | installer/migration review |
| 07 | 04 | 08, 09 | Brain/handoff boundary review |
| 08 | accepted LiNKskills releases from 05 and transport from 04 | 07, 09 | skill authority/cache/privacy review |
| 09 | 04 | 07, 08 | Libraries/Autowork contract review |
| 10 | 04, 07, 08 and applicable 09 interfaces | 11 | Codex adapter review and isolated app fixture |
| 11 | 04, 07, 08 and applicable 09 interfaces | 10 | Cursor adapter review and isolated app fixture |
| 12 | 10, 11 | 13–15 if paths do not collide | canary security/truthfulness review |
| 13 | 01–03; auth canary from 02 before live publication | 12, 14 design, 15 design | delivery-controller review and simulated lifecycle |
| 14 | 02, 03, 13 | 12, 15 | workflow/security review and atomic migration simulation |
| 15 | 03, 13, 14 contract identities | 12 | test-coverage/evidence review and hosted timing proof |
| 16 | 05–12, 14, 15 | 17 documentation after interfaces freeze | generated package/installer exact-tree review |
| 17 | stable interfaces from 13–16 | late 16 generation | operator/documentation review |
| 18 | accepted 01–17 | none | Phase integration checks; not a substitute for packet reviews |
| 19 | 18 exact tree | none | distinct combined reviewer; no source mutation |
| 20 | clean 19 exact tree | none | receipt/inventory verification distinct from implementers |
| 21 | 20 and required approvals | none | protected GitHub checks/reviews and publication identity verification |
| 22 | 21 published artifact and canary authorization | none | real Codex/Cursor canary evidence plus rollback/re-update verification |
| 23 | accepted 22 | repository lanes may run in parallel after per-repo preflight | per-repository review/check/canary evidence |
| 24 | 23 | none | independent reconciliation of repositories, GitHub, worktrees, sessions, and evidence |

“May run with” permits concurrency only when the collision ledger proves disjoint paths and repositories. The executing agent remains responsible for sequencing and context; it does not require the founder to coordinate these lanes.

### WP25-00 — baseline, freeze, and collision map

**Repository:** IDE Development  
**Objective:** Freeze exact protected source/external state and assign exclusive paths.  
**Work:**

- Fetch protected `development`, `staging`, `main`; record commits/trees and package/release identities.
- Inventory manifest entries, workflows/jobs/triggers, required contexts, variables, labels, GitHub App installation/permissions, credentials by name only, active PRs/branches/worktrees/agents, test commands/durations, provider pins, and consumer v2.4 installed states.
- Confirm whether Issue #339 requirements branch has been integrated or import its exact accepted document commit through the Packager later.
- Create collision map assigning every planned path to exactly one packet.
- Freeze v2.5 requirement IDs and acceptance mapping.

**Owned paths:** v2.5 planning/evidence documents only.  
**Acceptance:** exact identities, no secrets, all nine consumers inventoried, no implementation edits.

### WP25-01 — schemas and architecture contracts

**Objective:** Implement schemas/records from §11 and stable error/state identifiers.  
**Files:** new schemas under `core/managed-core/schemas/`; canonical examples; schema tests.  
**Acceptance:** positive/negative/unknown/version tests; every FR maps to a schema, component, test, or explicit non-schema implementation.

### WP25-02 — GitHub App bootstrap and durable authentication

**Objective:** Replace fragile local/static-token publication with one provisioned App route.  
**Files:** `scripts/gitops/` auth/bootstrap modules, tests, managed non-secret config/schema.  
**Required operations:** plan/apply/verify/rollback; permission parity; installation/repository scope; secret-name existence; short-lived mint/refresh; harmless publisher/check canary; rate-limit/removal/expiry negatives; before/after archive.  
**Hard stop:** first-time App installation/private-key authorization absent and cannot be performed by authenticated operator. Report one exact external action; do not fall back silently.  
**Acceptance:** Review Ready/delivery publication works before another packet relies on it; no token printed or committed.

### WP25-03 — delivery contract and test inventory

**Objective:** Define one delivery state/check contract and canonical test profiles.  
**Files:** delivery config/schema, test inventory, risk selector, state tests.  
**Acceptance:** one managed development context, one promotion context, no impossible name, complete test inventory, fixture simulations for every state.

### WP25-04 — provider registry, transport foundation, Platform

**Objective:** Convert offline validator boundary into a real, bounded transport foundation and Platform client.  
**Files:** `core/link-integrations/` canonical modules/tests/fixtures; provider registry/config schemas.  
**Acceptance:** validators remain fail-closed; transport has timeout/retry/redaction; Platform live read canary from a non-production-mutating test client; no credentials in source.

### WP25-05 — LiNKskills skill migration

**Repositories:** LiNKskills (provider changes), IDE Development (inventory/lock only after provider acceptance).  
**Objective:** Move every IDE skill to LiNKskills and publish the exact v2.5 skill-set lock.  
**Process:** inventory 43 skills; deduplicate/retire; create provider issues; qualify immutable releases; independently review; promote through LiNKskills governed source path if authorized; freeze provider commit/tree/releases/digests; generate lock.  
**Acceptance:** no unresolved skill; no mutable alias; exact namespace; progressive fragments; telemetry/redaction; provider source clean/pushed/promoted as authorized.  
**Hard stop:** provider release not qualified/published; do not delete IDE copies yet.

### WP25-06 — installer/manifest migration preparation

**Objective:** Add manifest/migration capabilities required to remove skills and install providers/workflows safely.  
**Files:** `scripts/ide_development/`, manifest/state/transaction schemas, migrations, tests.  
**Acceptance:** plan is deterministic; exact-hash supersession; unknown modifications preserved/fail; rollback restores; package version remains 2.4.0 until integration.

### WP25-07 — Brain and handoffs

**Objective:** Implement bounded Brain reads and isolated handoff lifecycle behind Platform capabilities.  
**Acceptance:** positive/empty/denied/unavailable/incompatible/malformed; advisory-only; no raw content; isolated handoff create/read/accept/cleanup in authorized test environment.

### WP25-08 — IDE LiNKskills loader

**Objective:** Implement exact skill discovery/retrieval and eliminate fallback authority.  
**Acceptance:** lock/pin/digest validation, progressive fragments, cache isolation, telemetry, unavailable fail, rejection of local/global/marketplace/model-invented alternatives.

### WP25-09 — Libraries and Autowork

**Objective:** Complete real retrieval/request clients while preserving contract ownership.  
**Acceptance:** full native Libraries profiles/identities; Autowork ordering/expiry/idempotency/status; live canary only when runtime exists; no provider mutation from IDE tests.

### WP25-10 — Codex adapter

**Objective:** Make provider tools and LiNKskills retrieval available to Codex from any consumer directory without physical workflow skills.  
**Files:** Codex managed platform source, managed AGENTS block, adapter/config tests.  
**Acceptance:** real non-interactive session discovers only allowlisted tools/skills; nested directory works; consumer AGENTS content preserved.

### WP25-11 — Cursor adapter

**Objective:** Make equivalent provider tools/skills available to Cursor without blanket approval.  
**Files:** Cursor managed rules/config/materialization source and tests.  
**Acceptance:** Cursor CLI and macOS app-compatible path; narrow tool policy; no `--force` requirement; nested directory; no external symlink.

### WP25-12 — application-canary harness

**Objective:** Implement §12 CLI and evidence schemas.  
**Acceptance:** Codex/Cursor provider-read and Brain-handoff profiles; sanitized results; cleanup; no screen automation; unavailable app/tool fails; direct outside-app call cannot satisfy result.

### WP25-13 — Packager and Delivery Controller

**Objective:** Retain one real Packager and one real Delivery Controller.  
**Files:** simplify `packager_coordinator.py`, `delivery_controller.py`, completion/evidence interaction; retire/rename misleading alternatives.  
**Acceptance:** harmless end-to-end simulated Phase lifecycle; implementer cannot self-merge; exact reread before transition; bounded repair/stall handling.

### WP25-14 — workflow/protection consolidation

**Objective:** Implement three managed consumer workflows and atomic external migration.  
**Acceptance:** workflow validation/security; required contexts produced; branch-source integrated; reviewer unavailable fallback; no candidate code in privileged context; full rollback simulation.

### WP25-15 — risk selection, Fast, Full inventory, evidence reuse

**Objective:** Meet runtime and non-redundancy targets.  
**Acceptance:** Fast under five minutes in representative hosted run; Full inventory omission negative; unchanged evidence reuse; optional cache failure non-blocking; changed tree invalidates receipt; promotions run no equivalent application suite.

### WP25-16 — managed package integration and v2.4 migration

**Objective:** Materialize providers/adapters/harness/workflows; remove physical skill copies; regenerate 2.5 package.  
**Files:** `core/managed-core/`, generated `MANIFEST.json`, migrations, installer tests.  
**Acceptance:** deterministic second generation; expected file-count reduction documented; no active workflow skill implementation remains in IDE system source or any managed consumer destination; install/update/verify/drift/rollback; extracted archive; cross-platform matrix.

### WP25-17 — docs, operator interface, and stale removal

**Objective:** Make installed and operator behavior understandable without historical docs.  
**Work:** update root/current technical/operator docs, CLI help, error messages, rollout/rollback runbook; archive/retire obsolete active instructions and components.  
**Acceptance:** command/link checks; no obsolete version/check/skill instructions in active surfaces; plain-English blocker messages.

### WP25-18 — Phase integration

**Objective:** Serially integrate accepted packet commits into one v2.5 Phase candidate.  
**Rules:** Packager only; resolve conflicts deliberately; regenerate all generated surfaces after serial integration; set `2.5.0` identities; no Full yet.  
**Acceptance:** one Phase PR, exact commit/tree/dependency inventory, Fast PASS.

### WP25-19 — independent combined review

**Objective:** Review the entire exact v2.5 candidate, including generated files and external migration plans.  
**Acceptance:** clean exact-head review; findings repaired on issue/phase repair commits within bounds; any repair invalidates prior review and requires a new exact-head review.

### WP25-20 — final combined validation

**Objective:** Execute the one final release-level Full on the sealed exact tree.  
**Contents:** complete inventory, installer/migrations, providers/contracts, Codex/Cursor adapters, workflow/security, release candidate reproducibility, cross-platform when installer changed, automated mutation guards.  
**Acceptance:** all required components PASS; one sealed receipt; no rerun unless tree/dependencies/workflow changed or explicit authorized infrastructure retry.

### WP25-21 — IDE promotion and publication

**Objective:** Merge normally to `development`, promote identical tree to `staging`, obtain main approval, promote, publish immutable v2.5.0.  
**Acceptance:** exact tree/evidence reuse, generated promotion packages, no application suite reruns, tag/release/checksums match main, rollback release retained.

### WP25-22 — LiNKplatform real canary

**Objective:** Upgrade one existing consumer first.  
**Sequence:** drift/plan; bootstrap/App/check migration; rollout PR; Fast/review/conditional Full only for actual consumer changes; merge/promote as authorized; run Codex and Cursor release-acceptance canaries; perform update rollback and re-update proof; verify no product regression.  
**Acceptance:** live Platform + Brain + Skills + handoff proof from both apps; Libraries/Autowork per availability; delivery dry run; rollback; clean branches/worktrees/sessions.

### WP25-23 — remaining eight rollouts

**Objective:** Upgrade the remaining repositories after canary acceptance.  
**Parallelism:** one repository-scoped lane each where capacity allows; systemic package changes forbidden inside consumer lanes.  
**Special:** openclaw/Lisa runtime is not redeployed unless separately authorized; LiNKtrading gets IDE-only change.  
**Acceptance per repo:** drift/plan, rollout PR, installed hashes/config, app discovery, applicable small canaries, permanent branch equality per authorized promotion scope, rollback identity, cleanup.

### WP25-24 — reconciliation and closure

**Objective:** Prove the program is finished and remove temporary state.  
**Acceptance:** nine repository records; no open program PRs, obsolete branches/worktrees, stale agents, old managed workflows/checks, active legacy auth, or unresolved systemic holds; one consolidated report; deferred live-provider holds explicitly owned.

## 17. Acceptance matrix

| Acceptance ID | Required proof | Owning packets |
|---|---|---|
| AC-01 | Complete baseline/collision/external inventory | 00 |
| AC-02 | All schemas/examples/negative tests | 01, 03 |
| AC-03 | GitHub App provision/repair/canary/rollback, no repeated missing credential | 02, 14, 22 |
| AC-04 | One real Packager and Delivery Controller | 13 |
| AC-05 | One managed development context and one promotion context; atomic ruleset parity | 03, 14 |
| AC-06 | Fast under five minutes | 15, 18 |
| AC-07 | One final exact-tree Full receipt and promotion reuse | 15, 20, 21 |
| AC-08 | No optional cache/post-job can invalidate required proof | 15, 20 |
| AC-09 | No packaged IDE workflow skills; all resolved from LiNKskills lock | 05, 08, 16 |
| AC-10 | Platform identity/capability behavior | 04, 12, 22 |
| AC-11 | Brain read/handoff behavior | 07, 12, 22 |
| AC-12 | Skills discovery/retrieval/telemetry/no fallback | 05, 08, 10, 11, 12, 22 |
| AC-13 | Libraries native retrieval | 09, 12, 22 |
| AC-14 | Autowork behavior or truthful live hold | 09, 12, 22 |
| AC-15 | Codex/Cursor functional equivalence and narrow permissions | 10, 11, 12, 22 |
| AC-16 | Transactional v2.4→v2.5 update, skill removal, rollback, cross-platform | 06, 16 |
| AC-17 | Automated mutation/stall/model/resource/path/shell negative protections | 13, 15, 16, 20 |
| AC-18 | Published artifact equals accepted main tree/package bytes | 21 |
| AC-19 | LiNKplatform canary complete before other rollout | 22 |
| AC-20 | Nine consumers verified and cleaned | 23, 24 |

No acceptance row may be marked passed by a packet owner alone when independent review or live application proof is required.

### 17.1 Complete requirement-family trace

The machine-readable requirement trace expands every individual ID. This table supplies the deterministic initial mapping; no ID may remain without component, test, evidence, and final state.

| Requirement IDs | Primary packets | Minimum proof/evidence |
|---|---|---|
| G-01–G-02 | 04, 05, 07–12, 16, 22 | installed adapters, exact skill lock, real Codex/Cursor provider and handoff canaries |
| G-03–G-07 | 02, 03, 13–15, 18–21 | App bootstrap, workflow/check contract, Phase lifecycle, Fast/Full/review/promotion receipts |
| G-08–G-10 | 00, 16, 20–24 | canary-first rollout, rollback/re-update, negative recovery, nine rollout records |
| FR-PKG-01–08 | 01, 06, 16, 20, 21 | schema/installer/migration/archive/manifest tests and reproducible release artifact |
| FR-PLAT-01–04 | 04, 10–12, 22 | contract negatives, authorization/redaction, live app capability canaries |
| FR-BRAIN-01–05 | 07, 10–12, 22 | advisory read tests and isolated real handoff lifecycle/cleanup |
| FR-SKILL-01–09 | 05, 08, 10–12, 16, 22 | qualified releases/lock, no-fallback negatives, telemetry/redaction, absence of IDE-owned skills |
| FR-LIB-01–05 | 09, 12, 22 | exact identity/profile/release/receipt contract tests and applicable app canary |
| FR-AUTO-01–05 | 09, 12, 22 | request/status/ordering/expiry/idempotency/redaction tests and live canary or truthful hold |
| FR-APP-01–06 | 10–12, 16, 22 | equivalent Codex/Cursor discovery, narrow permissions, nested-directory, error taxonomy, cleanup |
| FR-AUTH-01–10 | 02, 14, 22 | App permission/install/token/refresh/trigger/rate-limit/removal/rollback canaries and single-route proof |
| FR-DEL-01–13 | 03, 13–15, 18–21 | versioned delivery state, Phase PR, exact review, real controllers, receipt reuse, promotion policy |
| FR-TEST-01–10 | 03, 12, 15, 18, 20–23 | profile inventory, under-five-minute Fast, one sealed Full, self-contained tests, evidence taxonomy |
| FR-OPS-01–07 | 00, 02, 13, 15, 16, 20, 23, 24 | dispatch/host/path/mutation/stall negatives, clean session/worktree closure |
| FR-ROL-01–09 | 16, 21–24 | exact release identity, first canary, nine repository records, rollback and cleanup |
| NFR-PERF-01–06 | 12, 15, 18, 20–23 | hosted/app/install/promotion timing receipts and bounded-wait tests |
| NFR-SEC-01–07 | 01, 02, 04, 07–12, 14, 20 | boundary fuzz/limits/redaction, tool allowlists, immutable Actions, privileged-context review |
| NFR-REL-01–06 | 02, 06, 13–16, 20–23 | deterministic/idempotent and rollback tests, bounded retry/repair, no-fallback negatives |
| NFR-PORT-01–05 | 06, 11, 16, 20 | Python/Bash/path/symlink tests and Ubuntu/macOS/Windows matrix |
| NFR-MAINT-01–04 | 01, 03, 16, 17, 24 | canonical generators/provenance, inactive legacy surfaces, operator-message review |
| AC-01–20 | owning packets in §17 | exact acceptance evidence referenced from program and packet ledgers |

### 17.2 Acceptance decision algorithm

For each requirement ID, the executing agent must record:

1. `implementedBy`: exact repository/path/component and commit/tree;
2. `verifiedBy`: named command/canary/review and immutable result;
3. `evidence`: committed sanitized evidence path or hosted receipt coordinates;
4. `proofLevel`: one of `source`, `package`, `installed`, `hosted`, `application`, `stage`, `VPS`, `E2E`, `production`;
5. `state`: `passed`, `failed`, `blocked`, `not_applicable`, or `deferred`;
6. `rationale`: mandatory for `not_applicable`/`deferred`, with owner and later gate.

An acceptance criterion passes only when every required constituent ID has the required proof level. A stronger-sounding narrative cannot substitute for a missing level; for example, installed hashes cannot pass an application canary, and a direct provider call cannot pass a Codex/Cursor application requirement.

## 18. Failure and recovery policy

### 18.1 Source defects

- Repair within owning packet, maximum three ordinary cycles.
- Rerun focused affected tests, not unchanged unrelated suites.
- New head invalidates exact-head review/receipts that depended on prior tree.

### 18.2 Infrastructure defects

- Retry same exact candidate at most twice.
- Preserve exact failure and distinguish GitHub/provider/host/tool outage from source failure.
- No code change merely to make an infrastructure-only failure disappear.

### 18.3 Stalled agents/workflows

- A run without material heartbeat/progress beyond configured limit is inspected once, then cancelled and replaced if truly stalled.
- Close stale sessions before claiming capacity exhaustion.
- A Cursor API `resource_exhausted` or busy response is not accepted as a final capacity diagnosis until the controller has reconciled the selected environment's active-run list, cancelled or closed completed/abandoned runs, retried one bounded allocation, and recorded the resulting active identities and API response.
- Do not interrupt healthy CPU-bound work solely for elapsed time.
- Do not inspect, cancel, or replace unrelated work in another repository or Cursor environment.

### 18.4 Broad automated mutation

- Abort immediately when path/line limits are exceeded.
- Identify introducing tool/commit.
- Restore last known-good tree via targeted revert/transaction rollback.
- Re-run syntax/build before any merge.

### 18.5 Rollout defect

- Repository-specific: rollback/pause that repository; continue others only if package is proven unaffected and scope authorizes.
- Systemic package/provider/adapter/workflow defect: stop all remaining rollouts, rollback affected consumers, repair in IDE Development, produce new exact release candidate/version as required, re-canary.

## 19. Approval gates

This document does not grant these approvals. The execution task must provide them or the executing agent stops at the gate with evidence:

| Gate | Approval required |
|---|---|
| Provider repository implementation/promotion | Authorization for the named provider packet and repository |
| First-time GitHub App installation/permission/private-key setup | Authenticated owner/admin authorization when not already established |
| Live ruleset/protection/secret/variable mutation | Exact bootstrap/migration apply authorization |
| Merge v2.5 Phase PR to IDE `development` | Normal protected delivery authority |
| Promote IDE to `staging` | Normal protected promotion authority |
| Promote IDE to `main` | Explicit founder approval unless already recorded for exact tree/operation |
| Publish v2.5.0 tag/release | Exact release publication authority |
| Install/mutate first consumer | Canary rollout authorization |
| Remaining consumer rollouts | Program/repository authorization; preserve repository-specific exclusions |
| Deploy/restart live VPS/runtime services | Separate runtime deployment authorization; not implied by IDE rollout |

## 20. Executor handoff checklist

Before declaring v2.5 ready, the executing agent must answer **yes** with evidence to every item:

- [ ] Requirements and packet path ownership frozen.
- [ ] All implementation branches clean, pushed, and either integrated or explicitly retired.
- [ ] Provider pins/contracts and skill-set lock are exact and current.
- [ ] IDE Development packages no workflow skills.
- [ ] IDE Development system source contains no active IDE-owned workflow skill implementation; its own agents use the LiNKskills loader.
- [ ] Codex and Cursor retrieve only approved LiNKskills releases.
- [ ] Platform, Brain, Skills, and handoff live canaries pass in both apps.
- [ ] Libraries/Autowork pass applicable live or truthful held acceptance.
- [ ] GitHub App route is provisioned, verified, refreshable, and the legacy route is retired after canary.
- [ ] One real Packager and Delivery Controller exist and are callable.
- [ ] Managed required checks match producible workflow outputs atomically.
- [ ] Fast target met.
- [ ] Final required Full ran once on the sealed tree and inventory proves every required component executed.
- [ ] Staging/main reused evidence and did not rerun equivalent suites.
- [ ] v2.5.0 artifact is reproducible and equals validated main bytes.
- [ ] LiNKplatform canary passed including rollback/re-update.
- [ ] Remaining eight consumers verified with rollback records.
- [ ] LiNKtrading received no unrelated product merge.
- [ ] No open program PR, temporary branch/worktree, stale agent, obsolete managed workflow/check, or competing authentication route remains.
- [ ] Consolidated completion report distinguishes source, package, installed, hosted, app, stage, VPS, E2E, and production proof.

## 21. Definition of ready and definition of done

### Ready for implementation

The program is ready to start when WP25-00 has revalidated the protected starting point, the execution task authorizes the named repositories/scope, and packet collision ownership is accepted.

### Ready for release

The v2.5 candidate is ready for protected merge/promotion when WP25-18 through WP25-20 have produced one exact candidate, clean independent review, Fast PASS, and the single required Full receipt with complete inventory.

### Done

IDE Development v2.5.0 is done only when:

1. the accepted system tree is protected on authorized IDE branches and published immutably;
2. one real consumer passed full Codex/Cursor/provider/handoff and rollback canaries before broad rollout;
3. all nine consumers contain verified v2.5 managed bytes and applicable functional evidence;
4. Codex and Cursor use LiNKskills as the sole IDE workflow-skill authority;
5. ordinary issue-to-main delivery follows the simplified topology without redundant tests/checks;
6. real failures still stop safely with one clear explanation; and
7. temporary program state and obsolete v2.4 delivery/skill/authentication surfaces are removed or archived and inactive.

Anything less is a checkpoint, partial acceptance, or explicit hold—not a completed v2.5 release.
