# Agent Completion Contract

**Status:** Active  
**Date:** 2026-07-30  
**Owner:** IDE Development (GitOps)

## Purpose

Define how Implementers finish a work session without opening PRs or falsely claiming review-ready.

## Modes (`scripts/gitops/completion_gate.py`)

| Mode | Meaning | Exit |
|---|---|---|
| `checkpoint` | Commit+push save; work unfinished | `0` → state `checkpointed_unfinished` |
| `review-ready` | Claim finished work is packager-eligible | `0` only when all gates pass; else `78` |
| `blocked` | Structured blocker JSON written | `2` |
| `status` | Report current completion state | `0` |

Other failures: exit `1` (`failed`).

## States

- `checkpointed_unfinished`
- `review_ready`
- `blocked`
- `failed`

## `review_ready` requirements (all required)

1. Evidence declared (`--evidence` or `COMPLETION_EVIDENCE`)
2. Tests declared passed (`--tests-ok` or `COMPLETION_TESTS_OK=1`)
3. Clean working tree
4. `HEAD == origin/<branch>` tip
5. Successful GitHub commit status **`Linktrend Review Ready`** on that exact SHA (`scripts/gitops/readiness_status.py`)

## Hard rules

- Implementers **never** open or update PRs. Review Packager opens PRs.
- Ship waves = checkpoint only (no Bugbot, no review-ready unless truly finished).
- Incomplete review-ready claims must fail closed (exit `78`), not soft-succeed.

## Related

- `docs/AUTONOMOUS-GIT-OPERATIONS.md`
- `core/github/REVIEW-READY.md`
- `docs/contracts/REPAIR-DISPATCHER.md`
