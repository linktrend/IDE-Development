---
name: intelligent-routing
description: Select trigger, hybrid skill, domain skill, command, artifact path, and agent role for a task.
version: 2.0.0
status: active
tags: [routing, skills, commands, agents, hybrid, triggers]
source_adapted_from:
  - link-antigravity-kit/.codex/skills/intelligent-routing
  - docs/HYBRID-SKILLS-REGISTRY.md
  - /Users/linktrend/Projects/Archive/LiNKdeveloper-Stage2-Runtime-20260710/docs/EXECUTOR_ROUTING_POLICY.md (read-only archive reference)
---

# Intelligent Routing

Use this skill when deciding how the system should handle a request. Carlos uses three triggers only; agents pick routes inside them.

## Routing order

1. **Identify Carlos's trigger** — New idea (Trigger 1), PRD in hand (Trigger 2), or Existing software (Trigger 3). See `docs/LINKDEVELOPER-OPERATIONS-MANUAL.md` (triggers and routing).
2. **Select hybrid macro or micro** — gstack (macro) or mattpocock skills (micro) per trigger stage. Registry: `docs/HYBRID-SKILLS-REGISTRY.md`.
3. **Select domain skills** — IDE Development core locals from `SKILLS_CATALOG.md` when hybrid does not cover the concern (APIs, UI, deploy execution, etc.).
4. **Select internal artifact commands** — only when work is decomposed into the canonical graph (`plan-program`, `execute-issue`, …).
5. **Select agent roles** as resources, not as the control structure.
6. **Load only required artifacts** — progressive disclosure (Law 19).

## Trigger → hybrid routes

### Trigger 1 — New idea

1. Interview Carlos for intent, constraints, success criteria.
2. gstack `/spec` (`core/commands/hybrid-spec.md`) — structured specification.
3. Optional gstack `/plan-ceo-review` for large or ambiguous bets.
4. mattpocock `/grill-with-docs` if documentation gaps remain.
5. mattpocock `/to-prd` when formalizing the PRD.
6. **Stop for Carlos approval** — spec/PRD gate before development.
7. Route app vs factory-style product: normal applications scaffold from the LiNKapps starter kit; factory-style products (continuous production lines) follow that product's own governing specification/roadmap — there is no shared generic factory-ops blueprint (see `docs/ARCHIVE-INDEX.md` for the retired one and why).
8. Core commands: `plan-program` → `plan-module` → execution commands.

### Trigger 2 — PRD in hand

1. mattpocock `/grill-with-docs` — clarify gaps against docs and codebase.
2. **Stop for Carlos approval** — clarified PRD gate.
3. mattpocock `/to-issues` — slice into dependency-aware issues.
4. Core commands: `execute-issue` → proof → `review-issue` → `integrate-issue`.
5. During execution: mattpocock `/tdd`, `/diagnosing-bugs`; domain skills as needed.

### Trigger 3 — Existing software

1. Assess codebase — scope, gaps, risks.
2. gstack `/health` when project health or gate discipline is unclear.
3. Plan: core `plan-module` or `small-change`; mattpocock `/improve-codebase-architecture` for structural refactors.
4. **Carlos approves** when direction is unclear or high-impact.
5. Develop with domain skills + `/tdd`; core integration gates always apply.
6. gstack `/ship` only after core integration passes — does not replace review or integration.

## Hybrid command index

**gstack (macro):**

- Spec — `hybrid-spec` → `/Users/linktrend/Projects/gstack/spec/SKILL.md`
- CEO plan review — `hybrid-plan-ceo-review` → `.../gstack/plan-ceo-review/SKILL.md`
- Health — `hybrid-health` → `.../gstack/health/SKILL.md`
- Ship — `hybrid-ship` → `.../gstack/ship/SKILL.md`
- Context save/restore — `hybrid-context-save`, `hybrid-context-restore` → `.../gstack/context-save/SKILL.md`, `context-restore/SKILL.md`

**mattpocock skills (micro):**

- Clarify PRD — `hybrid-grill` → `.../skills/skills/engineering/grill-with-docs/SKILL.md`
- PRD synthesis — `hybrid-to-prd` → `.../skills/skills/engineering/to-spec/SKILL.md`
- Issue slicing — `hybrid-to-issues` → `.../skills/skills/engineering/to-tickets/SKILL.md`
- TDD — `hybrid-tdd` → `.../skills/skills/engineering/tdd/SKILL.md`
- Debugging — `hybrid-diagnosing-bugs` → `.../skills/skills/engineering/diagnosing-bugs/SKILL.md`
- Architecture improve — `hybrid-improve-architecture` → `.../skills/skills/engineering/improve-codebase-architecture/SKILL.md`

## Domain skill shortcuts

After hybrid selection, prefer the smallest domain skill:

- UI → `frontend-ui-engineering`
- API → `api-patterns`
- Data → `database-design`
- Deploy execute → `deployment-procedures` (ship *decision* → gstack `/ship`)
- Browser flows → `webapp-testing`
- Criterion QA → `persistent-qa`
- Scaffold LiNKtrend app → `app-builder`
- Read order → `context-engineering`
- Review a PR / change / patch → `code-review-and-quality` (distinct from gstack `/plan-ceo-review`, which is executive-level plan review, not patch review)
- Bug report ("I found a bug", something broke) → mattpocock `/diagnosing-bugs`; if severity or scope is unclear, treat as Trigger 3 assess first
- Security concern (auth, secrets, input handling, trust boundary) → `security-and-hardening`

## Internal artifact commands (decomposition required)

Use only when the work graph exists or the task fits a bounded gate path:

- ambiguous greenfield after spec: `plan-program`
- module decomposition: `plan-module`
- tiny bounded fix: `small-change`
- ready issue: `execute-issue`
- evidence check: `review-issue`
- accepted work: `integrate-issue`
- recursive module: `complete-module`

## Validation and repair routing (reference)

Failed validation must not silently retry. Per archived Stage 2 reference `EXECUTOR_ROUTING_POLICY.md` (see `docs/ARCHIVE-INDEX.md`) and `VALIDATION-CONTRACT.md`:

- Reject progression when handoff cannot be validated.
- Record ambiguity or failure in artifacts.
- On validation failure during review, return to execution or create a repair issue with `depends_on` the failing proof — see `VALIDATION-CONTRACT.md` Remaining Ambiguity Rule and Stage 2 repair routing (reference only; no LiNKdev runtime dependency).

## Rules

- Do not over-plan trivial work — `small-change` may suffice under Trigger 3.
- Do not skip proof, review, or integration for speed.
- Do not choose multiple overlapping skills when one is enough.
- Do not treat specialist agents as sequence drivers.
- gstack `/ship` and macro QA do not override core integration gates.
- Record blockers when routing cannot proceed.

## Output

- Carlos trigger (1, 2, or 3)
- selected hybrid command(s) if any
- selected domain skill(s) if any
- selected core command if any
- active artifact level
- required reads
- reason for route

## Progressive disclosure

Read `docs/HYBRID-SKILLS-REGISTRY.md` and this catalog's overlap section first. Stop once the correct route is clear.
