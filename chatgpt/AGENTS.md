# ChatGPT / Work Agent — IDE Development

This file is the ChatGPT entrypoint for a **worker**. **Do not assume `.cursor` is read.**

## Authority

- `docs/CURRENT-STATUS.md`
- `docs/IDE-DEVELOPMENT-OPERATIONS-MANUAL.md`
- `docs/runbooks/project-setup-checklist.md`

## Branching

- Long-lived branches: `development` and `main` only.
- Work branches: `issue/<PREFIX>-<n>-<slug>`.
- Never commit directly to `development` or `main`.

## What a worker may do

| Action | Allowed |
|---|---|
| Commit and push on the issue branch | Yes — small commits, push often |
| Run the fast checks named in the Issue | Yes — required before the final push |
| Open or update a pull request | **No** — the orchestrator packages branches |
| Merge or promote | **No** |
| Removed: Review Ready | Workers do not mark a branch review-ready |

Everyday model route is Luna High (Codex on the orchestrator VM) or Grok 4.7 Medium (cursor-002). Hard route is Sol Medium or Opus 5.5 Medium. Codex is used while more than 25% of the allowance remains in every reported window.

If checks fail, follow the repair ladder in the operations manual. Do not invent a side process.

## Close-out

End the final reply with a short lessons note: what was unclear, what the next worker should not repeat.
