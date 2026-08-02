# Archive — superseded by the current source-of-truth documents

Everything under `docs/archive/` is retained for history but is **no longer authoritative** for how IDE Development works today. Some of it (Stage 2/3 OpenClaw-as-this-repo roadmap, Living Document / dual-PRD language, “hybrid skills are stubs,” `verify-stage1.sh` naming) is factually stale relative to the filesystem.

**Day-to-day status (2026-08-02, post-WP03 / pre-WP04):** [`../CURRENT-STATUS.md`](../CURRENT-STATUS.md)

**Source of truth quartet:**

- [`../IDE-DEVELOPMENT-INTENT.md`](../IDE-DEVELOPMENT-INTENT.md) — why IDE Development exists, scope, and what "done" means.
- [`../IDE-DEVELOPMENT-TECHNICAL-PRD.md`](../IDE-DEVELOPMENT-TECHNICAL-PRD.md) — exhaustive technical reference, including where archived documents have drifted from the real filesystem.
- [`../IDE-DEVELOPMENT-OPERATIONS-MANUAL.md`](../IDE-DEVELOPMENT-OPERATIONS-MANUAL.md) — plain-English handbook for the Principal.
- [`../OPEN-ISSUES.md`](../OPEN-ISSUES.md) — append-only engineering build log and open/deferred items.
- [`../HYBRID-SKILLS-REGISTRY.md`](../HYBRID-SKILLS-REGISTRY.md) — live hybrid command map (not archived; still cited by verify + commands).
- [`../../core/execution/`](../../core/execution/) — still live/operative doctrine (Laws, runtime model, application pipeline). **Not archived.**

For retired *system* names (LiNKdev, Stage 2 Runtime archive paths, Factory Operations Blueprint, etc.), see [`../ARCHIVE-INDEX.md`](../ARCHIVE-INDEX.md).

## WP03 tree equality (Issue #72)

Protected lines `development` / `staging` / `main` share content tree
`43b1333ae21f43a34c3bdcccb2aac96f3d6e007f` after WP03 (PR #69 → development, #70 → staging, #71 → main). WP04 consumer rollout is prepared / not executed under [`../work-packets/`](../work-packets/).

## What's here

**Issue #72 hierarchy (archived operational history)**

- `handoffs/completed/` — dated session handoffs formerly under `docs/handoff/`
- `handoffs/transcripts/` — historical transcript exports
- `work-packets/` — completed Wave 1 / Wave 2 / WP1 / WP02 packets
- `evidence/wp02/` — WP02 raw lane evidence (pointer: `docs/evidence/wp02/README.md`)
- `runbooks/LANE_F_RESULT.md` — WP1 Lane F development result (not an operator runbook)

**Stage 1 specs and reports (2026-07-10 closure wave)**

- `LINKDEVELOPER-STAGE1A-SPEC.md`, `*-REPORT.md`, `*-TEST-RUNBOOK.md`, `*-CLOSURE.md`, `*-HYBRID-REPORT.md`, `*-VERIFICATION-REPORT.md`
- `IDE-DEVELOPMENT-STAGE1.md` — short Application Factory declaration superseded by Intent + Operations Manual (archived 2026-07-19)

**Consolidation and policy**

- `LINKDEVELOPER-DOC-CONSOLIDATION-REPORT.md`, `SKILLS-SUNSET-REPORT.md`, `CORE-CURSOR-EQUIVALENCE-REPORT.md`, `COPY-FIRST-UI-RESKIN-POLICY.md`

**Product / factory notes**

- `LINKSITES-FACTORY-SETUP-REPORT.md`
- `FACTORY-OPERATIONS-BLUEPRINT.md` — retired product-coupled factory-ops planning

**Core design reports / pilots**

- `core-reports/` — historical core design and migration passes
- `pilots/hybrid-smoke/` — hybrid smoke test artifacts

**Planning / validation / workspace reports (archived 2026-07-19)**

- `planning/` — unification build-plan PRD copies (do not implement from these; see `core/execution/APPLICATION-PIPELINE.md`)
- `validation/` — point-in-time unification E2E / baseline / cross-system reports (GATE-STOP, feasibility, and **WP1 `docs/validation/wp1-evidence/`** remain live under `docs/validation/` because doctrine/scripts/acceptance cite them)
- `workspace-reports/` — point-in-time wire reports

If something here conflicts with CURRENT-STATUS, the Intent, Technical PRD, or Operations Manual, **those documents win.**

Automated re-check for active surfaces: `scripts/verify-ide-development.sh` (repo root).
