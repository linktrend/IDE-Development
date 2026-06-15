# Session Shutdown

This document defines the canonical responsibilities for ending a working session safely.

## Purpose

End a session without losing execution state, proof status, review context, blockers, or the next clear step.

## Shutdown Sequence

1. inspect the active artifact tree
2. record the real current state of the active work unit
3. confirm whether proof, review, or integration is pending
4. record blockers explicitly if progress stopped
5. leave the next required command or artifact obvious
6. stop only when the next operator can resume without hidden context

## Shutdown Responsibilities

- avoid leaving ambiguous partial completion
- distinguish `blocked` from unfinished
- preserve the current lifecycle stage
- ensure downstream operators know what to read next

## Minimum Shutdown Outputs

- current active artifact path
- current state
- pending gate, if any
- next command or next artifact to open
- explicit blockers if they exist

## Runtime-Specific Shutdown Flows

### Human

- record the next action and any unresolved decisions

### Cursor

- update the active artifacts instead of relying on ephemeral chat context

### Codex

- do the same as Cursor
- ensure repository state is inspectable before ending the session

### Claude

- do the same as other AI runtimes
- preserve explicit artifact-based handoff

## Healthy Shutdown Criteria

A session ends well when:

- no work unit is falsely treated as complete
- the next operator can resume from artifacts alone
- hidden mental context is not required
