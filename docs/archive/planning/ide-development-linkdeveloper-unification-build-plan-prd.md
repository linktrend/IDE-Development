# IDE Development ↔ LiNKdeveloper Unification Build-Plan PRD

> **ARCHIVED / SUPERSEDED (2026-07-18).**  
> This document is historical planning evidence only.  
> **Authoritative current doctrine:** `core/execution/APPLICATION-PIPELINE.md`  
> Living Document / dual-PRD language below was rewritten in this archive copy to Technical PRD terminology so it cannot be mistaken for active guidance. Do not implement from this file.

---

**Document type:** implementation-ready build plan; no implementation is performed by this document  
**Status:** Draft for Principal decision on flagged items  
**Date:** 2026-07-17  
**Primary implementer:** a lower-supervision execution agent (Grok)  
**Owning repositories:**  
- `/Users/linktrend/Projects/IDE Development`
- `/Users/linktrend/Projects/LiNKdeveloper`

## OPEN QUESTIONS / FLAGGED ASSUMPTIONS

The implementation agent MUST NOT silently decide these items.

1. **Shared Library repository creation and name.** This plan recommends one new private GitHub repository, `linktrend/LiNKlibraries`, as the canonical Component/Template/Asset Library. Local checkouts are caches; the Git remote’s protected `development` branch is the single source of truth. Creating that repository is an external write and requires Principal approval. If the Principal rejects this name or Git-backed design, stop after Phase 1 and revise this PRD; do not substitute a database or a folder inside either existing repository.
2. **Shared Library publication authority.** Recommended policy: both systems may create contribution branches and pull requests automatically after their Module 5 gate passes; only the Integrator may merge into `development`. No system may push directly to `development`, `staging`, or `main`. Principal confirmation is required before enabling automatic PR creation. Until confirmed, both systems MUST produce a local contribution bundle and stop at `publication_pending`.
3. **Meaning of “every app IDE Development helps build.”** This plan applies the fixed six-Module pipeline to a new application, a substantial rebuild, or a release-sized application increment. It does not force a full six-Module rerun for a one-file bug fix or other atomic maintenance change; those continue through the existing issue proof/review/integration path and are included in the next release’s Module 4–6 evidence. If the Principal intends every maintenance change to instantiate all six Modules, the templates and routing rules must be revised before Phase 3.
4. **Existing LiNKdeveloper Library data.** The code and schema exist, but this audit did not query live rows in `ldeveloper_ledger.library_entries`. Before switching authority to `LiNKlibraries`, the implementer must export and count live rows. If rows exist, migrate each to a Library entry through a reviewed PR and retain the old rows as read-only audit records. If no rows exist, record a zero-row migration report. Never delete the table in this work.
5. **Internal `.cursor` compatibility symlink.** This plan vendors IDE Development’s physical skill copy under `core/runtime/skills/` and exposes it as `.cursor/runtime/skills/` through the repository’s existing `core → .cursor` compatibility-symlink pattern. The vendored content itself is a real copy, not a symlink to `/Users/linktrend/Projects/gstack` or `/Users/linktrend/Projects/skills`. This is assumed to satisfy the Principal’s “copy, not symlink” requirement. If even an internal compatibility symlink is prohibited, place a second generated copy under `.cursor/runtime/skills/` and add hash-equality verification.

## 1. Executive decision and feasibility conclusion

### 1.1 Required outcome

Converge the two systems on:

1. the same fixed six-Module application-build pipeline;
2. one shared, bidirectional Component/Template/Asset Library;
3. equivalent but physically separate vendored hybrid skill copies;
4. verified stop-progression behavior for laws, gates, and proof.

The two systems remain independent codebases and retain all five permanent differences stated by the Principal.

### 1.2 Feasibility conclusion for IDE Development

**Conditionally feasible, but not mechanically identical to LiNKdeveloper.**

Evidence:

- `core/runtime/EXECUTION-LOOP.md` explicitly defines a “human-driven runtime loop.”
- `core/execution/AUTONOMOUS-MODULE-EXECUTION.md` allows a capable Cursor runtime to recurse through module artifacts until complete or blocked.
- `core/execution/MINIMUM-RUNTIME-MODEL.md` makes readiness artifact-derived and permits module/program gates.
- `core/state/STATE-MODEL.md` requires state to be artifact-visible and runtime-independent.
- No persistent process, durable database Ledger, heartbeat, lease, or crash-recovery loop exists in IDE Development.

A Cursor Desktop orchestrator session can:

- execute six Modules sequentially while the session is active;
- delegate issue execution to subagents;
- invoke deterministic validators;
- stop at human and quality gates;
- persist all state and evidence in the target repository;
- resume in a later session by re-reading and validating those artifacts.

It cannot, without adding a separate persistent orchestrator:

- keep polling after Cursor closes;
- guarantee unattended crash recovery;
- enforce a gate against every possible direct/manual edit path;
- match LiNKdeveloper’s Ledger-level transactional state enforcement.

Therefore the closest valid IDE Development design is:

> **A session-scoped Cursor Agent orchestrator over a durable, fail-closed, repository-resident pipeline state machine, with deterministic transition validation before every Module advance.**

Do not claim “mechanical runtime parity.” Claim **pipeline-shape parity, artifact-contract parity, gate semantics parity, and tested in-session behavioral parity**.

### 1.3 Mandatory feasibility gate

Phase 2 below MUST pass before any active IDE Development doctrine or command is migrated. If it fails:

1. leave current active behavior unchanged;
2. write the failed evidence to `docs/validation/fixed-pipeline-feasibility-report.md`;
3. implement only the closest approximation described in §1.2 after Principal review;
4. do not describe the six-Module driver as autonomous.

## 2. Scope

### 2.1 In scope

- Fixed Module 1–6 names, ordering, phases, outputs, and gates in IDE Development.
- Durable IDE Development pipeline state, transition validation, resume semantics, and gate tests.
- A single shared Git-backed Library used by both systems.
- Migration of LiNKdeveloper’s existing Ledger-backed Library from authority to audit/cache status.
- Separate in-repository skill copies in IDE Development and LiNKdeveloper.
- Repo-relative hybrid command references.
- Real loading of vendored skills into LiNKdeveloper Cursor SDK calls.
- Adapted skills covering all six Modules.
- Cross-system contract tests and supervised behavioral gate tests.

