---
name: agentcomply
description: >-
  Migrate an ALREADY-OPEN agent from wrong or long-lived branches onto a proper
  short-lived issue/* (or cleanup) branch for the repo being touched, safely
  moving dirty work. Use when Carlos runs /agentcomply or asks to comply with
  studio branching rules.
version: 1.2.0
status: active
tags: [git, agent, migration, compliance, branching, ship-pull]
related_commands:
  - agentcomply
related_skills:
  - agentsetup
  - git-safeguard
---

# Agent Comply (ALREADY-OPEN session)

Migrate an **already-open agent** onto a proper short-lived `issue/*` branch for the **repo being touched**. Prefer this over starting fresh when there is uncommitted or wrong-branch work to preserve.

## Authority

- `.cursor/rules/01-git-branching.mdc`
- `.cursor/rules/02-autonomous-ship-pull.mdc`
- `docs/AUTONOMOUS-GIT-OPERATIONS.md`
- Pair with `git-safeguard` before any commit or push

## House rules (locked)

- **No code/repo touch → no branch required.** Coordination-only sessions that do not edit a repo do not need `/agentcomply`.
- **Touch a repo → comply for that repo.** Any agent that edits a repo (including an orchestrator that starts coding) runs `/agentcomply` or `/agentsetup` for **that** repo and uses `issue/<id>-slug` for the work package.
- One short-lived `issue/<id>-slug` per piece of governed work — no forever `dev/*` home.
- Branch must match **this work package**. Do not silently adopt an unrelated open PR branch just because it exists.
- Multi-root: if which repo is being touched is ambiguous, ask (normal ambiguity ask).
- `cursor/*` for cloud; `dev/*` rare ad-hoc only.
- Never dump work onto `development` / `staging` / `main`.
- Never merge own PR; never self-review; Bugbot reviews; Integrator merges.

## Use When

- Carlos invokes `/agentcomply`
- Session is on `dev/*`, `development`, detached, stale, or otherwise non-compliant **and** this session is touching (or about to touch) a repo
- Dirty files or commits need to move onto a proper `issue/*` branch

## Scope Out

- Brand-new clean bootstrap → `agentsetup`
- Sessions that will not touch any repo (no branch work needed)
- Lisa Option A clock, doctrine rewrites, Integrator/Promoter landing
- Force-push, hard reset, or rewriting shared history unless Carlos explicitly authorizes

## Inputs (ask only if needed)

1. **Issue id + short slug** for `issue/<id>-<slug>`
2. Or allow **`issue/cleanup-<topic>`** if no issue id exists yet
3. **Target repo** if multi-root / ambiguous
4. Whether to **commit** and/or **open/update PR** (ask if commit message or readiness is ambiguous)

## Workflow

### 1. Inspect current state

In the target repo, gather:

```bash
git status --short --branch
git branch --show-current
git remote -v
git stash list
```

Note: current branch, dirty files, unpushed commits, whether HEAD is `development`/`staging`/`main`/`dev/*`/`cursor/*`/`issue/*`.

### 2. Resolve branch name

- Prefer `issue/<id>-<slug>` when id is known.
- Else `issue/cleanup-<topic>` (kebab-case topic).
- Ask only if both are missing.
- Never adopt an unrelated open branch just because it exists in the same repo — the branch must match **this work package**.

### 3. Park dirty work safely

Never checkout shared branches with uncommitted governed work in a way that could land it there.

Preferred pattern when dirty:

```bash
git stash push -u -m "agentcomply: park before issue branch"
git fetch origin
git checkout development
git pull --ff-only origin development
git checkout -b issue/<id>-<slug>   # or issue/cleanup-<topic>
git stash pop
```

If already on a usable `issue/*` that matches this work package, skip recreate; still confirm base is recent `development` (merge/rebase per repo rule — default merge from `origin/development` on Pull waves).

If stash pop conflicts: stop, report conflicted paths, help resolve — do not abort onto `development`.

### 4. Commits (ask when ambiguous)

- **Do not commit secrets** (`.env`, credentials, tokens). Use `git-safeguard`.
- Commit **only** if Carlos wants it, or staged work is clearly ready with an unambiguous conventional message.
- If message/content is ambiguous: ask once, then proceed.
- Do not commit unrelated pre-existing dirty files without Carlos confirmation.

### 5. Push and PR policy

Prefer this order:

1. Get onto the correct `issue/*` (or cleanup) branch.
2. **Push** the branch (`git push -u origin HEAD`) once there is at least one commit to share, or Carlos asks to publish the branch tip.
3. **Open or update PR → `development`** when commits are ready for review.
4. If work is unfinished/dirty and should wait for a Ship wave: leave **ready-to-ship** on the issue branch; state clearly that no PR was opened yet.

Never open a PR from `development`/`staging`/`main`. Never merge the PR.

### 6. Session contract

Tell the session explicitly:

- Work branch for this package is now `issue/…` (name it).
- Do not return to forever `dev/*` as home for this work.
- Hard stops: no self-merge, no self-review, no staging/main.

### 7. Report

Plain English summary of exactly what was done:

- previous branch → new branch
- stash/move outcome
- commits created (yes/no + message)
- push (yes/no)
- PR (opened / updated / skipped + why)
- remaining dirty files, if any
- next step for this session

## Output template

```text
Agent comply done
- Repo: <name>
- Was: <old-branch> (dirty: yes/no)
- Now: issue/<id>-<slug>   # branch for this work package
- Moved: stash pop / cherry-pick / already clean
- Commit: <none | conventional message>
- Push: <yes | no>
- PR → development: <url | none — waiting for Ship / unfinished>
- Hard stops: no merge, no self-review, no staging/main
- Reminder: work package lives on issue/… — not forever dev/*
```

## Blockers

Stop and ask when:

- multi-root and target repo is ambiguous
- moving work would require destructive history rewrite
- secrets appear in the dirty set
- stash pop / rebase conflicts cannot be resolved safely
- Carlos has not confirmed commit when the diff is mixed or unclear

## Progressive Disclosure

Read only this skill, `git-safeguard` when committing/pushing, live git state for the target repo, and the authority docs above if needed.
