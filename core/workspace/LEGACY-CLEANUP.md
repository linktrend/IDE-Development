# Legacy Cleanup

## Purpose

Define how legacy repository artifacts are reviewed and handled during workspace adoption without risking data loss.

## Inspection Targets

Inspect for:

- existing `.cursor`
- old rules
- legacy LiNKdev remnants
- obsolete IDE-Development adapters
- uncertain local artifacts that may still matter

## Safety Rules

- preserve anything uncertain
- do not delete ambiguous material
- do not remove local repository-specific artifacts unless they are clearly obsolete shared-system remnants
- prefer backup before replacement when destructive change is involved

## Safe Replacement Cases

Replacement may be safe when:

- the existing `.cursor` is clearly an old shared-system copy
- the existing adapter is obsolete and superseded by the current `IDE Development/.cursor`
- legacy LiNKdev remnants are clearly not repository-specific and only duplicate the shared system

## Backup Rule

When replacing a clearly obsolete shared-system artifact:

- create a backup first
- record the backup location in the workspace adoption report

## Stop Conditions

Stop and ask when:

- repository-specific local changes are mixed with shared-system artifacts
- it is unclear whether a `.cursor` folder contains unique local knowledge
- cleanup would require guessing intent
