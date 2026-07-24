# IDE Development — Technical PRD

**Status:** Technical reference for the IDE Development repository as actually built on disk (verified against `core/`, `.cursor/`, `scripts/`, `.githooks/`, and git history through 2026-07-19).

**Ground rule:** The filesystem and verification scripts are the source of truth. Where older docs (`docs/archive/**`, historical Stage 1/2/3 framing, earlier “skills are stubs” audits) disagree with what is wired today, this document follows the filesystem and calls out the discrepancy in §12.

**Companion:** [`IDE-DEVELOPMENT-INTENT.md`](./IDE-DEVELOPMENT-INTENT.md) — why this repository exists.

---

## 1. System overview / architecture

IDE Development is **not** a persistent orchestrator process. It is an **installable knowledge + runtime surface** that Cursor (and Codex/Claude entrypoints) load when a workspace includes this repo and/or a product repo wired to it.

| Part | Implementation on disk |
|---|---|
| **Canonical knowledge** | `core/` — doctrine, skills, commands, templates, contracts, workflows, session, workspace adoption, library client, examples, pilots |
| **Cursor compatibility runtime** | `.cursor/` — mostly symlinks into `core/`; real Cursor-only files: `rules/`, `mcp.json`, `INDEX.yaml`, `README.md`, `import-core.md` |
| **Instructions** | Commands under `core/commands/`, prompts under `core/prompts/`, progressive-disclosure `INDEX.yaml` files |
| **Memory (session-scoped)** | Repo artifacts + `docs/development/<program-id>/PIPELINE-STATE.json` + optional `docs/handoff/YYYY-MM-DD.md` — not a database Ledger |
| **Tools / skills** | Local domain skills (`core/skills/`), vendored gstack + mattpocock (`core/runtime/skills/`), Module composites (`core/runtime/skills/linktrend/`) |
| **Grading / gates** | Independent review commands + fail-closed `validate-application-pipeline.mjs`; model-routing `independent_review` / `evaluation` routes |
| **Guardrails** | Canonical Laws, git hooks on `PIPELINE-STATE.json`, CI verify workflow, branch-source policy |
| **Install into consumers** | `scripts/wire-repo.sh` → consumer `.cursor` symlink → IDE Development `.cursor` → `core/` |

### Symlink install model

```
ProductRepo/.cursor  →  ../IDE Development/.cursor  →  (symlinks)  →  ../IDE Development/core
```

- Preferred one-time wiring: `./scripts/wire-repo.sh /path/to/ProductRepo` (backs up replaceable `.cursor`, creates relative symlink, verifies required paths, idempotent).
- Manual / judgment path: `core/workspace/WORKSPACE-ADOPTION.md`, `REPO-WIRING.md`, `LEGACY-CLEANUP.md`.
- Do **not** copy `core/` into every product repo when a symlink suffices.
- Multi-machine sync: GitHub `linktrend/IDE-Development` is source of truth; clone as `~/Projects/IDE Development` (see `SETUP.md`).

### `core/` vs `.cursor/`

| Concern | Where it lives |
|---|---|
| Edit knowledge | Prefer `core/` |
| What Cursor loads | `.cursor/` paths (symlinked) |
| Cursor-only rules | `.cursor/rules/*.mdc` (real files, not symlinked from core) |
| Equivalence | Historical proof archived; verify script checks critical symlinks + required files |

### Relationship to LiNKdeveloper

| Dimension | IDE Development | LiNKdeveloper |
|---|---|---|
| Role | Human-assisted shared OS | Autonomous application factory Program |
| Runtime | Session-scoped Cursor/Codex | Persistent orchestrator + Program Ledger |
| Modules | **Six** fixed Modules | **Seven** (`environment_bootstrap` inserted) |
| Starter Kit | Optional | Mandatory when registry non-empty |
| Promotion | Principal Release OK at Module 6 | Automatic canary-protected promotion (LAW-06 rewrite) |
| Coupling | None at runtime either direction | May *author* using this `.cursor` surface only |

---

## 2. Terminology glossary

