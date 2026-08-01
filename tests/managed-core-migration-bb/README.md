# Managed-core migration black-box fixtures (WP4)

Disposable-repository fixtures and focused tests for migration, conflict,
rollback, idempotence, and portability contracts from Issue #43 Wave 1.

## Scope

- Owns only this directory plus `core/managed-core/migrations/`
- Does **not** implement the installer engine (WP2)
- Does **not** edit existing GitOps suites

## Run

```bash
python3 tests/managed-core-migration-bb/run_tests.py
```

Optional live installer probes (skipped when entrypoint absent):

```bash
python3 tests/managed-core-migration-bb/run_tests.py --with-installer
```

## Fixtures

Each `fixtures/<id>/scenario.json` declares setup + expected classifications
aligned with `docs/contracts/MANAGED-CORE-V2.md` conflict matrix and the
reviewed migration catalog.
