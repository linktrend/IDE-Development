# Command Classification

## Scope

Reviewed only:

- `.cursor/commands/`
- `.cursor/commands/INDEX.yaml`

## Command Inventory

Indexed command files:

- `.cursor/commands/plan-program.md`
- `.cursor/commands/plan-module.md`
- `.cursor/commands/complete-module.md`
- `.cursor/commands/execute-issue.md`
- `.cursor/commands/review-issue.md`
- `.cursor/commands/integrate-issue.md`
- `.cursor/commands/linkdev-go.md`
- `.cursor/commands/linkdev-dispatch.md`
- `.cursor/commands/linkdev-ui-automations.md`
- `.cursor/commands/linkdev-wire-post-dispatch.md`
- `.cursor/commands/linkdev-wire-post-ui.md`
- `.cursor/commands/wire-linkdev.md`

Non-indexed file:

- `.cursor/commands/README.md`

## Discoverability

### Command Files

All executable command wrapper files are discoverable through `.cursor/commands/INDEX.yaml`.

There are no orphan command wrappers in the current directory.

### README

`commands/README.md` is not indexed.

Verdict:

- if the index is meant to cover only executable command wrappers, excluding `README.md` is reasonable
- if the index is meant to make every file in the directory discoverable, `README.md` should be indexed

Recommended interpretation:

- `commands/README.md` should be intentionally excluded only if the team explicitly defines the index as "wrapper inventory only"
- otherwise it should be indexed as a navigational file

Because the current system emphasizes progressive disclosure, indexing the README would be cleaner and more consistent.

## Classification

### ACTIVE

These commands are clear, doctrine-aligned, and appropriate for new work.

- `plan-program`
- `plan-module`
- `complete-module`
- `execute-issue`
- `review-issue`
- `integrate-issue`

Reason:

- they align with the current execution doctrine
- they map cleanly onto `Program -> Module -> Phase -> Issue`
- they preserve issue as the atomic executable unit

### OPTIONAL

None identified in the current command surface.

Reason:

- the current set splits cleanly between canonical active commands and older compatibility commands
- no command appears to be both doctrine-aligned and merely situational enough to warrant an `OPTIONAL` classification

### LEGACY

These commands are retained for continuity with older workflows but are not preferred for new work.

- `linkdev-go`
- `linkdev-dispatch`
- `linkdev-ui-automations`
- `linkdev-wire-post-dispatch`
- `linkdev-wire-post-ui`
- `wire-linkdev`

Reason:

- they are explicitly described as compatibility-oriented
- they route into older planning or setup prompts rather than the canonical execution command layer
- they do not express the current execution hierarchy directly

### DEPRECATED

Strong candidates for deprecation, but not yet formally marked as such:

- `linkdev-ui-automations`
- `linkdev-wire-post-ui`

Reason:

- both are alias-style wrappers rather than distinct command concepts
- each mostly redirects to another legacy command or prompt
- their names are less clear than the command they point to

Current status:

- not formally deprecated today
- should be treated as legacy aliases pending a later policy decision

## Naming Issues

### Canonical Commands

The newer execution commands are consistent:

- verb-noun
- kebab-case
- outcome-oriented
- doctrine-aligned

Examples:

- `plan-program`
- `complete-module`
- `execute-issue`

### Legacy Commands

Naming drift exists in the older set:

- `wire-linkdev` reverses the dominant `linkdev-*` prefix pattern
- `linkdev-go` is vague compared with `plan-program`
- `linkdev-ui-automations` is broad and ambiguous
- `linkdev-wire-post-ui` reads like an alias chain rather than a primary command concept

This does not break functionality, but it weakens discoverability and increases cognitive load.

## Doctrine Alignment

### Aligned With Execution Doctrine

- `plan-program`
- `plan-module`
- `complete-module`
- `execute-issue`
- `review-issue`
- `integrate-issue`

These are aligned because they reflect the actual execution model and gate structure.

### Not Aligned As Canonical Execution Commands

- `linkdev-go`
- `linkdev-dispatch`
- `linkdev-ui-automations`
- `linkdev-wire-post-dispatch`
- `linkdev-wire-post-ui`
- `wire-linkdev`

These are not violations by themselves because they are compatibility commands, but they are outside the canonical doctrine-driven execution surface.

## `wire-linkdev.md` Verdict

Current file:

- `.cursor/commands/wire-linkdev.md`

Current behavior:

- thin wrapper to `.cursor/prompts/setup/WIRE.md`

Assessment:

- it is not aligned with the canonical execution doctrine
- its name is inconsistent with the `linkdev-*` pattern used by the other legacy commands
- it appears to be a legacy setup command, not a current execution command

Verdict:

- it should not remain active
- it does not need immediate removal
- it should be treated as `LEGACY` now
- it is a reasonable future `DEPRECATED` candidate if compatibility demand falls away

Rename recommendation:

- no rename should occur automatically during analysis
- if renamed later, it should be for compatibility cleanup only, not because it belongs in the active execution layer

Best current classification:

- `LEGACY`

## Recommended Actions

### High Value

1. Decide explicitly whether `commands/README.md` belongs in `INDEX.yaml`.

2. Preserve the six execution commands as the only active canonical command surface:
   - `plan-program`
   - `plan-module`
   - `complete-module`
   - `execute-issue`
   - `review-issue`
   - `integrate-issue`

3. Keep `wire-linkdev.md` as legacy, not active.

### Medium Value

1. Mark alias-like legacy commands more clearly in the index:
   - `linkdev-ui-automations`
   - `linkdev-wire-post-ui`

2. Separate the command inventory conceptually into:
   - canonical execution commands
   - legacy compatibility commands

3. Consider whether `wire-linkdev.md` should later be formally deprecated rather than merely legacy.

### Low Value

1. Normalize legacy naming only if compatibility constraints permit it.

2. Decide whether any setup-era commands still need first-class visibility at all.

## Files Affected

Reviewed files:

- `.cursor/commands/INDEX.yaml`
- `.cursor/commands/README.md`
- `.cursor/commands/complete-module.md`
- `.cursor/commands/execute-issue.md`
- `.cursor/commands/integrate-issue.md`
- `.cursor/commands/linkdev-dispatch.md`
- `.cursor/commands/linkdev-go.md`
- `.cursor/commands/linkdev-ui-automations.md`
- `.cursor/commands/linkdev-wire-post-dispatch.md`
- `.cursor/commands/linkdev-wire-post-ui.md`
- `.cursor/commands/plan-module.md`
- `.cursor/commands/plan-program.md`
- `.cursor/commands/review-issue.md`
- `.cursor/commands/wire-linkdev.md`

Report created:

- `.cursor/reports/COMMAND-CLASSIFICATION.md`

## Summary Verdict

The command layer is structurally usable and fully covers its executable wrapper files through the index.

The active command surface is clean and doctrine-aligned.

The main remaining issues are:

- whether `commands/README.md` should be indexed
- inconsistent naming among legacy commands
- legacy alias wrappers that are plausible deprecation candidates

`wire-linkdev.md` should be treated as `LEGACY`, not active.
