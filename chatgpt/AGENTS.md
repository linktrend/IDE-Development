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
| Mark review-ready | Yes, when finished — `scripts/mark-review-ready.sh` + `scripts/gitops/completion_gate.py review-ready` |
| Merge / promote | **No** |

## Repair

GitHub records durable repair tasks. Lisa ACP Repair Dispatcher dispatches Cursor ACP. Max 3 attempts. No prefer-incoming. Immediate failure types do not auto-repair. GitHub never spawns Cursor.
