# Archive Index — Retired Development Systems

**Date:** 2026-07-10 (active-docs section updated 2026-07-19)  
**Purpose:** Name retired systems, explain why they were archived, and state when operators may read from archive. Day-to-day authority is the source-of-truth quartet listed under **Active docs**.

---

## Retired systems

**LiNKdev** — GitHub: [linktrend/LiNKdev](https://github.com/linktrend/LiNKdev) (archived). Local snapshot: `/Users/linktrend/Projects/Archive/LiNKdev-legacy-20260710/`. Standalone portable factory (`LiNKdev/` tree, swarm rules, issue dispatch). Tried once; abandoned. Superseded by this repo (`IDE Development`) for human-assisted work, and by the independent **LiNKdeveloper** Program (`/Users/linktrend/Projects/LiNKdeveloper`) for autonomous work.

**LiNKdeveloper Stage 2 Runtime** — GitHub: [linktrend/LiNKdeveloper](https://github.com/linktrend/LiNKdeveloper) (archived). Local snapshot: `/Users/linktrend/Projects/Archive/LiNKdeveloper-Stage2-Runtime-20260710/`. A prior attempt at an autonomous orchestrator runtime (continuous lifecycle, executor routing, work-packet schema), built tightly coupled to the since-abandoned LiNKaios Admin/Plane/GitHub-dispatch governance stack. Not built or wired into this repo. Consulted as read-only concept reference when standing up the new, independent **LiNKdeveloper** Program repo — code, infrastructure, and runtime behavior are not copied wholesale.

**Factory Operations Common Blueprint** — Local: [`docs/archive/FACTORY-OPERATIONS-BLUEPRINT.md`](archive/FACTORY-OPERATIONS-BLUEPRINT.md) (archived 2026-07-13). Planning-only design for Website/Automation/Content factory operations. Retired because it hardcoded specific product architecture into what must be a shared, product-agnostic system. Never implemented.

**LiNKapps** (`LiNKdev Starter Kit` / `LTM Starter Kit`) — Local snapshot: `/Users/linktrend/Projects/Archive/LiNKapps-legacy-20260715/`. Retired name for the web + mobile starter-kit monorepo. Content vendored into LiNKdeveloper at `/Users/linktrend/Projects/LiNKdeveloper/starter-kits/linkapps-fullstack/` (2026-07-15) before archiving.

**LiNKtrend-System/LiNKdev factory** — Local snapshot: `/Users/linktrend/Projects/Archive/LiNKdev-factory-legacy-20260715/`. Doctrine vendored into `/Users/linktrend/Projects/LiNKdeveloper/doctrine/` (2026-07-15) before archiving; its GitHub Actions dispatch loop was not carried forward.

None of the systems above are installed, extended, or required for day-to-day IDE Development operation.

---

## When operators read from archive

Both **IDE Development** (this repo) and the independent **LiNKdeveloper** Program may consult archived Stage 2 **docs only** as read-only reference when mapping Application Factory concepts. Do **not** copy code, infrastructure, or runtime behavior from the Stage 2 archive.

**LiNKdev** archive is **not** a bootstrap or runtime source.

**Unification build-plan PRD** — Archived under [`docs/archive/planning/`](archive/planning/). Historical implementation plan; Living Document / dual-PRD language superseded by Technical PRD in `core/execution/APPLICATION-PIPELINE.md` and `docs/IDE-DEVELOPMENT-TECHNICAL-PRD.md`. Do not implement from the archive copies.

Historical Stage 1 completion evidence lives under [`docs/archive/`](archive/README.md).

---

## Embedded LiNKdev in product repos — deferred

Embedded `LiNKdev/` folders in product repositories are **legacy remnants**, not active factory surfaces.

**Posture:** Wire and develop using `.cursor/` + `core/` in **IDE Development**. Confirm no required runtime dependency on `LiNKdev` per `core/checklists/wire-checklist.md`.

**Cleanup:** Selective removal is **deferred** until the Principal explicitly schedules adoption/cleanup per repo.

---

## Active docs (not archived)

### Source of truth (2026-07-19)

- [`IDE-DEVELOPMENT-INTENT.md`](IDE-DEVELOPMENT-INTENT.md) — why this repository exists
- [`IDE-DEVELOPMENT-TECHNICAL-PRD.md`](IDE-DEVELOPMENT-TECHNICAL-PRD.md) — exhaustive technical reference
- [`IDE-DEVELOPMENT-OPERATIONS-MANUAL.md`](IDE-DEVELOPMENT-OPERATIONS-MANUAL.md) — Principal handbook
- [`OPEN-ISSUES.md`](OPEN-ISSUES.md) — append-only build log

### Still live operational companions

- [`HYBRID-SKILLS-REGISTRY.md`](HYBRID-SKILLS-REGISTRY.md) — hybrid command routing map (required by verify + command entrypoints)
- [`adr/0002-shared-component-template-asset-library.md`](adr/0002-shared-component-template-asset-library.md) — accepted Library ADR
- [`handoff/`](handoff/) — session handoff template
- [`validation/GATE-STOP-001-report.md`](validation/GATE-STOP-001-report.md) — Law 16 behavioral coverage report
- [`validation/fixed-pipeline-feasibility-report.md`](validation/fixed-pipeline-feasibility-report.md) — feasibility runner companion
