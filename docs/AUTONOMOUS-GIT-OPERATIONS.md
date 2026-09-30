# Historical Git operations doctrine (v3; superseded 2026-09-30)

> **Superseded on 2026-09-30.** This document preserves its former body for
> historical context; it is not active operating guidance. Follow
> [`docs/runbooks/hosted-delivery-operations.md`](https://github.com/linktrend/IDE-Development/blob/bdf19134a8e0dbd592e84b1fea9d5516b40135b5/docs/runbooks/hosted-delivery-operations.md)
> for the current setup: issue checkpoints feed one combined Phase PR, the
> existing Fast and Verify checks produce exact-head evidence, and promotion
> reuses a matching receipt after independent review. Work is coordinated by
> the designated project orchestrator under Eric through the verified IDE
> route. A Cursor Project is not required; the approved plan groups issues into
> dependency-aware waves.

**Status:** Superseded historical text (ADR 0006). This repository remains the
IDE Development source and is not a consumer install target. The guidance below
is retained as the prior operating model only.

## Model

Each repository has **one cloud orchestrator** (a Cursor Project). The
orchestrator owns the delivery loop end to end:

1. picks an Issue and dispatches it to a worker (Codex CLI on the
   orchestrator's VM, or cursor-002 through the Cursor API);
2. watches dispatched work with a **watchdog timer**
   (`scripts/orchestrator/watchdog.py`) and records every dispatch, check,
   repair and outcome in the run log (`scripts/orchestrator/runlog.py`);
3. packages finished worker branches into PRs into `development`;
4. merges on green Full CI plus one independent exact-head review;
5. promotes `development` → `main`.

There are no scheduled waves and no local coordinator host. The
watchdog timer replaces fixed wake-up times: it notices stalled, failed or
finished workers and moves the loop forward. Any local machine may be off.

## Workers

- Work only on the branch the orchestrator assigns:
  `issue/<PREFIX>-<n>-<slug>`.
- **Checkpoint** = commit + push that branch. Checkpoint often, in small,
  clear commits.
- Run the Issue's fast checks before the final push.
- Never open PRs, never merge, never push `development` or `main`.
- End the final reply with a short lessons note so the orchestrator can
  record it.

A checkpoint is not a review request. The orchestrator decides when a branch
is finished and packages it.

## Packaging and merge

- The orchestrator opens the PR from the worker branch into `development`.
- A PR merges only when **both** hold for the exact PR head SHA:
  - Full CI is green; and
  - one independent review by a **different model family** than the author
    approved that exact head.
- A new push to the PR invalidates the earlier review and CI result for
  merge purposes; both must be repeated on the new head.
- Merges go through GitHub branch protection. Nobody bypasses it.

## Repair ladder

When CI or review fails, the orchestrator dispatches repair work on the same
branch, climbing one rung at a time:

1. Luna/Grok, up to 3 attempts;
2. Sol/Opus, 1 attempt;
3. if the work originally started on Sol/Opus, the other of Sol/Opus,
   1 attempt;
4. flag Carlos with the run-log entry and stop.

Each attempt and its outcome is written to the run log (and the Ledger).
Infrastructure-only failures may be re-run without consuming a rung.

## Promotion

- `development` → `main` is promoted by the orchestrator after the merged
  work is green on `development`.
- Product release/live deploy remains a separate Principal decision where a
  product's own specification requires one.

## Hard stops

- No self-review: the reviewer is never the author or the author's model
  family.
- No prefer-incoming merges. Resolve conflicts deliberately on the named
  branch and re-run checks.
- Never bypass branch protection.
- Workers never open, merge or promote PRs.

## Worktrees

Allowed. Prefer cleanup after merge or abandon. Caps: 12 worktrees / 20 GB.

## External boundary

This doctrine does not itself perform GitHub, host, consumer, release or
billing operations; those happen only through the orchestrator under each
product's approval policy.
