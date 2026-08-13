# W2-P2 — Package, Installer, Manifest, Migration, and Legacy Removal

## Objective

Make the GitHub-hosted delivery system the actual managed-core product, migrate
existing consumers deterministically, and remove former App/self-hosted/Mac
implementation files from the released package.

## Dependencies and base

- Wave 1 combined PASS and exact Phase SHA.
- Consume W2-P1 workflow filenames through the frozen list Terra records before
  dispatch. If W2-P1 is not complete, use agreed filenames and let Terra integrate.

## Owned paths

- `core/managed-core/MANIFEST.json` and manifest source/generator
- `scripts/ide-development.py`, `scripts/ide_development/*`
- managed-core default configs and migration definitions
- package/version/release metadata except final version number chosen in W3-P1
- installer/migration/idempotence tests
- obsolete managed source files positively identified during preflight

Do not edit live workflow logic owned by W2-P1 or external GitHub/host state.

## Required implementation

1. Include the new schemas/config/workflows/receipts/lifecycle/docs/tests in the
   managed manifest with deterministic digests.
2. Remove obsolete App-backed publisher/Packager/Integrator/repair/promotion files
   or replace them with non-App hosted equivalents from W2-P1; no dead App path may
   remain installable.
3. Remove self-hosted/Mac/ephemeral runner config, runner image definitions,
   coordinator installation hooks, and host service material from the package.
4. Implement exact migration from the currently released package. Preserve
   repository-owned config and required checks; translate known legacy defaults.
5. Delete stale managed files during upgrade only when installed-state proves
   ownership and bytes are known or safely classified. Preserve modified or
   consumer-owned files and report conflicts.
6. Make install twice byte-idempotent.
7. Add uninstall/rollback support for the new managed version without resurrecting
   custom App or self-hosted infrastructure automatically.
8. Ensure IDE Development system source remains a self-verification target and is
   never nested-installed.
9. Generate a managed external-cleanup plan listing names/IDs without secret values;
   applying external cleanup remains W3 authority.
10. Keep the exact nine-repository rollout inventory current.

## Acceptance criteria

- Fresh disposable consumer install succeeds and contains no old App/runner path.
- Upgrade disposable consumer preserves consumer-owned sentinel files/settings.
- Modified obsolete managed file is not destructively deleted; installer stops or
  preserves/reports according to policy.
- Second install yields no diff.
- Generated manifest matches disk and all managed paths exist.
- Static scan of active package/source finds no former custom App secret names,
  token minting, self-hosted labels, Mac runner labels, or coordinator installer,
  except migration/removal detection constants clearly marked non-executable.
- Rollback fixture works and does not silently reinstall legacy external state.

## Validation

Run installer, manifest, managed-workflow parity, fresh-install, upgrade,
idempotence, and rollback suites discovered in preflight, plus:

```bash
bash scripts/verify-ide-development.sh
```

Use temporary directories created safely; never install into IDE Development.

## Prohibited

- No consumer production edit, live GitHub setting/App/runner mutation, host or
  Docker deletion, PR, merge, promotion, tag, release publication, or billing.
- No deletion based only on filename resemblance.

## Handoff

Return one exact commit, manifest digest, fresh/upgrade/idempotence/rollback logs,
list of package files removed/replaced, and redacted external cleanup plan.

