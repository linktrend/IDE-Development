# Dependency Resolution

## Purpose

This document defines how the runtime evaluates dependencies, computes readiness, and allows safe concurrency.

## Dependency Unit

The authoritative dependency unit is the issue.

Programs, modules, and phases may group work, but issue-level dependencies govern execution order.

## Dependency Rules

1. Dependencies must be explicit in issue artifacts whenever they affect sequencing.
2. Dependency cycles are invalid and must be resolved before execution can proceed safely.
3. A dependency is satisfied only when the upstream issue is integrated, not merely executed.
4. Downstream readiness must be recomputed after every successful integration.

## Readiness Computation

An issue is ready only when all of the following are true:

- all declared dependencies are satisfied
- required inputs are available
- no blocking question prevents execution
- scope and acceptance are specific enough to perform the work
- no higher-priority gate prevents progression

Readiness is therefore a computed runtime conclusion, not a manual label of convenience.

## Dependency Sources

The runtime may derive dependencies from:

- `depends_on` in issue artifacts
- explicit module or phase entry conditions
- explicit integration dependencies recorded in review or integration artifacts

The runtime must not invent hidden dependencies without recording them as blockers or artifact updates.

## Concurrency Rules

Concurrency is allowed when:

- multiple issues are independently ready
- their outputs do not require serialized integration for correctness
- execution does not rely on the same unresolved artifact or contested decision

Concurrency is restricted when:

- issues touch the same integration boundary in conflicting ways
- review capacity is too limited to preserve gate discipline
- integration order materially affects correctness

## Downstream Recalculation

After integration, the runtime must:

1. identify issues that depend on the integrated issue
2. recompute readiness for those issues
3. update any relevant phase or module progress
4. determine whether new concurrent work has become available

## Failure Handling

### Upstream Failure

If an upstream issue fails review or becomes blocked, downstream issues that depend on it remain not ready.

### Integration Failure

If integration fails, the upstream issue is not dependency-satisfying. Downstream issues remain blocked from using it.

### Dependency Ambiguity

If dependency relationships are ambiguous, the runtime should:

- stop treating the affected issue as ready
- record the ambiguity as a blocker
- resolve the ambiguity before proceeding

## Human-Driven Coordination

Because this runtime is human-driven:

- dependency resolution may be computed manually or by a local AI assistant
- concurrency decisions should remain conservative where integration risk is unclear
- every dependency-related decision should remain artifact-traceable

## Read Next

1. `STATE-MODEL.md`
2. `EXECUTION-LOOP.md`
