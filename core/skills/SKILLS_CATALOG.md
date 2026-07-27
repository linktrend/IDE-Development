# Skills Catalog

Use this file to route into local domain skills and hybrid macro/micro skills.

## Rules

1. Read this catalog first.
2. Open only the skill needed for the task.
3. Prefer the smallest skill that covers the work.
4. Route through Carlos's three triggers before picking hybrid vs domain skills (see `intelligent-routing`).
5. If a skill is missing, improve the nearest existing skill before creating a parallel one.

---

## Hybrid macro (gstack)

**Fork:** https://github.com/linktrend/gstack  
**Vendored copy:** `.cursor/runtime/skills/gstack/` (physical adapted copy; verify via `scripts/verify-vendored-skills.sh`)  
**Registry:** `docs/HYBRID-SKILLS-REGISTRY.md`

Command entrypoints: `core/commands/hybrid-spec.md`, `hybrid-plan-ceo-review.md`, `hybrid-health.md`, `hybrid-ship.md`, `hybrid-context-save.md`, `hybrid-context-restore.md`

- **`/spec`** — structured specification from vague intent (Trigger 1)
- **`/plan-ceo-review`** — executive plan review before large decomposition
- **`/health`** — project health and repair loops (Trigger 3 assess)
- **`/ship`** — ship verdict; subordinate to core integration gates
- **`/context-save`**, **`/context-restore`** — session persistence across long runs

Extended fork skills (`/review`, `/qa`, `/retro`, `/learn`) available for macro QA and retros after module work.

---

## Hybrid micro (mattpocock skills)

**Fork:** https://github.com/linktrend/skills  
**Vendored copy:** `.cursor/runtime/skills/mattpocock/` (physical adapted copy; verify via `scripts/verify-vendored-skills.sh`)  
**Registry:** `docs/HYBRID-SKILLS-REGISTRY.md`

Command entrypoints: `core/commands/hybrid-grill.md`, `hybrid-to-prd.md`, `hybrid-to-issues.md`, `hybrid-tdd.md`, `hybrid-diagnosing-bugs.md`, `hybrid-improve-architecture.md`

- **`/grill-with-docs`** — clarify PRD gaps against documentation (Trigger 2)
- **`/to-prd`** — PRD/spec synthesis (`to-spec` in fork)
- **`/to-issues`** — issue slicing (`to-tickets` in fork)
- **`/tdd`** — test-driven implementation loop
- **`/diagnosing-bugs`** — systematic debugging
- **`/improve-codebase-architecture`** — architecture refactor guidance

Setup once per machine: `skills/engineering/setup-matt-pocock-skills/SKILL.md` in the skills fork.

---

## Domain skills (IDE Development core)

Forty-three local skills remain after hybrid sunset. Grouped by concern.

### UI and frontend

- `frontend-ui-engineering` — UI architecture, components, accessibility, layout, visual proof
- `tailwind-patterns` — Tailwind tokens, utilities, responsive structure
- `mobile-design` — touch, mobile navigation, small-screen ergonomics
- `i18n-localization` — locale files, formatting, RTL

### Web testing and browser proof

- `webapp-testing` — user flows, routes, forms, e2e-style browser checks (replaces deleted `browser-qa` routing)
- `lint-and-validate` — build, lint, typecheck, focused test commands

### Test strategy and QA

- `testing-patterns` — choose test type and coverage shape (strategy above `/tdd`)
- `persistent-qa` — independent criterion-level verification and evidence mapping
- `code-review-and-quality` — patch/PR review (distinct from gstack `/plan-ceo-review`)

### Planning and implementation flow

- `incremental-implementation` — verified vertical slices during execution
- `app-builder` — scaffold or extend apps using LiNKtrend stack conventions and starter kit routing
- `intelligent-routing` — trigger → hybrid → domain → artifact command router
- `model-routing` — spawn pinned `.cursor/agents/route-*` subagents (ports LiNKdeveloper router.ts)
- `context-engineering` — progressive disclosure and read order (pairs with gstack context-save/restore)

### Architecture, APIs, data, source grounding

- `architecture` — boundaries, tradeoffs, structural design
- `api-patterns` — contracts, versioning, errors
- `database-design` — schemas, migrations, indexes, data safety
- `source-driven-development` — ground work in authoritative docs and upstream code
- `documentation-and-adrs` — durable docs and decision records

### Operations, release execution, runtime

- `server-management` — processes, env, logs, health diagnostics
- `ci-cd-and-automation` — pipelines and automated gates
- `deployment-procedures` — deploy execute, verify, rollback (execution; `/ship` decides)
- `observability-and-instrumentation` — logs, metrics, traces in product code
- `performance-optimization` — measurement-backed performance improvement

### Tools, agents, automation

- `tool-architect` — small local CLIs and helper scripts
- `mcp-builder` — MCP servers and agent-callable interfaces
- `parallel-agents` — coordinate independent issue work across agents

