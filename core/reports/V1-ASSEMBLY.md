# V1 Assembly

## Architecture Overview

The `.cursor` system is now assembled as a layered operating model:

1. Doctrine
2. Artifacts
3. Agents
4. Commands
5. Runtime
6. Workflows
7. Contracts
8. State
9. System

The system remains:

- artifact-driven
- doctrine-governed
- runtime-independent
- implementation-free at the specification level

## Dependency Graph

High-level dependency graph:

- Doctrine -> Artifacts
- Doctrine -> Agents
- Doctrine -> Commands
- Doctrine -> Runtime
- Doctrine -> Workflows
- Doctrine -> Contracts
- Doctrine -> State
- Artifacts -> Runtime
- Artifacts -> Workflows
- Artifacts -> Contracts
- Runtime -> Workflows
- Runtime -> Contracts
- Runtime -> State
- Workflows -> Contracts
- Workflows -> State
- Contracts -> State
- All lower layers -> System

## Unresolved Questions

1. Whether the top-level `.cursor/README.md` should explicitly route into the newer `runtime/`, `workflows/`, `contracts/`, `state/`, and `system/` layers.

2. Whether older specification files in lower layers should be reconciled to point explicitly at the newer canonical state and contract layers.

3. Whether a release-specific workflow or release-specific contract layer is needed before a v1.0 release call.

4. Whether compatibility assets should eventually be reorganized into a clearer compatibility zone without changing semantics.

## What Remains Before v1.0 Release

1. A final cross-layer consistency audit.

2. Confirmation that the assembled layer stack is the intended public model.

3. A release-readiness pass over canonical versus compatibility versus legacy labeling.

4. A decision on whether broader top-level discovery wiring is needed.

## Recommended V1.0 Release Checklist

- confirm every canonical layer has an index and readme where appropriate
- confirm no canonical layer has orphan files
- confirm canonical versus compatibility versus legacy boundaries are explicit
- confirm issue remains the atomic executable unit everywhere
- confirm proof, review, and integration remain distinct everywhere
- confirm agents remain resources rather than the control structure
- confirm state, workflow, runtime, and contract semantics do not contradict each other
- confirm the assembled system can be explained end-to-end from one entrypoint
