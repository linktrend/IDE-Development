# LiNKdeveloper Stage 1a — Specification

**Mission:** Define Workflow
**Author:** Sonnet 5 agent, medium reasoning, first pass
**Reviewer:** Lisa (strategy agent), with Carlos
**Status:** Draft for review — not yet approved
**Date:** 2026-07-10

This document is the primary Stage 1a deliverable. It verifies the common workflow blueprint in this repository, documents how the Application Factory variant maps into that blueprint, defines the three-layer skills architecture, excludes LiNKdev from the active stack, and sets acceptance criteria for Stage 1a → Stage 1b promotion.

---

## A. Blueprint Verification

### A.1 Verdict: the common blueprint is complete and internally consistent

The lifecycle `Intent → Program → Module → Phase → Issue → Proof → Review → Integration → Complete` is fully specified, with session start/end as wrappers rather than a separate model, exactly as the mission describes. No missing stage, no missing handoff contract, and no contradiction was found between the workflow files, the contract files, the state files, and the canonical laws. This matches the repo's own conclusion in `core/reports/V1-READINESS-ASSESSMENT.md`: *"The `.cursor` system is close to v1.0 and is functionally usable now for supervised real work."* (`core/reports/V1-READINESS-ASSESSMENT.md`, Overall Verdict).

This is a **confirmation**, not a gap list — but see A.4 for should-fix items and A.5 for a naming-drift note that affects Stage 1b setup.

### A.2 Files verified (with evidence)

| File | Verified content |
|---|---|
| `core/workflows/WORKFLOW-MODEL.md` | Canonical lifecycle: *"`Intent -> Program -> Module -> Phase -> Issue -> Proof -> Review -> Integration -> Complete`"* with session start/end as wrappers: *"Session start and session end sit around this lifecycle as repository-level continuity behavior."* |
| `core/workflows/PROGRAM-WORKFLOW.md` | Input: `INTENT.md` → Output: `PROGRAM.md` + module list. Exit: *"at least one module can enter the module workflow."* |
| `core/workflows/MODULE-WORKFLOW.md` | Input: parent `PROGRAM.md` → Output: `MODULE.md`, `PHASE.md`, `ISSUE.md` with dependencies. Exit requires "required module review is complete." |
| `core/workflows/ISSUE-WORKFLOW.md` | Governs `ISSUE.md` → `PROOF.md`, up to `review_ready`. Entry requires issue state `ready` and dependencies satisfied. |
| `core/workflows/REVIEW-WORKFLOW.md` | Governs `PROOF.md` → `REVIEW.md`. Verdict is one of `pass`/`fail`/`blocked`. Entry requires *"the reviewing party is independent enough to evaluate the work credibly."* |
| `core/workflows/INTEGRATION-WORKFLOW.md` | Governs `REVIEW.md` → `INTEGRATION.md`. Entry requires review verdict `pass`. Responsibility: *"integrate only work with passing review."* |
| `core/workflows/planning-lifecycle.md` | Present at lowercase path (mission listed `PLANNING-LIFECYCLE.md`; actual file is `core/workflows/planning-lifecycle.md` — see A.4 for the casing note). Defines 6-stage planning entry: clarify → define finished state → capture constraints → create program/issue structure → verify consistency → hand off to execution. |
| `core/workflows/dispatch-v2.md` | Defines roles (planner/executor/reviewer/integrator/operator) and a minimal trigger table. Principle: *"Review and integration must be separate concerns."* |
| `core/contracts/` (all 6 files + README) | `CONTRACT-MODEL.md` defines producer/consumer per artifact and 7 cross-cutting invariants including *"Proof precedes review,"* *"Review precedes integration."* `INPUT-CONTRACT.md`/`OUTPUT-CONTRACT.md`/`STATE-CONTRACT.md`/`SIDE-EFFECT-CONTRACT.md`/`VALIDATION-CONTRACT.md` each specialize one contract question from the universal contract principle. |
| `core/state/` (all 7 files + README) | `STATE-MODEL.md` defines full state vocabularies per artifact type (Intent, Program, Module, Phase, Issue, Proof, Review, Integration) and 5 state invariants, including *"`done` for issue always implies proof, review, and integration are complete."* |
| `core/runtime/EXECUTION-LOOP.md` | 14-step standard loop from index load through downstream readiness recomputation. Defines "genuine block condition" distinct from mere difficulty. |
| `core/runtime/DEPENDENCY-RESOLUTION.md` | Issue is *"the authoritative dependency unit."* Readiness is *"a computed runtime conclusion, not a manual label of convenience."* |
| `core/skills/SKILLS_CATALOG.md` and `core/skills/` (all ~48 skill dirs + README + catalog) | Routing catalog is a rules + bullet-list structure (not a table — see A.4), covering ~48 skills with explicit overlap-routing rules per domain. |
| `core/reports/V1-READINESS-ASSESSMENT.md` | Full readiness audit — see A.3. |
| `core/system/SYSTEM-ARCHITECTURE.md` | 9-layer stack: Doctrine → Artifacts → Agents → Commands → Runtime → Workflows → Contracts → State → System. Enforcement model is explicitly compliance-based, not controller-based: *"An executable controller is not required for the core system to work as designed."* |
| `core/system/V1-BUILD-ORDER.md` | Confirms the same 9-layer assembly order and states remaining work is "final cross-layer audit... release checklist confirmation," not new architecture. |
| `core/workspace/WORKSPACE-ADOPTION.md` | Confirms symlink-based, one-time adoption model; explicitly lists "legacy LiNKdev remnants" as a discovery/cleanup target during adoption (not an active dependency). |
| `core/workspace/REPO-WIRING.md` | Confirms `repo/.cursor -> ../IDE Development/.cursor -> ../IDE Development/core` resolution chain and the no-duplicate-copy rule. |
| `SETUP.md` | Confirms symlink adoption model, machine setup for MacBook/Mac Mini, and the safety rule to run `git status` before letting an agent modify the system. |
| `README.md` | Confirms `core/` is canonical, `.cursor/` is the compatibility runtime surface, and GitHub is the source of truth. |
| `core/checklists/planning-readiness.md`, `core/checklists/wire-checklist.md` | Operational checklists that gate program/module planning and repo wiring respectively; `wire-checklist.md` explicitly requires "no required runtime dependency on `LiNKdev`." |
| Canonical Laws doctrine — `core/execution/CANONICAL-LAWS.md` | Exactly **20 laws**, verbatim, verified directly (see A.3 for full text). |

