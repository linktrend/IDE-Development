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
| Content head/tree | `39d2afca2e383b982ad03284232ed3acf74102e0` / `18a56e15dc7a784a3908ba34379b56d24f7c3681` |
| Evidence head/tree | `b0ff0eca52223869aab9a9e4d7f84ffa55bd07aa` / `4dc97d47ea10d2d35b1d8bca27e099ef8649b1fe` |
| Final tip binding | branch HEAD after this bind-metadata commit; tip SHA not self-embedded (non-self-reference boundary) |
| Novel packet commit range | `39d2afca2e383b982ad03284232ed3acf74102e0..b0ff0eca52223869aab9a9e4d7f84ffa55bd07aa` (through evidence head; bind-metadata tip follows without self-SHA) |
| Phase base at handoff | not used |

## Topology notes

Retry branch created from the serially integrated `phase/v240-core-through-u01` tip after matrix dependencies WP-U03/U07/U01 were integrated. Prior HOLD branch left unchanged as audit history. Spec Update-6 language naming Update 2 is treated as forward-reference; matrix order places WP-U02 after WP-U06 (not implemented here).

Identity model: **content-head / evidence-head / final-bind-tip**.

## Rollback

Leave the issue branch unmerged. Do not invent empty commits/PRs. Do not weaken FullSuiteReceipt schemaVersion 2 identity. Do not prefer-incoming. No U02/U05/Full/PR/promotion/rollout in this packet.
