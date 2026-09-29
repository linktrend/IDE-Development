---
name: agentcomply
description: >-
  Move an ALREADY-OPEN agent onto issue/<PREFIX>-<n>-<slug> for this repo,
  keeping dirty work. The Project orchestrator assigns the Ledger ID.
version: 3.0.0-managed
status: active
tags: [git, agent, migration, compliance, branching]
related_commands:
  - agentcomply
related_skills:
  - agentsetup
---

# Agent Comply (ALREADY-OPEN session) — Cursor managed adapter

Move an already-open agent onto `issue/<PREFIX>-<n>-<slug>` for **this repository**, preserving dirty work.

## Authority

- `.cursor/rules/linktrend-git-branching.mdc`
- `.cursor/commands/agentcomply.md`
- `.cursor/skills/agentcomply/SKILL.md` (this file)
- `scripts/gitops/create_issue_branch.py`

## House rules

- Wrong homes include `development`, `main`, `issue/<number>-slug`, and `cursor/*`.
- If no Ledger ID was given, stop and ask the Project orchestrator. Never invent an ID.
- Never force-push. Never prefer-incoming.
- Workers push the branch and never open pull requests.

## Workflow

1. Inspect `git status`, the current branch, and remotes.
2. If already on the matching clean issue branch, confirm and stop.
3. Stash or commit, then:

```bash
python3 scripts/gitops/create_issue_branch.py --id IDE-42 --slug fix-login
```

4. Re-apply the work and verify nothing was lost.
5. Commit small, push often, run the Issue's fast checks, end with a short lessons note.

## Fail closed

If the helper or the git move fails, stop with the error. Do not invent an ID or force-push.
