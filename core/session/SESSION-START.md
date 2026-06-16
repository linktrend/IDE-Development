# Session Start

## Purpose

Define the operational behavior for natural-language session start and resume requests.

## Trigger Examples

- `Let's continue.`
- `Continue development.`
- `Pick up where we left off.`
- `Resume work.`

## Start Sequence

1. determine the active repository from the files visible to the current chat
2. if no active repository is clear, stop and ask which repository is intended
3. run `git pull`
4. locate the newest handoff report under `docs/handoff/`
5. read the latest `docs/handoff/YYYY-MM-DD.md`
6. reconstruct:
   - completed work
   - remaining work
   - blockers
   - recommended next action
7. inspect the active program, module, phase, and issue artifacts relevant to the resumed scope
8. compute ready issues from dependencies and current states
9. identify the current module if module-scoped work is active
10. present the recommended next action
11. continue through the existing execution path

## If No Handoff Exists

If `docs/handoff/` does not exist or no handoff report is present:

- inspect git status
- inspect the relevant artifact tree
- reconstruct context from repository files and recent git history
- state explicitly that no handoff report was available

## Pull Failure Behavior

If `git pull` fails:

- stop
- surface the exact failure
- do not continue execution until repository state is coherent

## Start Outputs

Minimum outputs:

- active repository confirmation
- latest handoff location, if present
- concise resumed-context summary
- current module, if identifiable
- ready issues, if identifiable
- recommended next action

## Integration With Existing System

After context is reconstructed:

- use `.cursor/bootstrap/SESSION-STARTUP.md` for startup responsibilities
- use `.cursor/commands/INDEX.yaml` to select the normal execution entrypoint
- use `.cursor/runtime/DEPENDENCY-RESOLUTION.md` to compute ready issues
- use `.cursor/workflows/` and `.cursor/templates/` as required by the chosen path
