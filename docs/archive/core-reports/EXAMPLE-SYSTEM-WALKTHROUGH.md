# Example System Walkthrough

## Purpose

This report explains how the canonical examples under `.cursor/examples/` demonstrate practical use of the assembled `.cursor` system.

## Lifecycle Walkthroughs

### EXAMPLE-SIMPLE-FEATURE

- starts with `INTENT.md` approving a small additive feature
- `PROGRAM.md` turns that intent into one executable module
- `MODULE.md` narrows scope and points to one phase
- `PHASE.md` exposes one atomic issue
- `ISSUE.md` shows readiness with no dependencies and records the required state path
- `PROOF.md` maps acceptance criteria to evidence
- `REVIEW.md` independently validates the proof
- `INTEGRATION.md` records downstream completion effects

### EXAMPLE-BUGFIX

- starts with a defect-oriented `INTENT.md`
- `PROGRAM.md` and `MODULE.md` keep the work bounded to one bugfix slice
- `ISSUE.md` reframes proof around before-and-after behavior rather than feature scope only
- `PROOF.md` demonstrates defect closure evidence
- `REVIEW.md` validates that closure is specific enough to rely on
- `INTEGRATION.md` records that downstream work may trust the bug as closed

### EXAMPLE-MODULE

- starts with an intent that naturally matches the command "Complete this module"
- `PROGRAM.md` makes the module the primary execution target
- `MODULE.md` shows how a runtime should enter module execution
- `PHASE.md` and `ISSUE.md` show the atomic execution slice
- `PROOF.md`, `REVIEW.md`, and `INTEGRATION.md` show the completion gates that make module roll-up safe

## Participating Layers

- doctrine: establishes the execution laws, atomicity, and completion gates
- artifacts: define the concrete work units and proof surfaces
- commands: route users into `plan-program`, `plan-module`, `complete-module`, `execute-issue`, `review-issue`, and `integrate-issue`
- workflows: explain movement from intent through integration
- contracts: clarify producer and consumer handoffs between artifacts
- state: defines readiness, review readiness, done, and blocked semantics
- system: explains how these layers assemble into one operating model

## Lessons Learned

- the system is understandable when examples stay small and read in strict progressive-disclosure order
- issue atomicity becomes clearer when each issue explicitly names its command path, workflow path, and handoff expectations
- proof stays useful when it maps criteria to evidence instead of repeating the issue text
- bugfix examples benefit from explicitly contrasting symptom and corrected behavior
- module-oriented examples are the best way to teach upward roll-up semantics

## Gaps Discovered

- module-level review and module-level integration remain described by doctrine but are not instantiated in these minimal examples because the requested artifact set was limited to the canonical chain ending at integration for one issue
- examples teach the command path clearly, but they do not yet show a multi-issue dependency graph or real concurrency
- examples are strong as reference material, but a later real low-risk repository test is still needed to confirm day-to-day ergonomics

## Overall Assessment

The examples prove that the current system can be read and executed as an artifact-driven operating model. A human or capable AI runtime can follow the examples to understand ownership, state transitions, command routing, workflow movement, proof discipline, review flow, and integration flow without additional architecture work.
