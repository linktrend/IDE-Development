---
name: agentcomply
description: >-
  Move an ALREADY-OPEN session off the wrong branch onto
  issue/<PREFIX>-<n>-<slug>, keeping dirty work. The Project orchestrator
  assigns the Ledger ID.
version: 3.0.0
status: active
tags: [git, agent, migration, compliance, branching]
related_commands:
  - agentcomply
related_skills:
  - agentsetup
  - git-safeguard
---

# Agent Comply (ALREADY-OPEN session)

Move an already-open session onto `issue/<PREFIX>-<n>-<slug>` for this repo and keep its dirty work. A brand-new clean session uses `agentsetup`.

## Authority

- `.cursor/rules/01-git-branching.mdc`
- `scripts/gitops/create_issue_branch.py`
- Pair with `git-safeguard` before any commit or push

## House rules

- The Project orchestrator assigns the Ledger ID. If none was given, stop and ask the orchestrator. Never ask Carlos. Never invent an ID.
- Wrong homes include `development`, `main`, an old `issue/<number>-slug`, and a `cursor/*` branch.
- One short-lived `issue/<PREFIX>-<n>-<slug>` per Ledger task. `dev/*` is rare ad-hoc human work, not a forever home.
- Never dump work onto `development` or `main`.
- Never force-push. Never prefer-incoming.
- Workers push the branch and never open pull requests.

## Use when

- The session is already open on the wrong branch and has dirty files or commits to keep

## Workflow

### 1. Inspect

```bash
git status --short --branch
git branch --show-current
git remote -v
git stash list
```

Note the current branch, dirty files, and unpushed commits.

### 2. Create the correct branch

If you are already on the matching clean `issue/<PREFIX>-<n>-<slug>` for this Ledger ID, confirm and stop.

Otherwise:

```bash
python3 scripts/gitops/create_issue_branch.py --id IDE-42 --slug fix-login
```

If the current tree is dirty, stash or commit first so checkout cannot drop files. Prefer a worktree when the helper should leave the current checkout alone:

```bash
git stash push -u -m "agentcomply: park before issue branch"
python3 scripts/gitops/create_issue_branch.py --id IDE-42 --slug fix-login --worktree /path/to/wt
```

### 3. Re-apply and verify nothing was lost

```bash
git stash pop
git status --short
git diff
```

Confirm every dirty path is present on `issue/<PREFIX>-<n>-<slug>`. If pop conflicts, stop and resolve those paths. Do not abort onto `development` or `main`. Do not force-push. Do not prefer-incoming.

### 4. Continue

- Commit small. Push often with `git push -u origin HEAD`.
- Run the Issue's fast checks before the final push.
- End with a short lessons note.
- Never open a pull request.

### 5. Report

```text
Agent comply done
- Was: <old-branch> (dirty: yes/no)
- Now: issue/<PREFIX>-<n>-<slug>
- Moved: stash pop / already clean
- Lost files: none
- Next: commit small, push often, run fast checks
```

## Blockers

Stop when:

- no Ledger ID was given
- moving work would need a force-push or a history rewrite
- stash pop conflicts cannot be resolved safely
- secrets appear in the dirty set

## Progressive disclosure

Read this skill, `git-safeguard` when committing or pushing, and the live git state of the target repo.
