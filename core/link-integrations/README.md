# IDE Development five-provider consumer (pre-rollout source)

This directory is the **fail-closed consumer boundary** for exactly five
providers: LiNKplatform, LiNKlibraries, LiNKbrain, LiNKskills, and LiNKautowork.

| Module | Role |
|---|---|
| `pins.mjs` / `errors.mjs` | Frozen GitHub `development` tips and typed `ConsumerContractError` |
| `platform.mjs` | Identity / permissions / capabilities (`AuthClaims 1.1.0`) |
| `libraries.mjs` | Revision-2 immutable library references |
| `brain.mjs` | Advisory knowledge / coordination projections |
| `skills.mjs` | Immutable skill release addressing and bounded telemetry |
| `autowork.mjs` | Request / status / handoff / receipt validators |
| `mcp.mjs` | Shared MCP `2026-07-28` modern negotiation and optional OKF `0.2` mapping |
| `index.mjs` | Public barrel after S1–S5 validators exist |

This module has **no** transport, credentials, Git write, Ledger, Gate mutation,
or nested self-install APIs. It does not call live provider runtimes. Provider
repositories are not modified by this work.

IDE Development is the system source. It must never receive a nested
`.ide-development/` install of itself. Do not run
`python3 scripts/ide-development.py install` against this repository.

## Pin authority

Pins are the GitHub `development` tip of each provider repository at freeze
time. They are **not** local sibling checkout HEADs, even when a sibling clone
is ahead of `origin/development`. Live `HEAD` or `latest` is not a pin.

Freeze command (read-only):

```bash
gh api repos/linktrend/<Provider>/commits/development --jq '{sha:.sha,tree:.commit.tree.sha}'
```

Frozen on 2026-08-19 (Asia/Taipei) from that GitHub API:

| Key | Repository | Commit | Tree |
|---|---|---|---|
| platform | `linktrend/LiNKplatform` | `adbabf7d399cbfe5c1056d275c3d98eb480397cc` | `b76993f458b6dbed5d2c3e09c2c5e8ad87c6a45d` |
| libraries | `linktrend/LiNKlibraries` | `4cbe7fb174aba4b159d6c37ba1ef65fd3221510f` | `60e582fbd1ce988538b650c99878e700c6cfa0d2` |
| brain | `linktrend/LiNKbrain` | `9042e668dd0c7cef232cb427ffc9c76f06a7a446` | `303a15936932fb5a54b208c934a6d511045cc8e4` |
| skills | `linktrend/LiNKskills` | `e3d80fd22a05a4f68207e130c50b772b5acffda4` | `69a131b46a73a4ef724694bfe240b1a11652bcc9` |
| autowork | `linktrend/LiNKautowork` | `79ee98eb3bd1ae0cce9d34872e90fe7101a9f353` | `deb37e4f3a29339b35613ee799d461c74bb7b585` |

Issue 244 pin SHAs are refused and must not appear as pins in `pins.mjs`.

## MCP and OKF

`negotiateMcp('2026-07-28', 'modern')` is the only accepted negotiation.
Legacy or session `initialize` negotiation fails closed. Optional OKF `0.2`
mapping is field mapping only: it cannot override Brain
`authority=advisory` / `executionAuthority=none`.

Export: `FROZEN_PROVIDERS` from `pins.mjs` (also re-exported from `index.mjs`).
Typed failures use `ConsumerContractError` with a stable `code` from `errors.mjs`.

The installed Wave-1 `core/library/library-client.mjs` stays in place. This
directory does not replace it.

Managed-core materialization for the nine consumers is a later packet after
`v2.4.0`. Pre-rollout source stays under `core/link-integrations/` and
`tests/link-integrations/` only.
