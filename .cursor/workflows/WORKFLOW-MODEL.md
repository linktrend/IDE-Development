# Workflow Model

## Purpose

The workflow layer connects doctrine, artifacts, runtime behavior, agents, commands, and human decisions into a single artifact-driven lifecycle.

## Workflow Responsibilities

The workflow layer must:

1. define how work moves from intent to completion
2. define entry and exit conditions for each major stage
3. define input and output contracts between stages
4. define the expected side effects of each stage
5. preserve issue as the atomic execution unit
6. preserve proof, review, and integration as distinct completion stages

## Workflow Boundaries

The workflow layer must not:

- replace the execution doctrine
- replace the runtime specification
- define implementation code or automation behavior
- treat agents as the control structure

## Lifecycle

The canonical lifecycle is:

`Intent -> Program -> Module -> Phase -> Issue -> Proof -> Review -> Integration -> Complete`

## Stage Relationships

### Intent

- validates whether work should become a program at all
- produces the go or no-go basis for program creation

### Program

- defines the top-level body of work
- groups modules
- defines program-level completion and release conditions

### Module

- defines a coherent domain area within the program
- groups phases
- establishes module definition of done

### Phase

- groups issues into checkpointed work segments
- may add local entry, exit, and optional review conditions

### Issue

- is the atomic executable unit
- carries dependencies, scope, proof, review, and integration requirements

### Proof

- supplies evidence that execution satisfies acceptance criteria

### Review

- independently determines whether proof and completion claims are acceptable

### Integration

- incorporates passing work into the active line
- recomputes downstream readiness

### Complete

- is reached only when local and higher-level completion conditions are satisfied

## Ownership Model

- artifacts define what must happen
- runtime defines how stages are traversed
- agents and humans perform work inside stages
- ownership is stage-specific, not globally agent-specific

## Side Effects

Allowed side effects include:

- creation or update of structured artifacts
- state progression
- downstream readiness recomputation
- higher-level progress roll-up

Disallowed workflow side effects include:

- hidden sequencing outside artifacts
- implicit completion without proof
- direct jumps from execution to done

## Read Next

1. `PROGRAM-WORKFLOW.md`
2. `MODULE-WORKFLOW.md`
3. `ISSUE-WORKFLOW.md`
4. `REVIEW-WORKFLOW.md`
5. `INTEGRATION-WORKFLOW.md`
