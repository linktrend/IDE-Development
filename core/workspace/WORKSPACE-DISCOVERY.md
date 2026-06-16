# Workspace Discovery

## Purpose

Define how repositories are discovered inside the current workspace before consumer wiring begins.

## Active Workspace Rule

The active workspace is the parent workspace whose repositories are visible to the current chat.

If no workspace is clearly visible:

- stop
- ask which workspace is intended
- do not guess

## Discovery Rules

1. identify repository roots inside the current workspace
2. treat the repository named `IDE Development` as the system repository when present
3. skip the system repository during consumer adoption
4. treat every other repository root as a consumer candidate
5. inspect only the repository roots required for the adoption decision

## Candidate Signals

For each repository candidate, inspect:

- `.git/`
- `.cursor/`
- known legacy rules or adapters
- legacy LiNKdev remnants

## Exclusion Rule

Do not attempt to adopt:

- the `IDE Development` repository itself
- non-repository folders unless the user explicitly wants them converted into repositories
- ambiguous directories that cannot be classified safely

## Discovery Output

Minimum discovery output:

- workspace root
- system repository path
- consumer repository list
- skipped directories
- ambiguous directories requiring user judgment