### A.3 Canonical Laws — full verification (exactly 20, as required)

Read directly from `core/execution/CANONICAL-LAWS.md` and cross-checked by an independent audit pass. All 20 laws are present, numbered 1–20, and internally consistent with every workflow, contract, and state file read above.

1. The issue is the atomic executable unit.
2. Programs, modules, and phases are control containers, not execution units.
3. Dependencies determine execution order.
4. Readiness is computed, not declared.
5. Concurrency emerges from dependency satisfaction.
6. Planning must produce an executable graph.
7. Every issue must have explicit scope.
8. Every issue must have testable completion criteria.
9. Completion requires evidence, not confidence.
10. Proof must be non-vacuous.
11. Blocked work must leave a trail.
12. Review is separate from execution.
13. Integration is separate from review.
14. Release is separate from integration.
15. Higher-level completion is stricter than lower-level completion.
16. Quality gates must stop progression, not merely warn.
17. Definitions of done exist at every level.
18. Agents are resources, not the control structure.
19. Progressive disclosure is mandatory.
20. The system must remain tool-independent.

### A.4 Canonical principles — cited evidence per mission requirement

| Principle | Evidence |
|---|---|
| Issue is the atomic executable unit | `core/execution/CANONICAL-LAWS.md` Law 1; `core/workflows/WORKFLOW-MODEL.md` Stage Relationships: "Issue... is the atomic executable unit"; `core/runtime/DEPENDENCY-RESOLUTION.md`: "The authoritative dependency unit is the issue." |
| Agents are resources, not the control structure | `core/execution/CANONICAL-LAWS.md` Law 18; `core/contracts/CONTRACT-MODEL.md` Invariant 6; `core/system/SYSTEM-ARCHITECTURE.md` Control Structure section: control comes from doctrine/artifacts/dependencies/gates/workflows/contracts/state, explicitly "Not from... agents alone." |
| Handoff contracts required between issues/phases/modules | `core/contracts/CONTRACT-MODEL.md` Purpose: "The contract layer defines the rules that govern handoffs between work units, workflow stages, and runtimes"; each of the 8 work-unit types (Intent through Integration) has a defined producer/consumer pair. |
| QA gates block progression (not merely advisory) | `core/execution/CANONICAL-LAWS.md` Law 16: "Quality gates must stop progression, not merely warn." |
| Proof required for completion | `core/execution/CANONICAL-LAWS.md` Laws 9–10; `core/runtime/EXECUTION-LOOP.md` Completion Conditions: "An issue is complete only after: proof, passing review, successful integration." |
| Review separate from execution | `core/execution/CANONICAL-LAWS.md` Law 12; `core/workflows/REVIEW-WORKFLOW.md` Entry Conditions require an independent reviewing party. |
| Integration separate from review | `core/execution/CANONICAL-LAWS.md` Law 13; `core/workflows/INTEGRATION-WORKFLOW.md` governs `INTEGRATION.md` separately from `REVIEW.md` and states integration "does not perform... review." |
| Progressive disclosure | `core/execution/CANONICAL-LAWS.md` Law 19; `.cursor/rules/00-linkdev-bootstrap.mdc`: "Use progressive disclosure. Open only the files required for the current task." |

All eight principles are present, consistent, and independently cross-referenced across at least two files each. No principle is asserted in only one place.

### A.5 Contradictions and naming drift — flagged, not resolved

Per the working rule to flag rather than silently resolve, the following inconsistencies were found. None are law-level contradictions (no file asserts the opposite of a canonical law), but they are real drift that should be resolved before or during Stage 1b:

