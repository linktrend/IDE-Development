---
name: agentsetup
description: >-
  Bootstrap a NEW agent session onto a short-lived issue/* work branch from
  latest development. Use when Carlos runs /agentsetup or asks to start a new
  agent on the correct governed branch.
version: 1.0.0
status: active
tags: [git, agent, bootstrap, branching, ship-pull]
related_commands:
  - agentsetup
related_skills:
  - agentcomply
  - git-safeguard
---

# Agent Setup (NEW session)

Bootstrap a **new** agent onto a short-lived `issue/<id>-<slug>` branch. Do not use this for already-open agents with dirty or wrong-branch work — use `agentcomply`.

## Authority

- `.cursor/rules/01-git-branching.mdc`
- `.cursor/rules/02-autonomous-ship-pull.mdc`
- `docs/AUTONOMOUS-GIT-OPERATIONS.md`

## House rules (locked)

- **One short-lived `issue/<id>-slug` per piece of governed work** — not forever `dev/*` home branches.
- `cursor/*` for cloud/dashboard agents.
- `dev/*` rare ad-hoc only.
- Never merge own PR; never self-review; never touch `staging`/`main`. Bugbot reviews; Integrator merges.

## Use When

- Carlos invokes `/agentsetup`
- A brand-new agent session needs a correct work branch before coding

## Scope Out

- Migrating an already-open dirty session → `agentcomply`
- Lisa Option A clock, doctrine rewrites, Integrator/Promoter landing
- Committing or opening PRs unless Carlos explicitly asks during setup

## Inputs (ask only if missing)

Ask Carlos only for missing required info — few sharp questions, then proceed:

1. **Issue id** (e.g. `123` or `LAW-05`)
2. **Short slug** (kebab-case, e.g. `agent-setup-commands`)
3. **Target repo** if multi-root / ambiguous

Do not re-ask what is already clear from the message or workspace.

## Workflow

### 1. Detect repo context

- Identify the git repo for this session (`git rev-parse --show-toplevel`).
- Multi-root workspace: if more than one product repo is in play and Carlos did not name one, ask which repo.
- Confirm remote and that `development` exists as the integration branch.

### 2. Sync to latest development

```bash
git fetch origin
git checkout development
git pull --ff-only origin development
```

If checkout/pull is blocked (dirty tree on a fresh session), stop and report — do not invent stashes unless Carlos confirms. Prefer a clean start for `/agentsetup`.

### 3. Create and checkout issue branch

```bash
git checkout -b issue/<id>-<slug>
```

Normalize: lowercase slug, hyphens only, no spaces. Branch name form: `issue/<id>-<slug>`.

### 4. Confirm ready + hard stops

Confirm:

- current branch is `issue/<id>-<slug>`
- working tree clean (or only expected pre-existing noise Carlos knows about)
- tracking not yet required (push happens at Ship or when Carlos asks)

Remind hard stops in plain English:

- Do **not** merge into `development`
- Do **not** self-review (Bugbot reviews)
- Do **not** promote to `staging` or `main`
- Ship waves: commit → push → PR → `development` → stop

### 5. Report

Plain English summary:

- **Repo:** path or name
- **Branch:** `issue/<id>-<slug>`
- **Base:** latest `origin/development`
- **Next:** implement the issue; at Ship, push and open/update PR to `development`

## Output template

```text
Agent setup ready
- Repo: <name>
- Branch: issue/<id>-<slug>
- Base: origin/development (fetched)
- Hard stops: no merge, no self-review, no staging/main
- Next: do the work on this branch; Ship = commit + push + PR → development
```

## Blockers

Stop and ask when:

- multi-root and target repo is ambiguous
- issue id or slug still missing after one tight question set
- cannot reach `origin/development`
- working tree is dirty in a way that would risk losing work

## Progressive Disclosure

Read only this skill, git status/branch/remote for the target repo, and the three authority docs above if needed. Do not scan unrelated modules or catalogs.
