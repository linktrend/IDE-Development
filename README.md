# IDE Development

IDE Development is LiNKtrend’s shared, human-assisted Application Factory operating system. It installs into product repositories (via `.cursor` symlink) so Cursor/Codex agents follow one doctrine, one six-Module pipeline, one hybrid skill surface, and fail-closed gates — with the Principal approving Intent and release, not day-to-day coding.

It is distinct from **LiNKdeveloper**, the separate VPS-hosted autonomous application-factory Program (`/Users/linktrend/Projects/LiNKdeveloper`). LiNKdeveloper may be *authored* using this repo’s `.cursor` surface, but it does not depend on this repo at runtime.

## Start here (source of truth)

These documents are the current, authoritative description of this repository. If anything elsewhere (including older docs under `docs/archive/`) disagrees with them, **these win**:

- **[`docs/IDE-DEVELOPMENT-INTENT.md`](docs/IDE-DEVELOPMENT-INTENT.md)** — why IDE Development exists, who it’s for, scope, and what “done” means.
- **[`docs/IDE-DEVELOPMENT-TECHNICAL-PRD.md`](docs/IDE-DEVELOPMENT-TECHNICAL-PRD.md)** — exhaustive technical reference: architecture, six-Module pipeline, doctrine, hybrid skills, model routing, hooks/CI, LiNKlibraries, and what is not built yet.
- **[`docs/IDE-DEVELOPMENT-OPERATIONS-MANUAL.md`](docs/IDE-DEVELOPMENT-OPERATIONS-MANUAL.md)** — plain-English handbook for the Principal.
- **[`docs/OPEN-ISSUES.md`](docs/OPEN-ISSUES.md)** — append-only engineering build log and open/deferred items.

Live operational companions (not archived): [`docs/HYBRID-SKILLS-REGISTRY.md`](docs/HYBRID-SKILLS-REGISTRY.md) (hybrid command map), [`docs/ARCHIVE-INDEX.md`](docs/ARCHIVE-INDEX.md) (retired systems), [`SETUP.md`](SETUP.md) (clone / multi-machine setup).

## Layout

- `core/` — canonical portable knowledge asset (doctrine, skills, commands, templates, library client, workspace adoption, …).
- `.cursor/` — Cursor compatibility runtime (mostly symlinks into `core/`, plus Cursor-only `rules/` and `mcp.json`).
- `core/execution/` — operative Laws, runtime model, and application pipeline contract (**not** archived).
- `core/runtime/skills/gstack/`, `mattpocock/`, `linktrend/` — vendored hybrid skills + Module composites (`VENDOR-MANIFEST.json` + `scripts/verify-vendored-skills.sh`).
- `scripts/` — wire, vendor, verify, install-hooks, feasibility, gate-stop tests.
- `codex/`, `claude/` — non-Cursor consumption entrypoints.
- `docs/archive/` — superseded descriptive docs; see `docs/archive/README.md`.

## Status

**Ready for daily wired use (as of 2026-07-19).** Version `v1.2`. Automated Stage 1 verification: `scripts/verify-ide-development.sh`. Hybrid skills are physically vendored and wired — not stubs.

**Deliberately not claimed here:** persistent autonomous orchestration, Principal phone dashboard, or automatic product deploy past Module 6 Release OK. See Technical PRD §9 and Operations Manual “Current status.”
