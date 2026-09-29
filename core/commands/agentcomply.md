# Agent Comply

Use in an **ALREADY-OPEN** session to move off the wrong branch onto `issue/<PREFIX>-<n>-<slug>` and keep dirty work.

Wrong branches include `development`, `main`, an old `issue/<number>-slug`, and `cursor/*`.

The Project orchestrator assigns the Ledger ID. If no ID was given, stop and ask the orchestrator. Never ask Carlos. Never invent an ID.

Operational summary:

- inspect git status, branch, dirty files, and remotes
- stash or commit, then run `python3 scripts/gitops/create_issue_branch.py --id IDE-42 --slug fix-login`
- re-apply the work and verify nothing was lost
- never force-push and never prefer-incoming
- workers push the branch and never open pull requests
- commit small, push often, run the Issue's fast checks, end with a short lessons note

For a brand-new clean session, use `/agentsetup` instead.

Read and execute `.cursor/skills/agentcomply/SKILL.md`.
