# Coding Execution Protocol

**Status:** Canonical  
**Protocol id:** `coding-execution-protocol`  
**Protocol version:** 1.0.1  
**Schema:** `core/contracts/EXECUTION-MANIFEST.schema.json`  
**Control contract:** `core/contracts/EXECUTION-CONTROL-CONTRACT.md`

This document installs the execution semantics for bounded implementer packets. It does not copy project history, prior PRDs, or chat transcripts. Runtime discovery and schema validation live beside this file; delivery workflow YAML is out of scope.

## 1. Identity

1. The protocol id is `coding-execution-protocol` and the version is `1.0.1`.
2. An execution program is described by a schema-valid **execution-manifest**.
3. Work is packet-scoped. An issue (`ISS-*`) is the atomic executable unit inside a packet (`PKT-*` or equivalent).
4. Doctrine copy: `core/managed-core/content/doctrine/CODING-EXECUTION-PROTOCOL.md` must match this protocol version.

## 2. Runtime discovery

Runtimes must discover these surfaces from the repository root and fail closed if any file is missing:

- `core/execution/CODING-EXECUTION-PROTOCOL.md`
- `core/contracts/EXECUTION-CONTROL-CONTRACT.md`
- `core/contracts/EXECUTION-MANIFEST.schema.json`
- `core/managed-core/content/doctrine/CODING-EXECUTION-PROTOCOL.md`

Discovery is read-only. Discovering the protocol is not authorization to merge, publish, deploy, or mutate providers.

## 3. Execution-manifest

A valid manifest declares:

- protocol id and version `1.0.1`
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
| Automatic approval | Checkpoints are automatic. Staging promotion may be automatic when receipt identity holds. Main, publish, deploy, protection changes, and live provider mutation require recorded founder approval. Self-review, self-merge, and prefer-incoming are forbidden. |
| Repository/Git authority | Implementers work on `issue/<n>-<slug>` and must not push protected refs, open or merge their own delivery PRs, or install a nested `.ide-development` copy of this system repository. Packager opens PRs. Delivery controller merges. |
| Publisher authority | The only Review Ready publisher is `linktrend-review-ready-publisher`. Legacy duplicates (`mark-review-ready.sh` as publisher, `.linktrend/review-ready.json`, user PAT publication) are forbidden in this control layer. |
| LiNKautowork discovery | When Autowork discovery is callable it is required. When it is not callable, record an unavailable hold. Do not claim hosted, provider-live, or production proof. |

## 5. Proof limits

This protocol authorizes local schema, unit, and discovery proof only. It does not by itself prove hosted CI, provider-live calls, application canaries, consumer rollout, staging, VPS, E2E, or production behavior.

## 6. Rollback

Revert the introducing Git commit. Protocol identity `1.0.1` is removed with that commit. Do not leave a mixed protocol/schema pair.
