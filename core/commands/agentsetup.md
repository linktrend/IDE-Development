# Agent Setup

Use at the **start of a NEW** session that will code in a repo to bootstrap onto a short-lived `issue/<id>-<slug>` branch from latest `development`.

Simple model: no repo touch → no branch. Touch a repo → `/agentsetup` for that repo. **Workspace Orchestrators** should not invent a fake home repo/branch; open or direct a per-repo Implementer for coding work.

Operational summary:

- role / touch gate: Orchestrator vs Implementer
- detect current repo / multi-root context
- ask Carlos only for missing **task description** and target repo if ambiguous — **never** ask for issue id/slug
- run `scripts/gitops/create_issue_branch.py` (creates/reuses GitHub issue + `issue/<n>-<slug>` from `origin/development`; prefer worktree when dirty)
- confirm ready; remind Ship/Pull hard stops (no implementer PR, no merge, no self-review, no staging/main; Ship = checkpoint only)
- when finished later: `scripts/gitops/completion_gate.py` + review-ready; Packager opens the PR
- report branch, issue, repo, and next steps in plain English

House rule: one short-lived `issue/*` per governed work package — not forever `dev/*`. Cloud uses `cursor/*`; `dev/*` rare ad-hoc only.

For an already-open dirty or wrong-branch session, use `/agentcomply` instead.

Read and execute `.cursor/skills/agentsetup/SKILL.md`.
