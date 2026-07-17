# ADR 0002: Shared Component/Template/Asset Library

**Status:** Accepted (Principal approved Phase 1 remote creation + publication path, 2026-07-17)  
**Date:** 2026-07-17  
**Related:** LiNKdeveloper `docs/adr/0002-shared-library-client.md`

## Context

IDE Development and LiNKdeveloper both need a Component/Template/Asset Library for Module 2 (query / starter-kit decisions) and Module 5 (contribution). Keeping separate libraries would diverge catalogs and break bidirectional reuse. A folder inside either existing repository would make that system the authority and create a runtime coupling the Principal forbids. A database-only catalog without Git-backed entry assets would not satisfy reproducible file hashes and offline-verifiable provenance.

## Decision

1. **Canonical remote:** `https://github.com/linktrend/LiNKlibraries.git` (private).
2. **Canonical branch:** `development` is the single source of truth for approved entries.
3. **Local clones are caches, never authority.** Readers must record the Library commit SHA they used. A stale checkout must be reported with its commit SHA.
4. **Contributions use branches + pull requests.** No system may push directly to `development`, `staging`, or `main`.
5. **Publication authority:** both systems may open contribution PRs after Module 5 gate pass; only the **Librarian** (or Principal override) merges into `development`.
6. **Offline behavior:** read-only from the last verified checkout; never invent or fall back to a private/local Library inside IDE Development or LiNKdeveloper.
7. **No fallback** to either system’s private/local Library on shared Library failure.
8. **Entry layout:**
   ```text
   entries/<entry-id>/entry.json
   entries/<entry-id>/README.md
   entries/<entry-id>/assets/...
   entries/<entry-id>/tests/...
   ```
9. **Schemas:** `schemas/library-entry.schema.json` (schemaVersion `1`) and `schemas/catalog.schema.json`; generated `indexes/catalog.json` sorted by `entryId`, including source commit SHA; not manually edited.
10. **Validation** rejects schema-invalid metadata, missing files, SHA mismatch, duplicate IDs, absolute paths, secret-like material, incomplete `vetted_oss` records, and vendored third-party source without compatible redistribution license.

## Consequences

- IDE Development exposes a repo-relative client under `core/library/` (via `.cursor/library/` compatibility).
- This ADR does **not** authorize deploying applications or coupling LiNKdeveloper runtime to IDE Development.

## Resolved: access pattern

Neither system keeps a full permanent clone, and neither makes a live network call per individual asset lookup (npm / Terraform Registry / Backstage catalog pattern):

1. At Module 2 Library-query, the client fetches lightweight `indexes/catalog.json` only (git sparse-checkout) and caches it with the **fetch commit SHA** (authoritative evidence SHA for Module 2 reports).
2. When a specific entry is selected, the client fetches only `entries/<entry-id>/` into a disposable cache keyed `entryId@commitSHA`.
3. Cache is always safe to delete and re-fetch; never authoritative if it disagrees with a fresh catalog fetch.
4. Implemented in IDE Development as `core/library/library-client.mjs` (same pattern as LiNKdeveloper `packages/shared-library` — not a third different client).

## Resolved: Librarian

- **Where it lives:** inside `LiNKlibraries` as `.github/workflows/librarian-review.yml` + `scripts/librarian/` (not in IDE Development — no persistent runtime; must work for PRs from either system).
- **Authority:** only automated merge authority for `LiNKlibraries` `development` (mirrors Integrator elsewhere). Principal may override manually.
- **Review (above `validate-library.mjs`):** flag likely near-duplicates (non-blocking); block placeholder `vetted_oss` security/license/notes; block vague `integrationNotes`/`gotchas` on `custom_component`/`code_pattern`.
- **Starter Kit:** after merge, may open a PR into LiNKdeveloper (`librarian/<entry-id>-starter-kit-integration`) — does not self-merge. See LiNKdeveloper `docs/librarian/starter-kit-integration-policy.md`.
- IDE Development contributors’ Module 5 PRs are reviewed by this same Librarian.
