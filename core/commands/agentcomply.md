# Agent Comply

Use in an **ALREADY-OPEN Implementer** session to migrate onto a proper short-lived `issue/*` (or `issue/cleanup-<topic>`) branch and move uncommitted/wrong-branch work safely.

**Workspace orchestrator edge case:** If the chat title contains Orchestrator, Carlos says workspace-wide, or the session spans many repos without one implementer mandate — ask Carlos: **(a)** stay orchestrator-only (inspect + remind; no personal `issue/*` home), or **(b)** pick **one** repo and do normal implementer comply there. Never silently adopt a random open doctrine branch from IDE Development.

Operational summary (Implementer only):

- role gate: Implementer vs Orchestrator
- inspect git status, branch, dirty files, remotes
- ask only if needed for issue id/slug (or allow `issue/cleanup-<topic>`)
- from latest `development`, create the proper branch
- move dirty work safely (stash/checkout/pop or equivalent); never dump onto development/staging/main
- commit only when Carlos wants or the commit is clearly ready; never commit secrets
- push the branch; open/update PR → `development` if commits are ready — otherwise leave ready-to-ship for Ship wave
- tell the session: home is now `issue/…`; no forever `dev/*`
- plain English summary of what was done

For a brand-new clean Implementer session, use `/agentsetup` instead.

Read and execute `.cursor/skills/agentcomply/SKILL.md`.
