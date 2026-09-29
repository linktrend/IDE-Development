---
name: agentsetup
description: >-
  Bootstrap a NEW agent session onto issue/<PREFIX>-<n>-<slug> from latest
  development for this repo. The Project orchestrator assigns the Ledger ID.
version: 3.0.0-managed
status: active
tags: [git, agent, bootstrap, branching]
related_skills:
  - agentcomply
discovery:
  - .agents/skills/agentsetup/SKILL.md
---

# Agent Setup (NEW session) — Codex managed adapter

Bootstrap a **new agent** onto `issue/<PREFIX>-<n>-<slug>` for **this repository**. Dirty or wrong-branch work uses `agentcomply`.

## Authority

- This file: `.agents/skills/agentsetup/SKILL.md`
- Peer: `.agents/skills/agentcomply/SKILL.md`
- `scripts/gitops/create_issue_branch.py`

Do **not** require `.cursor` to be loaded.

## House rules

- If no Ledger ID was given, stop and ask the Project orchestrator. Never invent an ID.
- Workers push the branch and never open pull requests.
- Commit small, push often, run the Issue's fast checks, end with a short lessons note.

## Workflow

1. `git rev-parse --show-toplevel`
2. Create or reuse the branch:

```bash
python3 scripts/gitops/create_issue_branch.py --id IDE-42 --slug fix-login
```

3. Read JSON `{id, branch, worktree, base, baseSha, pushed}`.
4. Report the branch and the next step in plain English.

## Fail closed

If `create_issue_branch.py` fails, stop and report the error. Do not invent a Ledger ID.