1. **"`.cursor` operating system" vs. "`core/` canonical asset" naming drift.** `core/system/SYSTEM-ARCHITECTURE.md`, `core/system/V1-BUILD-ORDER.md`, and `core/reports/V1-READINESS-ASSESSMENT.md` all refer to the audited system as *"the `.cursor` operating system"* and structure their layer inventory around `.cursor` subfolders (`bootstrap/`, `agents/`, `commands/`, etc.), while `README.md` states the canonical asset is `core/` and `.cursor/` is merely *"the compatibility runtime surface."* These are not contradictory in effect — `.cursor/` and `core/` are kept in sync/symlinked per `core/workspace/REPO-WIRING.md` — but the reports were evidently written against `.cursor/` as the primary reading surface, not `core/`. Carlos/Lisa should confirm `core/` and `.cursor/` are still content-equivalent before Stage 1b, since this audit read only `core/`.
2. **File casing mismatch.** The mission lists `core/workflows/PLANNING-LIFECYCLE.md`; the actual file is `core/workflows/planning-lifecycle.md` (lowercase). Content matches expectation; only the casing differs. Low severity — cosmetic.
3. **`SKILLS_CATALOG.md` structure.** An early audit pass (later corrected by direct read) assumed a `| Skill | Purpose | Status | Source |` table format. The actual file uses a rules-and-bullet-list structure, not a table. Flagged here only to prevent this same misreading from propagating into Stage 1b tooling that might try to parse the catalog programmatically.
4. **Tension (not contradiction) on readiness.** `core/reports/V1-READINESS-ASSESSMENT.md` itself flags: *"the system is declared ready for supervised real use... but multiple reports also state that unsupervised rollout and real-repository validation are still pending."* The report resolves this itself as a normal release boundary (supervised v1.0-candidate: yes; unsupervised autonomous production: not yet) — consistent with this repo being Stage 1 (semi-manual), not Stage 2 (autonomous).
5. **`gstack` naming collision (see Section D.4).** The skills already in `core/skills/` cite provenance from `LiNKtrend-System/LiNKdev/skills/gstack` (an internal folder inside the abandoned LiNKdev repo). The Stage 1a skills manual (`layered_hybrid_runtime_manual.md`) defines Layer 2 as `garrytan/gstack`, an unrelated external open-source skill repo. Both are called "gstack." This is a real naming collision requiring a Carlos/Lisa decision — see open question in the report.

### A.6 Gaps

No blocker-severity gaps were found in the doctrine, workflow, contract, or state layers themselves. Gaps found are all pre-existing and already self-documented by the repository's own `V1-READINESS-ASSESSMENT.md`:

| Gap | Severity | Source |
|---|---|---|
| Example layer does not instantiate module-level review/integration artifacts, multi-issue dependency graphs, or safe concurrency | **should-fix** | `core/reports/V1-READINESS-ASSESSMENT.md` §B, Important Gaps 1–2 |
| No real low-risk repository has yet exercised the bootstrap + command surface end-to-end | **should-fix** (directly relevant to Stage 1b entry) | `core/reports/V1-READINESS-ASSESSMENT.md` §B, Important Gap 3 |
| Contracts layer is "structurally complete but not yet strongly validated by real repository execution" | **should-fix** | `core/reports/V1-READINESS-ASSESSMENT.md` §A layer inventory, `contracts/` = PARTIAL |
| Top-level discoverability across rules/skills/prompts/checklists is denser than ideal for first-time operators | **nice-to-have** | `core/reports/V1-READINESS-ASSESSMENT.md` §B, Important Gap 4 |
| Legacy compatibility noise (legacy flat agents, legacy `linkdev-*` commands, compatibility templates) not yet retired | **nice-to-have** | `core/reports/V1-READINESS-ASSESSMENT.md` §B Optional Improvements |
| `gstack` naming collision between LiNKdev-legacy content and `garrytan/gstack` Layer 2 source (new finding, this audit) | **should-fix before Stage 1b skills work** | Section D.4 below |
| No wiring yet exists anywhere in this repo to `garrytan/gstack` or `mattpocock/skills` (Layer 2 / Layer 3) | **expected — Stage 1b work, not a Stage 1a defect** | Section C.4 below |

No missing handoff contract was found at any stage boundary: every stage in the lifecycle (Intent, Program, Module, Phase, Issue, Proof, Review, Integration) has an explicit producer/consumer pair in `core/contracts/CONTRACT-MODEL.md`.

### A.7 Readiness assessment for Stage 1b

**Verdict: ready, with the same "supervised, not yet field-validated" caveat the repository already places on itself.**

The blueprint is complete enough to support Stage 1b semi-manual operation today. The repository's own recommended checklist (`core/reports/V1-READINESS-ASSESSMENT.md` §D) — confirm root entrypoints, confirm layer discoverability, confirm the canonical command surface (`plan-program`, `plan-module`, `complete-module`, `execute-issue`, `review-issue`, `integrate-issue`), confirm issue remains atomic, confirm `review_ready` is mandatory, confirm proof/review/integration stay separate gates, confirm compatibility assets are marked, confirm examples still teach correctly, and **run one supervised low-risk real repository test** — is a reasonable Stage 1b entry gate and this Stage 1a audit did not find anything that would block executing that checklist.

---

## B. Application Factory Variant

The Application Factory is **not** a separate workflow. It is the common blueprint (`Intent → Program → Module → Phase → Issue → Proof → Review → Integration → Complete`) populated with app-factory-specific module content, sourced from LiNKdeveloper Stage 2's design docs (read-only reference) and the LiNKapps starter kit.

### B.1 Module map

