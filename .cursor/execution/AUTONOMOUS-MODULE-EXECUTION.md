# Autonomous Module Execution

This document defines expected runtime behavior for a command such as:

`Complete Authentication Module.`

A capable human or AI runtime should be able to execute the module recursively using artifacts alone.

## Entry Behavior

1. Load the execution doctrine from `.cursor/execution/`.
2. Load the target module artifact.
3. Read only the program-level constraints needed by that module.

## Recursive Execution Behavior

1. Inspect the module artifact and identify its phases.
2. Inspect the phase artifacts and enumerate their issues.
3. Resolve the issue dependency graph.
4. Compute which issues are currently `ready`.
5. Select a ready issue.
6. Execute the issue within its declared scope.
7. Produce the required proof artifact.
8. Review the proof and resulting work independently.
9. If review passes, integrate the work into the active line.
10. Mark the issue `done` only after integration succeeds.
11. Recompute downstream readiness.
12. Continue until the module reaches its definition of done or becomes genuinely blocked.

## Runtime Rules

- Execution order is determined by issue dependencies.
- Concurrency is allowed when dependencies permit it.
- Proof is required before review.
- Review is required before integration.
- Integration is required before downstream issues may rely on the work.
- A blocked issue must leave an explicit trail of attempted work and open blockers.

## Completion

A module is complete only when:

- all required issues are `done`
- all relevant phase criteria are satisfied
- the module definition of done is satisfied
- module-level proof, review, and integration requirements are met

If these conditions are not satisfied, the runtime should continue or report a genuine blocker rather than stopping at partial completion.
