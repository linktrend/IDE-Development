# Repo Wiring

## Purpose

Define how consumer repositories are attached to the shared runtime surface after safe discovery and cleanup review.

## Wiring Rule

For each consumer repository:

- create `repo/.cursor` as a symbolic link to `../IDE Development/.cursor`

This preserves the existing runtime surface while keeping `IDE Development/core` as canonical storage through the packaging chain.

## Resolution Chain

Expected resolution:

`repo/.cursor` -> `../IDE Development/.cursor` -> `../IDE Development/core`

## Preconditions

Before wiring:

- repository identity must be clear
- any existing `.cursor` state must be inspected
- uncertain material must be preserved
- backups must exist when replacement is safe but destructive

## Verification

After wiring, verify:

- `repo/.cursor` exists
- the symlink resolves correctly
- `.cursor/README.md` is accessible from the consumer repository
- `.cursor/execution/INDEX.yaml` is accessible from the consumer repository
- `.cursor/templates/INDEX.yaml` is accessible from the consumer repository
- `.cursor/commands/INDEX.yaml` is accessible from the consumer repository

## Backward Compatibility Rule

Consumer repositories should continue to see a normal `.cursor/...` runtime surface.

The consumer repository should not need to know that:

- `IDE Development/.cursor` is itself an adapter
- `IDE Development/core` is canonical storage

## Duplicate Copy Rule

Do not create duplicate content copies inside consumer repositories when a symlink is sufficient and safe.