| Module | In common blueprint? | App-specific? | Phases (typical) | Hardest handoff boundary? |
|---|---|---|---|---|
| Opportunity intake & triage | Common container (`Module` under a `Program`) | Yes — content is app-factory-specific (source: `LiNKdeveloper/docs/LINKDEVELOPER_AS_SUITE_MAP.md` §3, "decide whether a raw idea deserves deeper validation") | Intake → Triage decision | No — clean go/no-go gate, low ambiguity |
| Market, feasibility, and validation | Common container | Yes (`LINKDEVELOPER_AS_SUITE_MAP.md` §4, "determine whether the opportunity should be built") | Feasibility research → Validation verdict | No |
| Product blueprint & approval | Common container; maps to `Intent`/`Program` acceptance gate | Yes — human governance gate (`SOFTWARE_DEVELOPMENT_LIFECYCLE_MODEL.md`: "A product is done only when: product blueprint is approved"; `LINKDEVELOPER_AS_SUITE_MAP.md` §5: "Principal/admin approves product blueprint") | Draft blueprint → Human approval | **Yes — Boundary #1** (see B.2) |
| Architecture, tech stack, & reuse strategy | Common container | Yes — human governance gate (`LINKDEVELOPER_AS_SUITE_MAP.md` §6: "architecture and reuse strategy approved") | Draft architecture → Starter kit selection → Human approval | **Yes — Boundary #2** (see B.2) |
| Implementation planning & work graph | Maps directly to Module→Phase→Issue decomposition, already native to common blueprint | Partially — issue schema is app-factory-specific (`ISSUE_AND_WORK_PACKET_SCHEMA.md`) | Work graph generation → Issue decomposition | No — this is the blueprint's strongest native fit |
| Development execution | Maps directly to `Issue Workflow` | Partially — executor routing is app-factory-specific (`EXECUTOR_ROUTING_POLICY.md`) | Per-issue execution, Cursor/Codex-assisted, human-approved handoffs in Stage 1 | No |
| Continuous validation & self-healing (repair loop) | Extends `Review Workflow`'s fail path | Yes — automatic repair-issue creation on failed validation (`LINKDEVELOPER_AS_SUITE_MAP.md` §9: "create repair Issue for failed test") | Validate → (if fail) generate repair issue → re-execute | **Yes — Boundary #3** (see B.2) |
| Release readiness & deployment | Maps to `Integration Workflow` + Program-level release gate (Canonical Law 14: "Release is separate from integration") | Yes — concrete scripts (`LiNKapps/scripts/release-readiness.sh`) and deploy gates | Release checklist → Staging → Launch approval | No |
| Launch, monitoring, & operations transition | Extends `Complete` stage / program-level release review | Yes — human launch gate + Product Steward handoff (`LINKDEVELOPER_AS_SUITE_MAP.md` §10–11) | Launch approval → Monitoring → Operations handoff | No |

### B.2 Three hardest handoff boundaries and required contracts

1. **Boundary 1 — Product blueprint approval → Architecture module.** This is hard because it is the first point where a human governance decision (not proof-based review) gates progression into technical work, and the common blueprint's `Review Workflow` assumes an independent reviewer evaluating *proof*, not a Principal evaluating a *business* artifact. **Required contract:** an explicit `INPUT-CONTRACT`/`OUTPUT-CONTRACT` pair specific to this boundary stating that "architecture module" issues cannot enter `ready` state until a recorded, dated, human-approval artifact exists for the product blueprint — modeled on the existing `Review Workflow` verdict pattern (`pass`/`fail`/`blocked`) but produced by a human operator rather than a reviewer resource.
2. **Boundary 2 — Architecture approval → Starter kit selection & clone.** This is hard because it is the first point where an approved decision triggers an irreversible, external side effect: `create-app-repo.sh` creates an independent Git repository outside this system's tracked artifact tree. **Required contract:** a `SIDE-EFFECT-CONTRACT` addendum documenting that repo creation is a governed side effect requiring the architecture-approval artifact as a precondition, and that the resulting repo's identity (slug, path, remote) must be recorded back into the Module artifact so downstream issues can reference it — otherwise the issue graph loses track of where its own output lives.
3. **Boundary 3 — Validation failure → Automatic repair issue creation.** This is hard because it is the one place the common blueprint's `Review Workflow` fail path ("return the work to execution or blocker resolution") must be made concrete and automatic rather than human-triggered, without violating Canonical Law 11 ("Blocked work must leave a trail") or Law 16 ("Quality gates must stop progression, not merely warn"). **Required contract:** an explicit rule (new `VALIDATION-CONTRACT` addendum or a documented extension of the existing one) specifying that every failed validation must deterministically produce a new `ISSUE.md` with `depends_on` pointing at the original failing issue's proof, rather than silently retrying or silently marking the parent issue blocked with no artifact trail.

### B.3 Starter kit integration points

- LiNKapps maintains a starter-kit registry; `starter_linkapps_fullstack` is the first registry candidate (`LiNKdeveloper/docs/STARTER_KIT_AND_REUSE_POLICY.md` §3; `ARCHITECTURE_PROPOSAL.md` §7: "LiNKdeveloper MUST maintain a starter-kit registry").
- `LiNKapps/scripts/create-app-repo.sh` performs the clone/fork mechanically: it clones the LiNKapps template via `rsync` (excluding `.git`, `node_modules`, etc.), writes `specify/PRD.md` (from an input PRD path or a placeholder) and `specify/APP_BOOTSTRAP_CONTEXT.md`, and initializes a fresh git repository unless `--skip-git` is passed. Inputs: `--slug` (required), `--out` (required), `--name`, `--prd`, `--remote`, `--skip-git`.
- This mapping treats the starter-kit clone as the concrete mechanism satisfying "Starter kit selection" and "Clone/fork" in the Application Factory module map (B.1) and as the trigger event for handoff Boundary 2 (B.2).

### B.4 Copy-first UI reskin policy

The exact phrase "not greenfield AI codegen" was **not found verbatim** in any LiNKdeveloper or LiNKapps source document read for this audit. The closest supporting language found:

