# V1 Build Order

## Purpose

This document defines the assembled order in which the `.cursor` operating system reaches v1.0 coherence.

## Canonical Order

1. Doctrine
2. Artifacts
3. Agents
4. Commands
5. Runtime
6. Workflows
7. Contracts
8. State
9. System

## Why This Order Holds

- doctrine defines what the system must obey
- artifacts define what the system manipulates
- agents and commands expose how users and runtimes enter the system
- runtime defines how execution actually proceeds
- workflows define how stages connect
- contracts define how handoffs stay valid
- state defines how progression is interpreted consistently
- system finally assembles every lower layer into one model

## V1.0 Readiness Interpretation

The system is nearer to v1.0 when:

- every canonical layer exists
- every layer is discoverable
- compatibility and legacy assets are clearly bounded
- cross-layer invariants are coherent
- the assembled operating model can be explained without contradiction

## Remaining Assembly Work

Remaining work before a v1.0 release decision may include:

- final cross-layer audit
- top-level discovery reconciliation if desired
- release checklist confirmation

## Read Next

1. `SYSTEM-ARCHITECTURE.md`
2. `COMPATIBILITY-MATRIX.md`
