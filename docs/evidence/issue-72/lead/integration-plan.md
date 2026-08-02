# Issue #72 lead integration plan

**Lead model:** Cursor Grok 4.5 High
**Branch:** `issue/72-pre-launch-ide-development-codebase-cleanup-arch`
**Base tip:** `e6301fc` (WP03 #69 on development)
**Tree equality:** development/staging/main → `43b1333ae21f43a34c3bdcccb2aac96f3d6e007f`

## Parallel lanes (cursor-grok-4.5-high)

| Lane | Scope | Evidence |
|------|--------|----------|
| A | Active docs + CURRENT-STATUS + WP04 packet | `docs/evidence/issue-72/lane-a/` |
| B | Archive moves + indexes + link repair | `docs/evidence/issue-72/lane-b/` |
| C | Dead-code / platform entrypoints | `docs/evidence/issue-72/lane-c/` |
| D | gitignore + temp hygiene | `docs/evidence/issue-72/lane-d/` |
| E | GitHub hygiene disposition (plan only) | `docs/evidence/issue-72/lane-e/` |
| F | Independent review after integration | `docs/evidence/issue-72/lane-f/` |

## Integration order

1. Collect A–E summaries; resolve ownership conflicts (A content wins on SOT; B move-map wins on paths).
2. Apply any `lane-a-link-fix-requests.md` patches.
3. Confirm WP04 packet exists and is marked prepared/not-executed.
4. Confirm Claude exclusion + no-consumer-mutation preserved.
5. Run validation suite (see validation-checklist.md).
6. Spawn Lane F independent Grok High reviews.
7. Repair ≤3 cycles.
8. Conventional commits + push checkpoint only (no review-ready/PR/Bugbot).

## Hard stops

No consumer mutation; no credential/settings/Bugbot/ruleset/protection changes; no GitHub cleanup apply; no stash modification; no review-ready.
