# Archive Index — Retired Development Systems

**Date:** 2026-07-10  
**Purpose:** Name retired systems, explain why they were archived, and state when Stage 1 may read from archive. Active operator docs live outside this index.

---

## Retired systems

| System | GitHub (archived) | Local archive snapshot | Why archived |
|---|---|---|---|
| **LiNKdev** | [linktrend/LiNKdev](https://github.com/linktrend/LiNKdev) | `/Users/linktrend/Projects/Archive/LiNKdev-legacy-20260710/` | Standalone portable factory (`LiNKdev/` tree, swarm rules, issue dispatch). Tried once; abandoned. Superseded by **LiNKdeveloper Stage 1** (this repo: `IDE Development`). |
| **LiNKdeveloper Stage 2** | [linktrend/LiNKdeveloper](https://github.com/linktrend/LiNKdeveloper) | `/Users/linktrend/Projects/Archive/LiNKdeveloper-Stage2-Runtime-20260710/` | Autonomous orchestrator runtime (continuous lifecycle, executor routing, work-packet schema). Not built or wired during Stage 1. Future work; not an active dependency. |

Neither system is installed, extended, or required for day-to-day Stage 1 operation.

---

## When Stage 1 reads from archive

**LiNKdeveloper Stage 1** (`IDE Development`) may consult archived Stage 2 **docs only** as read-only reference when mapping Application Factory concepts (lifecycle stage names, governance gates, work-packet shape). Do **not** copy code, infrastructure, or runtime behavior from the Stage 2 archive.

**LiNKdev** archive is **not** a bootstrap or runtime source. Do not install `LiNKdev/` from archive into this repo or treat archive paths as active doctrine.

Historical Stage 1 completion evidence (specs, reports, runbooks from the closure wave) lives under [`docs/archive/`](archive/README.md).

---

## Embedded LiNKdev in product repos — deferred

Embedded `LiNKdev/` folders in product repositories (`LiNKsites`, `LiNKtrend-System`, `LiNKautowork`, `LiNKbot-core`, and similar) are **legacy remnants**, not active factory surfaces.

| Posture | Detail |
|---|---|
| **Stage 1** | Wire and develop using `.cursor/` + `core/` in **IDE Development**. Confirm no required runtime dependency on `LiNKdev` per `core/checklists/wire-checklist.md`. |
| **Cleanup** | Selective removal or replacement of embedded `LiNKdev/` in each product repo is **deferred** until Carlos explicitly schedules adoption/cleanup per repo. |
| **Archive** | Use `/Users/linktrend/Projects/Archive/LiNKdev-legacy-20260710/` only for historical lookup — not for copy-into-product installs. |

---

## Active docs (not archived)

| Document | Role |
|---|---|
| [`LINKDEVELOPER-OPERATIONS-MANUAL.md`](LINKDEVELOPER-OPERATIONS-MANUAL.md) | Day-to-day operator instructions |
| [`LINKDEVELOPER-STAGE1.md`](LINKDEVELOPER-STAGE1.md) | Stage 1 declaration |
| [`LINKDEVELOPER-STAGE1-CLOSURE.md`](LINKDEVELOPER-STAGE1-CLOSURE.md) | Closure summary and deliverable index |
| [`FACTORY-OPERATIONS-BLUEPRINT.md`](FACTORY-OPERATIONS-BLUEPRINT.md) | Factory operations common blueprint (planning) |
| [`HYBRID-SKILLS-REGISTRY.md`](HYBRID-SKILLS-REGISTRY.md) | Active hybrid skills registry |

Moved guide: [`LINKDEVELOPER-WORKSPACE-OPERATOR-GUIDE.md`](LINKDEVELOPER-WORKSPACE-OPERATOR-GUIDE.md) redirects to the operations manual.
