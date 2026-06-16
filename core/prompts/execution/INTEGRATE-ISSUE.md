# Integrate Issue

## Read First

1. `.cursor/README.md`
2. `.cursor/rules/00-linkdev-bootstrap.mdc`
3. `.cursor/execution/INDEX.yaml`
4. `.cursor/execution/MINIMUM-RUNTIME-MODEL.md`
5. `.cursor/templates/INDEX.yaml`
6. `.cursor/agents/INDEX.yaml`
7. `.cursor/agents/integrator/AGENT.md`
8. the target `ISSUE.md`
9. the passing `REVIEW.md`

## Doctrine

Only passing review permits integration. Dependencies are satisfied by integrated work, not by partially executed work.

## Templates

- `ISSUE.md`
- `REVIEW.md`
- `INTEGRATION.md`

## Expected Output

- an integration artifact that records final state and downstream effects
- downstream readiness recomputation inputs for the orchestrator

## Stop When

- the issue has been explicitly integrated and downstream effects are recorded

## Blocked Means

- review did not pass
- integration impact cannot be determined safely
- integration reveals unresolved conflicts or new blockers

## Must Not Skip

- verification of passing review
- final-state recording
- downstream readiness effects
