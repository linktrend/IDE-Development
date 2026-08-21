# Cursor Cloud dispatch doctrine

Cursor Cloud is an API authority, not a synonym for an authenticated local
`cursor-agent` CLI. The reusable dispatcher requires `CURSOR_API_KEY`, targets
the exact cloud environment `{type: "cloud", name: "IDE Development 2.5.1"}`
and an exact non-Fast model, and never exposes the key in durable evidence.

The dispatcher writes and reads back a durable `PREPARED` intent before
`POST /v1/agents`. Its deterministic idempotency key and client-supplied agent
ID suppress duplicate creation. Agent ID, run ID, environment, model, exact
repository/ref/commit/tree matrix, toolchain, and expected build ID provenance
are retained in the committed record. Build ID is provenance only, never an API
selector.

The initial prompt is attestation-only and explicitly forbids mutation. A
mutation gate requires an exact `PASS`, `noMutation: true`, and exact matches
for environment, repository/ref/commit/tree, and toolchain. Missing or
mismatched attestation fails closed. All tests use fake HTTP; no Cursor agent
is created by package validation.
