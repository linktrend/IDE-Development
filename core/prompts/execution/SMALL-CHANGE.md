# Small Change

## Read First

1. `.cursor/README.md`
2. `.cursor/rules/00-linkdev-bootstrap.mdc`
3. `.cursor/execution/INDEX.yaml`
4. `.cursor/execution/MINIMUM-RUNTIME-MODEL.md`
5. `.cursor/templates/ISSUE.md`
6. `.cursor/templates/PROOF.md`
7. `.cursor/templates/REVIEW.md`
8. `.cursor/templates/INTEGRATION.md`

## Purpose

Provide a lightweight path for tiny bugs and simple changes while preserving the anti-incompletion rules.

## Eligibility

Use this path only when all are true:

- the requested change is clear
- the expected code or documentation change is small
- no new module, program, architecture decision, or product discovery is needed
- dependencies are obvious or absent
- risk is low enough that a compact issue record is sufficient

If any condition is false, route to `plan-program`, `plan-module`, or `execute-issue`.

## Doctrine

Small changes still execute as issues.

The issue record may be compact, but it must still include:

- objective
- scope
- acceptance criteria
- proof requirement
- review expectation
- integration expectation

## Expected Output

- minimal issue record or update to an existing issue
- implemented change
- concrete proof
- review verdict
- integration record
- final state of `done` only after proof, passing review, and integration

## Stop When

- the change is integrated and verified, or
- the work is no longer small and must be routed into the normal planning or issue path, or
- a genuine blocker prevents completion

## Must Not Skip

- explicit acceptance criteria
- proof before review
- review before integration
- integration before `done`
- blocker trail if the change cannot complete

## Compact Artifact Guidance

For a tiny change, proof, review, and integration may be concise. They may be separate short artifacts or clearly labeled sections in the issue-adjacent work record if the repository has not created a full artifact tree yet.

Concise does not mean vague. The proof must identify what changed and how it was verified.
