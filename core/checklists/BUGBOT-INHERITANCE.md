# Bugbot Inheritance Checklist

Complete for every repo that inherits autonomous Git ops from IDE Development (after wire or backfill).

**SOT:** `docs/AUTONOMOUS-GIT-OPERATIONS.md` · ADR `docs/adr/0003-autonomous-ship-pull-promote.md`

## Why

Layer B installs GitHub Actions. **Bugbot** is the Reviewer for PRs into `development`. It is enabled on [cursor.com](https://cursor.com) / GitHub integration — not by the symlink alone.

## What “Bugbot pass” means

Authoritative signal is the GitHub check named **`Cursor Bugbot`** (see [Cursor Bugbot docs](https://cursor.com/docs/bugbot)):

| Check conclusion | Meaning | Integrator |
|---|---|---|
| `success` | No issues, and no unresolved Bugbot comments from earlier runs | **May merge** |
| `neutral` | Findings remain (default when Bugbot reports issues), cancelled, or internal error | **Must not merge** |
| `failure` | Findings and fail-on-unresolved-issues is enabled | **Must not merge** |

Bugbot usually posts **`COMMENTED`** reviews. It does **not** need to GitHub-APPROVE. Integrator keys off the check, not `review.state == approved`.

Optional (if available on the Cursor team): enable **fail on unresolved issues** so findings become `failure` instead of `neutral`. Integrator already treats non-`success` as a block, so this is defense-in-depth for the GitHub merge button / ruleset.

## Checklist (per GitHub repo)

1. Confirm repo is under the `linktrend` GitHub org connected to Cursor.
2. Open Cursor dashboard → **Bugbot** (or Agents / Bugbot settings).
3. Enable Bugbot for this repository (or org-default that includes it).
4. Open a test PR into `development` and confirm Bugbot posts a review **and** a `Cursor Bugbot` check.
5. Apply the development merge ruleset (requires Bugbot + CI checks):
   ```bash
   # IDE Development defaults:
   ./scripts/apply-development-merge-ruleset.sh

   # Consumer with different CI job name(s):
   ./scripts/apply-development-merge-ruleset.sh linktrend/YourRepo \
     "Cursor Bugbot" "Your CI job name" "Enforce allowed PR source branches"
   ```
6. Confirm Integrator workflow is present: `.github/workflows/linktrend-integrator-merge.yml`.
7. Set GitHub Actions variable `LINKTREND_INTEGRATOR_REQUIRED_CHECKS` to this repo's **fast-gate** CI job name(s), comma-separated (example for IDE Development: `Verify IDE Development`). Integrator no longer waits for every visible check — see `core/github/CI-GATE-CONTRACTS.md`. Leave unset only if the managed workflow default is wrong for the consumer (then set explicitly).
8. Confirm Review Packager workflow is present: `.github/workflows/linktrend-review-packager.yml` (Tue/Fri 08:00 Asia/Taipei). Bugbot request default command is `@cursor review` (configurable; with the `@`); success check remains `Cursor Bugbot`. The 2-request limit counts only comments with an executable trigger (`@cursor review` or `bugbot run`) **plus** `<!-- linktrend-bugbot-requested: <sha> -->`; bare historical `cursor review` + marker does not count.
9. Confirm Integrator managed template matches live file after sync (`cmp` in IDE Development verify).
10. Record completion in the adoption/wire report: `Bugbot: enabled | blocked:<reason>`.

## If Bugbot cannot be enabled

- Do **not** invent a Mini-side Reviewer as the default.
- Document the blocker for the Principal.
- Integrator must **not** force-merge without an independent review path.

## Related

- Managed workflows: `core/github/managed-workflows/`
- Integrator: `core/github/managed-workflows/linktrend-integrator-merge.yml`
- Ruleset helper: `scripts/apply-development-merge-ruleset.sh`
- Wire: `scripts/wire-repo.sh`
- Automations: `docs/CURSOR-AUTOMATIONS-SETUP.md`