- `LiNKdeveloper/docs/STARTER_KIT_AND_REUSE_POLICY.md` §7 lists allowed reuse decisions including *"use starter kit"* and *"extract pattern only"* — consistent with a copy-first posture but not an explicit prohibition on greenfield codegen.
- `LiNKapps/docs/00_OPERATOR_LIBRARY/APP_LIFECYCLE_POLICY.md` §3 lists "UI polish updates" as optional per-app work, implying the base UI is expected to come from the starter kit, not be regenerated per app.

**Recommendation:** the copy-first UI reskin policy as described in the mission ("clone proven app UI/UX, change look and feel — do NOT greenfield AI codegen") is Carlos's stated intent, not yet a written policy in any source document read. This should be written down explicitly as a new policy statement in Stage 1b rather than assumed from adjacent language. This is listed as an open question in the accompanying report.

---

## C. Skills Map

### C.1 Three-layer architecture (from `layered_hybrid_runtime_manual.md`)

Per the manual's Section 03 (Layered System Architecture), the full stack is actually six layers, of which the mission's three are the ones in scope for this repo:

| Layer | Owner | Responsibility | Authority |
|---|---|---|---|
| Layer 0 | Human / Business Intent | Source of business goals and strategic priorities | — |
| **Layer 1** | **IDE Development (this repo) / "Open Engine" control plane** | Governance, workflow, contracts, gates, state, evidence rules | **Master authority — owns state model, task hierarchy, and completion criteria; decides ready and complete** |
| **Layer 2** | **`garrytan/gstack`** | Macro-orchestration: autoplan/spec (`/spec`), persona routing, plan review (`/plan-ceo-review`), health checks (`/health`), shipping (`/ship`), context save/restore | May plan, review, ship (after gates pass) — **may not declare complete** |
| **Layer 3** | **`mattpocock/skills`** | Micro-execution: clarification (`/grill-with-docs`), PRD generation (`/to-prd`), issue slicing (`/to-issues`), TDD implementation (`/tdd`), debugging (`/diagnosing-bugs`), architecture refactor (`/improve-codebase-architecture`) | May implement — **may not review its own work, may not ship, may not declare complete** |
| Layer 4 | Project CI / Evals / Validation Gateway | Hard pass/fail validation authority | Provides evidence only |
| Layer 5 | Deployment / Canary / Production Monitoring | Smoke tests, canary checks | — |

**Layer 1 is master authority, verified verbatim from the manual:** *"Agent statements are not evidence unless accompanied by command output, test logs, diff references, review records, or deployment/canary records."* The manual's authority matrix (§10.5.4) explicitly denies "May Declare Complete" to both the Gstack Macro-Orchestrator and the Matt Pocock Skills Developer rows — only the Layer 1 control plane and the Human Operator retain that authority. This directly matches this repo's own Canonical Laws 9, 10, 12, 13, 16 (proof/review/integration/gates) with no contradiction found between the manual and this repo's doctrine.

The manual's routing table (§10.6.3) maps task types to layers:

| Task Type | Primary Layer | Secondary Layer |
|---|---|---|
| Vague user intent | `gstack /spec` | `mattpocock /grill-with-docs` |
| Issue slicing | `mattpocock /to-issues` | Open Engine issue model |
| Implementation | `mattpocock /tdd` | IDE agent / Cursor |
| Shipping | `gstack /ship` | Open Engine gate policy |
| Context save | `gstack /context-save` | State/evidence schema |
| Execution handoff | `mattpocock /handoff` | `gstack /context-save` |

The manual's required-files list (§10) for a fully wired system includes `core/agents/authority.md`, `core/agents/routing.md`, `core/gates/`, and `core/personas/`. **None of these exact paths exist in this repo today** (`core/agents/` exists but does not contain `authority.md` or `routing.md`; there is no `core/gates/` or `core/personas/` directory). This is expected — it is Stage 1b/Layer-2/3-wiring work, not a Stage 1a defect, and is listed explicitly in Section C.4 below.

### C.2 Skills table (full, per mission requirement)

Status legend: **exists** = present and usable today in `core/skills/`; **integrate** = candidate source has content worth pulling in during Stage 1b; **defer** = worth revisiting after Stage 1b, not urgent; **reject** = do not import as-is (either superseded or out of scope).

