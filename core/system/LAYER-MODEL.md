# Layer Model

## Purpose

This document defines the canonical layer stack, ownership boundaries, and dependency relationships.

## Layer Order

1. Doctrine
2. Artifacts
3. Agents
4. Commands
5. Runtime
6. Workflows
7. Contracts
8. State
9. System

## Dependency Model

### Doctrine

- depends on no lower specification layer
- governs every other layer

### Artifacts

- depend on doctrine
- provide structured units consumed by runtime, workflows, contracts, and commands

### Agents

- depend on doctrine and artifacts
- describe who can perform work, not the primary sequencing mechanism

### Commands

- depend on doctrine, artifacts, and agents
- route requests into the system

### Runtime

- depends on doctrine and artifacts
- defines how execution proceeds in practice

### Workflows

- depend on doctrine, artifacts, and runtime
- define stage-to-stage movement

### Contracts

- depend on doctrine, artifacts, runtime, and workflows
- validate handoffs between stages

### State

- depends on doctrine, runtime, workflows, and contracts
- provides shared state vocabulary across the stack

### System

- depends on every lower layer
- assembles the complete operating model

## Ownership Boundaries

- doctrine owns laws and execution semantics
- artifacts own structured work representation
- agents own resource definitions
- commands own invocation entrypoints
- runtime owns traversal and execution behavior
- workflows own lifecycle flow
- contracts own handoff validity
- state owns shared progression vocabulary
- system owns top-level assembly

## Boundary Rule

No layer should absorb the concerns of another unless the system explicitly decides to refactor the stack.

## Read Next

1. `RESPONSIBILITY-MATRIX.md`
2. `COMPATIBILITY-MATRIX.md`
