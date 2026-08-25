# Cursor Cloud SDK/API dispatch contract

**Control:** `cursor-cloud-dispatch-v1`

This contract is the reusable authority boundary for creating a Cursor Cloud
agent for IDE Development 2.5.1. An authenticated `cursor-agent` CLI session
proves only local workspace access. It does not authorize the Cursor Cloud API.
Cloud creation requires the `CURSOR_API_KEY` user or service key, which must be
held by the HTTP adapter and never written to intents, receipts, logs, or
diagnostics.

## Dispatch controls

Planner manifests may bind the dispatch controls through
`controls.cursorCloudExecution`. The binding requires pre-dispatch advertised
ref validation, governed rebaseline/hold handling for a missing ref, immutable
prepared-intent supersession without reusing a Cloud attempt, and effective
model readback. The execution-manifest schema validates this object strictly;
unknown fields are rejected.

The preferred adapter uses the official Python `cursor-sdk` and binds one exact
repository URL plus `starting_ref` as first-class SDK fields. Repository-specific
work uses one repository per run. Multi-repository execution is admitted only
when the packet explicitly owns coordinated changes across those repositories;
contract dependencies alone do not justify a shared write environment.
Audit launches bind Grok 4.6 with SDK model parameters `effort=medium` and
`fast=false`; provider readback remains mandatory.

Direct REST remains the bounded fallback and authoritative readback surface.
The REST adapter calls `POST /v1/agents` through an injected HTTP port. It supplies
the exact named environment `{type: "cloud", name: "IDE Development 2.5.1"}`
and one exact non-Fast model. The saved environment's public identity
`1937ddb1-9d3e-11f1-a7d1-d6b4613131ce` is carried in PREPARED/readback evidence,
not as an unsupported API selector. Cursor's public API does not provide an exact
repository checkout selector, so repository binding is not claimed in the API
body. Instead, the saved environment target is deterministically selected as
`/agent/repos/<repo>`. For example, LiNKbrain must select
`/agent/repos/LiNKbrain` with remote `https://github.com/linktrend/LiNKbrain`;
the default LiNKharness primary repository is rejected. The first prompt must
resolve that path, and fetch/checkout the required ref or exact commit only as
governed setup, before remote/repository/ref/commit/tree/toolchain attestation.
The expected build ID is recorded as provenance only; it is deliberately not
sent as a selectable build or model selector. After creation, the provider run
readback must explicitly record the public environment ID, observed build
provenance, expected build provenance, effective model and `fast=false`; a
mismatch is a hard stop.

Before the API call, the durable store must contain a read-back-verified
`PREPARED` intent. The idempotency key and deterministic client-supplied agent
ID bind the repository path, remote, ref, commit, tree, environment, model,
build provenance, toolchain, and the exact governed setup receipt digest
(`sha256:<digest>`). A committed intent is returned as a duplicate and never
creates a second agent. An unknown API outcome receives at most one retry with
the same idempotency key.

Before preparing a new request, the store enumerates all intents. Every
uncompleted `PREPARED` record that names the retired fixed hosted-worker cap is
atomically marked `SUPERSEDED` with the adaptive policy and must receive a new
idempotency identity. `COMMITTED` records are preserved as completed evidence.
If the store cannot enumerate and read back these records, dispatch stops
before the API call. Capacity evidence is bound to the exact account, API-key
name, team, and Program Run identity; a missing or mismatched identity is not
usable evidence.

The first prompt is an attestation-only prompt. The agent must not mutate,
commit, push, migrate, or invoke side effects. It must report the cloud
environment identity, repository/ref/commit/tree matrix, and toolchain. A
mutation gate accepts only an explicit `PASS` with `noMutation: true` and an
exact match for every expected field. Any mismatch is a hard stop.

Tests use fake HTTP ports and test-only keys. No Cursor endpoint or real agent
creation is part of source or package validation.
