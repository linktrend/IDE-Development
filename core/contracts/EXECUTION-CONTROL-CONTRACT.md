# Execution Control Contract

**Status:** Canonical for Coding Execution Protocol 1.0.1 amendment `V25_BOOTSTRAP_LEAN`
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

## v2.5 Issue checkpoint (`V25_BOOTSTRAP_LEAN`)

A v2.5 Issue checkpoint is accepted when all of the following are present:

1. exact pushed commit and tree
2. scoped diff
3. focused tests
4. independent Terra verification
5. manifest evidence

Review Ready publication and publisher tokens are **not** required and must not block that acceptance.

## Publisher authority (no singular legacy canonical)

`canonicalForV25` is `none`. No singular legacy publisher is canonical for v2.5, including `linktrend-review-ready-publisher`, `mark-review-ready.sh-as-publisher`, `.linktrend/review-ready.json`, and user-PAT publication.

A failed or missing legacy publisher is classified **`WAIVED_LEGACY_GATE`**. That classification is never PASS and never an implementation failure.

Delivery and workflow implementation remain owned by other packets.

## Administrator recovery

A later exact-head administrator recovery is allowed only as a **named** exception, only after substantive replacement proof, and only for:

- `protection_snapshot`
- `restore`
- `readback`

Unnamed recovery, recovery without replacement proof, or any other operation is forbidden by this control contract.

## Semantic lifecycle (beyond JSON Schema)

`validate_execution_lifecycle` / `validate_plan_or_runtime` reject inconsistent manifests. They do not silently normalize fields. Every diagnostic names `packet=<id> attempt=<id|->`.

- `COMPLETE` and `ARCHIVE_CONFIRMED` require a valid accepted commit/tree plus packet-level `packet_completion` evidence bound to that identity. Event-only or empty completion evidence is rejected.
- `ARCHIVE_CONFIRMED` additionally requires archive API readback evidence.
- Every attempt on a completed packet must be terminal: `lifecycle=TERMINAL`, terminal `rawStatus`, `endedAt`, and `result` or `reason`.
- `RUNNING` requires exactly one authoritative nonterminal current attempt, that attempt's active write lock, and a current orchestration lease. Prior repaired terminal attempts may remain.
- Completed packets must not retain an active write lock.
- `COMPLETE` plus a RUNNING attempt is rejected.

## LiNKautowork automation discovery

When Autowork discovery is callable, it is required. Skipping a callable discovery is a control violation.

When discovery is not callable, the truthful result is an unavailable hold. That hold is not hosted, provider-live, application, consumer, staging, VPS, E2E, or production proof.
