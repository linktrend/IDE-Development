# Responsibility Matrix

## Purpose

This document clarifies which layer owns which responsibility.

## Matrix

### Doctrine

Owns:

- laws
- execution semantics
- gate principles

Does not own:

- concrete work instances
- runtime traversal details
- command invocation wording

### Artifacts

Own:

- structured work representation
- evidence containers
- definitions of done

Do not own:

- sequencing computation by themselves
- review judgment
- runtime traversal policy

### Agents

Own:

- role descriptions
- resource responsibilities

Do not own:

- primary execution control structure
- dependency ordering

### Commands

Own:

- invocation surface
- routing into doctrine and workflows

Do not own:

- execution semantics
- state truth

### Runtime

Owns:

- execution traversal
- readiness computation behavior
- stop behavior

Does not own:

- handoff validity rules in isolation
- artifact definitions

### Workflows

Own:

- stage sequencing
- entry and exit conditions

Do not own:

- universal invariants alone
- state vocabulary alone

### Contracts

Own:

- producer-consumer validity
- input/output obligations
- handoff invariants

Do not own:

- execution sequencing logic
- state transitions in isolation

### State

Owns:

- canonical state vocabulary
- transition legality
- blocked, retry, failure, and terminal semantics

Does not own:

- lifecycle stage design
- artifact structures

### System

Owns:

- top-level assembly
- layer interaction model
- canonical versus compatibility versus legacy mapping

Does not own:

- lower-layer local semantics beyond assembly interpretation

## Read Next

1. `COMPATIBILITY-MATRIX.md`
2. `EXTENSION-MODEL.md`
