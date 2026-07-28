# Agent Setup

Use at the **start of a NEW** session that will code in a repo to bootstrap onto a short-lived `issue/<id>-<slug>` branch from latest `development`.

Simple model: no repo touch → no branch. Touch a repo → `/agentsetup` for that repo. **Workspace Orchestrators** should not invent a fake home repo/branch; open or direct a per-repo Implementer for coding work.

Operational summary:

- role / touch gate: Orchestrator vs Implementer
- detect current repo / multi-root context
- ask Carlos only for missing issue id, short slug, and target repo if ambiguous
- sync to latest `origin/development`
- create and checkout `issue/<id>-<slug>`
- confirm ready; remind Ship/Pull hard stops (no merge, no self-review, no staging/main; Ship = checkpoint only)
- report branch, repo, and next steps in plain English

House rule: one short-lived `issue/*` per governed work package — not forever `dev/*`. Cloud uses `cursor/*`; `dev/*` rare ad-hoc only.

For an already-open dirty or wrong-branch session, use `/agentcomply` instead.

Read and execute `.cursor/skills/agentsetup/SKILL.md`.
