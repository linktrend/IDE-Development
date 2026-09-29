# Migration catalog (Wave 1 / WP4)

Reviewed supersession catalog for IDE Development managed-core v2.

## Authority

- Contract: `docs/contracts/MANAGED-CORE-V2.md` (exact identity + hash removals; fail closed on mismatch)
- Installer loader (WP2): expects `schemaVersion: 1` and `entries[]` with `identity`, `path`, `contentHash`, `action: "remove"`
- This directory (`core/managed-core/migrations/`) is the Wave 1 packet-owned catalog root

## Layout

```text
migrations/
  README.md
  schema.json
  catalog.json
  scenarios.json
  known-bytes/          # reviewed exact bytes for supersession hashes
```

## Hard rules

1. Removals require **exact** `identity` and `contentHash` match.
2. Hash mismatch or unknown/modified content → **fail closed** (do not delete).
3. No absolute host paths, credentials, tokens, or secret values in catalog or known-bytes.
4. Catalog paths are repo-relative POSIX paths only (no `..`, no drive letters).
5. Symlink / sparse-GitOps / dirty-tree / rollback / idempotence behaviors are proven by black-box fixtures under `tests/managed-core-migration-bb/`; this catalog supplies exact-removal identities those fixtures exercise.
6. `scenarios.json` ids / `fixture` fields must match `tests/managed-core-migration-bb/fixtures/<id>/` directory names one-to-one (titles stay aligned with each fixture’s `scenario.json`).

## v3.0.0 retirements

- Generated, never hand-edited: `python3 -m ide_development.v3_retirements --write` (from `scripts/`) adds one `remove` entry (`sincePackageVersion: "3.0.0"`, `reason: "Retired in v3 (<component>)"`) for every destination in the v2.5.2 manifest (release commit `5a64f7f`) that the current manifest no longer declares, with the v2.5.2 hash. `--check` fails on drift.
- One `contentHash` per path (the loader rejects duplicate paths). The v2.5.2 hash is kept because v3 upgrades start from v2.5.2; an older-release entry for the same path is replaced. `--report-older` lists paths whose bytes differed in an older published release; those bytes are refused as conflicts, never deleted (`docs/runbooks/v3-upgrade.md`).
- Retired root workflows in consumer `.github/workflows/` were rendered per consumer by the v2 `scripts/sync-managed-workflows.sh`, so they have no fixed hash. `known-bytes/retired-workflow-<release>-<name>` holds every distinct published v2 template (named by the first release that shipped it); `scripts/ide_development/retired_workflows.py` renders them for the consumer and adds one exact-hash identity per workflow to the installer plan and to the sync script.

## Related

- Black-box fixtures/tests: `tests/managed-core-migration-bb/`
- WP1 layout note: `core/managed-core/migration/` (singular) is a discovery alias pointer only — no duplicate catalog file
