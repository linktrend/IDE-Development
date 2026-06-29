# System Architecture

## Purpose

This document defines the assembled top-level architecture of the `.cursor` operating system.

It does not create new concepts. It explains how the existing layers interact as one coherent system.

## Complete Layer Stack

The assembled stack is:

1. **Doctrine**
2. **Artifacts**
3. **Agents**
4. **Commands**
5. **Runtime**
6. **Workflows**
7. **Contracts**
8. **State**
9. **System**

## Architectural Principle

The `.cursor` system is:

- artifact-driven
- doctrine-governed
- runtime-independent
- implementation-free at the specification level
- compatible with human and AI runtimes

## Enforcement Model

The system is intentionally compliance-based rather than controller-based.

Cursor and Codex primarily operate by reading repository-visible instructions, artifacts, rules, prompts, and files. Because of that, the durable control mechanism is:

- clear doctrine
- explicit artifacts
- visible state
- dependency gates
- proof requirements
- review and integration handoffs
- progressive-disclosure read paths

An executable controller is not required for the core system to work as designed. Adding one would make sense only as an optional adapter for a specific runtime that can actually delegate execution through that controller.

The core must remain usable when the only available runtime is an AI agent operating inside a repository.

## Layer Interaction Summary

### Doctrine

Defines the laws and minimum execution semantics.

### Artifacts

Provide the structured work units and evidence containers that doctrine governs.

### Agents

Provide reusable resources and control roles, but do not become the control structure.

### Commands

Provide natural entrypoints that route work into the doctrine, artifact, and role system.

### Runtime

Defines how artifacts are traversed and executed in practice without introducing automation software.

### Workflows

Define how work moves from one stage to the next across the lifecycle.

### Contracts

Define what makes each handoff valid between stages, artifacts, and runtimes.

### State

Provides the shared vocabulary for readiness, blockage, failure, retry, and completion.

### System

Assembles the full model and describes how all other layers coexist and interact.

## Control Structure

Control comes from:

- doctrine
- artifacts
- dependencies
- gates
- workflows
- contracts
- state rules

Not from:

- agents alone
- commands alone
- runtime identity alone

## Compatibility Principle

The system preserves compatibility-only and legacy assets where needed, but canonical behavior is defined by the assembled core layers.

## Read Next

1. `LAYER-MODEL.md`
2. `EXECUTION-MAP.md`
3. `RESPONSIBILITY-MATRIX.md`