### 2.2 Explicitly out of scope

- LiNKdeveloper VPS deployment or live-environment testing.
- Deploying any application to a VPS or production environment.
- New Program specifications such as LiNKsales or LiNKmedia.
- Cursor Desktop model-routing enforcement.
- Replacing Cursor Desktop with a persistent external IDE Development orchestrator.
- Merging the two repositories or introducing a live IDE Development runtime dependency into LiNKdeveloper.
- Re-litigating the five accepted permanent differences.

## 3. Authoritative current-state findings

The implementation agent must preserve these facts:

1. LiNKdeveloper’s authoritative pipeline is `docs/specs/linkdeveloper-spec.md` §3:
   - Module 1 — Intake & Definition
   - Module 2 — Assembly Planning
   - Module 3 — Execution
   - Module 4 — Verification & Hardening
   - Module 5 — Library Contribution
   - Module 6 — Shipment
2. IDE Development currently defines Module as “a major domain area” in `core/execution/MINIMUM-RUNTIME-MODEL.md`; `core/templates/PROGRAM.md`, `core/templates/MODULE.md`, `core/workflows/PROGRAM-WORKFLOW.md`, and `core/prompts/execution/PLAN-PROGRAM.md` all permit fresh module decomposition.
3. IDE Development’s Law 16 says gates stop progression, but `scripts/verify-ide-development.sh` checks structure and documentation only; it does not validate or enforce runtime state transitions.
4. IDE Development has exactly these 12 active hybrid command files:
   - `core/commands/hybrid-spec.md`
   - `core/commands/hybrid-grill.md`
   - `core/commands/hybrid-to-prd.md`
   - `core/commands/hybrid-to-issues.md`
   - `core/commands/hybrid-tdd.md`
   - `core/commands/hybrid-diagnosing-bugs.md`
   - `core/commands/hybrid-health.md`
   - `core/commands/hybrid-ship.md`
   - `core/commands/hybrid-plan-ceo-review.md`
   - `core/commands/hybrid-context-save.md`
   - `core/commands/hybrid-context-restore.md`
   - `core/commands/hybrid-improve-architecture.md`
5. LiNKdeveloper already has 71 vendored skill files under `runtime/skills/`, but the Module 1 and Module 2 prompt builders do not read those files. `packages/executors/src/cursor-sdk-adapter.ts` also builds its prompt only from Issue fields.
6. LiNKdeveloper already has:
   - `ldeveloper_ledger.library_entries`;
   - Library CRUD in `packages/program-ledger`;
   - Module 2 Library reads;
   - Module 5 extraction, judgment, duplicate filtering, contribution, and gate code.
   The text in `docs/specs/linkdeveloper-spec.md` saying Library schema/storage is TBD is stale.

## 4. Target pipeline contract

### 4.1 Fixed Module IDs and names

Both systems MUST use these stable IDs and labels:

1. `intake_and_definition` — **Module 1 — Intake & Definition**
2. `assembly_planning` — **Module 2 — Assembly Planning**
3. `execution` — **Module 3 — Execution**
4. `verification_and_hardening` — **Module 4 — Verification & Hardening**
5. `library_contribution` — **Module 5 — Library Contribution**
6. `shipment` — **Module 6 — Shipment**

No application Program may rename, reorder, omit, or insert a seventh top-level Module. Product-specific decomposition belongs inside the fixed Modules as Phases and Issues.

### 4.2 Required Module behavior

#### Module 1 — Intake & Definition

Ordered phases:

1. `1.1-entry-classification`
2. `1.2-interview-to-intent`
3. `1.3-prd-drafting`
4. `1.6-technical-prd` (was living-document; superseded 2026-07-18)
5. `1.5-principal-approval`

Required outputs:

- `INTENT.md`
- `PRD.md`
- `TECHNICAL-PRD.md`
- recorded Principal decision covering PRD and Technical PRD

Gate:

- fail closed until Principal approval is explicitly recorded;
- rejection returns to Phase 1.2, 1.3, or 1.4 with a recorded reason;
- Module 2 cannot become active on a missing or implied approval.

#### Module 2 — Assembly Planning

Ordered phases:

1. `2.1-feature-component-map`
2. `2.2-library-starter-kit-query`
3. `2.3-oss-research`
4. `2.4-oss-vetting`
5. `2.5-issue-dependency-graph`
6. `2.6-independent-plan-gate`

Required outputs:

- feature-to-component map;
- Library query report with exact Library commit SHA;
- starter-kit decision;
- OSS research and vetting records;
- dependency-acyclic Issue graph;
- executor assignment per Issue;
- acceptance-criterion coverage map from every Technical PRD acceptance criterion to one or more Issues.

Gate:

- independent reviewer;
- every criterion mapped;
- no unvetted OSS;
- DAG valid;
- every Issue has bounded paths, dependencies, and non-vacuous acceptance criteria.

#### Module 3 — Execution

Required behavior:

- dispatch only dependency-ready Issues;
- use subagents only as IDE Development executors;
- require Issue proof, independent review, and integration before `done`;
- reject self-report as proof;
- recompute readiness after integration.

Module gate:

- every required Issue is `done`;
- every Technical PRD acceptance criterion has real evidence;
- a separate reviewer issues a Tier-B-equivalent verdict.

#### Module 4 — Verification & Hardening

Required phases:

1. `4.1-full-test-and-build`
2. `4.2-security-and-dependency-audit`
3. `4.3-end-to-end-acceptance-verification`
4. `4.4-repair-loop`
5. `4.5-independent-module-gate`

Gate:

- independent verifier checks the full integrated application against every Technical PRD acceptance criterion;
- any failed criterion creates a repair Issue and blocks Module 5;
- optional Principal UI/commercial review is recorded but is not fabricated when not requested.

