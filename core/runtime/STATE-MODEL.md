# State Model

## Purpose

This document defines the runtime state model for executable work, especially issues.

## Issue Lifecycle

Issue states (identical to the Ledger, `core/ledger/sql/ide_ledger.sql`):

- `planned`
- `ready`
- `in_progress`
- `blocked`
- `in_review`
- `done`
- `cancelled`

These states are normative for runtime behavior. Readers accept the pre-v3
value `review_ready` as an alias of `in_review`; writers always write
`in_review`.

## State Meanings

### `planned`

The issue is structurally defined, but the runtime cannot yet treat it as executable.

### `blocked`

The issue cannot currently proceed because one or more of the following is unresolved:

- a dependency
- a gate
- a missing input
- a decision
- a failed review or failed integration path

Blocked state must always preserve a visible trail of the reason.

### `ready`

The issue is executable because:

- dependencies are satisfied
- scope is clear
- required inputs exist
- no unresolved blocker remains

Readiness is computed, not manually granted.

### `in_progress`

The issue is actively being executed by a human or AI resource.

### `in_review`

Execution work has been completed far enough that:

- proof exists
- the issue can be evaluated independently

This is the mandatory handoff state between execution and the independent review.

### `done`

The issue is complete only when:

- proof exists
- review passes
- integration succeeds

### `cancelled`

The issue was withdrawn before `done`. It is terminal and keeps its history.

## Allowed Transitions

Primary forward path:

- `planned -> ready`
- `ready -> in_progress`
- `in_progress -> in_review`
- `in_review -> done`

Blocking transitions:

- `planned -> blocked`
- `ready -> blocked`
- `in_progress -> blocked`
- `in_review -> blocked`

Recovery transitions:

- `blocked -> planned`
- `blocked -> ready`
- `in_review -> in_progress`

The recovery path chosen depends on what failed.

## Failure States

The runtime does not introduce a separate `failed` state.

Instead, failure is represented through:

- `blocked` when work cannot continue
- return from `in_review` to `in_progress` when rework is required
- explicit failure evidence in proof, review, and blocker records

## Retry Behavior

Retry is allowed when:

- a blocker is resolved
- missing evidence is produced
- review findings are addressed
- integration conflicts are corrected

Retry must not erase prior history. The runtime should preserve:

- what was attempted
- what failed
- what changed before retry

## Review And Integration Flow

The runtime must enforce:

1. execution creates or updates proof
2. proof enables review
3. passing review enables integration
4. successful integration enables `done`

If review fails:

- the issue returns to `in_progress` or `blocked`

If integration fails:

- the issue returns to `blocked` until the integration problem is resolved

## Higher-Level Completion States

Programs, modules, and phases may maintain local status fields, but they are not the atomic execution lifecycle.

Their completion is computed from:

- child issue completion
- local completion criteria
- required higher-level review and integration conditions

## Read Next

1. `EXECUTION-LOOP.md`
2. `DEPENDENCY-RESOLUTION.md`
