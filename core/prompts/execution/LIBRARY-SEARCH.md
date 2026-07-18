# LIBRARY-SEARCH

## Purpose

Query the shared LiNKlibraries catalog during Module 2 (`2.2-library-starter-kit-query`).

## Steps

1. Run `node .cursor/library/library-client.mjs sync` (or `search`).
2. Record the returned `fetchCommitSha` in the Library query report — this SHA is authoritative evidence.
3. When an entry is selected, run `show --entry <id>` to sparse-fetch only that entry subtree.
4. Never fall back to a private/local Library. If the remote/cache is unavailable, stop and report the last verified SHA (or that none exists).

## Output

- Matches from `indexes/catalog.json`
- Exact Library commit SHA used
- Selected entry local cache path (`entryId@commitSHA`) when fetched
