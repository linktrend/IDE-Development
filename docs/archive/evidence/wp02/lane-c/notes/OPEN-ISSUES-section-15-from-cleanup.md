# Recommended OPEN-ISSUES.md merge fragment (after WP01 §14)

Append this **after** the WP01 “## 14. Work Packet 1 …” section (do not replace it).
Source cleanup tip `5cf0991` §14, renumbered to 15.

---

## 15. Reconcile approved stale IDE Development PRs / worktrees — 2026-08-01

Branch `issue/51-reconcile-approved-stale-ide-development-prs-wor` (Issue #51).

**Goal:** Document safe deterministic stale-cleanup controls for IDE Development remote branches, Lisa-local worktrees, open-PR deferrals, and completed-repair inventory dry-run — without auto-closing open PRs or touching preserve-listed issues/PRs/protected branches.

**Authoritative contract:** `docs/contracts/STALE-CLEANUP-CONTROLS.md` (cross-links `LISA-LOCAL-CLEANUP-HANDOFF.md`, `REPAIR-DISPATCHER.md`).

**WP02 note:** Controls restored via cleanup tip `5cf0991` into the canonical lineage; live apply deferred to WP03 per `docs/evidence/wp02/lane-c/cleanup-plan-post-wp03.md`.
