# Named CI gate contracts

**Audience:** Review Packager, Integrator, Staging/Main promotion, agents, CI maintainers.  
**Status:** Binding for IDE Development GitOps redesign.  
**Related:** `docs/adr/0003-autonomous-git-operations.md`, `core/github/REVIEW-READY.md`.

---

## Why named gates exist

Workflows must **not** wait for “every visible GitHub check.” That pattern is fragile (renamed checks, optional jobs, third-party noise). Instead, each lifecycle stage waits only on a **named gate contract**.

Missing required checks are **failure / not-ready**, never success.

---

## Gate names

| Gate | Used by | Purpose |
|------|---------|---------|
| `fast-gate` | Review Packager (before Bugbot), Integrator (before merge to `development`) | Deterministic PR validation that must pass before human/Bugbot review or auto-merge. |
| `staging-gate` | Development → Staging promotion | Validates the promotion candidate before staging advances. |
| `release-gate` | Staging → Main merge (Approve path) | Validates the exact release SHA before main advances. |

Check conclusion names that satisfy each gate are defined below for **this** repository. Consumer repos map their own job names to the same gate ids when they adopt the managed workflows.

---

## IDE Development mappings

### `fast-gate`

All of the following must conclude **success** on the PR head SHA (when the workflow exists and is required for that event):

| Check name (GitHub check / workflow job display) | Source |
|--------------------------------------------------|--------|
| `Verify IDE Development` | `.github/workflows/verify-ide-development.yml` (job `verify`) |

Optional / informational checks that must **not** block `fast-gate`:

- Docs-only or advisory workflows not listed above
- `Cursor Bugbot` (separate success check — see Bugbot contract)
- Unrelated third-party checks not in this table

If `Verify IDE Development` did not run for the head SHA, treat as **not ready** (missing ≠ success).

### `staging-gate`

For development→staging **promotion PRs** from temporary `promote/staging/*` branches:

| Check name | Source |
|------------|--------|
| `Verify IDE Development` | Must be **success on the promotion PR head** (combined staging candidate), not merely on `development` alone |

### `release-gate`

For staging→main **promotion PRs** from temporary `promote/main/*` branches (Approve path):

| Check name | Source |
|------------|--------|
| `Verify IDE Development` | Must be **success on the promotion PR head** (combined main candidate), not merely on `staging` alone |

Prior green results on source branches are **not** proof of the combined promotion.

---

## Bugbot success check (separate from gates)

| Check name | Meaning |
|------------|---------|
| `Cursor Bugbot` | Required Bugbot success conclusion for Integrator auto-merge. |

Bugbot is **not** part of `fast-gate`. Deterministic gates run first; Bugbot is requested only after `fast-gate` is green (or after Review Packager has confirmed deterministic readiness).

---

## Integrator decision matrix (summary)

Auto-merge to `development` only when **all** are true:

1. PR is into `development`, non-draft, open.
2. Head SHA equals the recorded reviewed SHA (Bugbot marker / review-ready association).
3. `fast-gate` all required checks = success.
4. `Cursor Bugbot` = success for that head SHA.
5. No `conflict_blocked` / mergeability conflict.
6. Within conflict-repair budget (see conflict recovery).

Otherwise: leave open, comment why, or wait.

---

## Consumer adoption

When syncing managed workflows into a consumer:

1. Keep gate **ids** (`fast-gate`, `staging-gate`, `release-gate`) stable.
2. Replace IDE check names with that repo’s primary verify workflow job names.
3. Document the mapping in the consumer’s `docs/` or workflow comments.
4. Never invent “wait for all checks” as a shortcut.

---

## Change control

Changing required check names is a **contract change**: update this file, tests that assert the names, and any workflow `env` lists in the same PR.
