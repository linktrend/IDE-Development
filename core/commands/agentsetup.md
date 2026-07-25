# Agent Setup

Use at the **start of a NEW Implementer** session to bootstrap onto a short-lived `issue/<id>-<slug>` branch from latest `development`.

**Not for workspace Orchestrators.** Do not invent a fake home repo/branch for a multi-repo coordinator. Orchestrators keep coordinating; open or direct a per-repo Implementer and run `/agentsetup` there for coding work.

Operational summary (Implementer only):

- role gate: Implementer vs Orchestrator
- detect current repo / multi-root context
- ask Carlos only for missing issue id, short slug, and target repo if ambiguous
- sync to latest `origin/development`
- create and checkout `issue/<id>-<slug>`
- confirm ready; remind Ship/Pull hard stops (no merge, no self-review, no staging/main)
- report branch, repo, and next steps in plain English

House rule: one short-lived `issue/*` per governed Implementer work — not forever `dev/*`. Cloud uses `cursor/*`; `dev/*` rare ad-hoc only.

For an already-open dirty or wrong-branch Implementer session, use `/agentcomply` instead.

Read and execute `.cursor/skills/agentsetup/SKILL.md`.
