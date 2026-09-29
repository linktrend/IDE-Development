# Agent Setup

Use at the **start of a NEW** session that will code in this repo. Check out `issue/<PREFIX>-<n>-<slug>` from latest `development`.

The Project orchestrator assigns the Ledger ID. If no ID was given, stop and ask the orchestrator. Never invent an ID.

Operational summary:

- detect the current repo
- run `python3 scripts/gitops/create_issue_branch.py --id IDE-42 --slug fix-login`
- read JSON `{id, branch, worktree, base, baseSha, pushed}`
- workers push the branch and never open pull requests
- commit small, push often, run the Issue's fast checks, end with a short lessons note

For an already-open dirty or wrong-branch session, use agentcomply instead.

Read and execute `.cursor/skills/agentsetup/SKILL.md`.
