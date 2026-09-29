---
name: agentsetup
description: >-
  Bootstrap a NEW agent session onto issue/<PREFIX>-<n>-<slug> from latest
  development. The Project orchestrator assigns the Ledger ID. Use when
  starting a new coding session on the correct branch.
version: 3.0.0
status: active
tags: [git, agent, bootstrap, branching]
related_commands:
  - agentsetup
related_skills:
  - agentcomply
  - git-safeguard
---

# Agent Setup (NEW session)

Bootstrap a **new agent** onto `issue/<PREFIX>-<n>-<slug>` from latest `origin/development`. Already-open dirty or wrong-branch work uses `agentcomply`.

## Authority

- `.cursor/rules/01-git-branching.mdc`
- `scripts/gitops/create_issue_branch.py`

## House rules

- The Project orchestrator owns the Ledger and assigns IDs (`IDE-42`). Workers and humans never invent an ID.
- If no Ledger ID was given, stop and ask the Project orchestrator. Never ask Carlos. Never invent an ID.
- One short-lived `issue/<PREFIX>-<n>-<slug>` per Ledger task. Slug: lowercase `[a-z0-9-]`, max 48 characters.
- `phase/*` is an orchestrator package branch. `dev/*` is rare ad-hoc human IDE work.
- Workers push the branch and never open pull requests. The orchestrator opens pull requests.
- Only `development` and `main`. Pull requests into `main` come only from `promote/main/*`.
- Commit small, push often, run the Issue's fast checks, and end with a short lessons note.

## Use when

- A brand-new coding session was given a Ledger ID and should start on that issue branch

## Inputs

You were given a Ledger ID and either a slug or a short description. If the ID is missing, stop.

## Workflow

### 1. Detect the repo

- `git rev-parse --show-toplevel`
- Confirm `origin/development` is the integration branch.

### 2. Create or reuse the branch

```bash
python3 scripts/gitops/create_issue_branch.py --id IDE-42 --slug fix-login
# or derive the slug from a description:
python3 scripts/gitops/create_issue_branch.py --id IDE-42 "Fix the login form"
```

Optional: `--base development` (default), `--worktree PATH`, `--no-push`.

Read the JSON `{id, branch, worktree, base, baseSha, pushed}`. `cd` into `worktree` when it differs from the current checkout.

### 3. Confirm

- Current branch is `issue/<PREFIX>-<n>-<slug>`
- It was cut from latest `origin/development` (or an existing branch was reused without resetting unique work)
- You will not open a pull request

### 4. Report

```text
Agent setup ready
- Repo: <name>
- Ledger ID: <PREFIX>-<n>
- Branch: issue/<PREFIX>-<n>-<slug>
- Worktree: <path|same>
- Base: origin/development @ <baseSha>
- Next: commit small, push often, run the Issue fast checks, end with a lessons note
```

## Blockers

Stop when:

- no Ledger ID was given
- `create_issue_branch.py` fails (invalid ID or slug, or reuse would lose work)
- the working tree is dirty and a worktree could not be created

## Progressive disclosure

Read this skill, the helper `--help`, and git status for the target repo.
