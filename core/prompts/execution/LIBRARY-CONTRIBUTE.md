# LIBRARY-CONTRIBUTE

## Purpose

Module 5 contribution path against the shared LiNKlibraries remote.

## Steps

1. Author `entries/<entry-id>/`-shaped bundle locally (entry.json, README.md, assets, tests).
2. `prepare-contribution --bundle <path>`
3. `validate-contribution --bundle <path>` — must pass before publication.
4. `publish-contribution --bundle <path>`:
   - Default: stop at `publication_pending` with a local bundle.
   - When `LINKTREND_SHARED_LIBRARY_PUBLISH=1`: open a PR into `LiNKlibraries` `development`.
5. The **Librarian** (GitHub Action in LiNKlibraries) reviews and merges — this system does not push to protected branches.

## Gate evidence

- Validation result
- Publication status: `merged` | `publication_pending` | `not_applicable`
- PR URL when opened
