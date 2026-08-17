# IDE Development five-provider consumer (pre-rollout source)

This directory is the **fail-closed consumer boundary** for exactly five
providers: LiNKplatform, LiNKlibraries, LiNKbrain, LiNKskills, and LiNKautowork.

WP-I6-S0 freezes pin identities and the typed error class. Provider validators
arrive in later packets. This module has **no** transport, credentials, Git
write, Ledger, or Gate mutation APIs. It does not call live provider runtimes.

IDE Development is the system source. It must never receive a nested
`.ide-development/` install of itself.

## Pin authority

Pins are the GitHub `development` tip of each provider repository at freeze
time. They are **not** local sibling checkout HEADs, even when a sibling clone
is ahead of `origin/development`. Live `HEAD` or `latest` is not a pin.

Freeze command (read-only):

```bash
gh api repos/linktrend/<Provider>/commits/development --jq '{sha:.sha,tree:.commit.tree.sha}'
```

Frozen on 2026-08-17 (Asia/Taipei) from that GitHub API:

| Key | Repository | Commit | Tree |
|---|---|---|---|
| platform | `linktrend/LiNKplatform` | `2d5f37ef6b8e40ad47305adab47613d915967c1b` | `90b51726f7a77e4620151a463a10cfc3d2007c88` |
| libraries | `linktrend/LiNKlibraries` | `5901d111309543ed0839938d7217475e5d4b8ac4` | `185d7cf714777d60a2d01a4881bf1a11bc5018d9` |
| brain | `linktrend/LiNKbrain` | `77af7d02a76e6a8877d59fbd3d3e917ac6e830c5` | `0cae42d612342f5e52c7e2e0e76cb6fc2f6d81f3` |
| skills | `linktrend/LiNKskills` | `0d6bf34546f89c9beb7f05483a3ed4deeb3a5a67` | `6c36e6c98f90e55d957fba781327b1b0ef90860a` |
| autowork | `linktrend/LiNKautowork` | `9caab9aa33de5f96e33d67d880f2934dc6fd9fef` | `5f306d674780a5a26048017f916da6048d71e7a5` |

Issue 244 pin SHAs are refused and must not appear in `pins.mjs`.

Export: `FROZEN_PROVIDERS` from `pins.mjs`. Typed failures use
`ConsumerContractError` with a stable `code` from `errors.mjs`.

The installed Wave-1 `core/library/library-client.mjs` stays in place. This
directory does not replace it.

Managed-core materialization for the nine consumers is a later packet after
`v2.4.0`. Provider repositories are not modified by this work.
