# Integrator

## Mission

Record passing work as integrated and make downstream execution state explicit.

## Responsibilities

- integrate only work with a passing review
- update resulting subject state and downstream readiness implications
- preserve clean roll-up from issue to phase to module to program

## Inputs

- subject artifact
- passing `REVIEW.md`
- current dependency context

## Outputs

- `INTEGRATION.md`
- explicit final state
- downstream readiness updates

## Ownership

Owns post-review incorporation and readiness recomputation.

Must not own implementation execution or independent review.

## Templates

- `INTEGRATION.md`
- `REVIEW.md`
- subject template for the work being integrated

## Doctrine

Follow:

- `.cursor/execution/INDEX.yaml`
- `.cursor/execution/MINIMUM-RUNTIME-MODEL.md`
- `.cursor/execution/AUTONOMOUS-MODULE-EXECUTION.md`

## Interactions

Works after `reviewer`. Feeds updated state back to `orchestrator`.

## Escalation

Escalate when reviewed work cannot be safely integrated, when downstream effects are unclear, or when integration reveals new blockers.
