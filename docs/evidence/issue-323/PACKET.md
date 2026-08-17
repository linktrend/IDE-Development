# Packet WP-U06 — Pre-merge receipt sealing and recovery

## Identity (fill at execution only)

| Field | Value |
|---|---|
| Packet ID | WP-U06 |
| Spec update | Update 6 |
| PRD acceptance | AC-U06-01–AC-U06-10 |
| Depends on (matrix) | WP-U03, WP-U07, WP-U01 |
| Repository |  |
| Issue | 323 |
| Branch |  |
| Parallel lane | serial |
| Docs authority |  / tree  |
| Start commit |  |
| Start tree |  |
| Predecessor phase |  (independently verified CLEAN) |
| HOLD audit branch preserved |  @  |
| Finding-reviewed tip |  (historical review target; not current tip claim) |
| Content head/tree |  /  |
| Evidence head/tree | (set at evidence commit; bind tip follows without self-SHA) |
| Final tip binding | branch HEAD after bind-metadata commit; tip SHA not self-embedded |
| Novel packet commit range | through evidence head; bind-metadata tip follows without self-SHA |
| Phase base at handoff | not used |

## Topology notes

Retry branch from serially integrated . HOLD branch preserved. R1 closed receipt-body trust findings. R2 requires exhaustive metadata/body cross-check of duplicated trust fields before exact selection; identity for expected matching is body-only.

Identity model: **content-head / evidence-head / final-bind-tip**.

## Rollback

Leave the issue branch unmerged. Do not invent empty commits/PRs. Do not weaken FullSuiteReceipt schemaVersion 2 identity. Do not prefer-incoming. No U02/U05/Full/PR/promotion/rollout in this packet.
