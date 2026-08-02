---
name: agentsetup
description: >-
  Bootstrap a NEW agent session onto a short-lived issue/* work branch from
  latest development for the repo being touched. Use when Carlos runs
  agentsetup or asks to start a new agent on the correct governed branch.
version: 2.0.0-system
status: active
tags: [git, agent, bootstrap, branching, ship-pull]
related_skills:
  - agentcomply
discovery:
  - .agents/skills/agentsetup/SKILL.md
---

# Agent Setup (NEW session) — IDE Development native Codex adapter

Bootstrap a **new agent** onto a short-lived `issue/<id>-<slug>` branch for the **repo being touched**. Do not use this for already-open agents with dirty or wrong-branch work — use `agentcomply`.

## Authority (Codex-native; no `.cursor` required)

- This file: `.agents/skills/agentsetup/SKILL.md`
- Full skill detail (optional): `core/skills/agentsetup/SKILL.md`
- Peer skill: `.agents/skills/agentcomply/SKILL.md`
- `scripts/gitops/create_issue_branch.py`
- `docs/AUTONOMOUS-GIT-OPERATIONS.md`
- `docs/contracts/AGENT-COMPLETION.md`
- Managed platform template (for consumers): `core/managed-core/platforms/codex/AGENTS.managed-section.md`

Do **not** require `.cursor` to be loaded. Prefer these paths over any `.cursor/...` compatibility surface.

## House rules

- `/agentsetup` is primarily for Implementers that own work in **one repo**.
- No code/repo touch → no branch required.
- Touch a repo → setup for **that** repo.
- One short-lived `issue/<id>-slug` per governed work package.
- **Do not ask Carlos for issue id or slug.** Use `scripts/gitops/create_issue_branch.py`.
- Never merge own PR; never self-review; never touch `staging`/`main`.

## Workflow

1. Identify repo root: `git rev-parse --show-toplevel`
2. Create/reuse issue + branch:

```bash
python3 scripts/gitops/create_issue_branch.py "<task description>" --prefer-worktree
```

3. Confirm `BRANCH=` / `WORKTREE=` / `ISSUE_NUMBER=`
4. Ship = checkpoint only; finished work uses `completion_gate.py write-evidence` then `review-ready`
5. Report in plain English

## Fail closed

If the helper fails, stop and report. Do not invent local issue numbers.
