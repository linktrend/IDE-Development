# Archive Index — Retired Development Systems

**Date:** 2026-07-10 (Issue #72 Lane B archive hierarchy update 2026-08-02)
**Purpose:** Name retired systems, explain why they were archived, and state when operators may read from archive. Day-to-day authority is **[`docs/CURRENT-STATUS.md`](CURRENT-STATUS.md)** plus the source-of-truth quartet below.

---

## Post-WP03 / pre-WP04 posture (Issue #72)

- **WP03 complete:** PR #69 → `development`, #70 → `staging`, #71 → `main`.
- **Tree equality fact:** `development` / `staging` / `main` share content tree
  `43b1333ae21f43a34c3bdcccb2aac96f3d6e007f` (issue branch tip starts at `e6301fc`; see `docs/evidence/issue-72/lead/integration-plan.md`).
- **WP04** packet is active and prepared / not executed:
  [`docs/work-packets/2026-08-02-work-packet-04-consumer-rollout.md`](work-packets/2026-08-02-work-packet-04-consumer-rollout.md).
- Completed Wave 1 / Wave 2 / WP1 / WP02 packets and WP02 lane evidence are under [`docs/archive/`](archive/README.md) (this cleanup). Production WP1 acceptance evidence stays active at [`docs/validation/wp1-evidence/`](validation/wp1-evidence/).

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

### Issue #72 archive hierarchy (added)

| Tree | Contents |
|------|----------|
| [`archive/handoffs/completed/`](archive/handoffs/completed/) | Dated completed session handoffs |
| [`archive/handoffs/transcripts/`](archive/handoffs/transcripts/) | Historical transcripts (e.g. abe8cc85) |
| [`archive/work-packets/`](archive/work-packets/) | Completed Wave 1 / Wave 2 / WP1 / WP02 packets |
| [`archive/evidence/wp02/`](archive/evidence/wp02/) | WP02 raw lane evidence |
| [`archive/runbooks/LANE_F_RESULT.md`](archive/runbooks/LANE_F_RESULT.md) | WP1 Lane F development result (not an operator runbook) |

Thin pointers remain at several historical active paths so older citations still resolve; prefer archive paths for new writing. Inventory: `docs/evidence/issue-72/lane-b/`.

---

## Embedded LiNKdev in product repos — deferred

Embedded `LiNKdev/` folders in product repositories are **legacy remnants**, not active factory surfaces.

**Posture:** Wire and develop using `.cursor/` + `core/` in **IDE Development**. Confirm no required runtime dependency on `LiNKdev` per `core/checklists/wire-checklist.md`.

**Cleanup:** Selective removal is **deferred** until the Principal explicitly schedules adoption/cleanup per repo.

---

## Active docs (not archived)

### Day-to-day status

- [`CURRENT-STATUS.md`](CURRENT-STATUS.md) — post-WP03 / pre-WP04 operator status (Issue #72 Lane A)

### Source of truth quartet

- [`IDE-DEVELOPMENT-INTENT.md`](IDE-DEVELOPMENT-INTENT.md) — why this repository exists
- [`IDE-DEVELOPMENT-TECHNICAL-PRD.md`](IDE-DEVELOPMENT-TECHNICAL-PRD.md) — exhaustive technical reference
- [`IDE-DEVELOPMENT-OPERATIONS-MANUAL.md`](IDE-DEVELOPMENT-OPERATIONS-MANUAL.md) — Principal handbook
- [`OPEN-ISSUES.md`](OPEN-ISSUES.md) — append-only build log / open items companion

### Still live operational companions

- [`HYBRID-SKILLS-REGISTRY.md`](HYBRID-SKILLS-REGISTRY.md) — hybrid command routing map (required by verify + command entrypoints)
- [`adr/0002-shared-component-template-asset-library.md`](adr/0002-shared-component-template-asset-library.md) — accepted Library ADR
- [`handoff/`](handoff/) — session handoff **README + `_TEMPLATE` only** (completed dated handoffs archived)
- [`work-packets/`](work-packets/) — active/prepared packets (WP04); completed packets archived with stubs
- [`validation/wp1-evidence/`](validation/wp1-evidence/) — WP1 production acceptance / RC evidence (retained active)
- [`validation/GATE-STOP-001-report.md`](validation/GATE-STOP-001-report.md) — Law 16 behavioral coverage report
- [`validation/fixed-pipeline-feasibility-report.md`](validation/fixed-pipeline-feasibility-report.md) — feasibility runner companion
- [`runbooks/release-candidate.md`](runbooks/release-candidate.md) · [`runbooks/rollback.md`](runbooks/rollback.md) — operator runbooks
