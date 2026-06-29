# Post-Readiness Clarifications

## Purpose

Record clarifications from the readiness review so deliberate design choices are not mistaken for unresolved gaps.

## Agent Compliance

The system is intentionally compliance-based.

Cursor and Codex consume repository-visible instructions, rules, prompts, artifacts, and files. The core therefore uses doctrine, artifacts, gates, proof, review, integration, and state transitions as the control structure.

An executable controller is not required for v1 because it would only help if Cursor or Codex could reliably route work through that controller. The core must remain usable when the runtime is an AI agent reading files in a workspace.

Optional future automation may be useful, but it should be treated as a runtime adapter, not as the source of truth.

## Installation

The intended installation model is workspace visibility plus symlink wiring.

For Cursor:

- include `IDE Development` as a folder in the workspace
- ensure consumer repository `.cursor` paths resolve to `../IDE Development/.cursor`

For Codex:

- ensure the `IDE Development` repository is discoverable from the working context
- ensure agents can follow `.cursor` compatibility paths into `core`

No installer script is required for normal use. A script or verifier may be added later only if repeated manual adoption becomes error-prone.

## Disposable Validation Repositories

Deleting disposable validation repositories after verification is acceptable.

The permanent evidence should live in retained reports, release notes, pilots, and canonical examples. Disposable repositories should not remain on disk unless they contain ongoing validation material that still needs inspection.

Keeping stale validation workspaces can create confusion about source of truth, current version, and whether old scaffolding is still active.

## Skills

The current local skills catalog is intentionally small.

The missing broader skill inventory is a migration task, not a blocker for the core workflow. Existing repository skills, including any referred to as `g skills` or `gstack`, should be inventoried and reviewed before import so they can be merged, rewritten, or left repository-local as appropriate.

## Usability Friction

Known friction means the system works, but some parts may feel heavier than ideal in day-to-day use.

Examples:

- small tasks may require more ceremony than they deserve
- first-time adoption may involve several files and concepts
- legacy compatibility names may add reading noise
- module-level review ownership may need clearer default guidance

These are usability improvements, not evidence that the core workflow is incomplete.