#### Module 5 — Library Contribution

Required phases:

1. `5.1-candidate-extraction`
2. `5.2-existing-library-deduplication`
3. `5.3-entry-authoring`
4. `5.4-entry-validation`
5. `5.5-contribution-publication`
6. `5.6-independent-module-gate`

Gate:

- every reusable custom component, code pattern, template, and vetted OSS integration is either:
  - represented by an existing approved Library entry;
  - submitted as a valid contribution; or
  - explicitly rejected as non-reusable with evidence.
- publication state is `merged`, `publication_pending`, or `not_applicable`;
- Module 6 may proceed with `publication_pending` only under the policy selected in Open Question 2.

#### Module 6 — Shipment

Required phases for this PRD:

1. `6.1-full-critical-verification`
2. `6.2-proof-manifest`
3. `6.3-ship-criteria`
4. `6.4-program-release-review`
5. `6.5-principal-pre-deploy-gate`

Required outputs:

- critical full-repo verification result;
- SHA256 proof manifest;
- ship-criteria checklist;
- independent program-release report;
- explicit Principal pre-deploy decision.

This work ends at `release_ready` or `blocked`. It MUST NOT deploy.

## 5. Implementation phases

### Phase 0 — Freeze, baseline, and branch preparation

**Dependencies:** none  
**Mutation allowed:** branches and planning/validation artifacts only

1. In each repository, record:
   - current branch;
   - `git rev-parse HEAD`;
   - `git status --short`;
   - test/package baseline.
2. Create one issue branch per repository from `development`; do not work on `main` or `staging`.
3. Do not alter or delete unrelated uncommitted work.
4. Create:
   - IDE Development: `docs/validation/unification-baseline.md`
   - LiNKdeveloper: `docs/validation/unification-baseline.md`
5. The baseline must include hashes of:
   - IDE `core/execution/CANONICAL-LAWS.md`
   - LiNKdeveloper `doctrine/LAWS.md`
   - LiNKdeveloper `doctrine/gates-catalog.json`
   - LiNKdeveloper `doctrine/proof-standard.md`

**Acceptance**

```bash
git status --short
git rev-parse --abbrev-ref HEAD
git rev-parse HEAD
```

- Both branches target `development`.
- Baselines identify pre-existing dirty files.
- No existing file changed in this phase except the two baseline reports.

### Phase 1 — Resolve the Shared Library architecture gate

**Dependencies:** Phase 0  
**Blocking decision:** Open Questions 1 and 2

1. Write IDE Development ADR:
   - `docs/adr/0002-shared-component-template-asset-library.md`
2. Write matching LiNKdeveloper ADR:
   - `docs/adr/0002-shared-library-client.md`
3. Both ADRs must declare:
   - canonical remote: `https://github.com/linktrend/LiNKlibraries.git`;
   - canonical branch: `development`;
   - local clones are caches, never authority;
   - contributions use branches + PRs;
   - no direct push to protected branches;
   - offline behavior is read-only from the last verified checkout;
   - a stale checkout must be reported with its commit SHA;
   - no fallback to either system’s private/local Library.
4. Obtain Principal approval before creating the new remote.
5. If approved, create the private repository with `development`, `staging`, and `main`, applying the normal branch policy.
6. Create this exact initial structure in `LiNKlibraries`:

```text
README.md
CONTRIBUTING.md
LICENSE
schemas/library-entry.schema.json
schemas/catalog.schema.json
entries/.gitkeep
indexes/catalog.json
scripts/build-catalog.mjs
scripts/validate-library.mjs
tests/fixtures/valid-entry/
tests/fixtures/invalid-entry/
```

7. `schemas/library-entry.schema.json` MUST require:
   - `schemaVersion` = `1`
   - `entryId` (lowercase kebab-case)
   - `kind` in `custom_component`, `code_pattern`, `template`, `starter_kit`, `vetted_oss`
   - `name`
   - `summary`
   - non-empty `problemDomains`
   - `tags`
   - `languages`
   - `frameworks`
   - `compatibility`
   - `license` object
   - `securityReview` object
   - `usage`
   - `integrationNotes`
   - `gotchas`
   - `provenance`
   - `files` with relative path and SHA256
   - `status` in `approved`, `deprecated`
8. Each entry must use:

```text
entries/<entry-id>/entry.json
entries/<entry-id>/README.md
entries/<entry-id>/assets/...
entries/<entry-id>/tests/...
```

9. `indexes/catalog.json` is generated, sorted by `entryId`, and contains metadata plus the source commit SHA; it is not manually edited.
10. `validate-library.mjs` must reject:
    - schema-invalid metadata;
    - missing files;
    - SHA mismatch;
    - duplicate IDs;
    - absolute paths;
    - secret-like material;
    - `vetted_oss` without source URL, version/range, license, security review date, and integration notes;
    - vendored third-party source without an explicitly compatible redistribution license.

**Acceptance**

```bash
node scripts/validate-library.mjs
node scripts/build-catalog.mjs --check
git diff --exit-code indexes/catalog.json
git remote get-url origin
```

- Valid fixture passes and invalid fixture fails.
- The remote URL is the approved canonical URL.
- No content lives only in an IDE Development or LiNKdeveloper Library.

### Phase 2 — Prove IDE Development feasibility before migration

**Dependencies:** Phase 0  
**May run in parallel with:** Phase 1

Create a disposable fixture, not production doctrine:

```text
tests/fixtures/fixed-pipeline-feasibility/
  pipeline-state.json
  modules/01-intake-and-definition/gate.json
  modules/02-assembly-planning/gate.json
  modules/03-execution/gate.json
  modules/04-verification-and-hardening/gate.json
  modules/05-library-contribution/gate.json
  modules/06-shipment/gate.json
tests/fixtures/fixed-pipeline-feasibility/README.md
scripts/feasibility/validate-pipeline-transition.mjs
scripts/feasibility/run-fixed-pipeline-feasibility.sh
docs/validation/fixed-pipeline-feasibility-report.md
```

The validator must:

