# Issue #72 — Lane A SUMMARY

**Lane:** A — active-doc truth + launch documentation  
**Model:** Cursor Grok 4.5 High  
**Branch:** `issue/72-pre-launch-ide-development-codebase-cleanup-arch` (tip `e6301fc` at start; branch not changed)  
**Date:** 2026-08-02  
**Commit/push:** none (Lane A deliverable only)

## Verdict

Active operator surfaces now describe **post-WP03 / pre-WP04** truth: WP1–WP03 complete; WP04 consumer rollout prepared / not executed; Issue #72 cleanup in progress. Claude exclusion and system-source vs consumer boundary preserved.

## Files changed (Lane A ownership)

| File | Action |
|---|---|
| `docs/CURRENT-STATUS.md` | **Created** — concise current status / launch-readiness board |
| `docs/work-packets/2026-08-02-work-packet-04-consumer-rollout.md` | **Created** — WP04 PREPARED / NOT EXECUTED |
| `README.md` | Start-here + status truth (WP1–WP03 done; WP04 pending; CURRENT-STATUS + WP04 pointers) |
| `SETUP.md` | Operator entry + WP04 gate; no nested self-install |
| `CHANGELOG.md` | Append Issue #72 Lane A unreleased note |
| `docs/IDE-DEVELOPMENT-INTENT.md` | Status/scope/out-of-scope + doc map |
| `docs/IDE-DEVELOPMENT-TECHNICAL-PRD.md` | Status + architecture bullets + drift table |
| `docs/IDE-DEVELOPMENT-OPERATIONS-MANUAL.md` | Current status table + FAQ WP04 |
| `docs/GITOPS-CONSUMER-ROLLOUT.md` | Post-WP03 / WP04 approval-pending rewrite of status boundaries |
| `docs/BUILD-LOG.md` | Append WP03-001, WP04-001, ISSUE72-001 |
| `docs/OPEN-ISSUES.md` | Append item #17 + obsolete-wording correction pointer |
| `docs/runbooks/release-candidate.md` | Status/boundary wording only |
| `docs/runbooks/rollback.md` | Status/boundary wording only |
| `docs/acceptance/acceptance-matrix.md` | Status/boundary wording only |
| `docs/contracts/MANAGED-CORE-V2.md` | Status line only |
| `docs/contracts/EXTERNAL-STATE-AUDIT.md` | Status line only |
| `docs/contracts/BUGBOT-MENTION-ONLY.md` | Status line only |
| `docs/evidence/issue-72/lane-a/SUMMARY.md` | This file |
| `docs/evidence/issue-72/lane-a/status-claims-before-after.md` | Representative claim fixes |

**Not edited (by design):** `docs/archive/**`, `docs/ARCHIVE-INDEX.md`, `LANE_F_RESULT.md`, code/scripts/claude/codex/.gitignore, GitHub mutations. Did not commit/push/review-ready/PR/Bugbot.

## Key claim updates

1. Stop claiming WP1/WP2/WP3 pending or “WP2 = integration/publication.”
2. State WP1 RC proof complete; WP2 lineage + live readiness complete; WP03 PRs #69/#70/#71 complete with tree `43b1333…`.
3. WP04 = consumer rollout, prepared, approval pending, **not executed**.
4. Issue #72 = pre-launch system-repo cleanup in progress.
5. Claude excluded; IDE Development not a consumer / no nested self-install.
6. Operators get `docs/CURRENT-STATUS.md` instead of only historical logs.

## Residual stale claims (outside Lane A write scope or status-line-only constraint)

See lead return note in this SUMMARY’s companion handoff; detail in `status-claims-before-after.md` § Residual.

Notable leftovers Lane A could not fully rewrite:

- `docs/contracts/MANAGED-CORE-V2.md` body still says “Work Packet 2 handles integration/publication” (status-line-only ownership).
- `docs/contracts/EXTERNAL-STATE-AUDIT.md` body still says consumer apply “WP2 / Principal-gated” (status-line-only).
- Historical append-only entries in `OPEN-ISSUES.md` #15–#16 and early `BUILD-LOG` WP1 rows retain original wording; #17 / CURRENT-STATUS supersede.
- Lane B archive stubs/moves and other-lane edits (`.gitignore`, `ARCHIVE-INDEX`, `AGENTS` managed section consumer framing, etc.) are outside this lane.
