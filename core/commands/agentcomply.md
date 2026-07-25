# Agent Comply

Use in an **ALREADY-OPEN** session to migrate onto a proper short-lived `issue/*` (or `issue/cleanup-<topic>`) branch for the **repo being touched**, and move uncommitted/wrong-branch work safely.

Simple model: no repo touch → no branch. Touch a repo → `/agentcomply` for that repo. Multi-root ambiguity → ask which repo. Never silently adopt an unrelated open PR branch — the branch must match this work package.

Operational summary:

- inspect git status, branch, dirty files, remotes
- ask only if needed for issue id/slug (or allow `issue/cleanup-<topic>`) and target repo if multi-root / ambiguous
- from latest `development`, create the proper branch for this work package
- move dirty work safely (stash/checkout/pop or equivalent); never dump onto development/staging/main
- commit only when Carlos wants or the commit is clearly ready; never commit secrets
- push the branch; open/update PR → `development` if commits are ready — otherwise leave ready-to-ship for Ship wave
- tell the session: this work package lives on `issue/…`; no forever `dev/*`
- plain English summary of what was done

For a brand-new clean session, use `/agentsetup` instead.

Read and execute `.cursor/skills/agentcomply/SKILL.md`.