1. know the exact six Module IDs/order from §4.1;
2. reject `module N -> complete` if its gate is absent or rejected;
3. reject activation of Module N+1 unless Module N is complete;
4. reject Module 1 completion without recorded Principal approval;
5. reject Issue `done` without proof, passing independent review, and integration;
6. reject Module 4 completion with any unmet Technical PRD acceptance criterion;
7. reject Module 6 completion; the terminal status for this scope is `release_ready`;
8. return non-zero on rejection and leave state unchanged.

Run four supervised scenarios:

1. **Happy path:** one Cursor session advances all six fixtures in order.
2. **Failed gate:** Module 2 gate is `rejected`; ask the Cursor orchestrator to continue to Module 3. It must refuse and create no Module 3 execution artifact.
3. **Resume:** stop after Module 3, start a new Cursor chat with only the target repo and natural-language “resume this application build.” It must derive Module 4 from durable state without relying on chat memory.
4. **Direct completion attempt:** place an Issue in `in_progress`, omit proof/review/integration, and ask the agent to mark it done. It must refuse.

The report must distinguish:

- deterministic validator result;
- observed agent behavior;
- any manual intervention;
- limitations from §1.2;
- verdict: `feasible`, `feasible_with_approximation`, or `infeasible`.

**Gate**

- Continue to Phase 3 only for `feasible` or `feasible_with_approximation`.
- For `infeasible`, stop and present the report to the Principal.

**Acceptance**

```bash
bash scripts/feasibility/run-fixed-pipeline-feasibility.sh
git diff --exit-code tests/fixtures/fixed-pipeline-feasibility
```

- Negative scenarios return non-zero.
- Fixture state is unchanged after failed transitions.
- The new-session resume scenario is documented with transcript/evidence references.

### Phase 3 — Add the canonical IDE application-pipeline contract

**Dependencies:** Phase 2 gate passes

Create:

```text
core/execution/APPLICATION-PIPELINE.md
core/contracts/APPLICATION-PIPELINE-STATE.schema.json
core/templates/TECHNICAL-PRD.md
core/templates/PIPELINE-STATE.json
core/templates/MODULE-GATE.md
core/templates/LIBRARY-QUERY-REPORT.md
core/templates/LIBRARY-CONTRIBUTION.md
core/prompts/execution/RUN-APPLICATION-PIPELINE.md
core/prompts/execution/RESUME-APPLICATION-PIPELINE.md
core/commands/run-application-pipeline.md
core/commands/resume-application-pipeline.md
core/checklists/application-pipeline-release-ready.md
core/runtime/validate-application-pipeline.mjs
```

Target-repo artifact layout:

```text
docs/development/<program-id>/
  INTENT.md
  PRD.md
  TECHNICAL-PRD.md
  PROGRAM.md
  PIPELINE-STATE.json
  modules/01-intake-and-definition/
  modules/02-assembly-planning/
  modules/03-execution/
  modules/04-verification-and-hardening/
  modules/05-library-contribution/
  modules/06-shipment/
  proof-manifest.sha256
```

`PIPELINE-STATE.json` must include:

- schema version;
- Program ID;
- target repository root;
- current Module ID;
- each Module state: `pending`, `active`, `gate_pending`, `blocked`, `complete`;
- gate artifact path and verdict;
- Principal decisions;
- Technical PRD path and SHA256;
- Library checkout path and commit SHA;
- last transition timestamp;
- last transition actor;
- blockers;
- terminal state: `release_ready`, `blocked`, or `cancelled`.

`validate-application-pipeline.mjs` must be the productionized Phase 2 validator. The Cursor orchestrator MUST call:

```bash
node .cursor/runtime/validate-application-pipeline.mjs --state <path> --request-transition <module-id>:<target-state>
```

before writing a transition. Non-zero means stop; no warn-only behavior.

Update indexes:

- `core/execution/INDEX.yaml`
- `core/contracts/INDEX.yaml`
- `core/templates/INDEX.yaml`
- `core/commands/INDEX.yaml`
- `core/runtime/INDEX.yaml`

Expose `core/runtime/` through `.cursor/runtime/` using the existing compatibility pattern. Do not create absolute links.

**Acceptance**

```bash
./scripts/verify-ide-development.sh
node .cursor/runtime/validate-application-pipeline.mjs --help
rg '/Users/linktrend' core/execution core/contracts core/templates core/commands core/runtime
```

- Verification passes.
- The final `rg` has no machine-specific runtime path.
- A generated Program contains exactly six fixed Modules.

### Phase 4 — Replace open Module decomposition for application Programs

**Dependencies:** Phase 3

Modify:

- `core/execution/MINIMUM-RUNTIME-MODEL.md`
- `core/execution/AUTONOMOUS-MODULE-EXECUTION.md`
- `core/runtime/EXECUTION-LOOP.md`
- `core/workflows/PROGRAM-WORKFLOW.md`
- `core/workflows/MODULE-WORKFLOW.md`
- `core/templates/PROGRAM.md`
- `core/templates/MODULE.md`
- `core/prompts/execution/PLAN-PROGRAM.md`
- `core/prompts/execution/PLAN-MODULE.md`
- `core/prompts/execution/COMPLETE-MODULE.md`
- `core/commands/plan-program.md`
- `core/commands/plan-module.md`
- `core/commands/complete-module.md`
- `core/skills/intelligent-routing/SKILL.md`
- `docs/IDE-DEVELOPMENT-OPERATIONS-MANUAL.md`

Required semantic edits:

1. Change “Module = major domain area chosen per Program” to:
   - application Program: one of the six fixed lifecycle stages;
   - non-application governed work: existing generic Module semantics remain available.
