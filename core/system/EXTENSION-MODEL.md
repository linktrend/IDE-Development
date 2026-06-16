# Extension Model

## Purpose

This document defines safe extension points for future growth without changing the core operating model unnecessarily.

## Extension Rule

An extension is acceptable only when:

- it fits an existing layer boundary
- it does not contradict doctrine
- it does not bypass contracts or state rules
- it does not convert compatibility concerns into hidden canonical behavior

## Safe Extension Points

### Doctrine Extensions

Allowed only when new laws or runtime semantics are genuinely needed.

### Artifact Extensions

Allowed when a clear missing work unit or support artifact exists.

### Agent Extensions

Allowed when a clearly distinct resource role is needed.

### Command Extensions

Allowed when a real invocation surface is missing.

### Runtime Extensions

Allowed when execution behavior needs more explicit specification without introducing implementation code.

### Workflow Extensions

Allowed when a lifecycle path is missing or ambiguous.

### Contract Extensions

Allowed when a handoff rule cannot be expressed using the existing contract model.

### State Extensions

Allowed when a missing state concept is required across multiple layers.

### System Extensions

Allowed when a top-level assembly question cannot be answered by current system documents.

## Unsafe Extensions

Unsafe extensions include:

- adding parallel concepts that duplicate current layers
- embedding implementation logic into specification layers
- creating agent-led control structures that bypass artifact-led control
- introducing hidden compatibility behavior

## Read Next

1. `V1-BUILD-ORDER.md`
