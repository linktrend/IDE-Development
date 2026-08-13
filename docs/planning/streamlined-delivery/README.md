# IDE Development Streamlined Delivery

Status: approved design direction; implementation requires a separately approved goal.

This directory is the execution package for the next IDE Development delivery-system feature. It is intentionally split so a Terra Medium orchestrator can give each GPT-5.6 Luna High Codex CLI executor one bounded packet without relying on conversation history.

## Reading order

1. `IMPLEMENTATION-PLAN.md` — scope, target behavior, waves, dependencies, release strategy, and definition of done.
2. `FROZEN-INTERFACES.md` — shared names, data shapes, state transitions, attempt rules, status contexts, and ownership boundaries that packet executors must not reinterpret.
3. `TERRA-ORCHESTRATOR-RUNBOOK.md` — dispatch, verification, two-attempt takeover, integration, concurrent-feature handling, and current-system override.
4. The executor's assigned file under `packets/` — exact objective, paths, work, prohibitions, tests, and handoff.
5. `TERRA-GOAL.md` — copy-ready goal text for the new Terra Medium task.

## Packet index

| Wave | Packet | Purpose | Parallel within wave |
|---|---|---|---|
| 1 | `W1-P1-CONFIG-STATE.md` | Delivery configuration and lifecycle state | Yes |
| 1 | `W1-P2-RECEIPTS.md` | Exact-content full-suite receipts | Yes |
| 1 | `W1-P3-EXECUTOR-RESOURCES.md` | Isolated execution and Mac resource controls | Yes |
| 2 | `W2-P1-COORDINATOR.md` | Local Mac Mini coordinator | Yes |
| 2 | `W2-P2-PHASE-LIFECYCLE.md` | Many issue branches into one Phase PR | Yes |
| 2 | `W2-P3-PROMOTION.md` | Thin GitHub fallback and receipt-based promotion | Yes |
| 3 | `W3-P1-INTEGRATE-RELEASE.md` | Reconcile, package, canary, PR, promote, release | Only packet in Wave 3 |

## Non-negotiable execution rules

- Codex CLI with the verified GPT-5.6 Luna model at high reasoning; never Cursor CLI.
- Terra Medium is the sole orchestrator and factual verifier.
- Luna gets two attempts per packet. After the second failure, Terra completes only that packet.
- One isolated worktree and `issue/*` branch per packet.
- Only Terra writes to `phase/streamlined-delivery`.
- No packet PRs. One Phase PR is opened at the end.
- Do not touch the separately developed concurrent feature's branches, worktrees, commits, or PR.
- No custom LiNKtrend GitHub App dependency.
- Never bypass failing tests, Bugbot, conflicts, or uncertain content identity.