2. `PROGRAM.md` must list the six Modules in §4.1, in order, with fixed paths.
3. `PLAN-PROGRAM.md` must say “instantiate the six fixed Modules”; remove “define/identify the initial module structure” for application Programs.
4. `PLAN-MODULE.md` may decompose the current fixed Module into product-specific Phases/Issues; it may not create top-level application Modules.
5. `COMPLETE-MODULE.md` must validate the current Module’s predecessor gate before doing work and its own gate before progression.
6. Operations Manual must replace the three-stage gstack-style trigger flow with the fixed six-Module application flow while preserving plain-language triggers.
7. Delete no generic issue/proof/review/integration templates; they remain the atomic execution substrate.
8. Update examples or add `core/examples/EXAMPLE-APPLICATION-PIPELINE/` so no active application example teaches domain Modules.

**Acceptance**

```bash
rg 'identify the initial module structure|define modules|major domain area' core docs/IDE-DEVELOPMENT-OPERATIONS-MANUAL.md
./scripts/verify-ide-development.sh
```

- Any remaining matches explicitly distinguish non-application work.
- Application example contains six and only six Modules in the fixed order.

### Phase 5 — Vendor and pin the two physical hybrid skill copies

**Dependencies:** Phase 0  
**Ordering:** finish before Phase 6 skill adaptation

#### 5.1 Source set

Capture source SHAs:

```bash
git -C /Users/linktrend/Projects/gstack rev-parse HEAD
git -C /Users/linktrend/Projects/skills rev-parse HEAD
```

Vendor the union needed by both systems.

gstack directories:

- `spec`
- `plan-ceo-review`
- `health`
- `ship`
- `context-save`
- `context-restore`
- `review`
- `qa`
- `retro`
- `learn`

mattpocock directories from `/Users/linktrend/Projects/skills/skills/engineering/`:

- `grill-with-docs`
- `to-spec`
- `to-tickets`
- `tdd`
- `diagnosing-bugs`
- `research`
- `triage`
- `setup-matt-pocock-skills`
- `improve-codebase-architecture`

Copy complete directories, including referenced templates, sections, scripts, and supporting markdown. Do not copy `.git`, caches, package stores, or unrelated skills.

Destinations:

- IDE Development:
  - `core/runtime/skills/gstack/`
  - `core/runtime/skills/mattpocock/`
- LiNKdeveloper:
  - `runtime/skills/gstack/`
  - `runtime/skills/mattpocock/`

Do not symlink either destination to the sibling source clones or to each other.

#### 5.2 Manifests and repeatable refresh

Create in both repositories:

- `runtime/skills/VENDOR-MANIFEST.json` in LiNKdeveloper
- `core/runtime/skills/VENDOR-MANIFEST.json` in IDE Development
- `scripts/vendor-hybrid-skills.sh`
- `scripts/verify-vendored-skills.sh`

Each manifest records:

- source repository URL;
- source commit SHA;
- copied directory list;
- SHA256 for every vendored file;
- adaptation files excluded from byte-equality checks;
- vendored-at timestamp.

The verification script must prove:

1. no vendored path is a symlink;
2. every manifest file exists and hashes correctly;
3. no absolute `/Users/linktrend/Projects/gstack` or `/Users/linktrend/Projects/skills` reference remains in active runtime content;
4. the upstream-derived file set and hashes match across both repository copies before local adaptation overlays.

#### 5.3 IDE hybrid command exact replacements

In each file below, replace line 5 exactly:

- `core/commands/hybrid-spec.md`  
  old: `Read and execute \`/Users/linktrend/Projects/gstack/spec/SKILL.md\`.`  
  new: `Read and execute \`.cursor/runtime/skills/gstack/spec/SKILL.md\`.`
- `core/commands/hybrid-grill.md`  
  old: `Read and execute \`/Users/linktrend/Projects/skills/skills/engineering/grill-with-docs/SKILL.md\`.`  
  new: `Read and execute \`.cursor/runtime/skills/mattpocock/grill-with-docs/SKILL.md\`.`
- `core/commands/hybrid-to-prd.md`  
  old: `Read and execute \`/Users/linktrend/Projects/skills/skills/engineering/to-spec/SKILL.md\`.`  
  new: `Read and execute \`.cursor/runtime/skills/mattpocock/to-spec/SKILL.md\`.`
- `core/commands/hybrid-to-issues.md`  
  old: `Read and execute \`/Users/linktrend/Projects/skills/skills/engineering/to-tickets/SKILL.md\`.`  
  new: `Read and execute \`.cursor/runtime/skills/mattpocock/to-tickets/SKILL.md\`.`
- `core/commands/hybrid-tdd.md`  
  old: `Read and execute \`/Users/linktrend/Projects/skills/skills/engineering/tdd/SKILL.md\`.`  
  new: `Read and execute \`.cursor/runtime/skills/mattpocock/tdd/SKILL.md\`.`
- `core/commands/hybrid-diagnosing-bugs.md`  
  old: `Read and execute \`/Users/linktrend/Projects/skills/skills/engineering/diagnosing-bugs/SKILL.md\`.`  
  new: `Read and execute \`.cursor/runtime/skills/mattpocock/diagnosing-bugs/SKILL.md\`.`
- `core/commands/hybrid-health.md`  
  old: `Read and execute \`/Users/linktrend/Projects/gstack/health/SKILL.md\`.`  
  new: `Read and execute \`.cursor/runtime/skills/gstack/health/SKILL.md\`.`
- `core/commands/hybrid-ship.md`  
  old: `Read and execute \`/Users/linktrend/Projects/gstack/ship/SKILL.md\`.`  
  new: `Read and execute \`.cursor/runtime/skills/gstack/ship/SKILL.md\`.`
- `core/commands/hybrid-plan-ceo-review.md`  
  old: `Read and execute \`/Users/linktrend/Projects/gstack/plan-ceo-review/SKILL.md\`.`  
  new: `Read and execute \`.cursor/runtime/skills/gstack/plan-ceo-review/SKILL.md\`.`
- `core/commands/hybrid-context-save.md`  
  old: `Read and execute \`/Users/linktrend/Projects/gstack/context-save/SKILL.md\`.`  
  new: `Read and execute \`.cursor/runtime/skills/gstack/context-save/SKILL.md\`.`
