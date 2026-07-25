# Agent Setup

Use at the **start of a NEW** session to bootstrap onto a short-lived `issue/<id>-<slug>` branch from latest `development` for the **repo being touched**.

Simple model: no repo touch → no branch. Touch a repo → `/agentsetup` for that repo. Multi-root ambiguity → ask which repo. Never silently adopt an unrelated open PR branch — the branch must match this work package.

Operational summary:

- detect current repo / multi-root context
- ask Carlos only for missing issue id, short slug, and target repo if ambiguous
- sync to latest `origin/development`
- create and checkout `issue/<id>-<slug>` for this work package
- confirm ready; remind Ship/Pull hard stops (no merge, no self-review, no staging/main)
- report branch, repo, and next steps in plain English

House rule: one short-lived `issue/*` per governed work package — not forever `dev/*`. Cloud uses `cursor/*`; `dev/*` rare ad-hoc only.

For an already-open dirty or wrong-branch session, use `/agentcomply` instead.

Read and execute `.cursor/skills/agentsetup/SKILL.md`.
