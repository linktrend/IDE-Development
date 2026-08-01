---
name: agentcomply
description: >-
  Migrate an ALREADY-OPEN agent from wrong or long-lived branches onto a proper
  short-lived issue/* branch for the repo being touched, safely moving dirty
  work. Use when Carlos runs agentcomply or asks to comply with studio branching.
version: 2.0.0-system
status: active
tags: [git, agent, migration, compliance, branching, ship-pull]
related_skills:
  - agentsetup
discovery:
  - .agents/skills/agentcomply/SKILL.md
---

# Agent Comply (ALREADY-OPEN session) — IDE Development native Codex adapter

Migrate an **already-open agent** onto a proper short-lived `issue/*` branch for the **repo being touched**. Prefer this over starting fresh when there is uncommitted or wrong-branch work to preserve.

## Authority (Codex-native; no `.cursor` required)

- This file: `.agents/skills/agentcomply/SKILL.md`
- Full skill detail (optional): `core/skills/agentcomply/SKILL.md`
- Peer skill: `.agents/skills/agentsetup/SKILL.md`
- `scripts/gitops/create_issue_branch.py`
- `docs/AUTONOMOUS-GIT-OPERATIONS.md`
- Managed platform template (for consumers): `core/managed-core/platforms/codex/AGENTS.managed-section.md`

Do **not** require `.cursor` to be loaded. Prefer these paths over any `.cursor/...` compatibility surface.

## House rules

- Primarily for Implementers that own work in **one repo**.
- No code/repo touch → no branch required.
- Never dump work onto `development` / `staging` / `main`.
- Never silently adopt an unrelated open PR branch.
- **Never ask for issue id/slug** — helper creates/reuses them.
- Never merge own PR; never self-review.

## Workflow

1. Inspect: `git status`, `git branch --show-current`, remotes
2. If already on a matching clean `issue/<id>-slug` for this work package, confirm and stop
3. Otherwise:

```bash
python3 scripts/gitops/create_issue_branch.py "<task description>" --prefer-worktree
```

4. Move dirty work safely; never force onto protected branches
5. Push checkpoint only when asked or clearly ready
6. When finished later: `completion_gate.py write-evidence` then `review-ready`

## Fail closed

If helper or git moves fail, stop with the error. Do not invent IDs or force-push.
