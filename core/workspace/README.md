# Workspace

This directory defines the canonical workspace adoption lifecycle.

Use it when an existing workspace already contains multiple repositories and needs to be wired to the shared IDE Development runtime as a one-time operation.

Read `INDEX.yaml` first.

Preferred documents are:

- `WORKSPACE-ADOPTION.md` for the overall model
- `WORKSPACE-DISCOVERY.md` for repository discovery
- `REPO-WIRING.md` for consumer repository symlink wiring
- `LEGACY-CLEANUP.md` for safe cleanup and backup rules
- `WORKSPACE-REPORT.md` for adoption reporting

Workspace adoption is separate from daily session behavior.

- workspace adoption: one-time installation and wiring
- session lifecycle: ongoing start-of-day and end-of-day behavior

This layer extends the existing bootstrap, session, packaging, and runtime surface. It does not introduce a new command family.
