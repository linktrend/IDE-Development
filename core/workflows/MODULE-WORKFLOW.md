# Module Workflow

## Purpose

This workflow defines how a module is decomposed into phases and issues and how module completion is determined.

## Responsibilities

- define executable module scope
- group work into phases where useful
- reduce work into issues
- maintain module definition of done
- roll issue completion upward into module completion

## Workflow Boundary

This workflow governs:

- `MODULE.md`
- `PHASE.md`
- `ISSUE.md`
- module-level review and integration expectations

It does not bypass issue-level execution.

## Input Contract

Required inputs:

- parent `PROGRAM.md`
- target module objective
- constraints relevant to the module

Required artifacts:

- `MODULE.md`
- zero or more `PHASE.md`
- one or more `ISSUE.md`

## Entry Conditions

- the program exists
- the module objective is defined
- module scope can be reduced to issue-level work

## Transitions

1. Load the program and module artifacts.
2. Define or confirm phases.
3. Define or confirm issues inside each phase.
4. Establish issue dependencies.
5. Hand executable issues to the issue workflow.
6. Track roll-up from issue completion to phase progress and module progress.
7. Complete required module review and any required module-level integration record.

## Output Contract

Required outputs:

- module artifact with phases and definition of done
- phase artifacts with issue lists
- issue artifacts with dependencies and acceptance criteria
- module-level completion evidence when done

## Exit Conditions

The workflow exits successfully when:

- required issues are done
- phase criteria are satisfied
- module definition of done is satisfied
- required module review is complete

The workflow exits unsuccessfully when:

- the module cannot be reduced to executable issues
- no issue can become ready and genuine blockers remain

## Ownership

Typical owners:

- human operator
- planner resource
- orchestrator resource
- technical lead resource

## Side Effects

- creates the issue graph for the module
- defines concurrency opportunities
- constrains downstream review and integration work

## Read Next

1. `ISSUE-WORKFLOW.md`
2. `REVIEW-WORKFLOW.md`
3. `INTEGRATION-WORKFLOW.md`