### Repository safety and change management

- `git-safeguard` — pre-commit/push safety
- `agentsetup` — NEW agent bootstrap onto short-lived `issue/*` from latest `development` (`/agentsetup`)
- `agentcomply` — ALREADY-OPEN agent migration onto `issue/*` (or cleanup), move dirty work safely (`/agentcomply`)
- `repository-manager` — workspace hygiene, handoffs, artifact placement
- `deprecation-and-migration` — safe retirement of old systems
- `code-simplification` — reduce complexity while preserving behavior
- `security-and-hardening` — trust boundaries, auth, secrets, input, dependency, and operational risk review

### Meta

- `skill-template` — golden template for creating or refactoring shared core skills; not a task-routing skill

### Language and shell

- `nodejs-best-practices`, `python-patterns`, `rust-pro`
- `bash-linux`, `powershell-windows`

### Admin/operator shell UI composites (optional)

Use only when the current work is building an admin or operator console surface for whichever product is in scope:

- `data-table` — columnar shell tables
- `action-queue` — feed-style attention rows
- `personal-information-forms` — shared PII form patterns

---

## Sunset (removed — use hybrid instead)

Do not route to these deleted skills. Use the hybrid command or fork skill listed.

| Removed skill | Use instead |
|---|---|
| `release-readiness` | gstack `/ship` via `hybrid-ship` |
| `browser-qa` | gstack `/health` + QA flows; fallback `webapp-testing` |
| `retrospective-learning` | gstack `/retro`, `/learn` |
| `spec-driven-development` | gstack `/spec` + mattpocock `/grill-with-docs` |
| `plan-writing` | mattpocock `/to-prd` + gstack `/spec` |
| `task-decomposition` | mattpocock `/to-issues` |
| `test-driven-development` | mattpocock `/tdd` |
| `systematic-debugging` | mattpocock `/diagnosing-bugs` |

Full audit: `docs/SKILLS-SUNSET-REPORT.md`

---

## Overlap routing (domain)

When multiple domain skills appear relevant:

- UI: `frontend-ui-engineering` first; then `tailwind-patterns`, `mobile-design`, or host composites as needed
- Browser proof: `webapp-testing` for flows; gstack QA for macro orchestration
- Tests: `testing-patterns` for strategy; mattpocock `/tdd` for execution loop
- Ship decision: gstack `/ship`; deploy execution: `deployment-procedures`
- Scaffold: `app-builder` for LiNKtrend stack; hybrid for generic PRD/issue decomposition
- Context: `context-engineering` for read order; gstack context-save/restore for session state

---

## Available skills (paths)

- `skills/action-queue/SKILL.md`
- `skills/agentcomply/SKILL.md`
- `skills/agentsetup/SKILL.md`
- `skills/api-patterns/SKILL.md`
- `skills/app-builder/SKILL.md`
- `skills/architecture/SKILL.md`
- `skills/bash-linux/SKILL.md`
- `skills/ci-cd-and-automation/SKILL.md`
- `skills/code-review-and-quality/SKILL.md`
- `skills/code-simplification/SKILL.md`
- `skills/context-engineering/SKILL.md`
- `skills/data-table/SKILL.md`
- `skills/database-design/SKILL.md`
- `skills/deprecation-and-migration/SKILL.md`
- `skills/deployment-procedures/SKILL.md`
- `skills/documentation-and-adrs/SKILL.md`
- `skills/frontend-ui-engineering/SKILL.md`
- `skills/git-safeguard/SKILL.md`
- `skills/i18n-localization/SKILL.md`
- `skills/incremental-implementation/SKILL.md`
- `skills/intelligent-routing/SKILL.md`
- `skills/lint-and-validate/SKILL.md`
- `skills/mcp-builder/SKILL.md`
- `skills/mobile-design/SKILL.md`
- `skills/model-routing/SKILL.md`
- `skills/nodejs-best-practices/SKILL.md`
- `skills/observability-and-instrumentation/SKILL.md`
- `skills/parallel-agents/SKILL.md`
- `skills/performance-optimization/SKILL.md`
- `skills/persistent-qa/SKILL.md`
- `skills/personal-information-forms/SKILL.md`
- `skills/powershell-windows/SKILL.md`
- `skills/python-patterns/SKILL.md`
- `skills/repository-manager/SKILL.md`
- `skills/rust-pro/SKILL.md`
- `skills/security-and-hardening/SKILL.md`
- `skills/server-management/SKILL.md`
- `skills/skill-template/SKILL.md`
- `skills/source-driven-development/SKILL.md`
- `skills/tailwind-patterns/SKILL.md`
- `skills/testing-patterns/SKILL.md`
- `skills/tool-architect/SKILL.md`
- `skills/webapp-testing/SKILL.md`

Hybrid skills are not duplicated under `core/skills/` — read from fork paths in `docs/HYBRID-SKILLS-REGISTRY.md`.
