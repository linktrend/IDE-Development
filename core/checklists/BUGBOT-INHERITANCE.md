# Bugbot Inheritance Checklist

Complete for every repo that inherits autonomous Git ops from IDE Development (after wire or backfill).

**SOT:** `docs/AUTONOMOUS-GIT-OPERATIONS.md` · ADR `docs/adr/0003-autonomous-ship-pull-promote.md`

## Why

Layer B installs GitHub Actions. **Bugbot** is the Reviewer for PRs into `development`. It is enabled on [cursor.com](https://cursor.com) / GitHub integration — not by the symlink alone.

## Checklist (per GitHub repo)

1. Confirm repo is under the `linktrend` GitHub org connected to Cursor.
2. Open Cursor dashboard → **Bugbot** (or Agents / Bugbot settings).
3. Enable Bugbot for this repository (or org-default that includes it).
4. Open a test PR into `development` and confirm Bugbot posts a review.
5. Prefer branch protection on `development` that requires:
   - relevant CI checks
   - at least one approving review (Bugbot counts when configured as a reviewer)
6. Record completion in the adoption/wire report: `Bugbot: enabled | blocked:<reason>`.

## If Bugbot cannot be enabled

- Do **not** invent a Mini-side Reviewer as the default.
- Document the blocker for the Principal.
- Integrator must **not** force-merge without an independent review path.

## Related

- Managed workflows: `core/github/managed-workflows/`
- Wire: `scripts/wire-repo.sh`
- Automations: `docs/CURSOR-AUTOMATIONS-SETUP.md`
