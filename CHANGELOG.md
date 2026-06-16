# Changelog

## v1.2

- introduced the workspace adoption lifecycle as a one-time operational capability for wiring existing multi-repository workspaces into the shared IDE Development runtime
- added the canonical workspace layer:
  - `core/workspace/INDEX.yaml`
  - `core/workspace/WORKSPACE-ADOPTION.md`
  - `core/workspace/WORKSPACE-DISCOVERY.md`
  - `core/workspace/REPO-WIRING.md`
  - `core/workspace/LEGACY-CLEANUP.md`
  - `core/workspace/WORKSPACE-REPORT.md`
- preserved the existing packaging model:
  - `core/` remains canonical knowledge
  - `.cursor/` remains the compatibility runtime surface
- added workspace adoption routing to bootstrap and root adapter documentation without introducing a new command family
- clarified the separation between one-time workspace adoption and daily session lifecycle operations
- released version `v1.2`

## v1.0.2

- introduced the session lifecycle capability for natural-language resume and close-out behavior
- added the canonical session layer and handoff template
- wired session behavior into bootstrap, workflow, and compatibility routing without adding a new command family

## v1.0.1

- converted the repository from `.cursor` source-of-truth packaging to `core` canonical storage plus `.cursor` compatibility runtime surface
- added Codex and Claude consumption entrypoints
- preserved backward compatibility through `.cursor` adapter links

## v1.0.0

- established the `.cursor` repository as the source of truth for the global AI development core
- finalized the canonical doctrine, artifact, agent, command, runtime, workflow, contract, state, system, bootstrap, and example layers
- added optional discovery and interview support for greenfield and ambiguous work
- completed supervised real-world validation in disposable consumer repositories
- confirmed dependency handling, safe concurrency, issue completion, module review, and module integration in practice
- released the stable v1.0 command surface:
  - `plan-program`
  - `plan-module`
  - `complete-module`
  - `execute-issue`
  - `review-issue`
  - `integrate-issue`
- deferred remaining usability and packaging improvements to later releases
