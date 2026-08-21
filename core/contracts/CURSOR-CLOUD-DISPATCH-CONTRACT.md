# Cursor Cloud API dispatch contract

**Control:** `cursor-cloud-dispatch-v1`

This contract is the reusable authority boundary for creating a Cursor Cloud
agent for IDE Development 2.5.1. An authenticated `cursor-agent` CLI session
proves only local workspace access. It does not authorize the Cursor Cloud API.
Cloud creation requires the `CURSOR_API_KEY` user or service key, which must be
held by the HTTP adapter and never written to intents, receipts, logs, or
diagnostics.

## Dispatch controls

The adapter calls `POST /v1/agents` through an injected HTTP port. It supplies
the exact named environment `{type: "cloud", name: "IDE Development 2.5.1"}`
and one exact non-Fast model. The expected build ID is recorded as provenance
only; it is deliberately not sent as a selectable build or model selector.

Before the API call, the durable store must contain a read-back-verified
`PREPARED` intent. The idempotency key and deterministic client-supplied agent
ID bind the repository, ref, commit, tree, environment, model, build
provenance, and toolchain. A committed intent is returned as a duplicate and
never creates a second agent.

The first prompt is an attestation-only prompt. The agent must not mutate,
commit, push, migrate, or invoke side effects. It must report the cloud
environment identity, repository/ref/commit/tree matrix, and toolchain. A
mutation gate accepts only an explicit `PASS` with `noMutation: true` and an
exact match for every expected field. Any mismatch is a hard stop.

Tests use fake HTTP ports and test-only keys. No Cursor endpoint or real agent
creation is part of source or package validation.
