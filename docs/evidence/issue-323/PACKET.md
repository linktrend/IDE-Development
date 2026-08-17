# Packet WP-U06 — Pre-merge receipt sealing and recovery

## Identity (fill at execution only)

| Field | Value |
|---|---|
| Packet ID | WP-U06 |
| Spec update | Update 6 |
| PRD acceptance | AC-U06-01–AC-U06-10 |
| Depends on (matrix) | WP-U03, WP-U07, WP-U01 |
| Repository | `linktrend/IDE-Development` |
| Issue | 323 |
| Branch | `issue/323-wp-u06-from-integrated-core` |
| Parallel lane | serial |
| Docs authority | `3a5d15231d65b8549d64971960b2aeb617b58838` / tree `6b9f73f1e78ae4abda3b78b939adc190b6d0842a` |
| Start commit | `194078a4186da110e42f514aed860683b0bdbe23` |
| Start tree | `9fb4583be84b1fe2bd9bf70fd5e15e65cf674117` |
| Predecessor phase | `phase/v240-core-through-u01` (independently verified CLEAN) |
| HOLD audit branch preserved | `issue/323-implement-ide-development-v2-4-0-wp-u06` @ `867009f0f33a9a6426c6680a8e95fbec66dc9b02` |
| Finding-reviewed tip | `0b4905f066a8248c39058d198d074b036a50d816` (historical review target; not current tip claim) |
| Content head/tree | `54e8e8ce0905988aa62116a5032e206c7454b1fe` / `c01ccf93215c1e5e49c2f5e9db41881f73d7a4ff` |
| Evidence head/tree | `293ce7d1e01e41681290313ae6e0f59cb7961d36` / `aa4c56173496e4aff7552a8b279a0bb90d31d9ef` |
| Final tip binding | branch HEAD after this bind-metadata commit; tip SHA not self-embedded (non-self-reference boundary) |
| Novel packet commit range | `54e8e8ce0905988aa62116a5032e206c7454b1fe..293ce7d1e01e41681290313ae6e0f59cb7961d36` (through evidence head; bind-metadata tip follows without self-SHA) |
| Phase base at handoff | not used |

## Topology notes

Retry branch from serially integrated `phase/v240-core-through-u01`. HOLD branch preserved. R1 closed receipt-body trust findings. R2 requires exhaustive metadata/body cross-check of duplicated trust fields before exact selection; identity for expected matching is body-only.

Identity model: **content-head / evidence-head / final-bind-tip**.

## Rollback

Leave the issue branch unmerged. Do not invent empty commits/PRs. Do not weaken FullSuiteReceipt schemaVersion 2 identity. Do not prefer-incoming. No U02/U05/Full/PR/promotion/rollout in this packet.
