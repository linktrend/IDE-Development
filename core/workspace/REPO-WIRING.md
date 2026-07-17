# Repo Wiring

## Purpose

Define how consumer repositories are attached to the shared runtime surface after safe discovery and cleanup review.

## Preferred Method — Deterministic Script

When the consumer repository path is known and legacy cleanup has already been reviewed, prefer the wiring script:

```bash
./scripts/wire-repo.sh /path/to/consumer-repo
```

From inside `IDE Development`, pass an absolute or relative path to the consumer repository root.

The script:

- verifies the target is a directory and is not the system repository itself
- detects an already-correct symlink and exits cleanly (idempotent)
- backs up an existing `.cursor` directory or mismatched symlink to `.cursor-backup-<timestamp>/`
- creates `repo/.cursor` as a relative symlink to `IDE Development/.cursor`
- verifies required runtime paths are reachable from the consumer repository
- touches only `.cursor` in the consumer repository

Agents receiving natural-language wiring requests should run this script and report its pass/fail output rather than improvising symlink commands by hand.

## Manual Fallback

Use manual wiring only when judgment is required first — for example, when an existing `.cursor` contains mixed repository-specific rules and shared-system copies that must be inspected per `LEGACY-CLEANUP.md` before replacement.

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
