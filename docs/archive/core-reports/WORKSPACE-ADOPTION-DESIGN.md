# Workspace Adoption Design

## Assumptions

- the active workspace is the workspace whose repositories are visible to the current chat
- `IDE Development` is the system repository inside that workspace
- all other repositories in the workspace are consumer candidates
- workspace adoption is one-time operational wiring, not daily execution behavior
- consumer repositories should keep seeing a normal `.cursor/...` runtime surface

## Workspace Model

Expected model:

```text
Projects/

    IDE Development/
        core/
        .cursor/

    ConsumerRepoA/
    ConsumerRepoB/
```

Interpretation:

- `IDE Development/core` is canonical knowledge
- `IDE Development/.cursor` is the compatibility runtime surface
- consumer repositories attach through `.cursor` symlinks pointing to `../IDE Development/.cursor`

## Repository Discovery

Discovery should:

1. identify repository roots in the active workspace
2. identify `IDE Development` as the system repository
3. skip the system repository
4. inspect all remaining repositories for existing `.cursor`, legacy rules, LiNKdev remnants, and obsolete adapters
5. preserve uncertainty rather than guessing

## Symlink Strategy

For each adopted consumer repository:

`repo/.cursor` -> `../IDE Development/.cursor`

This preserves:

- the existing `.cursor` runtime surface
- compatibility for all existing `.cursor/...` references
- canonical storage in `core/`

## Backup Strategy

Before replacing clearly obsolete shared-system artifacts:

- create backups
- record the backup locations
- avoid destructive change without a recoverable path

## Legacy Cleanup Rules

- inspect existing `.cursor`
- inspect old rules
- inspect legacy LiNKdev remnants
- inspect obsolete adapters
- delete only when the artifact is clearly obsolete shared-system material
- preserve ambiguous material

## Safety Rules

- stop if the active workspace is unclear
- stop if repository classification is ambiguous
- stop if local repository-specific artifacts may be mixed with shared-system artifacts
- prefer backup plus reportable replacement over silent deletion
- preserve backward compatibility of `.cursor/...` paths

## Rollback Strategy

Rollback should be possible by:

1. removing the newly created consumer `.cursor` symlink
2. restoring any backed-up legacy material
3. re-running verification

The adoption report should contain enough information to support rollback without hidden context.

## Integration Points

Integrated with:

- bootstrap onboarding after cloning `IDE Development`
- session lifecycle only as a distinction:
  - workspace adoption is one-time
  - session start and end remain daily behavior
- packaging model:
  - `core/` canonical
  - `.cursor/` compatibility runtime surface

## Expected Result

After adoption:

- no duplicate knowledge copies are needed
- consumer repositories resolve `.cursor/...` through the shared runtime surface
- `core/` remains canonical
- the existing runtime and architecture remain unchanged
