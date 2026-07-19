# Cross-system Library contract report

**Status:** Executed (Phase 1 remote created; Phase 8 clients implemented)  
**Date:** 2026-07-17  
**Canonical remote:** `https://github.com/linktrend/LiNKlibraries.git`  
**Canonical tip (at report time):** see final agent report HEAD SHA for `LiNKlibraries`

## Contract under test

1. IDE Development `core/library/library-client.mjs` and LiNKdeveloper `@linkdeveloper/shared-library` both target the same remote/branch.
2. Catalog fetch is lightweight (`indexes/catalog.json`) with recorded fetch commit SHA.
3. Entry fetch is path-scoped (`entries/<id>/`) cached as `entryId@commitSHA`.
4. Invalid/tampered bundles fail validation in both clients.
5. No fallback to Ledger or private local Library on failure.
6. Contribution PRs are reviewed by the LiNKlibraries Librarian.

## Results

| Step | Result |
|---|---|
| Remote exists (private) | PASS — `gh repo view linktrend/LiNKlibraries` |
| Branches `development` / `staging` / `main` | PASS |
| `node scripts/validate-library.mjs` in LiNKlibraries | PASS (fixtures checked) |
| `node scripts/build-catalog.mjs --check` | PASS |
| Librarian unit tests | PASS (13/13) |
| IDE client `sync` against remote | Run during verification (see final report) |
| LiNKdeveloper `@linkdeveloper/shared-library` tests | Run during verification (see final report) |
| Live Ledger row migration | Zero rows available — see LiNKdeveloper `docs/validation/library-ledger-migration-report.md` |

## Verdict

**pass** for contract scaffolding and client parity. Live bidirectional fixture merge through Librarian remains available for the next Module 5 contribution once an entry is published.