| Term | Meaning |
|---|---|
| **IDE Development** | This repository (`IDE Development` on disk, `linktrend/IDE-Development` on GitHub) — the shared Application Factory operating system |
| **Application Factory** | The shared product-building workflow (Intent → … → Complete), not a specific website/automation/content factory’s ops model |
| **core/** | Canonical portable knowledge asset |
| **.cursor/** | Compatibility runtime surface for Cursor-oriented consumers |
| **Program** | Total body of work toward a meaningful outcome; for application builds, drives the fixed six-Module pipeline |
| **Module** (application) | One of six fixed lifecycle stages in `APPLICATION-PIPELINE.md` |
| **Module** (generic) | Major domain area for non-application governed work only |
| **Phase** | Checkpointed subset of work within a Module |
| **Issue** | Atomic executable unit (Law 1) |
| **Proof** | Non-vacuous evidence mapping acceptance criteria to artifacts/observations |
| **Review** | Independent evaluation of proof + work (`pass` / `fail` / `blocked`) |
| **Integration** | Incorporation of reviewed work into the active line; required before downstream Issues may depend on it |
| **PIPELINE-STATE.json** | Durable, repository-resident state machine for an application Program |
| **Human gate** | Principal approve/reject checkpoint (Module 1 Intent+Technical PRD; Module 6 pre-deploy) |
| **Hybrid skills** | Vendored gstack (macro) + mattpocock (micro) + local domain skills, routed via `intelligent-routing` |
| **Route / RouteId** | Named model-routing policy (`default`, `escalation`, …) pinned on a Cursor subagent |
| **LiNKlibraries** | Canonical shared Component/Template/Asset Library remote |
| **Librarian** | Merge authority inside LiNKlibraries (not this repo) |
| **Wire** | One-time symlink install of this runtime into a consumer repo |

---

## 3. Prescribed workflow / lifecycle

### Shared lifecycle spine

```
Intent → Program → Module → Phase → Issue → Proof → Review → Integration → Complete
```

### Fixed six-Module application pipeline

Authoritative contract: `core/execution/APPLICATION-PIPELINE.md`.

```
intake_and_definition
→ assembly_planning
→ execution
→ verification_and_hardening
→ library_contribution
→ shipment
```

No application Program may rename, reorder, omit, or insert a seventh top-level Module. Product-specific decomposition belongs inside Modules as Phases and Issues.

#### Module 1 — `intake_and_definition`

Interview with four hard-gated Principal confirms (analysis → prioritization/MoSCoW → Intent) → author `TECHNICAL-PRD.md` → independent review → Principal approval of Intent + Technical PRD. Composite skill: `runtime/skills/linktrend/module1-intake-and-definition/`.

#### Module 2 — `assembly_planning`

Feature map → library query → OSS research/vetting → Technical Design + independent review → optional Starter Kit decision → Issue DAG → independent plan gate. Starter Kit is **never required**.

#### Module 3 — `execution`

Issue dispatch → implement+proof on `issue/<id>-<slug>` from `development` → independent review → PR+CI integration → Module gate.

#### Module 4 — `verification_and_hardening`

Mechanical test-planning + coverage-trace preflights → full test/build → security/dependency audit → E2E acceptance vs Technical PRD → repair loop → Module gate.

#### Module 5 — `library_contribution`

Extract candidates → dedup against LiNKlibraries → author/validate → publish contribution PR → Module gate.

#### Module 6 — `shipment`

Critical verification → SHA256 proof manifest → ship criteria → program-release review → **Principal pre-deploy gate** → terminal `release_ready` or `blocked` (**never deploy from this pipeline**).

### Target-repo artifact layout

```text
docs/development/<program-id>/
  INTENT.md
  TECHNICAL-PRD.md
  TECHNICAL-DESIGN.md
  PROGRAM.md
  PIPELINE-STATE.json
  modules/01-intake-and-definition/ … 06-shipment/
  proof-manifest.sha256
```

`PRD.md` and `LIVING-DOCUMENT.md` are retired for new application Programs.

### Operator entry commands

| Command | Role |
|---|---|
| `run-application-pipeline` | Start a fixed six-Module Program |
| `resume-application-pipeline` | Resume from `PIPELINE-STATE.json` only (no chat memory required) |
| `plan-program` / `plan-module` / `complete-module` | Artifact-graph planning and recursive Module completion |
| `execute-issue` / `review-issue` / `integrate-issue` | Issue lifecycle |
| `small-change` | Tiny low-risk work that still needs proof/review/integration |
| `library-search` / `library-contribute` | LiNKlibraries client entrypoints |
| `hybrid-*` | Thin entrypoints into vendored gstack/mattpocock skills |

### Gate repair (session-scoped)

On Tier-A (Issue) or Tier-B (Module) rejection: record severity, auto-redrive repair work, cap at **3** attempts (or lower `gateRepairBudget`), then `blocked` + briefing trail. No persistent Ledger repair driver — agents follow doctrine in-session.

### Transition enforcement

Before writing Module state transitions:

```bash
node .cursor/runtime/validate-application-pipeline.mjs \
  --state <PIPELINE-STATE.json> \
  --request-transition <module-id>:<target-state>
```

Non-zero = **stop**. Schema: `core/contracts/APPLICATION-PIPELINE-STATE.schema.json`.

---

## 4. Doctrine / laws / gates / proof system

All under `core/execution/` (operative — **not** archived):

| File | Role |
|---|---|
| `INDEX.yaml` | Progressive-disclosure index |
| `CANONICAL-LAWS.md` | 20 durable, tool-independent laws |
| `MINIMUM-RUNTIME-MODEL.md` | Hierarchy, issue states, dependencies, gates, proof/review/integration/release |
| `AUTONOMOUS-MODULE-EXECUTION.md` | Recursive Module completion behavior from artifacts alone |
| `APPLICATION-PIPELINE.md` | Fixed six-Module contract (above) |

### Issue state model (minimum)

`draft` → `planned` → `blocked` | `ready` → `in_progress` → `review_ready` → `done`

`done` requires proof, review, **and** integration.

### Gate model (minimum)

Planning → Readiness → Execution → Review → Integration → Release.

### Proof standard

Maps acceptance criteria to evidence; distinguishes facts from assumptions; records blockers. Vacuous “trust me” proof is rejected (Laws 9–10).

### Fail-closed Law 16 enforcement

- Validator: `core/runtime/validate-application-pipeline.mjs`
- Behavioral coverage: `scripts/test-gate-stop-progression.sh` + `docs/validation/GATE-STOP-001-report.md`
- Git hooks reject invalid `PIPELINE-STATE.json` transitions (see §7)

---

## 5. Hybrid skills system

Three installed sources (all wired — **not** stubs):

### 5.1 Local domain skills

~40 skills under `core/skills/` after hybrid sunset. Catalog: `core/skills/SKILLS_CATALOG.md`. Routing hub: `core/skills/intelligent-routing/SKILL.md`.

Sunset (removed, replaced by hybrid): `release-readiness`, `browser-qa`, `retrospective-learning`, `spec-driven-development`, `plan-writing`, `task-decomposition`, `test-driven-development`, `systematic-debugging`. Evidence: `docs/archive/SKILLS-SUNSET-REPORT.md`.

### 5.2 gstack (macro) — vendored

- Path: `.cursor/runtime/skills/gstack/` → `core/runtime/skills/gstack/`
- Fork: `https://github.com/linktrend/gstack` (upstream `garrytan/gstack`)
- Manifest: `core/runtime/skills/VENDOR-MANIFEST.json` (commit SHA + per-file hashes)
- Verify vendored copies: `scripts/verify-vendored-skills.sh` (no auto-refresh from upstream; copies are adapted in-repo)

Primary commands (via `core/commands/hybrid-*.md`):

| Slash | Entrypoint | Role |
|---|---|---|
| `/spec` | `hybrid-spec` | Structured specification from vague intent |
| `/plan-ceo-review` | `hybrid-plan-ceo-review` | Executive plan review |
| `/health` | `hybrid-health` | Project health / repair loops |
| `/ship` | `hybrid-ship` | Shippable vs blocked — **subordinate** to IDE Development integration/release gates |
| `/context-save` / `/context-restore` | matching hybrids | Session persistence |

Also vendored: `review`, `qa`, `retro`, `learn`.

### 5.3 mattpocock (micro) — vendored

- Path: `.cursor/runtime/skills/mattpocock/`
- Fork: `https://github.com/linktrend/skills` (upstream `mattpocock/skills`)

| Label | Fork skill | Entrypoint |
|---|---|---|
| `/grill-with-docs` | `grill-with-docs` | `hybrid-grill` |
| `/to-prd` | `to-spec` | `hybrid-to-prd` |
| `/to-issues` | `to-tickets` | `hybrid-to-issues` |
| `/tdd` | `tdd` | `hybrid-tdd` |
| `/diagnosing-bugs` | `diagnosing-bugs` | `hybrid-diagnosing-bugs` |
| `/improve-codebase-architecture` | same | `hybrid-improve-architecture` |

Also vendored: `research`, `triage`, `setup-matt-pocock-skills`.

### 5.4 Module composite skills (LiNKtrend local)

`core/runtime/skills/linktrend/module{1-6}-*/SKILL.md` — harness-specific Module skills; excluded from upstream byte-equality checks (`adaptationExclusions` in VENDOR-MANIFEST).

### 5.5 Registry document

Live operational map: [`docs/HYBRID-SKILLS-REGISTRY.md`](./HYBRID-SKILLS-REGISTRY.md). Kept in place because `scripts/verify-ide-development.sh` and many command/skill files cite it by path. This Technical PRD is authoritative for architecture; the registry remains the command-level routing map.

---

## 6. Model routing

IDE Development has **no** persistent Ledger process. Routing is enforced by pinned Cursor custom subagents + agent-followed doctrine (`core/skills/model-routing/SKILL.md`).

**Source of truth for route→task criteria:** LiNKdeveloper `packages/model-routing/src/router.ts` (ported, not live-imported).

**Model pin format:** Cursor subagent frontmatter uses base ID + `[id=value,...]` bracket params (not LiNKdeveloper’s flat internal route-name strings).

| RouteId | Subagent file | Model pin (as on disk) |
|---|---|---|
| `default` | `.cursor/agents/route-default.md` | `claude-sonnet-5[thinking=true,effort=medium,context=1m]` |
| `escalation` | `.cursor/agents/route-escalation.md` | `gpt-5.6-sol[reasoning=medium,context=1m,fast=false]` |
| `independent_review` | `.cursor/agents/route-independent-review.md` | `claude-opus-4-8[thinking=true,effort=medium,context=1m,fast=false]` |
| `economical` | `.cursor/agents/route-economical.md` | `composer-2.5[fast=true]` |
| `bulk_documents` | `.cursor/agents/route-bulk-documents.md` | `gemini-2.5-flash` |
| `evaluation` | `.cursor/agents/route-evaluation.md` | `grok-4.5[effort=medium,fast=false]` |

**Escalation:** on model-quality failure, log attempt and retry once with the different-family pairing from the skill (one-hop cap). Agent-followed — not mechanized by a Ledger.

**Still not same-session proven:** that each bracket-param string resolves as expected in a live Cursor Desktop invocation for every route (doctrine records this gap honestly).

Also present under `core/agents/`: role templates (planner, reviewer, integrator, …) and squads — separate from route pins.

---

## 7. Git hooks and CI

### Local hooks (`.githooks/`)

Install: `scripts/install-git-hooks.sh` → sets `core.hooksPath=.githooks`.

| Hook | Behavior |
|---|---|
| `pre-commit` | If `PIPELINE-STATE.json` is staged/changed, run validator `--check-consistency`. Missing validator while pipeline state exists = **fail closed** (broken install). |
| `pre-push` | Same check against tracked `PIPELINE-STATE.json` on the branch tip. |

### CI (`.github/workflows/`)

| Workflow | Role |
|---|---|
| `ci.yml` | On PR/push to `development`/`staging`/`main`: run `verify-ide-development.sh` + `verify-pipeline-states.sh` |
| `branch-source-policy.yml` | Enforces allowed PR sources: work branches → `development`; only `development` → `staging`; only `staging` → `main` |
| `linktrend-development-to-staging.yml` | Tue/Fri 08:00 Asia/Taipei auto `development`→`staging` |
| `linktrend-staging-to-main.yml` | Mon 08:00 package; merge on Principal Approve dispatch |
| `linktrend-integrator-merge.yml` | Auto-merge PRs into `development` when checks/reviews allow |

Managed copies live in `core/github/managed-workflows/` and sync via `scripts/sync-managed-workflows.sh` / `wire-repo.sh`. Consumer `ci.yml` is never overwritten by sync.

Allowed short-lived sources into `development`: `dev/*`, `issue/*`, `feature/*`, `fix/*`, `chore/*`, `codex/*`, `cursor/*`, `antigravity/*`, `dependabot/*`.

### Branching doctrine (consumer + this repo)

See `.cursor/rules/01-git-branching.mdc` and `docs/AUTONOMOUS-GIT-OPERATIONS.md`: Bugbot reviews; Integrator merges into `development`; Promoter auto-merges `development`→`staging` (Tue/Fri); Principal Approves `staging`→`main` via Lisa/Telegram (Mon). Module 6 product Release OK remains separate.

---

## 8. Relationship to LiNKlibraries

| Item | Value |
|---|---|
| Remote | `https://github.com/linktrend/LiNKlibraries.git` |
| Canonical branch | `development` |
| Client | `core/library/library-client.mjs` (compat path `.cursor/library/`) |
| ADR | `docs/adr/0002-shared-component-template-asset-library.md` (accepted; kept live because library commands cite it) |
| Local sibling clone | `/Users/linktrend/Projects/LiNKlibraries` (operator machine; not a runtime dependency of this repo’s git tree) |

Access pattern (same as LiNKdeveloper shared-library client):

1. Module 2: sparse-checkout `indexes/catalog.json`, cache with fetch commit SHA.
2. On entry select: fetch only `entries/<id>/`, cache as `entryId@commitSHA`.
3. Disposable cache under `LINKTREND_SHARED_LIBRARY_CHECKOUT` (default `core/library/.cache/linklibraries`).
4. Offline mode fails closed if cache missing.
5. Publish opens PR; **Librarian** in LiNKlibraries merges — this client never self-merges to `development`.

---

## 9. What is NOT yet built / deliberately deferred

Honest gaps (do not treat as “almost done” checkboxes):

1. **Persistent autonomous orchestrator / Program Ledger** — intentionally out of scope here (LiNKdeveloper).
2. **Telegram / OpenClaw executive routing** — historical Stage 2/3 framing in older manuals is **not** this repo’s roadmap.
3. **Automatic product promotion / live deploy from Module 6** — Module 6 stops at `release_ready` + Principal gate.
4. **Dedicated Principal web/phone approval UI** — Cursor + terminal/relay only.
5. **Same-session live verification of all six route model pins** in Cursor Desktop — pins are on disk; runtime parse confirmation still open.
6. **Embedded legacy factory-folder cleanup in product repos** — deferred until Principal schedules per-repo adoption cleanup (`docs/ARCHIVE-INDEX.md`).
7. **Dollar-cost accounting dashboard** — not present.
8. **Mandatory environment bootstrap Module** — deliberately not ported; optional Starter Kit + light git/CI sanity only.

Known past mistake to avoid repeating: earlier audits sometimes claimed hybrid skills were stubs when they were already vendored and wired. Always re-check `core/runtime/skills/{gstack,mattpocock}/`, `VENDOR-MANIFEST.json`, and `hybrid-*.md` entrypoints before asserting “not installed.”

---

## 10. Package / directory map appendix

| Path | One-line description |
|---|---|
| `core/execution/` | Canonical Laws, runtime model, autonomous Module behavior, application pipeline |
| `core/skills/` | ~40 domain skills + catalog + intelligent/model routing |
| `core/commands/` | Execution + hybrid + library + pipeline command entrypoints |
| `core/commands/compatibility-archive/` | Legacy setup/compatibility command entrypoints (not at commands root) |
| `core/templates/` | INTENT, TECHNICAL-PRD, TECHNICAL-DESIGN, PIPELINE-STATE, Issue/Proof/Review, … |
| `core/contracts/` | Schemas including `APPLICATION-PIPELINE-STATE.schema.json` |
| `core/runtime/` | Validator, vendored skills, Module composites, runtime README |
| `core/library/` | LiNKlibraries client + contract + disposable cache |
| `core/workspace/` | Adoption, discovery, wiring, legacy cleanup, reports |
| `core/session/` | Session lifecycle + handoff structure |
| `core/bootstrap/` | START-HERE, QUICKSTART, session startup/shutdown |
| `core/workflows/`, `core/checklists/`, `core/prompts/`, `core/agents/` | Workflow, checklist, prompt, and agent-role layers |
| `core/examples/EXAMPLE-APPLICATION-PIPELINE/` | Fixed six-Module example tree |
| `core/pilots/` | Operator smoke / pilot artifacts |
| `core/discovery/`, `core/state/`, `core/system/`, `core/reports/` | Discovery, state, system notes, reports |
| `.cursor/` | Compatibility runtime (symlinks + Cursor rules/MCP) |
| `.githooks/` | pre-commit / pre-push pipeline enforcement |
| `scripts/` | verify, vendor, wire, install-hooks, feasibility, gate-stop test |
| `tests/fixtures/` | Pipeline feasibility / gate-stop / unification fixtures |
| `docs/` | Source-of-truth docs (this set), hybrid registry, ADR, archive |
| `codex/`, `claude/` | Non-Cursor consumption entrypoints |
| `SETUP.md`, `VERSION`, `CHANGELOG.md` | Operator setup, version (`v1.2`), changelog |

---

## 11. Verification surface

| Script | What it proves |
|---|---|
| `scripts/verify-ide-development.sh` | Symlinks, required files, hybrid registry present, sunset skills gone, ops manual present, no forbidden legacy “layer model” terminology in active docs, catalog↔disk skill match, pipeline fixtures, vendored hashes, gate-stop test, feasibility runner |
| `scripts/verify-vendored-skills.sh` | VENDOR-MANIFEST hashes match on-disk vendored files |
| `scripts/verify-pipeline-states.sh` | Tracked `PIPELINE-STATE.json` files pass validator (CI equivalent of hooks) |
| `scripts/test-gate-stop-progression.sh` | Law 16 fail-closed behavior |
| `scripts/feasibility/run-fixed-pipeline-feasibility.sh` | Fixed-pipeline feasibility fixture |

CI invokes the first three families via `ci.yml` with `CI=true` (skips machine-local Archive directory checks).

---

## 12. Known doc drift (for reviewers)

| Claim in older docs | Actual filesystem today |
|---|---|
| This repo “evolves” into OpenClaw Stage 2/3 autonomy | Autonomy roadmap belongs to **LiNKdeveloper**; this repo stays human-assisted |
| Hybrid skills are stubs / reference-only | Physically vendored under `core/runtime/skills/{gstack,mattpocock}/` with hash manifest + hybrid commands |
| Six Modules including Living Document / dual PRD | Intent + **single Technical PRD**; Living Document retired |
| `scripts/verify-stage1.sh` | Renamed/replaced by `scripts/verify-ide-development.sh` |
| `docs/LINKDEVELOPER-OPERATIONS-MANUAL.md` / `LINKDEVELOPER-STAGE1.md` | Correct names use `IDE-DEVELOPMENT-*` prefix |
| Module 6 auto-deploys / LAW-06 auto-promotion | Module 6 → `release_ready` + Principal pre-deploy only |
| Factory Operations Common Blueprint is live | Archived; product-specific ops belong in product repos |
| Flat model slugs in route frontmatter | Bracket-param syntax required by Cursor subagent docs |

If something under `docs/archive/` conflicts with Intent, Technical PRD, or Operations Manual, **those three win.**
