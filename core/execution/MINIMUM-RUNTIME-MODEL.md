# Minimum Runtime Model

This model defines the minimum concepts required for autonomous execution using artifacts alone.

## Hierarchy

- **Program**: the total body of work directed toward a meaningful outcome.
- **Module**: a major domain area within a program.
- **Phase**: a checkpointed subset of work within a module.
- **Issue**: the atomic executable unit.

Programs, modules, and phases organize scope and checkpoints. Issues are the actual execution nodes.

## Issue State Model

Minimum issue states:

- `draft`
- `planned`
- `blocked`
- `ready`
- `in_progress`
- `review_ready`
- `done`

`ready` is computed from satisfied dependencies and unmet blockers. `done` requires proof, review, and integration.

## Dependency Model

- Dependencies are declared between issues.
- The issue graph must be acyclic.
- Readiness is derived from dependency satisfaction plus local gate satisfaction.
- Modules and phases may imply grouping, but issue-level dependencies remain authoritative.

## Concurrency Model

- Any issue with satisfied dependencies may execute.
- Modules, phases, and issues may progress in parallel if their issue dependencies allow it.
- Practical concurrency may still be limited by review capacity, integration risk, or shared execution scope.

## Gate Model

Minimum gates:

1. **Planning gate**: the work is defined well enough to execute.
2. **Readiness gate**: dependencies, scope, and required inputs are satisfied.
3. **Execution gate**: work has been performed and proof exists.
4. **Review gate**: an independent evaluator confirms the result is valid and non-vacuous.
5. **Integration gate**: reviewed work is incorporated into the active line.
6. **Release gate**: higher-level completion and release criteria are satisfied.

## Proof Model

Every issue must produce proof that:

- maps acceptance criteria to evidence
- identifies artifacts, observations, or state changes
- distinguishes verified facts from assumptions
- records blockers and failed attempts when incomplete

Proof may also exist at phase, module, and program level.

## Review Model

Review validates:

- scope compliance
- acceptance criteria satisfaction
- sufficiency of proof
- absence of vacuous completion claims

Review outcomes are `pass`, `fail`, or `blocked`.

## Integration Model

Integration:

- accepts reviewed work into the active line
- changes issue state to `done`
- enables recomputation of downstream readiness

Integrated work, not merely executed work, satisfies dependencies for downstream issues.

## Release Model

Release applies above issue level.

Module or program release requires:

- all required child work complete
- higher-level definition of done satisfied
- final proof and validation complete
- any required human approval recorded

## Agent Coordination Model

Humans and AI agents are runtime resources assigned to issues based on capability.

- artifacts and dependencies determine sequence
- agents perform work, review, or integration
- agent identity must not be the primary sequencing mechanism

## Progressive Disclosure Model

Agents should read:

1. the relevant index
2. the current program or module artifact
3. the current issue and its dependencies
4. only the rules, proofs, reviews, and related artifacts required for the current step

Agents should not scan the whole repository by default. Execution should emerge from targeted reads of structured artifacts.
