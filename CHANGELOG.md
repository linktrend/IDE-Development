# Changelog

## Unreleased — PKT-07 managed package integration (phase/v2.5)

- Materialized accepted `core/link-integrations/` provider runtime under `core/managed-core/platforms/providers/` and `.ide-development/providers/` manifest destinations
- Removed IDE-owned workflow `SKILL.md` implementations after PKT-04 dual-app proof; retained bootstrap adapters (`agentsetup`, `agentcomply`) and non-skill loaders only
- Extended migration catalog with exact v2.4 workflow skill supersessions; archived rollback bytes under `docs/archive/v24-skill-rollback/`
- Regenerated `core/managed-core/MANIFEST.json` once at package identity **2.4.0** (v2.5.0 reserved for final integration)
- Preserved atomic v2.4 rollback identity in skills lock (`004bd5f…` / `6c55220…`)

## v2.1.0 — 2026-08-03 (Issue #81)

- Added governed phase-delivery modes, schemas, readiness reporting, and fail-closed review-ready dispatch
- Promoted the release through PR #82 / #85 / #86
- Reconciled pre-rollout status truth and cleared preserve entries for closed work

## Unreleased — 2026-08-02 (Issue #72 Lane A)

- Post-WP03 / pre-WP04 documentation truth: WP1–WP03 complete; WP04 consumer rollout prepared / not executed; Issue #72 cleanup in progress
- Added `docs/CURRENT-STATUS.md` and `docs/work-packets/2026-08-02-work-packet-04-consumer-rollout.md`
- Updated Start-here surfaces (README, SETUP, Intent, Technical PRD, Operations Manual, GITOPS-CONSUMER-ROLLOUT)

## Unreleased — 2026-07-19

- Documentation source-of-truth cleanup: Intent, Technical PRD, rewritten Operations Manual, and `docs/OPEN-ISSUES.md`; superseded Stage 1 declaration / unification planning / workspace-report / unification validation docs archived under `docs/archive/`

## Unreleased — 2026-07-18

- Aligned the fixed six-Module application pipeline with LiNKdeveloper process improvements that apply inside Cursor:
  - Module 1: four hard-gated interview checkpoints; Intent + single Technical PRD (retired Living Document / dual PRD)
  - Module 2: Technical Design + independent review; Starter Kit optional (never mandatory)
  - Module 3: branch-per-Issue / PR / CI discipline documented
  - Module 4: lightweight test-planning and coverage-trace preflights; Technical PRD criteria
  - Session-scoped gate repair (default budget 3) + severity fields
  - Principal Module 1 and Module 6 pre-deploy gates retained (no LAW-06 auto-promotion)
- Pipeline state schemaVersion 2 (`technicalPrdPath` / `technicalPrdAcceptanceCriteria` / `confirmedInterviewCheckpoints`)
- New templates: `TECHNICAL-PRD.md`, `TECHNICAL-DESIGN.md`
- Validator mechanically enforces Module 1 checkpoints + Technical PRD review, Module 2 Technical Design review, and repair-budget ceiling
- Archived superseded unification build-plan PRD under `docs/archive/planning/`

## v1.2

- introduced the workspace adoption lifecycle as a one-time operational capability for wiring existing multi-repository workspaces into the shared IDE Development runtime
- added the canonical workspace layer:
  - `core/workspace/INDEX.yaml`
  - `core/workspace/WORKSPACE-ADOPTION.md`
  - `core/workspace/WORKSPACE-DISCOVERY.md`
  - `core/workspace/REPO-WIRING.md`
  - `core/workspace/LEGACY-CLEANUP.md`
  - `core/workspace/WORKSPACE-REPORT.md`
- preserved the existing packaging model:
  - `core/` remains canonical knowledge
  - `.cursor/` remains the compatibility runtime surface
- added workspace adoption routing to bootstrap and root adapter documentation without introducing a new command family
- clarified the separation between one-time workspace adoption and daily session lifecycle operations
- released version `v1.2`

## v1.0.2

- introduced the session lifecycle capability for natural-language resume and close-out behavior
- added the canonical session layer and handoff template
- wired session behavior into bootstrap, workflow, and compatibility routing without adding a new command family

## v1.0.1

- converted the repository from `.cursor` source-of-truth packaging to `core` canonical storage plus `.cursor` compatibility runtime surface
- added Codex and Claude consumption entrypoints
- preserved backward compatibility through `.cursor` adapter links

## v1.0.0

- established the `.cursor` repository as the source of truth for the global AI development core
- finalized the canonical doctrine, artifact, agent, command, runtime, workflow, contract, state, system, bootstrap, and example layers
- added optional discovery and interview support for greenfield and ambiguous work
- completed supervised real-world validation in disposable consumer repositories
- confirmed dependency handling, safe concurrency, issue completion, module review, and module integration in practice
- released the stable v1.0 command surface:
  - `plan-program`
  - `plan-module`
  - `complete-module`
  - `execute-issue`
  - `review-issue`
  - `integrate-issue`
- deferred remaining usability and packaging improvements to later releases
