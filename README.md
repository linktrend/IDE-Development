# IDE Development

**LiNKdeveloper** — the semi-manual Application Factory operating system for LiNKtrend venture development.

This repository contains the global AI development core used across Cursor, Codex, and future tools.

The canonical knowledge asset lives in [`core/`](core/). The compatibility runtime surface for existing Cursor-oriented consumers remains in [`.cursor/`](.cursor/README.md).

Repository structure:

- [`core/`](core/): canonical portable knowledge asset
- [`.cursor/`](.cursor/README.md): compatibility runtime surface and Cursor-specific adapter layer
- [`codex/`](codex/): Codex entrypoints and consumption guidance
- [`claude/`](claude/): Claude entrypoints and consumption guidance

Operational capabilities now include:

- session lifecycle for natural-language resume and close-out behavior
- workspace adoption for one-time installation into an existing multi-repository workspace

This repository is used to synchronize the shared development setup across the MacBook, Mac Mini, and future machines.

GitHub is the source of truth: [linktrend/IDE-Development](https://github.com/linktrend/IDE-Development).

## New operators

Start here: [docs/LINKDEVELOPER-OPERATIONS-MANUAL.md](docs/LINKDEVELOPER-OPERATIONS-MANUAL.md)

Machine setup and update guidance: [SETUP.md](SETUP.md)
