# Coding Execution Protocol

**Status:** Canonical  
**Protocol id:** `coding-execution-protocol`  
**Protocol version:** 1.0.1  
**Amendment:** `V25_BOOTSTRAP_LEAN`
**Schema:** `core/contracts/EXECUTION-MANIFEST.schema.json`  
**Control contract:** `core/contracts/EXECUTION-CONTROL-CONTRACT.md`

This document installs the execution semantics for bounded implementer packets. It does not copy project history, prior PRDs, or chat transcripts. Runtime discovery and schema validation live beside this file; delivery workflow YAML is out of scope.

## 1. Identity

1. The protocol id is `coding-execution-protocol` and the version is `1.0.1`.
2. Founder-approved amendment `V25_BOOTSTRAP_LEAN` is required on every execution-manifest.
3. An execution program is described by a schema-valid **execution-manifest**.
4. Work is packet-scoped. An issue (`ISS-*`) is the atomic executable unit inside a packet (`PKT-*` or equivalent).
5. Doctrine copy: `core/managed-core/content/doctrine/CODING-EXECUTION-PROTOCOL.md` must match this protocol version and amendment.

## 2. Runtime discovery

Runtimes must discover these surfaces from the repository root and fail closed if any file is missing:

- `core/execution/CODING-EXECUTION-PROTOCOL.md`
- `core/contracts/EXECUTION-CONTROL-CONTRACT.md`
- `core/contracts/EXECUTION-MANIFEST.schema.json`
- `core/managed-core/content/doctrine/CODING-EXECUTION-PROTOCOL.md`
- `core/managed-core/content/doctrine/HOSTED-CAPACITY-SCHEDULER.md`

Discovery is read-only. Discovering the protocol is not authorization to merge, publish, deploy, or mutate providers.

## 3. Execution-manifest

A valid manifest declares:

- protocol id, version `1.0.1`, and amendment `V25_BOOTSTRAP_LEAN`
- program identity
- exact Git baseline (`repository`, 40-character `commit`, 40-character `tree`)
- one or more packets with owned paths and verification commands
- the control object defined in the control contract

Unknown trust-boundary fields are rejected. Narrative “done” claims are not a substitute for schema-valid records.

## 4. Control semantics (normative summary)

The control contract is authoritative. Summary that tests and runtimes must enforce:

| Control | Rule |
|---|---|
| Exact-candidate invalidation | Identity is repository + commit + tree (plus optional workflow/profile digests). Any identity change invalidates prior seals, reviews, receipts, and late success. |
| Bounded retry | At most three ordinary source repairs. Infrastructure retries once per exact candidate (two attempts total) then stops. Code/test failure has zero automatic retries. |
| Orchestration lease | Mutation of a packet/repository pair requires a live exclusive lease. Expired, stolen, or conflicting leases fail closed. |
| Resource uncertainty | Unknown CPU, memory, disk, or Docker availability is blocking. Uncertainty is not admission. |
| Durable heartbeat write/readback | Packet mutation requires a persisted heartbeat that is read back and bound to the checkout identity. A write without matching readback is not durable and does not admit work. |
| Checkout-bound verification receipts | Verification receipts bind to the exact checkout `repository + commit + tree`. Merge-ref identity (`refs/pull/<n>/merge`) is never promotable. |
| Retry-exhaustion diagnosis/recovery | Exhaustion must be diagnosed before recovery. Silent retry on the same identity is forbidden. Ordinary and code-failure exhaustion recover on a new identity; infrastructure exhaustion holds unless a named exception exists. |
| Hosted-capacity scheduler | Hosted work is scheduled only from a complete resource snapshot plus known slots. A busy or exhausted allocator is not a capacity diagnosis until that snapshot is complete. This protocol does not authorize paid or Fast hosted runs. |
| Automatic approval | Checkpoints are automatic. Staging promotion may be automatic when receipt identity holds. Main, publish, deploy, protection changes, and live provider mutation require recorded founder approval. Self-review, self-merge, and prefer-incoming are forbidden. |
| Repository/Git authority | Implementers work on `issue/<n>-<slug>` and must not push protected refs, open or merge their own delivery PRs, or install a nested `.ide-development` copy of this system repository. Packager opens PRs. Delivery controller merges. |
| v2.5 Issue checkpoint (`V25_BOOTSTRAP_LEAN`) | Exact pushed commit/tree + scoped diff + focused tests + independent Terra verification + manifest evidence accepts the Issue checkpoint. Review Ready and publisher tokens are not required. |
| Legacy publisher | No singular legacy publisher is canonical for v2.5, including `linktrend-review-ready-publisher`. Failed or missing legacy publisher is `WAIVED_LEGACY_GATE`, never PASS and never an implementation failure. |
| Administrator recovery | A later exact-head recovery is only a named exception after substantive replacement proof, limited to protection snapshot, restore, and readback. |
| Semantic lifecycle | JSON Schema is not sufficient. Plan/runtime states are rejected (never repaired) when packet, attempt, evidence, execution-state, lease, lock, heartbeat, receipt, retry-exhaustion, or archive records are inconsistent. Diagnostics name `packet=` and `attempt=`. COMPLETE/ARCHIVE_CONFIRMED bind accepted commit/tree, packet-level completion evidence, and a checkout-bound verification receipt; ARCHIVE_CONFIRMED also requires archive API readback. Completed-packet attempts are terminal. RUNNING has exactly one authoritative nonterminal attempt, its active write lock, a current orchestration lease, and a durable heartbeat readback. Completed packets must not retain an active lock. |
| LiNKautowork discovery | When Autowork discovery is callable it is required. When it is not callable, record an unavailable hold. Do not claim hosted, provider-live, or production proof. |

## 5. Proof limits

This protocol authorizes local schema, unit, discovery, and Issue-checkpoint-contract proof only. It does not by itself prove hosted CI, provider-live calls, application canaries, consumer rollout, staging, VPS, E2E, or production behavior.

## 6. Rollback

Revert the introducing Git commit. Protocol identity `1.0.1` with amendment `V25_BOOTSTRAP_LEAN` is removed with that commit. Do not leave a mixed protocol/schema pair.