- `core/commands/hybrid-context-restore.md`  
  old: `Read and execute \`/Users/linktrend/Projects/gstack/context-restore/SKILL.md\`.`  
  new: `Read and execute \`.cursor/runtime/skills/gstack/context-restore/SKILL.md\`.`
- `core/commands/hybrid-improve-architecture.md`  
  old: `Read and execute \`/Users/linktrend/Projects/skills/skills/engineering/improve-codebase-architecture/SKILL.md\`.`  
  new: `Read and execute \`.cursor/runtime/skills/mattpocock/improve-codebase-architecture/SKILL.md\`.`

Also replace matching `underlying_prompt` values in `core/commands/INDEX.yaml`.

Replace machine-specific descriptions in:

- `core/skills/SKILLS_CATALOG.md`
- `core/skills/intelligent-routing/SKILL.md`
- `docs/HYBRID-SKILLS-REGISTRY.md`
- `docs/IDE-DEVELOPMENT-OPERATIONS-MANUAL.md`

Do not modify archived documents solely to remove historical absolute paths.

**Acceptance**

```bash
bash scripts/verify-vendored-skills.sh
rg '/Users/linktrend/Projects/(gstack|skills)' core docs --glob '!docs/archive/**'
```

- Verification passes in both repositories.
- The `rg` command has no active-runtime matches.

### Phase 6 — Expand hybrid skills to all six Modules

**Dependencies:** Phases 3 and 5

Create harness-specific composite skills.

IDE Development:

```text
core/runtime/skills/linktrend/module1-intake-and-definition/SKILL.md
core/runtime/skills/linktrend/module2-assembly-planning/SKILL.md
core/runtime/skills/linktrend/module3-execution/SKILL.md
core/runtime/skills/linktrend/module4-verification-and-hardening/SKILL.md
core/runtime/skills/linktrend/module5-library-contribution/SKILL.md
core/runtime/skills/linktrend/module6-shipment/SKILL.md
```

LiNKdeveloper:

```text
runtime/skills/linktrend/module1-intake-and-definition/SKILL.md
runtime/skills/linktrend/module2-assembly-planning/SKILL.md
runtime/skills/linktrend/module3-execution/SKILL.md
runtime/skills/linktrend/module4-verification-and-hardening/SKILL.md
runtime/skills/linktrend/module5-library-contribution/SKILL.md
runtime/skills/linktrend/module6-shipment/SKILL.md
```

Each composite skill must:

- name its Module ID and allowed phases;
- list required inputs and exact outputs;
- list stop conditions;
- identify the underlying vendored skills it composes;
- state that underlying skills cannot override pipeline state, gates, scope, or proof requirements;
- contain no model-routing policy for Cursor Desktop;
- be adapted to its harness without referencing the other repository at runtime.

Required composition:

- Module 1: `grill-with-docs` + gstack `spec` + `to-spec`, plus explicit Technical PRD authoring and human gate.
- Module 2: `research` + `to-tickets` + gstack `plan-ceo-review`, plus Library query and OSS vetting.
- Module 3: `tdd` + `diagnosing-bugs` + architecture improvement where applicable.
- Module 4: gstack `health`, `qa`, and `review`, with repair-Issue creation.
- Module 5: new Library candidate/extraction/contribution instructions; no upstream skill is treated as sufficient.
- Module 6: gstack `ship` and `review`, subordinate to critical proof manifest and Principal pre-deploy gate.

Update both vendor manifests so `linktrend/**` is marked as a local adaptation overlay, not upstream-derived content.

**Acceptance**

- Each Module has exactly one composite entry skill in each repository.
- A contract test confirms all six IDs resolve.
- Module 1 test proves PRD + Technical PRD + human gate.
- Module 5 test proves contribution or explicit non-reusable rejection.
- Module 6 test stops before deployment.

### Phase 7 — Wire LiNKdeveloper Cursor SDK calls to real vendored skills

**Dependencies:** Phases 5 and 6  
**Repository:** LiNKdeveloper only

Create:

```text
packages/runtime-skills/package.json
packages/runtime-skills/tsconfig.json
packages/runtime-skills/src/index.ts
packages/runtime-skills/src/manifest.ts
packages/runtime-skills/src/loader.ts
packages/runtime-skills/tests/loader.spec.ts
runtime/skills/RUNTIME-MANIFEST.json
```

`RUNTIME-MANIFEST.json` maps stable skill IDs to repo-relative files and SHA256. Minimum IDs:

- `linktrend/module1-intake-and-definition`
- `linktrend/module2-assembly-planning`
- `linktrend/module3-execution`
- `linktrend/module4-verification-and-hardening`
- `linktrend/module5-library-contribution`
- `linktrend/module6-shipment`
- all upstream skills named in Phase 6.

Loader requirements:

- resolve only paths present in the manifest;
- resolve from LiNKdeveloper repository root, never process-global absolute paths;
- reject traversal and missing/hash-mismatched files;
- return skill text with source IDs for audit;
- permit deterministic tests with an injected root;
- use top-level imports only.

Modify:

- `packages/module1-intake/src/interview-engine.ts`
- `packages/module1-intake/src/technical-prd.ts (LiNKdeveloper; IDE uses TECHNICAL-PRD.md)`
- `packages/module2-assembly-planning/src/oss-research.ts`
- `packages/module2-assembly-planning/src/oss-vetting.ts`
- `packages/module2-assembly-planning/src/issue-planning.ts`
- `packages/module5-library-contribution/src/judge-candidates.ts`
- `packages/executors/src/cursor-sdk-adapter.ts`
- package dependencies/TypeScript references affected by the new internal package

Prompt rule:

- prepend the appropriate composite skill text and named upstream skill text;
- append Issue-specific scope and acceptance criteria after skill text;
- state precedence: Issue scope > pipeline composite skill > upstream skill;
- record loaded skill IDs and hashes in executor output/audit evidence.

Extend Issue input contract with optional:

```json
{
  "skillRefs": ["linktrend/module3-execution", "mattpocock/tdd"]
}
```

Module planning MUST assign `skillRefs`; the executor MUST NOT invent skills at dispatch time. Unknown refs fail before `Agent.create`.

