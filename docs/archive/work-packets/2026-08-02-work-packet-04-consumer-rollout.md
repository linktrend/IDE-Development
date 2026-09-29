# Work Packet 04 — consumer rollout

**Status:** PREPARED / **NOT EXECUTED**
**Date:** 2026-08-02
**Authorization:** **Principal approval still pending.** This packet does **not** authorize any consumer repository mutation until Carlos explicitly approves execution.
**Owner (when approved):** Cursor Grok 4.5 High lead + subagents as assigned; Claude Code excluded
**SOT:** [`docs/GITOPS-CONSUMER-ROLLOUT.md`](../GITOPS-CONSUMER-ROLLOUT.md) · [`docs/CURRENT-STATUS.md`](../CURRENT-STATUS.md) · [`docs/runbooks/release-candidate.md`](../runbooks/release-candidate.md) · [`docs/runbooks/rollback.md`](../runbooks/rollback.md)
**Package:** portable managed-core **v2.1.0**
**Prerequisite:** the final pre-rollout reconciliation is merged and promoted; `origin/development`, `origin/staging`, `origin/main`, and the clean local `main` checkout are content-identical; no open PR or unintegrated checkpoint remains.

---

## Outcome (when approved)

Execute consumer rollout of the portable managed core in the **locked sequential order**, one repository at a time, with a read-only drift/plan report and **separate Principal approval per consumer** before each mutating `install` / `update`.

## Explicit non-authorization (now)

Until Principal approval of **this packet’s execution**:

- Do **not** run installer `install` / `update` against any real consumer listed below
- Do **not** apply live GitHub protections, secrets, variables, App, or Bugbot settings on consumers
- Do **not** treat Issue #72 cleanup work as rollout authorization
- Do **not** nest-install `.ide-development/` into **IDE Development** (system source / self-verification only)
- Do **not** add Claude Code entrypoints or claim Claude support

Preparing this document is documentation-only. It is not a go signal.

---

## Scope

### In scope (after approval)

1. Follow locked order exactly (one repo at a time):

   | # | Repo |
   |---|---|
   | 1 | `openclaw_prime` |
   | 2 | `LiNKplatform` |
   | 3 | `LiNKskills` |
   | 4 | `LiNKbrain` |
   | 5 | `LiNKsites` |
   | 6 | `LiNKdeveloper` |
   | 7 | `LiNKlibraries` |
   | 8 | `LiNKautowork` |
   | 9 | `LiNKtrading-codebase` |

2. Per consumer: drift → plan dry-run → Principal approval for that repo → `install` or `update` → `verify` / `version`; use `rollback` if needed ([`docs/runbooks/rollback.md`](../runbooks/rollback.md)).
3. Prefer install from system source or extracted RC (`--package`) per [`docs/runbooks/release-candidate.md`](../runbooks/release-candidate.md).
4. Preserve consumer-owned content outside managed ownership/markers; fail closed on unknown conflicts.
5. Keep credentials and live settings external (never package secrets into managed core / RC archives).

### Out of scope

- Nested self-install into IDE Development
- Claude Code support
- Automatic tag / GitHub Release publication unless separately approved
- Skipping the locked order or batch-mutating multiple consumers without per-repo approval
- Treating Ship/Pull processing of IDE Development as an install authorization

---

## Preconditions already met (system side)

| Precondition | Evidence / claim |
|---|---|
| WP1 RC proof | Issue #67 — disposable/RC proof complete |
| WP2 lineage + live readiness | Issue #68 — COMPLETE for stated scope (checkpoint) |
| WP03 integrate + promote | PR #69 → development, #70 → staging, #71 → main; tree equality `43b1333…` |
| v2.1 phase delivery | Issue #81; PR #82 → development, #85 → staging, #86 → main |
| Pre-rollout reconciliation | Closed/superseded work reconciled; stale branches/worktrees removed; protected lines and local verified equal before execution |
| Claude exclusion | Remains in force |
| System-source boundary | IDE Development absent from consumer table |

Issue #72 cleanup is complete. That completion does **not** change the WP04 approval gate.

---

## Approval gate

| Gate | Required |
|---|---|
| Principal explicit approval to **execute** WP04 | **Pending** |
| Per-consumer Principal approval before each mutating install/update | Required when execution proceeds |
| Drift/plan report before each mutation | Required |

Until the first gate clears, agents must leave real consumers untouched.

---

## Related

- [`docs/CURRENT-STATUS.md`](../CURRENT-STATUS.md)
- [`docs/GITOPS-CONSUMER-ROLLOUT.md`](../GITOPS-CONSUMER-ROLLOUT.md)
- [`docs/acceptance/acceptance-matrix.md`](../acceptance/acceptance-matrix.md) (WP1 proof matrix; historical)
- [`docs/archive/work-packets/2026-08-02-work-packet-1-production-readiness.md`](../archive/work-packets/2026-08-02-work-packet-1-production-readiness.md) (historical WP1; stub may remain under `docs/work-packets/`)
- [`docs/archive/work-packets/2026-08-02-work-packet-02-integration-lineage-and-live-readiness.md`](../archive/work-packets/2026-08-02-work-packet-02-integration-lineage-and-live-readiness.md) (historical WP02; stub may remain under `docs/work-packets/`)
