# Issue #72 Lane B — inbound reference audit

**Date:** 2026-08-02
**Method:** `rg` over worktree before `git mv`; re-check after moves excluding archived WP02 tree self-refs.

## Summary

| Candidate | Inbound outside self/archive | Decision |
|-----------|------------------------------|----------|
| Dated `docs/handoff/2026-*.md` | Almost only inside WP02 evidence (moved together); core/session cites **directory pattern** not specific dates | **Moved** → `docs/archive/handoffs/completed/` |
| `docs/handoff/README.md`, `_TEMPLATE.md` | core/session, ARCHIVE-INDEX, skills | **Retained** |
| `docs/handoffs/abe8cc85-post-ssh-messages.md` | No inbound path cites (only self + generic `docs/handoffs/` checklist in LISA-OPENCLAW-FOLLOW-UP) | **Moved** → `docs/archive/handoffs/transcripts/` |
| `docs/runbooks/LANE_F_RESULT.md` | `docs/BUILD-LOG.md` (Lane A); self | **Moved** + pointer stub |
| Completed work packets (4) | BUILD-LOG, OPEN-ISSUES, GITOPS-CONSUMER-ROLLOUT, contracts, managed-core AGENT-COMPLETION, WP04 Related | **Moved** + stubs + non-A repairs / A request file |
| `docs/evidence/wp02/**` | BUILD-LOG, OPEN-ISSUES, GITOPS-CONSUMER-ROLLOUT, archived WP02 packet | **Moved** + `docs/evidence/wp02/README.md` pointer |
| `docs/validation/wp1-evidence/` | BUILD-LOG only (outside self); **no** scripts/tests path hard-deps | **Retained active** |

## Scripts / tests

No matches under `scripts/` or `tests/` for:

- `wp1-evidence` / `WORK-PACKET-1-EVIDENCE`
- `evidence/wp02`
- `work-packets/2026-`
- `LANE_F_RESULT`
- dated `handoff/2026-`

Verify/RC tooling does not require relocating `docs/validation/wp1-evidence/`.

## Lane A surfaces (not edited by Lane B)

See [`lane-a-link-fix-requests.md`](./lane-a-link-fix-requests.md). Stubs keep old paths discoverable.

## Non-A repairs applied

- `docs/contracts/AGENT-COMPLETION.md` — Related → archive wave-2 path
- `core/managed-core/content/doctrine/AGENT-COMPLETION.md` — same
- `docs/archive/work-packets/2026-08-02-work-packet-02-…` — evidence paths → archive
- `docs/archive/runbooks/LANE_F_RESULT.md` — self + WP1 packet paths → archive
- `docs/handoff/README.md` — note pointing completed handoffs to archive
- `docs/ARCHIVE-INDEX.md`, `docs/archive/README.md` — hierarchy + CURRENT-STATUS + WP03 tree equality

## Historical strings inside `docs/archive/evidence/wp02/**`

Left as written at evidence time (audit snapshots). Discoverability via archive indexes + pointer README; rewriting the whole tree would churn historical lane transcripts without operational benefit.
