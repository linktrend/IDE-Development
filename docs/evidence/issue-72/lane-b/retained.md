# Issue #72 Lane B — retained active

Items kept **outside** `docs/archive/` on purpose.

| Path | Reason |
|------|--------|
| `docs/handoff/README.md` | Hard keep-active; core/session and skills cite `docs/handoff/` |
| `docs/handoff/_TEMPLATE.md` | Hard keep-active; session handoff template |
| `docs/validation/wp1-evidence/**` | Production acceptance / RC evidence; BUILD-LOG cites path; no complete non-A reference rewrite required; relocating without Lane A BUILD-LOG + acceptance updates would hide proof |
| `docs/work-packets/2026-08-02-work-packet-04-consumer-rollout.md` | Lane A WP04 prepared/not-executed; must stay active |
| `docs/work-packets/README.md` | Active index for WP04 + archive map |
| `docs/work-packets/2026-08-01-*.md`, `…work-packet-1…`, `…work-packet-02…` (stubs only) | Thin relocate pointers so WP04 Related + unrepaired SOT cites still resolve |
| `docs/evidence/wp02/README.md` | Stable pointer to `docs/archive/evidence/wp02/` |
| `docs/runbooks/LANE_F_RESULT.md` (stub only) | Stable pointer; active operator runbooks remain RC + rollback |
| `docs/runbooks/release-candidate.md`, `rollback.md` | Lane A / operator runbooks — not moved |
| `docs/handoffs/README.md` | Dir retained for future ad-hoc notes; transcript archived |
| `docs/CURRENT-STATUS.md` | Lane A active status (present at Lane B close) |

## Explicitly not retained as operational content

Completed dated handoffs, abe8cc85 transcript, LANE_F_RESULT body, completed work-packet bodies, and WP02 evidence tree — all under `docs/archive/**`.
