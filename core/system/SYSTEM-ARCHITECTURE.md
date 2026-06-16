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
