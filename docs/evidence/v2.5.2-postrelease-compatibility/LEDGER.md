# v2.5.2 post-release consumer compatibility ledger

**Issue:** #471
**Mode:** observation only
**Observed:** 2026-08-31T22:14:00Z
**Overall:** `fail_closed`

This packet verified the published v2.5.2 package identity and reconciled existing consumer installation receipts against that identity. It did not reinstall consumers, duplicate an active rollout worker, change immutable release files, promote staging/main, or run a Full suite.

## Released identity (PASS)

| Field | Value |
|---|---|
| Tag | `v2.5.2` (peeled commit `5a64f7f03d3463804b424cc59c4ee048473d9a51`) |
| Source tree | `d2188157f2c32f5ba9c0cf6a5a60c7553cdce58a` |
| `origin/main` | Same commit and tree as the tag |
| Manifest digest | `sha256:a40ef247933c1f3d8efb43f951ee5443a32c3c121e139d0c91d82ad8cd54c384` (bytes of `core/managed-core/MANIFEST.json` at the tag) |
| tar.gz | `sha256:f07224ab119c95ef33ebbebc8665bf11ac8db13b7e66ba550d8888dc8fae3569` (768948 bytes, locally hashed) |
| zip | `sha256:c3d736b7e02d5b95b014002674bc68989135cceedbdc114fd18374e6df5a55f9` (929374 bytes, locally hashed) |
| Publisher | `linktrend-managed-core-release-publisher` |
| Release | https://github.com/linktrend/IDE-Development/releases/tag/v2.5.2 (`378919561`) |

`origin/development` `63a40aafc7da3684c42a3897c5c85ec013cb7686` / tree `be18cecdea03c48a4a866b48182f3187d0169593` is **ahead** of the release (manifest `sha256:e86ce16d48194f75f48b51aaf2fcf31dc6737391aa8cd967ad904571b8c67c83`). That is not the released package. Receipts must bind to the tag/main identity, not to later development bytes that still say `2.5.2`.

## Consumer receipts

Locked order from `docs/GITOPS-CONSUMER-ROLLOUT.md`. Development is the installation-receipt surface for this packet. Staging/main were observed and not promoted.

| # | Repository | `development` receipt | Notes |
|---|---|---|---|
| 1 | `openclaw_prime` | **match** | Manifest hash equals the published release |
| 2 | `LiNKplatform` | **observation_unavailable** | GitHub API 404 |
| 3 | `LiNKskills` | **match** | Manifest hash equals the published release |
| 4 | `LiNKbrain` | **observation_unavailable** | GitHub API 404 |
| 5 | `LiNKsites` | **mismatch (fail closed)** | Version text `2.5.2`, manifest `sha256:b18da538fec322fc49989288d6aedeea92dd4e477ef1e65f222b9d44cbe54c61` |
| 6 | `LiNKdeveloper` | **observation_unavailable** | GitHub API 404 |
| 7 | `LiNKlibraries` | **observation_unavailable** | GitHub API 404 |
| 8 | `LiNKautowork` | **match** | Manifest hash equals the published release |
| 9 | `LiNKtrading-codebase` | **observation_unavailable** | GitHub API 404 |

Machine-readable record: `consumer-compatibility-ledger.json`.

## Fail-closed reasons

1. `portfolio_observation_incomplete` — five locked-order consumers were not readable with this token.
2. `consumer_manifest_hash_mismatch` — `linktrend/LiNKsites` `development` claims `2.5.2` with a different MANIFEST digest. This packet did not reinstall it.

## Out of scope (honored)

No consumer mutation, no second rollout worker, no VPS, no live trading, no live Lisa, no staging/main/production promotion, no Full suite.