| Skill name | Layer | Source repo | Status | Workflow stage used in | Notes |
|---|---|---|---|---|---|
| `plan-writing` | 1 | `core/skills/plan-writing/` | exists | Program/Module planning | Turns a request into an implementation-ready plan |
| `task-decomposition` | 1 | `core/skills/task-decomposition/` | exists | Module→Phase→Issue decomposition | Maps directly onto Canonical Law 6 |
| `spec-driven-development` | 1 | `core/skills/spec-driven-development/` | exists | Intent/Program | Used for exactly this Stage 1a deliverable |
| `architecture` | 1 | `core/skills/architecture/` | exists | Program/Module | Structural design tradeoffs |
| `app-builder` | 1 | `core/skills/app-builder/` | exists | Issue execution | Directly relevant to Application Factory Development Execution module |
| `test-driven-development` | 1 (routes to Layer 3 concept) | `core/skills/test-driven-development/` | exists | Issue execution | Conceptually overlaps `mattpocock/skills` `/tdd`; no direct wiring today |
| `systematic-debugging` | 1 (routes to Layer 3 concept) | `core/skills/systematic-debugging/` | exists | Issue execution | Overlaps `mattpocock/skills` `/diagnosing-bugs`; no direct wiring today |
| `code-review-and-quality` | 1 | `core/skills/code-review-and-quality/` | exists | Review | Canonical Law 12 enforcement aid |
| `release-readiness` | 1 (provenance from legacy gstack) | `core/skills/release-readiness/` | exists — **frontmatter cites `LiNKtrend-System/LiNKdev/skills/gstack/ship` and `.../land-and-deploy` as source** | Review/Program release gate | See naming collision, C.4 |
| `browser-qa` | 1 (provenance from legacy gstack) | `core/skills/browser-qa/` | exists — **frontmatter cites `LiNKtrend-System/LiNKdev/skills/gstack/qa`, `/qa-only`, `/browse`** | Review | See naming collision, C.4 |
| `retrospective-learning` | 1 (provenance from legacy gstack) | `core/skills/retrospective-learning/` | exists — **frontmatter cites `LiNKtrend-System/LiNKdev/skills/gstack/retro`, `/learn`** | Post-Integration / Program | See naming collision, C.4 |
| `deployment-procedures` | 1 | `core/skills/deployment-procedures/` | exists | Integration/Release | Maps to Application Factory "Release readiness & deployment" module |
| `ci-cd-and-automation` | 1 | `core/skills/ci-cd-and-automation/` | exists | Integration/Review | |
| `git-safeguard` | 1 | `core/skills/git-safeguard/` | exists | Review/Integration | Relevant to Boundary 2 (repo creation side effect) |
| `security-and-hardening` | 1 | `core/skills/security-and-hardening/` | exists | Cross-cutting | |
| `documentation-and-adrs` | 1 | `core/skills/documentation-and-adrs/` | exists | Cross-cutting | Used to produce this spec |
| `context-engineering` | 1 | `core/skills/context-engineering/` | exists | Cross-cutting | Directly implements Canonical Law 19 (progressive disclosure) |
| `parallel-agents` | 1 | `core/skills/parallel-agents/` | exists | Cross-cutting | Relevant once Stage 1b introduces concurrency per `DEPENDENCY-RESOLUTION.md` |
| `intelligent-routing` | 1 | `core/skills/intelligent-routing/` | exists | Cross-cutting | Closest existing analog to the manual's `core/agents/routing.md` requirement — candidate to extend, not replace |
| (remaining ~34 skills in `core/skills/`) | 1 | `core/skills/` | exists | Various — see `core/skills/SKILLS_CATALOG.md` for full routing table | Not individually re-audited here; catalog already routes them correctly per Stage 1a scope |
| `/spec`, `/plan-ceo-review`, `/health`, `/ship`, `/context-save`, `/context-restore` | 2 | `garrytan/gstack` (external, not in this workspace) | **missing** | Program intake, release gate, context handoff | Zero references found anywhere in this repo or in any candidate skill source to the external `garrytan/gstack` project by that name — this is a green-field integration for Stage 1b |
| `/grill-with-docs`, `/to-prd`, `/to-issues`, `/tdd`, `/diagnosing-bugs`, `/improve-codebase-architecture` | 3 | `mattpocock/skills` (external, not in this workspace) | **missing** | Intent clarification, work decomposition, issue execution | Zero references found anywhere in this repo or in any candidate skill source to `mattpocock` by that name — green-field integration for Stage 1b |
| `LiNKskills` (`services/`, `tools/`, `skills/`, `configs/`) | 1/2 candidate | `/Users/linktrend/Projects/LiNKskills` | **evaluate/defer** | — | Contains a "Logic Engine" control plane and workspace CLI tools (`gws`, `ltr`); plausible Layer 1/2 governance source, but not yet mapped to this repo's contract model — needs a dedicated Stage 1b evaluation pass |
| `linktrend-skills` (`agents/`, `skills/`, `workflows/`, `rules/`) | 2/3 candidate | `/Users/linktrend/Projects/linktrend-skills` | **evaluate/defer — overlap risk** | — | A version of an "Antigravity Kit" with ~20 specialist agents and ~36 skills; meaningful overlap risk against this repo's own `core/agents/` and `core/skills/` — must be de-duplicated before any import, not merged wholesale |
| `link-antigravity-kit` | 3 candidate | `/Users/linktrend/Projects/link-antigravity-kit` | **evaluate/defer** | — | Micro-execution templates and specialist personas (frontend, backend, security); no `garrytan` or `mattpocock` references found — this is a different, LiNKtrend-authored personas kit, not the external Layer 2/3 sources named in the manual |
| `link-awesome-openclaw-skills` | reference only | `/Users/linktrend/Projects/link-awesome-openclaw-skills` | **reject as primary source — reference index only, per mission instruction** | — | Large community skill index (thousands of entries); useful for discovery searches only |

### C.3 gstack integration plan (Layer 2)

