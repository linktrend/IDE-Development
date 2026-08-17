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
| Finding-reviewed tip | `90dd3faf88117cb3e488c7f17517d5a8b0fa8e5b` (historical review target; not current tip claim) |
| Content head/tree | `fc7936597bb4e3ba2453ff062e43ab93b57898e9` / `f196ad70995bf1514ab3a61d85901ea1adf668d6` |
| Evidence head/tree | `b5eace1792fe2727e37b9f9accef01dd57ec11d0` / `d467c0fdfa7142b6a997bfd5fcecdfbd796524db` |
| Final tip binding | branch HEAD after this bind-metadata commit; tip SHA not self-embedded (non-self-reference boundary) |
| Novel packet commit range | `fc7936597bb4e3ba2453ff062e43ab93b57898e9..b5eace1792fe2727e37b9f9accef01dd57ec11d0` (through evidence head; bind-metadata tip follows without self-SHA) |
| Phase base at handoff | not used |

## Topology notes

Retry branch created from the serially integrated `phase/v240-core-through-u01` tip after matrix dependencies WP-U03/U07/U01 were integrated. Prior HOLD branch left unchanged as audit history. Spec Update-6 language naming Update 2 is treated as forward-reference; matrix order places WP-U02 after WP-U06 (not implemented here).

Repair R1 closes independent findings on tip `90dd3fa`: trusted FullSuiteReceipt body parse + metadata/body equality before `exact`; schemaVersion exactly 2 + digest integrity on merge eligibility; Integrator `eligible` CLI routed through retained-receipt gate. U03 `phase_merge_eligibility` library checks remain available for non-CLI callers.

Identity model: **content-head / evidence-head / final-bind-tip**.

## Rollback

Leave the issue branch unmerged. Do not invent empty commits/PRs. Do not weaken FullSuiteReceipt schemaVersion 2 identity. Do not prefer-incoming. No U02/U05/Full/PR/promotion/rollout in this packet.
