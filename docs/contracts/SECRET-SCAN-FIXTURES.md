# Fixture-aware secret scanning

**Status:** Active for `v2.4.0` Update 10.
**Scanner:** `scripts/gitops/secret_scan.py`
**Migration helper:** `scripts/gitops/secret_scan_migrate.py`
**Declaration:** `.github/linktrend-secret-scan-fixtures.json`
**Schemas:** `core/managed-core/schemas/secret-scan-fixtures.schema.json`,
`core/managed-core/schemas/secret-scan-result.schema.json`

Managed Fast and Full run the scanner over every tracked file. Test
directories are never excluded wholesale. A synthetic value may pass only
through an exact versioned non-production declaration bound to repository
path, line and field, content digest or bytes, the candidate content tree,
and the scanner-policy version.

## Synthetic namespace

Approves only values in the `ltfx.` namespace. Realistic GitHub, cloud,
database, private-key, and high-entropy token formats cannot be approved,
even if declared.

## Result kinds

One run reports every finding and fixture error together:

- `credential_finding`
- `approved_synthetic_fixture`
- `stale_fixture_declaration`
- `fixture_scope_violation`

One-byte changes, stale digests, renamed files, duplicated values, unknown
rules, undeclared fixtures, and candidate-tree or scanner-policy drift fail
closed until the declaration is intentionally refreshed and reviewed.

## Repository-owned scanners

`.github/linktrend-repository-secret-scanners.json` may name additional
scanners such as GitHub secret scanning, CodeQL, or gitleaks. They remain
additive and blocking. The managed fixture mechanism cannot suppress them.

## Migration helper

`python3 scripts/gitops/secret_scan_migrate.py --repo .` identifies likely
synthetic candidates only. It never writes an approval and never auto-approve.
