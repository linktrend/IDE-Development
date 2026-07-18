# Shared Library client (IDE Development)

Repo-relative client for the canonical LiNKtrend Component/Template/Asset Library:

- **Remote:** `https://github.com/linktrend/LiNKlibraries.git`
- **Branch:** `development`
- **Compatibility path:** `.cursor/library/` → `core/library/`

## Access pattern (resolved)

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
node .cursor/library/library-client.mjs prepare-contribution --bundle <path>
node .cursor/library/library-client.mjs validate-contribution --bundle <path>
node .cursor/library/library-client.mjs publish-contribution --bundle <path>
```

Publication opens (or prepares) a PR into `LiNKlibraries`. The **Librarian** Action in that repo reviews and merges into `development` — not this client.

## Config

| Variable | Purpose |
|---|---|
| `LINKTREND_SHARED_LIBRARY_REPO_URL` | Canonical remote |
| `LINKTREND_SHARED_LIBRARY_CHECKOUT` | Disposable cache root |
| `LINKTREND_SHARED_LIBRARY_BASE_BRANCH` | Default `development` |
| `LINKTREND_SHARED_LIBRARY_OFFLINE` | `1` = cache-only |
| `LINKTREND_SHARED_LIBRARY_PUBLISH` | `1` = allow PR open |

Auth via environment / GSM injection — never committed.