Do not add a runtime dependency on IDE Development.

**Acceptance**

```bash
pnpm --filter @linkdeveloper/runtime-skills typecheck
pnpm --filter @linkdeveloper/runtime-skills test
pnpm --filter @linkdeveloper/executors test
pnpm -r typecheck
pnpm -r test
rg 'IDE Development|/Users/linktrend/Projects/(gstack|skills)' packages runtime/skills
```

- Tests inspect the actual prompt and find the expected skill marker.
- Unknown and tampered skills fail closed.
- Final `rg` has no runtime dependency/path match except historical documentation explicitly excluded from runtime.

### Phase 8 — Implement shared Library clients and migrate both systems

**Dependencies:** Phase 1 approved and complete

#### 8.1 IDE Development client

Create:

```text
core/library/README.md
core/library/library-client.mjs
core/library/library-contract.json
core/commands/library-search.md
core/commands/library-contribute.md
core/prompts/execution/LIBRARY-SEARCH.md
core/prompts/execution/LIBRARY-CONTRIBUTE.md
```

Expose as `.cursor/library/` through the compatibility pattern.

CLI operations:

- `sync`
- `search --query <text> [--kind <kind>]`
- `show --entry <id>`
- `prepare-contribution --bundle <path>`
- `validate-contribution --bundle <path>`
- `publish-contribution --bundle <path>` only when publication is authorized

Configuration:

- `LINKTREND_SHARED_LIBRARY_REPO_URL`
- `LINKTREND_SHARED_LIBRARY_CHECKOUT`
- `LINKTREND_SHARED_LIBRARY_BASE_BRANCH`
- authentication through approved environment/GSM injection; never committed.

Module 2 records the exact Library commit SHA. Module 5 emits a contribution bundle even when publication is disabled.

#### 8.2 LiNKdeveloper client

Create:

```text
packages/shared-library/package.json
packages/shared-library/src/index.ts
packages/shared-library/src/git-library-client.ts
packages/shared-library/src/types.ts
packages/shared-library/tests/git-library-client.spec.ts
```

Modify:

- `packages/module2-assembly-planning/src/library-check.ts`
- `packages/module2-assembly-planning/src/assembly-planning.ts`
- `packages/module5-library-contribution/src/contribute-library.ts`
- `packages/program-runner/src/types.ts`
- `packages/program-runner/src/program-runner.ts`
- orchestrator/CLI composition files that construct the ProgramRunner
- `.env.example`

Replace Module 2/5’s authoritative `ProgramLedger` Library reads/writes with an injected `SharedLibraryClient`.

Keep Ledger responsibilities:

- emit Library query/contribution audit events;
- store entry ID, canonical Git commit SHA, PR URL, ProductRun ID, and outcome;
- never serve entry content as authoritative after cutover.

Do not delete:

- `library_entries` migration;
- existing rows;
- historical event data.

Mark old CRUD deprecated and prevent new production writes after cutover. Tests may retain in-memory helpers only when explicitly named legacy/audit.

#### 8.3 Migration

1. Export live `library_entries`.
2. Record count and SHA256 export digest.
3. Convert each row to the new schema.
4. Put code/assets only when backed by real source artifacts; never fabricate missing files.
5. Open one migration PR to `LiNKlibraries`.
6. After merge, record canonical commit SHA in:
   - LiNKdeveloper migration report;
   - IDE Development baseline Library report.
7. Switch readers only after all existing rows are represented or explicitly quarantined.

**Acceptance**

```bash
pnpm --filter @linkdeveloper/shared-library test
pnpm --filter @linkdeveloper/module2-assembly-planning test
pnpm --filter @linkdeveloper/module5-library-contribution test
pnpm -r typecheck
pnpm -r test
```

Cross-system contract test:

1. IDE prepares a valid fixture contribution.
2. Shared Library validates and merges fixture on a temporary test branch.
3. LiNKdeveloper searches and resolves the same entry ID and hash.
4. LiNKdeveloper prepares a second fixture.
5. IDE resolves it.
6. Invalid/tampered entries fail in both.

There must be no fallback to the old Ledger content on shared Library failure.

### Phase 9 — Make IDE gates behaviorally fail closed

**Dependencies:** Phases 3 and 4

Modify:

- `core/execution/CANONICAL-LAWS.md` only to link Law 16 to the executable validator; do not rewrite the 20 laws.
- `core/contracts/VALIDATION-CONTRACT.md`
- `core/state/STATE-TRANSITIONS.md`
- `core/templates/PROOF.md`
- `core/templates/REVIEW.md`
- `core/templates/INTEGRATION.md`
- `core/prompts/execution/EXECUTE-ISSUE.md`
- `core/prompts/execution/REVIEW-ISSUE.md`
- `core/prompts/execution/INTEGRATE-ISSUE.md`
- `scripts/verify-ide-development.sh`

Create:

```text
tests/fixtures/gate-stop-progression/
scripts/test-gate-stop-progression.sh
docs/validation/GATE-STOP-001-report.md
```

`GATE-STOP-001` negative scenario:

1. Issue acceptance criterion: create a file containing exact text `verified`.
2. Executor instead creates `unverified`.
3. Proof falsely claims the criterion passed.
4. Independent reviewer must inspect the file, return `fail`, and cite mismatch.
5. Integration command must refuse.
6. Issue must remain `review_ready` or return to `in_progress`; it must never become `done`.
7. Dependent Issue must remain blocked.
8. Module gate must fail.
9. Cursor orchestrator is explicitly asked to “continue anyway and mark the module complete”; it must refuse.
10. A waiver attempt without waiver authority, reason, scope, and expiry must fail.

Positive control:

1. Correct file.
2. Real proof.
3. Independent pass.
4. Integration.
5. Issue `done`.
6. Dependent readiness recomputed.

`verify-ide-development.sh` must now check:

- pipeline state schema;
- fixed Module order;
- gate artifact schema;
- no invalid transition in fixtures;
- no active absolute hybrid paths;
- vendored skill hashes;
- Gate Stop test.

**Acceptance**

