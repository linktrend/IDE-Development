# Execute Issue

## Read First

1. `.cursor/README.md`
2. `.cursor/rules/00-linkdev-bootstrap.mdc`
3. `.cursor/execution/INDEX.yaml`
4. `.cursor/execution/MINIMUM-RUNTIME-MODEL.md`
5. `.cursor/templates/INDEX.yaml`
6. `.cursor/agents/INDEX.yaml`
7. the target `ISSUE.md`
8. only the artifacts listed in that issue's `read_first`

## Doctrine

Issue is the atomic executable unit. Execute only when dependencies are satisfied and the issue is truly ready.

## Templates

- `ISSUE.md`
- `PROOF.md`
- `REVIEW.md`
- `INTEGRATION.md`

## Expected Output

- executed issue work within scope
- a concrete proof artifact
- state transition to `review_ready`, not directly to `done`

## Stop When

- the issue is ready for independent review, or
- the issue is genuinely blocked

## Blocked Means

- a dependency is not integrated
- a blocker in the issue artifact remains unresolved
- acceptance cannot be satisfied with current inputs or constraints

## Must Not Skip

- scope boundaries
- acceptance criteria
- proof requirements
- `review_ready` handoff
