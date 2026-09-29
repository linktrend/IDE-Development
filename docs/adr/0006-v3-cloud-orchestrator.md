# ADR 0006: v3 Cloud Orchestrator

**Status:** Accepted (2026-09-29)
**Supersedes:** ADR 0003 (autonomous ship/pull/promote), ADR 0005 (streamlined delivery coordinator)
**Related:** `docs/AUTONOMOUS-GIT-OPERATIONS.md`, `.cursor/rules/02-autonomous-ship-pull.mdc`

## Context

v2 ran delivery from a Mac Mini. A local coordinator daemon (`host/coordinator/`)
queued and executed work; a scheduler ("Lisa", OpenClaw cron) woke shipper and
puller agents at fixed Ship 05 / Pull 07 / Ship 16 / Pull 18 waves; a heartbeat
controller, a portfolio control loop and a Lisa repair dispatcher kept state in
local stores and GitHub repair issues. On top of that sat a heavy gate stack
(completion gate, Review Ready publisher, Phase Packager, delivery controller,
receipts and receipt-based promotion).

That design made delivery depend on one always-on machine, fixed wake-up
times, and many interlocking scripts. Failures in any of them stalled the loop,
and the gates added cost without adding independent judgement.

## Decision

Each repository has **one cloud orchestrator** (a Cursor Project) that owns the
delivery loop:

- It dispatches Issues to workers: Codex CLI on its VM, or cursor-002 through
  the Cursor API.
- Workers commit and push their `issue/<PREFIX>-<n>-<slug>` branch often
  ("checkpoint" = commit + push), run the Issue's fast checks before the final
  push, never open PRs, never merge, never push `development`/`main`, and end
  with a lessons note.
- A **watchdog timer** (`scripts/orchestrator/watchdog.py`) replaces scheduled
  waves; every dispatch, check, repair and outcome is written to the run log
  (`scripts/orchestrator/runlog.py`).
- The orchestrator packages finished branches into PRs into `development` and
  merges only on green Full CI plus one independent exact-head review by a
  different model family than the author.
- Repair ladder: Luna/Grok ×3 → Sol/Opus ×1 → (if started on Sol/Opus) the
  other ×1 → flag Carlos.
- The orchestrator promotes `development` → `main`.
- Hard stops: no self-review, no prefer-incoming merges, never bypass branch
  protection.

## Consequences

- The Mac Mini can be off; nothing in delivery depends on it.
- Ship/pull waves, the local coordinator, heartbeat controller, portfolio
  control loop and repair dispatcher are removed, with their doctrine and
  tests.
- Liveness is the watchdog's job; repair history lives in the run log and
  Ledger instead of durable GitHub repair issues.
- Removing `staging` from the branch flow is handled separately.
- Consumers still carrying the removed managed files need a package upgrade
  that deletes them; that upgrade is a separate change.
