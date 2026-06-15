# Autonomous Development Squad

## Purpose

Provide the minimum role composition required for autonomous execution of a program, module, phase, or issue using artifacts and doctrine alone.

## Member Roles

- `planner`
- `orchestrator`
- `reviewer`
- `integrator`
- `product-owner`
- `technical-lead`
- `ui-ux-designer`
- `frontend-developer`
- `backend-developer`
- `qa-automation-engineer`

## Control Functions

- `planner` turns intent into executable artifact structure
- `orchestrator` computes readiness, sequencing, and concurrency from dependencies and gate state
- `reviewer` performs independent review and rejects vacuous completion
- `integrator` records accepted work as integrated and recomputes downstream readiness

## Work Flow

1. Start from the highest relevant artifact: `PROGRAM.md`, `MODULE.md`, `PHASE.md`, or `ISSUE.md`.
2. Use `read_first` and local indexes to load only the next required context.
3. Decompose work down to issues. Issue is the atomic executable unit.
4. Let dependencies, not roles, determine sequencing.
5. Assign ready issues to the specialist role best matched to the issue objective and scope.
6. Require proof before review, review before integration, and integration before downstream dependency satisfaction.
7. Roll completion upward from issue to phase to module to program.

## Dependency And Sequencing Model

- Program contains modules.
- Module contains phases.
- Phase contains issues.
- Issue readiness is computed from dependencies, gates, and blockers.
- A phase may have multiple ready issues.
- A module may have multiple ready phases or issues if dependencies allow it.

## Concurrency Model

- Concurrency is allowed when dependency satisfaction makes more than one issue ready.
- Concurrency is denied when one issue depends on another issue's integrated output.
- Orchestration should prefer safe parallelism without bypassing gates.

## Gate Enforcement

- Issue state must pass through `review_ready` before `done`.
- Issue completion requires proof, passing review, and integration.
- Phase review is optional unless the phase or module requires it.
- Module review is mandatory.
- Program or release review is mandatory where applicable.

## Stop Condition

Continue until the target artifact is complete according to its definition of done, or until no executable issue remains and the remaining blockers are genuine unresolved dependencies, decisions, or failed gates.

## Read First

1. `.cursor/execution/INDEX.yaml`
2. `.cursor/execution/MINIMUM-RUNTIME-MODEL.md`
3. `.cursor/execution/AUTONOMOUS-MODULE-EXECUTION.md`
4. `.cursor/agents/INDEX.yaml`
5. `.cursor/templates/INDEX.yaml`
