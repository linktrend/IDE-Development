# Consumer rollout (portable IDE Development v2)

**Status:** Active rollout inventory — read-only drift posture until Principal-approved
**Date:** 2026-08-01
**Version:** `v2.0.0` (identified in `VERSION`; no Git tag or GitHub release in Wave 1)
**Issue:** #43
**SOT:** `docs/AUTONOMOUS-GIT-OPERATIONS.md` · `docs/adr/0003-autonomous-ship-pull-promote.md` · `docs/adr/0004-portable-managed-core-v2.md` · `docs/contracts/REPOSITORY-PROTECTION.md`

This document covers **consumer** rollout of the portable managed core. It does **not** authorize edits to real consumer repositories or live GitHub settings from Wave 1 automation.

**IDE Development** (`linktrend/IDE-Development`) is the **system source and internal self-verification target**. It is **not** a consumer rollout entry and must not receive a nested installed copy of itself during Wave 1.

---

## What Wave 1 delivers (system repo only)

- Portable managed-core package and transactional installer (`scripts/ide-development.py`)
- Native Codex + Cursor physical discovery adapters
- Migration / conflict / rollback behavior
- Managed repository-protection **plan/verify** contract (dry-run default)
- Updated active documentation and integration harness

## What Wave 1 does NOT do

- Edit `openclaw_prime`, LiNKplatform, LiNKskills, LiNKbrain, LiNKsites, LiNKdeveloper, LiNKlibraries, LiNKautowork, or LiNKtrading-codebase
- Apply live GitHub rulesets, branch protection, secrets, variables, App, or Bugbot settings
- Create a Git tag or GitHub Release for `v2.0.0`
- Add Claude Code as a supported platform

---

## Locked consumer order

Drift reports, approvals, and installs use this **exact sequential order** (one repo at a time):

| # | Repo (disk) | GitHub slug (typical) | Notes |
|---|---|---|---|
| 1 | openclaw_prime | `linktrend/openclaw_prime` | Lisa runtime; follow-up PRs stay in that repo |
| 2 | LiNKplatform | `linktrend/LiNKplatform` | |
| 3 | LiNKskills | `linktrend/LiNKskills` | |
| 4 | LiNKbrain | `linktrend/LiNKbrain` | |
| 5 | LiNKsites | `linktrend/LiNKsites` | |
| 6 | LiNKdeveloper | `linktrend/LiNKdeveloper` | |
| 7 | LiNKlibraries | `linktrend/LiNKlibraries` | |
| 8 | LiNKautowork | `linktrend/LiNKautowork` | |
| 9 | LiNKtrading-codebase | `linktrend/LiNKtrading-codebase` | |

IDE Development is intentionally **absent** from this table.

**Do not confuse with Ship/Pull order.** Lisa Option A still processes IDE Development first as the system source during Ship/Pull waves (`docs/AUTONOMOUS-GIT-OPERATIONS.md`). That clock order is not an install/rollout authorization and does not make this repository a consumer install target.

---

## Gate before each consumer

For **every** consumer in the table above:

1. Produce a **read-only drift report** (installer `drift` / plan dry-run; compare managed templates without mutating the consumer).
2. Obtain **separate Carlos (Principal) approval** for that specific consumer.
3. Only then run `install` or `update` against an approved path.
4. Plan repository protections for `development`, `staging`, and `main` (dry-run). Live `--apply` is a separate approved action outside Wave 1 defaults.
5. Keep GitHub App credentials, secrets, variables, Bugbot dashboard settings, and other repository settings **external** — never package secret values into the managed core.

Also required before broad rollout:

1. Wave 1 changes reach IDE Development’s protected promotion path as required by studio process.
2. Bugbot mention-only / cost posture confirmed per repository when Bugbot is used (`docs/contracts/BUGBOT-MENTION-ONLY.md`, `docs/contracts/ACTIONS-COST-CONTROLS.md`).
3. GitHub App smoke posture understood (`docs/contracts/GITHUB-APP-GITOPS-CREDENTIALS.md`).
4. Platform adoption / disposable-repo installer proofs green (`tests/test-portable-v2-integration.sh` and suites it discovers).

### Static `workflow_run` gate workflow names

`workflow_run.workflows` is **static YAML** and cannot be configured through repository variables. When syncing managed workflows into a consumer, **substitute or generate** the list so it includes every Actions workflow display name that produces a configured named gate check. IDE Development lists:

- `CI`
- `Branch Source Policy`

Merging to `development` alone does **not** activate new scheduled workflows. Code alone does **not** enforce mention-only.

---

## Install / update commands (after approval)

