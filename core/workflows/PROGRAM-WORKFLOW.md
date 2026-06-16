# Program Workflow

## Purpose

This workflow defines how work moves from validated intent into a program that can support executable module work.

## Responsibilities

- validate that a program should exist
- establish the top-level structure of modules
- define program-wide constraints and definition of done
- provide the contract for module-level execution

## Workflow Boundary

This workflow governs:

- `INTENT.md`
- `PROGRAM.md`
- module references declared inside the program

It does not execute issues directly.

## Input Contract

Required inputs:

- intent objective
- scope and out-of-scope definition
- constraints
- success criteria

Required artifacts:

- `INTENT.md`

## Entry Conditions

- the work has been expressed clearly enough to evaluate as intent
- the runtime or operator can make a go or no-go decision

## Transitions

1. Create or refine `INTENT.md`.
2. Evaluate verdict and eligibility for program creation.
3. If accepted, create or update `PROGRAM.md`.
4. Define modules, global constraints, and program definition of done.
5. Hand off target modules to the module workflow.

## Output Contract

Required outputs:

- accepted or rejected intent decision
- `PROGRAM.md`
- module list with paths
- explicit program constraints and release expectations

## Exit Conditions

The workflow exits successfully when:

- program creation is justified
- `PROGRAM.md` is coherent
- at least one module can enter the module workflow

The workflow exits unsuccessfully when:

- intent is rejected, deferred, or still requires revision

## Ownership

Typical owners:

- human operator
- planner resource
- product owner resource
- technical lead resource

## Side Effects

- establishes the top-level work container
- creates module execution boundaries
- constrains downstream workflows

## Read Next

1. `MODULE-WORKFLOW.md`
