# Review Workflow

## Purpose

This workflow defines how proof is evaluated and how work either progresses to integration or returns for rework.

## Responsibilities

- evaluate proof against acceptance criteria or higher-level completion conditions
- reject vacuous completion
- determine `pass`, `fail`, or `blocked`
- preserve review findings clearly

## Workflow Boundary

This workflow governs:

- `PROOF.md`
- `REVIEW.md`
- review outcomes for issues, modules, and programs where applicable

It does not perform integration directly.

## Input Contract

Required inputs:

- subject artifact
- proof artifact
- relevant completion criteria

Required artifacts:

- review artifact

## Entry Conditions

- proof exists
- the subject is reviewable
- the reviewing party is independent enough to evaluate the work credibly

## Transitions

1. Load the subject artifact and proof.
2. Evaluate evidence against criteria.
3. Record findings.
4. Issue one of:
   - `pass`
   - `fail`
   - `blocked`
5. If pass, hand the work to the integration workflow.
6. If fail or blocked, return the work to execution or blocker resolution.

## Output Contract

Required outputs:

- `REVIEW.md`
- explicit verdict
- explicit next action

## Exit Conditions

The workflow exits successfully when:

- a defensible review verdict exists

The workflow exits unsuccessfully when:

- the proof is too incomplete or ambiguous to evaluate
- review is blocked by missing artifacts or unresolved criteria

## Ownership

Typical owners:

- human reviewer
- reviewer resource
- QA support resource
- product or technical escalation resource when needed

## Side Effects

- authorizes or prevents progression
- generates rework obligations
- may create escalation needs

## Read Next

1. `INTEGRATION-WORKFLOW.md`
2. `ISSUE-WORKFLOW.md`
