# Workspace Adoption

## Purpose

Define the one-time operational capability for adopting an existing multi-repository workspace into the IDE Development system.

This capability exists so phrases such as:

- `Install the system into this workspace.`
- `Adopt this workspace.`
- `Wire this workspace to IDE-Development.`

route into the correct workspace-level behavior without introducing a new command family.

## Workspace Model

Example:

```text
Projects/

    IDE Development/
        core/
        .cursor/

    LinkTrendMediaSite/
    LiNKvoice/
    AnotherRepo/
```

Rules:

- `IDE Development` is the system repository
- every other repository is a consumer repository
- the shared runtime surface comes from `IDE Development/.cursor`
- the canonical knowledge asset remains `IDE Development/core`

## One-Time Nature

Workspace adoption is a one-time installation and wiring operation.

It is not:

- a daily session-start behavior
- a daily session-end behavior
- a replacement for module or issue execution

After adoption is complete, normal work should continue through the existing session lifecycle and execution model.

## Adoption Sequence

1. determine the active workspace from the current chat-visible filesystem context
2. discover repositories in the workspace
3. identify the system repository and skip it
4. inspect every other repository for:
   - existing `.cursor`
   - old rules
   - legacy LiNKdev remnants
   - obsolete adapters
5. preserve anything uncertain
6. if safe, create backups of replaceable legacy material
7. remove only clearly obsolete shared-system artifacts
8. create `repo/.cursor` as a symlink to `../IDE Development/.cursor`
9. verify:
   - `repo/.cursor`
   - `IDE Development/.cursor`
   - `IDE Development/core`
10. produce an adoption report

## Natural-Language Trigger Rule

Natural-language workspace adoption requests should route into `.cursor/workspace/INDEX.yaml`.

No separate command family should be created.

## Read Next

1. `WORKSPACE-DISCOVERY.md`
2. `REPO-WIRING.md`
3. `LEGACY-CLEANUP.md`
4. `WORKSPACE-REPORT.md`
