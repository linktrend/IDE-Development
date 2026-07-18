# Archive Index — Retired Development Systems

**Date:** 2026-07-10  
**Purpose:** Name retired systems, explain why they were archived, and state when Stage 1 may read from archive. Active operator docs live outside this index.

---

## Retired systems

**LiNKdev** — GitHub: [linktrend/LiNKdev](https://github.com/linktrend/LiNKdev) (archived). Local snapshot: `/Users/linktrend/Projects/Archive/LiNKdev-legacy-20260710/`. Standalone portable factory (`LiNKdev/` tree, swarm rules, issue dispatch). Tried once; abandoned. Superseded by this repo (`IDE Development`) for human-assisted work, and by the independent **LiNKdeveloper** Program (`/Users/linktrend/Projects/LiNKdeveloper`) for autonomous work.

**LiNKdeveloper Stage 2 Runtime** — GitHub: [linktrend/LiNKdeveloper](https://github.com/linktrend/LiNKdeveloper) (archived). Local snapshot: `/Users/linktrend/Projects/Archive/LiNKdeveloper-Stage2-Runtime-20260710/`. A prior attempt at an autonomous orchestrator runtime (continuous lifecycle, executor routing, work-packet schema), built tightly coupled to the since-abandoned LiNKaios Admin/Plane/GitHub-dispatch governance stack. Not built or wired into this repo. Consulted as read-only concept reference (lifecycle stage names, governance gate shape, work-packet structure) when standing up the new, independent **LiNKdeveloper** Program repo (`/Users/linktrend/Projects/LiNKdeveloper`) — code, infrastructure, and runtime behavior are not copied wholesale; each piece is re-evaluated against current architecture before reuse.

**Factory Operations Common Blueprint** — Local: [`docs/archive/FACTORY-OPERATIONS-BLUEPRINT.md`](archive/FACTORY-OPERATIONS-BLUEPRINT.md) (archived 2026-07-13). Planning-only design for Website/Automation/Content factory operations. Retired because it hardcoded specific product architecture (LiNKbrain, LinkSkills, a named LiNKsites "Website Factory" plane) into what must be a shared, product-agnostic system. Never implemented. A product that needs factory-operations planning must define it in that product's own repository/specification instead (e.g. LiNKsites now has its own governing Program Manual).

**LiNKapps** (`LiNKdev Starter Kit` / `LTM Starter Kit`) — Local snapshot: `/Users/linktrend/Projects/Archive/LiNKapps-legacy-20260715/`. Retired name for the web + mobile starter-kit monorepo. Content vendored into the independent **LiNKdeveloper** Program repo at `/Users/linktrend/Projects/LiNKdeveloper/starter-kits/linkapps-fullstack/` (2026-07-15) before archiving.

**LiNKtrend-System/LiNKdev factory** — Local snapshot: `/Users/linktrend/Projects/Archive/LiNKdev-factory-legacy-20260715/`. The `factory/` tree inside the old `LiNKtrend-System` monorepo's embedded `LiNKdev/` copy (distinct from the standalone `LiNKdev-legacy-20260710` snapshot above). Doctrine (Laws, gate catalog, proof standard, handoff contracts, generic agent-role templates) vendored into `/Users/linktrend/Projects/LiNKdeveloper/doctrine/` (2026-07-15) before archiving; its GitHub Actions dispatch loop was not carried forward.

None of the systems above are installed, extended, or required for day-to-day Stage 1 operation.

---

## When Stage 1 reads from archive

Both **IDE Development** (this repo) and the independent **LiNKdeveloper** Program repo may consult archived Stage 2 **docs only** as read-only reference when mapping Application Factory concepts (lifecycle stage names, governance gates, work-packet shape). Do **not** copy code, infrastructure, or runtime behavior from the Stage 2 archive.

**LiNKdev** archive is **not** a bootstrap or runtime source. Do not install `LiNKdev/` from archive into this repo or treat archive paths as active doctrine.

**Unification build-plan PRD (2026-07-17)** — Archived 2026-07-18 to [`docs/archive/planning/ide-development-linkdeveloper-unification-build-plan-prd.md`](archive/planning/ide-development-linkdeveloper-unification-build-plan-prd.md). Historical implementation plan; Living Document / dual-PRD language superseded by Technical PRD in `core/execution/APPLICATION-PIPELINE.md`. Do not implement from the archive copy.

Historical Stage 1 completion evidence (specs, reports, runbooks from the closure wave) lives under [`docs/archive/`](archive/README.md).

---

## Embedded LiNKdev in product repos — deferred

Embedded `LiNKdev/` folders in product repositories (`LiNKsites`, `LiNKtrend-System`, `LiNKautowork`, `LiNKbot-core`, and similar) are **legacy remnants**, not active factory surfaces.

**Stage 1 posture:** Wire and develop using `.cursor/` + `core/` in **IDE Development**. Confirm no required runtime dependency on `LiNKdev` per `core/checklists/wire-checklist.md`.

**Cleanup:** Selective removal or replacement of embedded `LiNKdev/` in each product repo is **deferred** until Carlos explicitly schedules adoption/cleanup per repo.

**Archive lookup:** Use `/Users/linktrend/Projects/Archive/LiNKdev-legacy-20260710/` only for historical lookup — not for copy-into-product installs.

---

## Active docs (not archived)

- [`IDE-DEVELOPMENT-OPERATIONS-MANUAL.md`](IDE-DEVELOPMENT-OPERATIONS-MANUAL.md) — day-to-day operator instructions
- [`IDE-DEVELOPMENT-STAGE1.md`](IDE-DEVELOPMENT-STAGE1.md) — Application Factory declaration
- [`HYBRID-SKILLS-REGISTRY.md`](HYBRID-SKILLS-REGISTRY.md) — Active hybrid skills registry
