# Bootstrap Design

## Onboarding Flow

The bootstrap layer provides a canonical route from zero context into the assembled `.cursor` system.

The onboarding flow is:

1. start with `.cursor/bootstrap/START-HERE.md`
2. read `.cursor/README.md`
3. identify the active work level
4. open the nearest bootstrap document
5. route into the preferred command layer
6. load only the doctrine, templates, state, workflows, and contracts required for that work level

## Startup Flow

The startup model is intentionally narrow:

- new repository or project: `PROJECT-BOOTSTRAP.md`
- new module: `MODULE-BOOTSTRAP.md`
- atomic work: `ISSUE-BOOTSTRAP.md`
- active work resumption: `SESSION-STARTUP.md`

The bootstrap layer does not replace doctrine or workflows. It only tells the operator what to read first and what minimum artifacts are required.

## Session Lifecycle

Session lifecycle is split into two explicit documents:

- `SESSION-STARTUP.md` for establishing context, active level, active command, and current state
- `SESSION-SHUTDOWN.md` for preserving state, blockers, pending gates, and next actions

This keeps session handling artifact-driven and avoids hidden chat-only context.

## Minimum Viable System

The minimum viable usable system for a fresh repository is:

- `.cursor/README.md`
- `.cursor/execution/`
- `.cursor/templates/`
- `.cursor/commands/`
- one real artifact path at intent, program, module, or issue level

The bootstrap layer makes this minimum system discoverable and operational.

## Remaining Work Before v1.0 Release

- add bootstrap discoverability from higher-level entrypoints if broader onboarding becomes necessary
- validate the bootstrap sequence in a real low-risk repository handoff
- confirm that all supported runtimes can follow the startup path without over-reading the repository

## Overall Assessment

The bootstrap layer closes the zero-to-usable gap. A fresh repository or fresh AI session now has a canonical read order, startup path, shutdown path, and minimum artifact model without adding code, automation, or a new control structure.
