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
| Open / update PR | **No** (the v2 Review Packager is retired in v3 (IDE-22); see the v3 plan) |
| Finish | Yes — run appropriate tests/checks and auto-repair ordinary failures with at most 3 bounded repair cycles |
| Merge / promote | **No** |

The v2 completion gate and its readiness status are retired in v3 (IDE-22); see the v3 plan.

## Repair

GitHub records durable repair tasks. Lisa ACP Repair Dispatcher dispatches Cursor ACP. Max 3 attempts. No prefer-incoming. Immediate failure types do not auto-repair. GitHub never spawns Cursor.
