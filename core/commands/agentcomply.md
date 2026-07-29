# Agent Comply

Use in an **ALREADY-OPEN** session to migrate onto a proper short-lived `issue/*` (or `issue/cleanup-<topic>`) branch for the **repo being touched**, and move uncommitted/wrong-branch work safely.

Simple model: no repo touch → no branch. Touch a repo → `/agentcomply` for that repo. **Workspace Orchestrators** do not get a forever session-home issue branch — if only coordinating, stop; if dirty edits exist, hand off to that repo’s Implementer or open a correctly named issue for that change. Multi-root ambiguity → ask which repo. Never silently adopt an unrelated open PR branch.

Operational summary:

- role / touch gate first (Orchestrator vs Implementer)
- inspect git status, branch, dirty files, remotes
- ask only if needed for **task description** (helper creates issue id/slug) or `issue/cleanup-<topic>`, and target repo if multi-root / ambiguous
- run `scripts/gitops/create_issue_branch.py` when filing/reusing an issue branch from latest `development`
- move dirty work safely (stash/checkout/pop, worktree, or equivalent); never dump onto development/staging/main
- commit only when Carlos wants or the commit is clearly ready; never commit secrets
- push the branch as a **checkpoint** (no PR). When the issue is finished, mark review-ready via completion gate — Review Packager opens the PR. Do not self-merge.
- tell the session: this work package lives on `issue/…`; no forever `dev/*`
- plain English summary of what was done

For a brand-new clean session, use `/agentsetup` instead.

Read and execute `.cursor/skills/agentcomply/SKILL.md`.
