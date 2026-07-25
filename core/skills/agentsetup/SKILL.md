---
name: agentsetup
description: >-
  Bootstrap a NEW Implementer agent session onto a short-lived issue/* work
  branch from latest development. Not for workspace Orchestrators. Use when
  Carlos runs /agentsetup or asks to start a new agent on the correct governed
  branch.
version: 1.1.0
status: active
tags: [git, agent, bootstrap, branching, ship-pull]
related_commands:
  - agentsetup
related_skills:
  - agentcomply
  - git-safeguard
---

# Agent Setup (NEW Implementer session)

Bootstrap a **new Implementer** onto a short-lived `issue/<id>-<slug>` branch. Do not use this for already-open agents with dirty or wrong-branch work — use `agentcomply`.

**Not for Orchestrators.** Do not invent a fake “home repo” or forever `issue/*` home for a workspace-wide coordinator.

## Authority

- `.cursor/rules/01-git-branching.mdc`
- `.cursor/rules/02-autonomous-ship-pull.mdc`
- `docs/AUTONOMOUS-GIT-OPERATIONS.md`

## House rules (locked)

- **`/agentsetup` and `/agentcomply` are for Implementers** that own work in **one repo**.
- **Orchestrators** should not use setup to claim a home repo/branch. They coordinate; per-repo Implementers own `issue/*` branches.
- **One short-lived `issue/<id>-slug` per piece of governed work** — not forever `dev/*` home branches.
- `cursor/*` for cloud/dashboard agents.
- `dev/*` rare ad-hoc only.
- Never merge own PR; never self-review; never touch `staging`/`main`. Bugbot reviews; Integrator merges.

## Use When

- Carlos invokes `/agentsetup` for a **new Implementer**
- A brand-new coding agent needs a correct work branch before coding

## Scope Out

- Migrating an already-open dirty session → `agentcomply`
- **Workspace Orchestrator** sessions — do not create a fake home `issue/*`; tell Carlos to use per-repo Implementers for coding, and `/agentcomply` only in those sessions
- Lisa Option A clock, doctrine rewrites, Integrator/Promoter landing
- Committing or opening PRs unless Carlos explicitly asks during setup

## Inputs (ask only if missing)

Ask Carlos only for missing required info — few sharp questions, then proceed:

0. **Role** — if the session looks like a workspace Orchestrator (multi-root coordinator), confirm; if Orchestrator, stop (see Role gate)
1. **Issue id** (e.g. `123` or `LAW-05`)
2. **Short slug** (kebab-case, e.g. `agent-setup-commands`)
3. **Target repo** if multi-root / ambiguous

Do not re-ask what is already clear from the message or workspace.

## Workflow

### 0. Role gate

If this is a **workspace Orchestrator** (or Carlos says so):

- Do **not** create an `issue/*` branch as session home.
- Explain: orchestrators don’t get a forever home repo/branch via `/agentsetup`.
- Next step: open or direct a **per-repo Implementer** and run `/agentsetup` there for the actual coding work.
- Stop.

If **Implementer** — continue.

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

## Output template (Implementer)

```text
Agent setup ready
- Role: Implementer
- Repo: <name>
- Branch: issue/<id>-<slug>
- Base: origin/development (fetched)
- Hard stops: no merge, no self-review, no staging/main
- Next: do the work on this branch; Ship = commit + push + PR → development
```

## Output template (Orchestrator)

```text
Agent setup — skipped (Orchestrator)
- Role: Orchestrator (workspace-wide)
- Session home issue branch: none (by design)
- Next: open/direct a per-repo Implementer and run /agentsetup there for coding work
```

## Blockers

Stop and ask when:

- role is ambiguous (Implementer vs Orchestrator)
- multi-root and target repo is ambiguous
- issue id or slug still missing after one tight question set
- cannot reach `origin/development`
- working tree is dirty in a way that would risk losing work

## Progressive Disclosure

Read only this skill, git status/branch/remote for the target repo, and the three authority docs above if needed. Do not scan unrelated modules or catalogs.
