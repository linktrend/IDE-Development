# ChatGPT / Work Agent — IDE Development GitOps

This file is the ChatGPT entrypoint. **Do not assume `.cursor` is read.**

## Authority

- `docs/AUTONOMOUS-GIT-OPERATIONS.md`
- `docs/contracts/AGENT-COMPLETION.md`
- `docs/contracts/REPAIR-DISPATCHER.md`
- `core/commands/agentsetup.md`, `core/commands/agentcomply.md`

## Branching

- Integration branch: `development`
- Work branches: `issue/<id>-<slug>` via `scripts/gitops/create_issue_branch.py` (never invent issue IDs; never ask the Principal for id/slug)
- Never commit to `development` / `staging` / `main`

## Completion

| Action | Allowed |
|---|---|
| Checkpoint (commit + push) | Yes |
| Open / update PR | **No** — Review Packager only |
| Mark review-ready | Yes, when finished — run appropriate tests/checks, auto-repair ordinary failures with at most 3 bounded repair cycles, write machine-readable evidence with `scripts/gitops/completion_gate.py write-evidence`, then call `scripts/gitops/completion_gate.py review-ready` |
| Merge / promote | **No** |

`review-ready` is the authoritative fail-closed gate that publishes **Linktrend Review Ready**. Do not call `scripts/mark-review-ready.sh` as a pre-gate publisher; it is only a compatibility wrapper that requires evidence and delegates to the gate. If validation or repair cannot complete, call `scripts/gitops/completion_gate.py blocked` so `.linktrend/completion-blocker.json` records the durable blocker and the branch stays ineligible.

## Repair

GitHub records durable repair tasks. Lisa ACP Repair Dispatcher dispatches Cursor ACP. Max 3 attempts. No prefer-incoming. Immediate failure types do not auto-repair. GitHub never spawns Cursor.
