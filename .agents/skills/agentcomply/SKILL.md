---
name: agentcomply
description: >-
  Move an ALREADY-OPEN session onto issue/<PREFIX>-<n>-<slug> without losing
  dirty work. The Project orchestrator assigns the Ledger ID.
version: 3.0.0-system
status: active
tags: [git, agent, migration, compliance, branching]
related_skills:
  - agentsetup
discovery:
  - .agents/skills/agentcomply/SKILL.md
---

# Agent Comply (ALREADY-OPEN session) — IDE Development native Codex adapter

Move an already-open session off the wrong branch (`development`, `main`, `issue/<number>-slug`, `cursor/*`) onto `issue/<PREFIX>-<n>-<slug>` and keep its work.

## Authority

- This file: `.agents/skills/agentcomply/SKILL.md`
- Full skill: `core/skills/agentcomply/SKILL.md`
- Peer: `.agents/skills/agentsetup/SKILL.md`
- `scripts/gitops/create_issue_branch.py`

Do **not** require `.cursor` to be loaded.

## House rules

- If no Ledger ID was given, stop and ask the Project orchestrator. Never ask Carlos. Never invent an ID.
- Never force-push. Never prefer-incoming. Never dump work onto `development` or `main`.
- Workers push the branch and never open pull requests.

## Workflow

1. Inspect `git status`, the current branch, and remotes.
2. Stash or commit dirty work, then:

```bash
python3 scripts/gitops/create_issue_branch.py --id IDE-42 --slug fix-login
```

3. Re-apply the stash and verify nothing was lost.
4. Commit small, push often, run the Issue's fast checks, end with a short lessons note.

## Fail closed

If the helper or the git move fails, stop with the error. Do not invent an ID or force-push.
