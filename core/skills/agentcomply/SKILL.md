---
name: agentcomply
description: >-
  Migrate an ALREADY-OPEN Implementer agent from wrong or long-lived branches
  onto a proper short-lived issue/* (or cleanup) branch, safely moving dirty
  work. Not for workspace Orchestrators. Use when Carlos runs /agentcomply or
  asks to comply with studio branching rules.
version: 1.1.0
status: active
tags: [git, agent, migration, compliance, branching, ship-pull]
related_commands:
  - agentcomply
related_skills:
  - agentsetup
  - git-safeguard
---

# Agent Comply (ALREADY-OPEN Implementer session)

Migrate an **already-open Implementer** onto a proper short-lived `issue/*` branch. Prefer this over starting fresh when there is uncommitted or wrong-branch work to preserve.

**Not for Orchestrators.** Workspace-wide coordination agents must not be rehomed onto a random or stolen `issue/*` branch.

## Authority

- `.cursor/rules/01-git-branching.mdc`
- `.cursor/rules/02-autonomous-ship-pull.mdc`
- `docs/AUTONOMOUS-GIT-OPERATIONS.md`
- Pair with `git-safeguard` before any commit or push

## House rules (locked)

- **`/agentcomply` and `/agentsetup` are for Implementers** that own work in **one repo** on an `issue/*` branch.
- **Orchestrators** (workspace-wide coordination) do **not** get a forever “session home” issue branch. Implementer work happens in per-repo agents (or the orchestrator may spawn/direct those).
- One short-lived `issue/<id>-slug` per piece of governed Implementer work — no forever `dev/*` home.
- `cursor/*` for cloud; `dev/*` rare ad-hoc only.
- Never dump work onto `development` / `staging` / `main`.
- Never merge own PR; never self-review; Bugbot reviews; Integrator merges.

## Use When

- Carlos invokes `/agentcomply` in an **Implementer** session
- Session is on `dev/*`, `development`, detached, stale, or otherwise non-compliant
- Dirty files or commits need to move onto a proper `issue/*` branch

## Scope Out

- Brand-new clean Implementer bootstrap → `agentsetup`
- **Workspace Orchestrator** sessions (multi-repo coordination) — see Role gate below
- Lisa Option A clock, doctrine rewrites, Integrator/Promoter landing
- Force-push, hard reset, or rewriting shared history unless Carlos explicitly authorizes

## Inputs (ask only if needed)

0. **Role** — Implementer vs Orchestrator (ask if ambiguous; see Role gate)
1. **Issue id + short slug** for `issue/<id>-<slug>` (Implementer only)
2. Or allow **`issue/cleanup-<topic>`** if no issue id exists yet
3. **Target repo** if multi-root / ambiguous (Implementer must name one)
4. Whether to **commit** and/or **open/update PR** (ask if commit message or readiness is ambiguous)

## Workflow

### 0. Role gate (do this first)

Detect or ask once: is this session an **Implementer** or an **Orchestrator**?

**Orchestrator signals** (any one is enough — treat as Orchestrator):

- Session / UI title or Carlos wording says Orchestrator / workspace-wide / multi-repo coordinator
- Multi-root workspace with no single named target repo for *this* governed change
- Agent’s job is coordination, not owning one repo’s issue branch

**If Orchestrator — STOP rehoming. Ask Carlos which mode:**

- **(a) Stay orchestrator-only** — no personal work branch; `/agentcomply` = inspect + remind implementers / list non-compliant repos; do **not** re-home onto a random doctrine branch.
- **(b) Pick ONE target repo** for implementer comply — then require issue id/slug for **that repo only** and continue the Implementer workflow below.

Until Carlos answers (a) or (b), stop after classification + this short ask. Do not checkout.

**If mode (a) — do this (and stop):**

1. Do **not** create, checkout, or “claim” an `issue/*` branch as session home.
2. Do **not** associate this chat with an unrelated existing branch/PR (e.g. someone else’s Lisa doctrine / Option A branch).
3. Optionally report a **brief** multi-repo status (dirty? which branches?) — no forced compliance migrate.
4. Tell Carlos in plain English: orchestrators don’t get a forever session-home `issue/*`; implementer coding happens in per-repo agents.
5. If this orchestrator has **accidental dirty edits** in a repo: hand off to that repo’s Implementer + `/agentcomply` there, or open a **correctly named** `issue/<id>-slug` for *that specific change* — never steal another agent’s branch name.
6. End with the Orchestrator output template below. Do not continue steps 1–7.

**If mode (b) or Implementer** — continue below for the **one** named target repo only.

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
- Never adopt an unrelated open branch just because it exists in the same repo.

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

If already on a usable `issue/*` with only compliance messaging needed, skip recreate; still confirm base is recent `development` (merge/rebase per repo rule — default merge from `origin/development` on Pull waves).

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

- Home branch is now `issue/…` (name it).
- Do not return to forever `dev/*` as home.
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

## Output template (Implementer)

```text
Agent comply done
- Role: Implementer
- Repo: <name>
- Was: <old-branch> (dirty: yes/no)
- Now: issue/<id>-<slug>   # home for this session
- Moved: stash pop / cherry-pick / already clean
- Commit: <none | conventional message>
- Push: <yes | no>
- PR → development: <url | none — waiting for Ship / unfinished>
- Hard stops: no merge, no self-review, no staging/main
- Reminder: home is issue/… — not forever dev/*
```

## Output template (Orchestrator)

```text
Agent comply — Orchestrator (no rehome)
- Role: Orchestrator (workspace-wide)
- Session home issue branch: none (by design)
- Multi-repo snapshot: <brief dirty/branch notes or “clean / not scanned deeply”>
- Action: do not associate this chat with an unrelated issue/* branch
- If dirty edits exist in a repo: hand off to that repo’s Implementer + /agentcomply there,
  or open a correctly named issue/* for that specific change
- Next: keep coordinating here; spawn/direct per-repo Implementers for coding
```

## Blockers

Stop and ask when:

- role is ambiguous after one question (Implementer vs Orchestrator)
- multi-root and target repo is ambiguous (Implementer)
- moving work would require destructive history rewrite
- secrets appear in the dirty set
- stash pop / rebase conflicts cannot be resolved safely
- Carlos has not confirmed commit when the diff is mixed or unclear

## Progressive Disclosure

Read only this skill, `git-safeguard` when committing/pushing, live git state for the target repo, and the authority docs above if needed.
