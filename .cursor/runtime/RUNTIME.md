# Runtime

## Purpose

The runtime is the operational layer that carries out the execution doctrine using artifacts alone.

It does not replace the doctrine. It defines how a human or AI runtime should behave while using:

- `PROGRAM.md`
- `MODULE.md`
- `PHASE.md`
- `ISSUE.md`
- `PROOF.md`
- `REVIEW.md`
- `INTEGRATION.md`

## Runtime Responsibilities

The runtime must:

1. load only the minimum doctrine and artifacts required for the current scope
2. discover the current execution graph from program, module, phase, and issue artifacts
3. compute issue readiness from dependencies, gates, and blockers
4. assign ready work to available resources without letting resource identity determine sequencing
5. require proof before review and review before integration
6. recompute downstream readiness after every integration event
7. continue until the target artifact is complete or genuinely blocked

## Runtime Boundaries

The runtime must not:

- treat modules or phases as atomic execution units
- skip proof, review, or integration
- convert agents into the control structure
- invent hidden dependencies outside the artifacts without recording them
- stop at partial completion without an explicit blocker trail

## Runtime Inputs

Minimum runtime inputs:

- execution doctrine from `.cursor/execution/`
- the relevant artifact index entries
- the target program, module, phase, or issue artifact
- proof, review, and integration artifacts already produced
- available human or AI resources

## Runtime Outputs

Minimum runtime outputs:

- ready-work selection
- explicit state transitions
- proof artifacts
- review artifacts
- integration artifacts
- blocker records
- completion or blocked status at the requested scope

## Runtime Control Principle

The control structure comes from:

- artifacts
- dependencies
- gates
- definitions of done

Resources perform work, but they do not determine execution order by themselves.

## Human-Driven Mode

This runtime is human-driven.

That means:

- humans may execute, review, integrate, or coordinate work directly
- AI tools may assist as resources under human control
- no daemon, scheduler, external queue, or cloud orchestration is assumed
- runtime behavior must still remain valid if different tools are used later

## Read Next

1. `STATE-MODEL.md` for state transitions and failure handling
2. `EXECUTION-LOOP.md` for step-by-step runtime behavior
3. `DEPENDENCY-RESOLUTION.md` for readiness and concurrency rules
