# Complete Module

## Read First

1. `.cursor/README.md`
2. `.cursor/rules/00-linkdev-bootstrap.mdc`
3. `.cursor/execution/INDEX.yaml`
4. `.cursor/execution/MINIMUM-RUNTIME-MODEL.md`
5. `.cursor/execution/AUTONOMOUS-MODULE-EXECUTION.md`
6. `.cursor/templates/INDEX.yaml`
7. `.cursor/agents/INDEX.yaml`
8. `.cursor/agents/squads/autonomous-development-squad.md`
9. the target `MODULE.md`

## Doctrine

Use the autonomous module execution model. Issue is the atomic executable unit. Dependencies determine order. Review and integration gates cannot be skipped.

## Templates

- `MODULE.md`
- `PHASE.md`
- `ISSUE.md`
- `PROOF.md`
- `REVIEW.md`
- `INTEGRATION.md`

## Expected Output

- execution through ready issues until the module reaches its definition of done or becomes genuinely blocked
- proof, review, and integration artifacts for completed work
- explicit module-level review and module-level integration if module state changes

## Stop When

- the module has satisfied its definition of done and mandatory module review, or
- no executable issue remains and the unresolved blockers are genuine

## Blocked Means

- dependencies are unsatisfied
- required proof fails review
- an unresolved decision or external dependency prevents further ready issues

## Must Not Skip

- readiness computation
- `review_ready` before `done`
- independent review
- integration after passing review
- downstream readiness recomputation
