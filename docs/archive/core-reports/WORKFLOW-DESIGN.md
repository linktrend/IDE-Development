# Workflow Design

## Workflow Architecture

The workflow layer connects:

- execution doctrine
- execution artifacts
- runtime behavior
- human and AI resources
- review and integration gates

The workflow layer is implementation-free. It defines stage contracts and transitions, not automation.

Canonical workflow specifications:

- `.cursor/workflows/WORKFLOW-MODEL.md`
- `.cursor/workflows/PROGRAM-WORKFLOW.md`
- `.cursor/workflows/MODULE-WORKFLOW.md`
- `.cursor/workflows/ISSUE-WORKFLOW.md`
- `.cursor/workflows/REVIEW-WORKFLOW.md`
- `.cursor/workflows/INTEGRATION-WORKFLOW.md`

Retained compatibility workflow notes:

- `.cursor/workflows/dispatch-v2.md`
- `.cursor/workflows/planning-lifecycle.md`

## Workflow Relationships

The lifecycle is:

`Intent -> Program -> Module -> Phase -> Issue -> Proof -> Review -> Integration -> Complete`

Stage relationships:

- `Intent` governs whether `Program` should exist
- `Program` governs module boundaries and release expectations
- `Module` governs phase grouping and issue decomposition
- `Phase` groups issues but does not replace issue execution
- `Issue` governs atomic execution
- `Proof` enables review
- `Review` authorizes or blocks integration
- `Integration` produces completion and downstream readiness effects

## Contracts Between Stages

### Intent -> Program

- input contract: objective, scope, success criteria, constraints
- output contract: accepted program creation basis

### Program -> Module

- input contract: module definitions and global constraints
- output contract: executable module boundaries

### Module -> Phase -> Issue

- input contract: module objective and phase grouping
- output contract: issue graph with dependencies and acceptance criteria

### Issue -> Proof

- input contract: ready issue and execution work
- output contract: evidence mapped to criteria

### Proof -> Review

- input contract: reviewable proof and subject artifact
- output contract: pass, fail, or blocked review verdict

### Review -> Integration

- input contract: passing review
- output contract: integrated work and downstream readiness recomputation

## Remaining Gaps Before v1.0

1. Decide whether the workflow layer should be wired into the top-level `.cursor` discovery path more explicitly.

2. Validate the workflow model against a supervised real module execution in a live repository.

3. Decide whether formal workflow-specific blocker recording needs its own artifact or should remain embedded in existing execution artifacts.

4. Decide whether older workflow notes should eventually be reclassified more explicitly as legacy or deprecated once compatibility needs are clearer.

5. Clarify whether release-level workflow specification is needed as a separate future document or can remain covered by the current program and review semantics.