```bash
# From IDE Development (system source) — disposable or approved consumer path only:
python3 scripts/ide-development.py drift --repo /path/to/consumer
python3 scripts/ide-development.py plan --repo /path/to/consumer
python3 scripts/ide-development.py install --repo /path/to/consumer   # or update
python3 scripts/ide-development.py verify --repo /path/to/consumer
```

Physical install leaves `.ide-development/`, Cursor adapters under `.cursor/{rules,commands,skills}`, and Codex adapters (`AGENTS.md` managed block + `.agents/skills`). Consumer-owned content outside managed ownership is preserved. Never overwrite consumer `ci.yml`.

Legacy `scripts/wire-repo.sh` / sync helpers remain for pre-v2 GitOps compatibility until a consumer migrates; they are not the portable v2 path and must not create consumer-to-system `.cursor` symlinks for new installs.

---

## Branch protection (standard system behavior)

Every installed consumer must protect:

| Branch | Purpose |
|---|---|
| `development` | Strict required checks, source policy, Bugbot, Integrator compatibility |
| `staging` | Promotion-only PR sources + staging gates |
| `main` | Promotion-only PR sources + release gates + Main Approve compatibility |

The GitHub **default branch** remains the repository’s configured default (typically `main`); managed protections still apply to `development`, `staging`, and `main` regardless of which branch is the default branch.

Existing legitimate repository-specific required checks are preserved and unioned deterministically. Tooling: `docs/contracts/REPOSITORY-PROTECTION.md` (dry-run default; no live apply in Wave 1).

### Consumer check-name variables (`LINKTREND_*_CHECKS`)

Managed workflows already read repository variables for named gate check display names.
Consumers **must** set these so Integrator / Packager / promote / repair-observer match their `ci.yml` job names:

| Variable | Purpose | IDE default |
|---|---|---|
| `LINKTREND_INTEGRATOR_REQUIRED_CHECKS` | fast-gate comma-separated check names | `Verify IDE Development,Enforce allowed PR source branches` |
| `LINKTREND_STAGING_GATE_CHECKS` | staging promote gate | `Verify IDE Development` |
| `LINKTREND_RELEASE_GATE_CHECKS` | main promote gate | `Verify IDE Development` |
| `LINKTREND_CI_WORKFLOW_NAME` | `workflow_run` / observer CI name | `CI` |
| `LINKTREND_BRANCH_POLICY_WORKFLOW_NAME` | branch policy workflow display name | `Branch Source Policy` |
| `LINKTREND_BUGBOT_CHECK_NAME` | Bugbot check run name | `Cursor Bugbot` |

Note: `workflow_run.workflows` lists in YAML are **static** and must still be substituted when a consumer renames `CI` / `Branch Source Policy`.

---

## Drift detection (read-only)

Before any mutating install/update:

| Check | Action |
|---|---|
| Installer drift | `python3 scripts/ide-development.py drift --repo <consumer>` |
| Dry-run plan | `python3 scripts/ide-development.py plan --repo <consumer>` |
| Managed workflows (legacy compare) | `cmp` / `scripts/sync-managed-workflows.sh --dry-run` when relevant |
| Protection plan | repository-protection tooling in dry-run mode |
| Integrator variable | `gh api repos/linktrend/REPO/actions/variables/LINKTREND_INTEGRATOR_REQUIRED_CHECKS` (read-only) |

Record gaps in adoption notes. Do **not** auto-fix consumers from Wave 1.

---

## Related documents

- `docs/GITOPS-CONSUMER-ROLLOUT.md` (this file)
- `docs/adr/0004-portable-managed-core-v2.md`
- `docs/contracts/REPOSITORY-PROTECTION.md`
- `docs/contracts/LISA-OPENCLAW-FOLLOW-UP.md`
- `docs/contracts/LISA-MAIN-APPROVE-DISPATCH.md`
- `docs/contracts/BUGBOT-MENTION-ONLY.md`
- `docs/contracts/GITHUB-APP-GITOPS-CREDENTIALS.md`
- `SETUP.md`, `README.md`, `VERSION`
- `tests/test-portable-v2-integration.sh`

## Consumer workflow display names

Managed workflows contain `__LINKTREND_*` placeholders. Install/sync paths render names from the committed consumer config:

`.github/linktrend-gitops-consumer.json`

```json
{
  "schemaVersion": 1,
  "ciWorkflowName": "Consumer CI",
  "branchPolicyWorkflowName": "Branch Source Policy",
  "bugbotCheckName": "Cursor Bugbot"
}
```

Repository variables cannot change `workflow_run.workflows` — names must be rendered into static YAML.

## Physical Cursor / Codex bootstrap

Portable v2 installs **physical** Cursor and Codex discovery files inside the consumer.
It does **not** symlink consumer `.cursor` to IDE Development (that breaks Cursor Cloud and violates the portable model).
