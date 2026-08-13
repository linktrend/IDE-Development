# Shared Library client (IDE Development)

Repo-relative client for the canonical LiNKtrend Component/Template/Asset Library:

- **Remote:** `https://github.com/linktrend/LiNKlibraries.git`
- **Branch:** `development`
- **Compatibility path:** `.cursor/library/` → `core/library/`
- **Schemas:** `schemas/catalog.schema.json` and `schemas/library-entry.schema.json` are the
  immutable Wave 1 contract copies; the client applies their v2 shape plus the
  authority's admission, inventory, and state semantics.

## Revision 2 consumer (canonical)

`library-v2-client.mjs` is the canonical frozen-provider consumer for the
LiNKlibraries Revision 2 contract. It accepts only provider commit
`87dbb71da8b07be8f83eb82f8f769e16b062e7b2` and tree
`f258bf45d91a90fb4c818ee9012c7a85b1fa96da`, then enforces the progressive
sequence: a bounded catalogue page, a shortlist record, its immutable manifest,
and selected facts with a local consumption receipt. It validates the catalogue,
manifest, inventory, and closure chain, rejects legacy catalogues or mutable
references, and permits offline reuse only of a fresh, receipt-verified v2
chain. It does not execute provider code or make provider authority decisions.

`library-client.mjs` below is the retained legacy compatibility client. It is
not Revision 2 proof and must not be used to claim Revision 2 consumption.

## Legacy access pattern (resolved)

Same mechanism as LiNKdeveloper `@linkdeveloper/shared-library` (do not invent a third client):

1. **Module 2 Library-query:** `sync` / `fetchCatalog()` pulls only `indexes/catalog.json` via git sparse-checkout and caches it with the **fetch commit SHA**.
2. **On entry selection:** `show --entry <id>` / `fetchEntry()` pulls only `entries/<entry-id>/` and caches as `entryId@commitSHA`.
3. **Disposable cache** under `LINKTREND_SHARED_LIBRARY_CHECKOUT` (default `core/library/.cache/linklibraries`). Safe to delete; never authoritative over a fresh catalog fetch. Offline (`LINKTREND_SHARED_LIBRARY_OFFLINE=1`) reads the last verified cache only and fails closed if missing.
4. **No private/local Library fallback** on shared Library failure.

## CLI

```bash
node .cursor/library/library-client.mjs sync
node .cursor/library/library-client.mjs search --query <text> [--kind <kind>]
node .cursor/library/library-client.mjs show --entry <id>
node .cursor/library/library-client.mjs select --entry <id> \
  [--consumer-root <path>] [--framework <name>] \
  [--dependency <name=version>] [--service <name>] \
  [--runtime <name>] [--node-version <version>] [--operating-system <name>]
node .cursor/library/library-client.mjs report --entry <id>
node .cursor/library/library-client.mjs verify-cache --entry <id>
node .cursor/library/library-client.mjs prepare-contribution --bundle <path>
node .cursor/library/library-client.mjs validate-contribution --bundle <path>
node .cursor/library/library-client.mjs publish-contribution --bundle <path>
```

`select` is the only selection path. It rejects metadata-only, quarantined,
superseded, and non-selectable records, then checks Node/runtime/framework/
dependency compatibility. `report` and `verify-cache` expose durable evidence.
By default, CLI selection reads `package.json` from the current working
directory. Repeat `--framework`, `--dependency`, or `--service` to supply
explicit consumer context when it is not represented by that package file.

Publication never mutates GitHub from this client. It reports
`publication_disabled`, `publication_missing_authority`, or
`publication_pending` truthfully; the **Librarian** Action in LiNKlibraries
reviews and merges contribution PRs into `development`.

## Config

| Variable | Purpose |
|---|---|
| `LINKTREND_SHARED_LIBRARY_REPO_URL` | Canonical remote |
| `LINKTREND_SHARED_LIBRARY_CHECKOUT` | Disposable cache root |
| `LINKTREND_SHARED_LIBRARY_BASE_BRANCH` | Default `development` |
| `LINKTREND_SHARED_LIBRARY_OFFLINE` | `1` = cache-only |
| `LINKTREND_SHARED_LIBRARY_PUBLISH` | `1` = allow PR open |

Auth via environment / GSM injection — never committed.
