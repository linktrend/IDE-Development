# Stabilization Pass

## Changes Performed

1. Indexed navigational README files for strict discoverability:
   - `.cursor/agents/README.md`
   - `.cursor/commands/README.md`

2. Indexed the agent and command index files themselves so strict file-by-file discoverability no longer leaves the index entrypoints as exceptions.

3. Clarified the overlap between:
   - `.cursor/agents/project-planner.md`
   - `.cursor/agents/planner/AGENT.md`

   The legacy flat role was preserved for backward compatibility, but it is now explicitly marked as compatibility-only and not preferred for new execution work.

4. Reclassified legacy command wrappers in `.cursor/commands/INDEX.yaml`:
   - `linkdev-go` -> `legacy`
   - `linkdev-dispatch` -> `legacy`
   - `linkdev-wire-post-dispatch` -> `legacy`
   - `wire-linkdev` -> `legacy`

5. Marked deprecated compatibility aliases in `.cursor/commands/INDEX.yaml`:
   - `linkdev-ui-automations` -> `deprecated`
   - `linkdev-wire-post-ui` -> `deprecated`

6. Updated `.cursor/commands/README.md` so direct readers see the legacy versus deprecated split without needing to infer it from the index.

## Files Modified

- `.cursor/agents/INDEX.yaml`
- `.cursor/agents/project-planner.md`
- `.cursor/commands/INDEX.yaml`
- `.cursor/commands/README.md`

## Files Created

- `.cursor/reports/STABILIZATION-PASS.md`

## Legacy Commands Retained

- `.cursor/commands/linkdev-go.md`
- `.cursor/commands/linkdev-dispatch.md`
- `.cursor/commands/linkdev-wire-post-dispatch.md`
- `.cursor/commands/wire-linkdev.md`

## Deprecated Commands Retained

- `.cursor/commands/linkdev-ui-automations.md`
- `.cursor/commands/linkdev-wire-post-ui.md`

## Orphan Check

Within the scoped directories:

- no orphan command wrapper files remain
- no orphan agent files remain
- the scoped README files are now discoverable through their directory indexes
- the scoped index files are now self-describing and no longer remain as strict discoverability exceptions

## Remaining Concerns

1. `architect-integrator.md` still has name overlap with the canonical `integrator` control role, but this was not changed in the controlled pass.

2. Legacy command naming remains historically inconsistent, especially `wire-linkdev`, but backward compatibility was preserved.

3. The reports directory itself is intentionally not indexed in this pass because report indexing was outside the stabilization scope.
