# Managed-core migration black-box fixtures (WP4)

Disposable-repository fixtures and focused tests for migration, conflict,
rollback, idempotence, and portability contracts from Issue #43 Wave 1 /
Issue #64 live installer proofs.

## Scope

- Owns only this directory plus `core/managed-core/migrations/`
- Does **not** implement the installer engine (WP2)
- Does **not** edit existing GitOps suites

## Run

Fixture classification + catalog checks (skip live installer):

```bash
python3 tests/managed-core-migration-bb/run_tests.py --without-installer
```

Default when `scripts/ide-development.py` is present: also run live installer
end-to-end proofs (or force with `--with-installer`):

```bash
python3 tests/managed-core-migration-bb/run_tests.py
python3 tests/managed-core-migration-bb/run_tests.py --with-installer
```

Live proofs invoke the real CLI against disposable repos and the hermetic
package at `fixtures/live-package/` (not the system MANIFEST, which may be
dirty during parallel installer work).

## Live scenarios

| Fixture | Live proof |
|---------|------------|
| `01-external-cursor-symlink` | Physical migrate required; outside untouched; rollback restores symlink |
| `07-interrupted-transaction` | Recover via next mutating `update` |
| `08-byte-exact-rollback` | CLI `rollback` restores bytes+modes |
| `09-idempotent-repeat` | Repeat install/update byte-identical |

## Fixtures

Each `fixtures/<id>/scenario.json` declares setup + expected classifications
aligned with `docs/contracts/MANAGED-CORE-V2.md` conflict matrix and the
reviewed migration catalog.