- **Reference path:** `garrytan/gstack` does not exist anywhere in this workspace today. It must be vendored or referenced (per the mission's instruction, not copied into this repo in Stage 1a) at a path to be decided in Stage 1b — likely as a sibling `Projects/` repo, consistent with how this repo's own workspace-adoption model treats other repos as consumers, not embedded copies (`core/workspace/WORKSPACE-ADOPTION.md`).
- **gstack workflow → app-factory stage mapping (proposed, from the manual's routing table plus the Application Factory module map in Section B):**
  - `gstack /spec` → Opportunity intake & triage / Product blueprint drafting (Module 1–3 in B.1)
  - `gstack /plan-ceo-review` → Product blueprint & architecture human-approval gates (Boundary 1 and 2, Section B.2)
  - `gstack /health` → Continuous validation & self-healing module (repair loop)
  - `gstack /ship` → Release readiness & deployment module — **must remain subordinate to this repo's Integration Workflow and Canonical Law 14 (release separate from integration); `/ship` may propose, this repo's gates decide**
  - `gstack /context-save` / `/context-restore` → Session start/end wrapper behavior already defined in `core/session/SESSION-START.md` / `SESSION-END.md` — candidate for a compatibility bridge, not a replacement
- **What is missing and must be created in Stage 1b:** the actual `garrytan/gstack` reference/vendoring decision; a Layer 1→2 authority contract equivalent to the manual's `core/agents/authority.md`; and explicit test that `/ship` cannot bypass this repo's review/integration gates.

### C.4 mattpocock integration plan (Layer 3) and the gstack naming collision

- **Reference path:** `mattpocock/skills` also does not exist anywhere in this workspace today (verified — zero matches for "mattpocock" in this repo or any candidate skill source directory).
- **mattpocock skill → issue-type mapping (proposed, from the manual's routing table):**
  - `/grill-with-docs` → Issue-level clarification before an issue is marked `ready` (supports Law 4, "Readiness is computed, not declared")
  - `/to-prd`, `/to-issues` → Module/Phase decomposition into `ISSUE.md` (overlaps this repo's own `task-decomposition` skill — reconcile, don't duplicate)
  - `/tdd` → Issue execution proof production (overlaps this repo's own `test-driven-development` skill — reconcile, don't duplicate)
  - `/diagnosing-bugs` → Issue execution when blocked (overlaps this repo's own `systematic-debugging` skill — reconcile, don't duplicate)
  - `/improve-codebase-architecture` → Module-level refactor issues
- **What is missing and must be created in Stage 1b:** the actual `mattpocock/skills` reference/vendoring decision, plus a reconciliation pass between `mattpocock/skills`' TDD/debugging skills and this repo's own pre-existing `test-driven-development` and `systematic-debugging` skills so Stage 1b does not end up with two competing versions of the same micro-execution discipline.
- **IMPORTANT — naming collision, flagged not resolved:** three of this repo's *existing* skills (`release-readiness`, `browser-qa`, `retrospective-learning`) carry frontmatter provenance pointing at `LiNKtrend-System/LiNKdev/skills/gstack/...` — i.e., an internal folder named "gstack" that lived inside the now-abandoned **LiNKdev** repository, mined for content per `core/reports/SKILL-MIGRATION-PASS-1.md` ("`LiNKtrend-System/LiNKdev/skills/gstack` is a large legacy skill system... it should be mined selectively, not copied wholesale"). This is a **different artifact** from `garrytan/gstack`, the external open-source Layer 2 orchestration tool named in the skills manual. Both are called "gstack." Nothing in this repo currently confuses the two — the existing skills only reference the legacy LiNKdev-internal folder, and no file anywhere claims a live dependency on `garrytan/gstack` — but Stage 1b work that introduces the real `garrytan/gstack` will create two same-named things in the same knowledge base. This must be named unambiguously (e.g., "LiNKdev-legacy-gstack" vs. "garrytan-gstack") before Stage 1b skill work begins. See open question in the report.

### C.5 What is missing and must be created in Stage 1b (skills, summary)

- `core/agents/authority.md` and `core/agents/routing.md` (or their equivalents inside this repo's existing `core/agents/` and `core/skills/intelligent-routing/` structures)
- `core/gates/` — this repo's gate logic is currently distributed across `core/contracts/`, `core/state/`, and Canonical Laws rather than centralized; the manual's implementation blueprint assumes a dedicated `gates/` directory. Decide in Stage 1b whether to centralize or keep distributed.
- `core/personas/` — no equivalent exists; `core/agents/` currently plays this role informally
- An explicit vendoring/reference decision for `garrytan/gstack` and `mattpocock/skills`
- A disambiguating rename or clarifying note resolving the gstack naming collision (C.4)
- A reconciliation pass between `mattpocock/skills` concepts and this repo's own `test-driven-development` / `systematic-debugging` skills

---

## D. Legacy Exclusions

### D.1 LiNKdev is explicitly out of the active stack

Confirmed directly: `.cursor/rules/00-linkdev-bootstrap.mdc` (alwaysApply: true) already states *"Do not depend on `LiNKdev`, chat memory, IDE memory, or unstated assumptions."* This file's own *name* is misleading — it is called "linkdev-bootstrap" but its content is the general shared-system bootstrap rule and explicitly excludes LiNKdev. This naming should be corrected in Stage 1b (e.g., rename to `00-bootstrap.mdc`) to avoid new operators mistaking it for a LiNKdev dependency.

### D.2 What embedded LiNKdev content is worth reading as history only

The only LiNKdev content with any ongoing value, per this audit, is the internal `gstack` skill folder (`LiNKtrend-System/LiNKdev/skills/gstack`), which has already been "mined selectively, not copied wholesale" into three of this repo's current skills (`release-readiness`, `browser-qa`, `retrospective-learning`) per `core/reports/SKILL-MIGRATION-PASS-1.md`. That mining is already done and already recorded as historical provenance in those skills' frontmatter. No further LiNKdev content is worth reading as a source of truth for Stage 1 design, per the mission's exclusion rule.

### D.3 Migration notes for `00-linkdev-bootstrap.mdc` alwaysApply

- **File:** `/Users/linktrend/Projects/IDE Development/.cursor/rules/00-linkdev-bootstrap.mdc`
- **Current state:** `alwaysApply: true`, content correctly excludes LiNKdev as a dependency, but the filename itself invokes "linkdev" in a way that could be misread as endorsing it.
- **Recommendation for Stage 1b:** rename the file (e.g., to `00-bootstrap.mdc`) and update any cross-references, while preserving the alwaysApply behavior and the "do not depend on LiNKdev" content unchanged. This is a rename-only change; no doctrine content changes are proposed here per the working rule against modifying `core/` files without a clear factual error.

### D.4 Summary table — LiNKdev references found in this repo (all already treated as legacy, none active)

| File | Reference | Treatment |
|---|---|---|
| `.cursor/rules/00-linkdev-bootstrap.mdc` | "Do not depend on `LiNKdev`..." | Correctly excludes LiNKdev; filename should be renamed (D.3) |
| `.cursor/README.md` | "`LiNKdev` is legacy source material only. It is not a required runtime dependency for this system." | Already correctly stated |
| `core/workspace/WORKSPACE-ADOPTION.md` | "legacy LiNKdev remnants" listed as a cleanup target during adoption | Correctly treated as legacy |
| `core/checklists/wire-checklist.md` | "no required runtime dependency on `LiNKdev`" required before a repo is wired | Correctly treated as a gate, not a dependency |
| `core/reports/SKILL-MIGRATION-PASS-1.md` | `LiNKtrend-System/LiNKdev/skills/gstack` described as "a large legacy skill system... mined selectively, not copied wholesale" | Correctly treated as historical source only |
| `core/skills/SKILLS_CATALOG.md` (line 151) | Lists `LiNKtrend-System/LiNKdev/skills/gstack` under "Known source systems for future migration review" | Correctly treated as a future-review source, not active |
| `core/skills/release-readiness/SKILL.md`, `browser-qa/SKILL.md`, `retrospective-learning/SKILL.md` (frontmatter) | Cite `LiNKtrend-System/LiNKdev/skills/gstack/...` as provenance | Historical provenance only — see naming collision, C.4 |

No file found treats LiNKdev as an active dependency, a parallel workflow, or a source of truth for current design. The exclusion rule is already satisfied by the existing repository state; Stage 1a introduces no new LiNKdev references.

---

## E. Stage 1a Acceptance Criteria

Carlos should approve Stage 1a only if all of the following are independently true:

- [ ] All three deliverables exist: `docs/LINKDEVELOPER-STAGE1.md`, `docs/LINKDEVELOPER-STAGE1A-SPEC.md`, `docs/LINKDEVELOPER-STAGE1A-REPORT.md`.
- [ ] Every file cited in Section A.2 was actually opened and quoted, not assumed (spot-check: open `core/execution/CANONICAL-LAWS.md` and confirm it has exactly 20 laws matching Section A.3 verbatim).
- [ ] No Canonical Law was contradicted by any workflow, contract, or state file (spot-check any 2–3 of the 20 laws against the workflow files cited in A.4).
- [ ] The Application Factory module map (B.1) covers all 12 app-factory-specific concerns listed in the mission, with none left unmapped.
- [ ] The three hardest handoff boundaries (B.2) each have a named required contract, not just a description of difficulty.
- [ ] The skills table (C.2) explicitly marks every Layer 2 and Layer 3 skill as **missing** (none should be marked "exists" for external `garrytan/gstack` or `mattpocock/skills` content, since neither is vendored yet).
- [ ] The gstack naming collision (C.4, D.4) is understood and a decision path exists (does not need to be resolved in Stage 1a, but must be visible).
- [ ] LiNKdev appears only under legacy-to-migrate framing anywhere in this spec (D.1–D.4) — grep this document for "LiNKdev" and confirm every occurrence is in a legacy/historical/exclusion context.
- [ ] No file under `core/` was modified by this Stage 1a pass (verify with `git status` in this repository).
- [ ] No commit was made during Stage 1a (verify with `git log` — no new commits from this session).

**How to validate before Stage 1b begins:** Carlos and Lisa review this spec together; Lisa checks the citations against the actual files (a sample of 5–10 citations is sufficient, not a full re-audit); Carlos makes the go/no-go call. If approved, the Stage 1b prerequisites in Section F below become the next actionable checklist.

---

## F. Stage 1b Preview (outline only — not implemented)

**What becomes semi-autonomous in Stage 1b:** issue-level execution assisted by Cursor/Codex inside the existing `Execute-Issue`/`Review-Issue`/`Integrate-Issue` command surface (`core/commands/execute-issue.md`, `review-issue.md`, `integrate-issue.md`), with a human still approving every module-level and program-level gate. Program and module planning stay human-led per `core/workflows/planning-lifecycle.md`.

**Cursor workspace setup prerequisites (outline only):**
- A `Projects/` workspace containing `IDE Development` alongside consumer repos, per `core/workspace/WORKSPACE-ADOPTION.md`.
- Symlink adoption (`repo/.cursor -> ../IDE Development/.cursor`) for each consumer repo that will run Stage 1b work, per `core/workspace/REPO-WIRING.md`.
- This Stage 1a spec approved by Carlos, per the mission's explicit gate.

**First product build after Stage 1b:** the mission specifies **Website Factory**, not the Application Factory documented in Section B of this spec. The Application Factory variant mapping in this document is preparatory documentation for a later build, not the first Stage 1b product. This distinction should not be lost when Stage 1b planning begins — Website Factory's own module map is out of scope for this Stage 1a deliverable and was not audited here.

No Stage 1b work — Cursor workspace changes, symlink creation, consumer repo wiring, or product scaffolding — was started during this Stage 1a pass.
