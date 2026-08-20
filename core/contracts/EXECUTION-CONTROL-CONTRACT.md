# Execution Control Contract

**Status:** Canonical for Coding Execution Protocol 1.0.1  
**Consumes:** `core/execution/CODING-EXECUTION-PROTOCOL.md`  
**Schema:** `core/contracts/EXECUTION-MANIFEST.schema.json`

This contract governs execution-manifest controls. It does not implement delivery workflows, GitHub Actions, or publisher YAML.

## Producer and consumer

- Producer: program planner that emits a schema-valid execution-manifest.
- Consumer: implementer runtime that validates the manifest, discovers protocol surfaces, and evaluates control decisions before mutation.

## Exact-candidate invalidation

A candidate identity is the tuple:

`repository + commit + tree` and, when supplied, `workflowDigest` and `profileDigest`.

A later head, tree, repository, or bound digest **invalidates** the previous candidate. Seals, reviews, receipts, and late success for the previous identity must be rejected. Checkpoints may record Git state without sealing.

## Bounded retry

| Failure class | Attempts | Next |
|---|---|---|
| Ordinary source repair | at most 3 | fourth attempt stops |
| Infrastructure on the same exact candidate | 2 total | second failure stops; no third try |
| Code or test failure | 0 automatic retries | return to development / repair on a new identity |

Unknown failure classes stop. Retry is never a reason to prefer-incoming.

## Orchestration lease

Packet mutation requires a lease scoped to `packet-repository`.

- A live lease from another holder is `orchestration_lease_held`.
- An expired lease cannot authorize mutation.
- Holder, packet id, and repository must match.

Discovery and schema validation do not require a lease.

## Resource uncertainty

Admission fails closed when the resource snapshot is missing or any of `cpu_percent`, `memory_percent`, `free_disk_gib`, or `docker_available` is unknown. Uncertainty is a blocker, not an invitation to guess. Interactive-use pressure also refuses admission.

A busy or exhausted allocator response is not a final capacity diagnosis until the snapshot is complete; incomplete snapshots remain `resource_uncertain`.

## Automatic approval rules

| Action | Decision |
|---|---|
| `checkpoint`, `issue_commit` | automatic |
| `staging_promote` | automatic when receipt identity holds (this contract does not evaluate receipts) |
| `main_promote`, `publish_release`, `deploy_production`, `github_protection_change`, `provider_live_mutation` | founder approval must already be recorded for the exact action |
| `self_review`, `self_merge`, `prefer_incoming` | forbidden |

Absence of a recorded founder approval is not a request to invent one.

## Repository and Git authority

- Work branches match `issue/<n>-<slug>`.
- Protected refs: `development`, `staging`, `main`. Implementers must not push them.
- Implementers must not open or merge delivery PRs.
- Nested `.ide-development` install into this system repository is forbidden.
- Packager / packager coordinator opens Phase PRs.
- Delivery controller merges to `development` through protection.

This contract does not change workflow files. It forbids claiming Git authority the workflows have not granted.

## Publisher authority (singular)

Canonical Review Ready publisher: **`linktrend-review-ready-publisher`**.

Legacy duplicates are non-authoritative in this control layer and must not be advertised as publishers:

- `mark-review-ready.sh-as-publisher`
- `review-ready.json`
- `user-pat-publisher`

Delivery and workflow implementation remain owned by other packets. This packet only removes duplicate **control-contract** publisher authority.

## LiNKautowork automation discovery

When Autowork discovery is callable, it is required. Skipping a callable discovery is a control violation.

When discovery is not callable, the truthful result is an unavailable hold. That hold is not hosted, provider-live, application, consumer, staging, VPS, E2E, or production proof.