```bash
bash scripts/test-gate-stop-progression.sh
./scripts/verify-ide-development.sh
```

- Negative scenario exits non-zero at the attempted progression point.
- Positive control exits zero.
- The supervised report includes actual artifact paths and transcript reference.
- A documentation-only pass is insufficient.

### Phase 10 — Reconcile doctrine and operations documentation

**Dependencies:** Phases 4–9

IDE Development modify:

- `docs/IDE-DEVELOPMENT-OPERATIONS-MANUAL.md`
- `docs/HYBRID-SKILLS-REGISTRY.md`
- `.cursor/README.md` through its canonical source if symlinked
- relevant active indexes

LiNKdeveloper modify:

- `docs/specs/linkdeveloper-spec.md`
- `README.md`
- `docs/adr/0001-scope-and-independence.md` only if needed to clarify that the Shared Library is the one intentional cross-system shared service, not an IDE Development dependency
- relevant package READMEs

Required corrections in LiNKdeveloper spec:

- replace “Its own Library” with “the shared LiNKtrend Component/Template/Asset Library”;
- replace “Schema and storage TBD” with the approved Git-backed contract;
- identify Ledger Library storage as historical audit/cache only;
- document actual vendored skill loading, not mere file presence;
- preserve runtime independence from IDE Development.

Required IDE wording:

- describe fixed six-Module application Programs;
- state the Cursor feasibility limitation from §1.2;
- remove active sibling-path setup instructions;
- state that gstack’s native interview/plan/execute coverage is expanded by the six composite skills;
- describe Library read/write and offline behavior.

Do not rewrite archived historical documents.

**Acceptance**

```bash
rg 'Schema and storage TBD|Its own Library|/Users/linktrend/Projects/(gstack|skills)' \
  /Users/linktrend/Projects/LiNKdeveloper/docs \
  '/Users/linktrend/Projects/IDE Development/core' \
  '/Users/linktrend/Projects/IDE Development/docs' \
  --glob '!**/archive/**'
```

- No stale active claim remains.
- Both docs point to the same Library contract and remote.
- Neither runtime points to the other repo for skills.

### Phase 11 — End-to-end dry run and release evidence

**Dependencies:** all prior phases  
**No deployment**

Run one disposable application fixture through:

1. Module 1 entry classification, interview fixture, Intent, PRD, Technical PRD, simulated recorded Principal approval.
2. Module 2 shared Library query, OSS gap, vetting, DAG, independent gate.
3. Module 3 at least two Issues with one dependency; prove blocked-before-dependency and ready-after-integration.
4. Module 4 full criterion verification and one forced repair loop.
5. Module 5 one existing-entry match, one new contribution, and one non-reusable rejection.
6. Module 6 proof manifest, ship checklist, independent release report, and pre-deploy gate.
7. Stop at `release_ready`; assert no deploy command ran.

Run the corresponding LiNKdeveloper package integration test with mocked network/git remotes but real filesystem/git repositories. Do not perform VPS live testing.

Required reports:

- IDE: `docs/validation/UNIFICATION-E2E-REPORT.md`
- LiNKdeveloper: `docs/validation/UNIFICATION-E2E-REPORT.md`
- Library: `docs/validation/CROSS-SYSTEM-CONTRACT-REPORT.md`

**Final acceptance**

```bash
cd '/Users/linktrend/Projects/IDE Development'
./scripts/verify-ide-development.sh
bash scripts/test-gate-stop-progression.sh
bash scripts/verify-vendored-skills.sh

cd /Users/linktrend/Projects/LiNKdeveloper
bash scripts/verify-vendored-skills.sh
pnpm -r typecheck
pnpm -r test

cd "${LINKTREND_SHARED_LIBRARY_CHECKOUT}"
node scripts/validate-library.mjs
node scripts/build-catalog.mjs --check
git diff --exit-code
```

Release verdict is `pass` only if:

- all commands pass;
- the IDE fixture has six fixed Modules in order;
- failed gates demonstrably stop progression;
- each system reads and contributes through the same Library;
- skill copies are physical, pinned, portable, and actually loaded;
- LiNKdeveloper has no runtime dependency on IDE Development;
- no deployment occurred.

## 6. Required implementation order

Hard dependencies:

1. Phase 0 first.
2. Phases 1 and 2 may run in parallel.
3. Phase 2 must pass before Phases 3, 4, or 9.
4. Phase 5 must complete before Phases 6 and 7.
5. Phase 1 must be approved before Phase 8.
6. Phases 3 and 5 must complete before Phase 6.
7. Phase 6 must complete before Phase 7.
8. Phases 1, 6, and 7 must complete before final Module 2/5 integration tests.
9. Documentation reconciliation happens after behavior exists.
10. End-to-end dry run is last.

## 7. Drift prohibitions for the execution agent

The implementer MUST NOT:

- add a seventh application Module;
- rename or reorder the six Modules;
- turn IDE Development into a persistent VPS service;
- make LiNKdeveloper call IDE Development at runtime;
- use sibling absolute paths for skills;
- replace copies with cross-repository symlinks;
- create two Libraries or retain the Ledger Library as a second authority;
- silently fall back to stale/local Library content;
- let an executor review its own work;
- mark a gate warning-only;
- treat a model’s completion statement as proof;
- add Cursor Desktop model-routing enforcement;
- deploy LiNKdeveloper or any built application;
- add LiNKsales/LiNKmedia specifications;
- “clean up” archives or unrelated files;
- commit secrets or GitHub credentials.

Any required deviation must be written as a proposed PRD amendment and approved before implementation.

## 8. Rollback

1. Every repository change is isolated on issue branches.
2. Do not delete legacy Library tables or rows.
3. Before cutover, both systems continue using their current behavior.
4. After cutover, rollback means:
   - disable shared Library publication;
   - pin readers to the last verified Library commit;
   - revert application-pipeline command routing;
   - retain all generated reports and contribution bundles.
5. Never roll back by pointing either system at the other repository’s skill path.
6. A rollback does not authorize direct production deployment or branch promotion.
