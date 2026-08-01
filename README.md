# IDE Development

IDE Development is LiNKtrend’s shared, human-assisted Application Factory operating system — version **v2.0.0**. It installs a portable managed core into product repositories as committed physical files (`.ide-development/` plus Cursor/Codex discovery adapters) so agents follow one doctrine, one six-Module pipeline, one hybrid skill surface, and fail-closed gates — with the Principal approving Intent and release, not day-to-day coding.

It is distinct from **LiNKdeveloper**, the separate VPS-hosted autonomous application-factory Program. LiNKdeveloper may be *authored* using this system’s guidance, but it does not depend on this repo at runtime.

**This repository** is the system source and internal self-verification target. It is **not** a consumer rollout entry and does not receive a nested installed copy of itself during Wave 1.

## Start here (source of truth)

These documents are the current, authoritative description of this repository. If anything elsewhere (including older docs under `docs/archive/`) disagrees with them, **these win**:

- **[`docs/IDE-DEVELOPMENT-INTENT.md`](docs/IDE-DEVELOPMENT-INTENT.md)** — why IDE Development exists, who it’s for, scope, and what “done” means.
- **[`docs/IDE-DEVELOPMENT-TECHNICAL-PRD.md`](docs/IDE-DEVELOPMENT-TECHNICAL-PRD.md)** — exhaustive technical reference: architecture, six-Module pipeline, doctrine, hybrid skills, model routing, hooks/CI, LiNKlibraries, and what is not built yet.
- **[`docs/IDE-DEVELOPMENT-OPERATIONS-MANUAL.md`](docs/IDE-DEVELOPMENT-OPERATIONS-MANUAL.md)** — plain-English handbook for the Principal.
- **[`docs/OPEN-ISSUES.md`](docs/OPEN-ISSUES.md)** — append-only engineering build log and open/deferred items.
- **[`docs/adr/0004-portable-managed-core-v2.md`](docs/adr/0004-portable-managed-core-v2.md)** — portable managed-core v2 decision.
- **[`docs/GITOPS-CONSUMER-ROLLOUT.md`](docs/GITOPS-CONSUMER-ROLLOUT.md)** — consumer rollout inventory, drift posture, and Principal approval gate.

Live operational companions (not archived): [`docs/HYBRID-SKILLS-REGISTRY.md`](docs/HYBRID-SKILLS-REGISTRY.md) (hybrid command map), [`docs/ARCHIVE-INDEX.md`](docs/ARCHIVE-INDEX.md) (retired systems), [`SETUP.md`](SETUP.md) (clone / install / update), [`docs/AUTONOMOUS-GIT-OPERATIONS.md`](docs/AUTONOMOUS-GIT-OPERATIONS.md) (ship/pull/promote), [`docs/contracts/REPOSITORY-PROTECTION.md`](docs/contracts/REPOSITORY-PROTECTION.md) (branch protection contract).

## Portable install model (v2)

Consumers receive a **physical** managed installation — not a symlink back to this checkout:

| Surface | What gets installed |
|---|---|
| Managed core | Committed `.ide-development/` tree inside the consumer |
| Cursor discovery | Physical `.cursor/rules`, `.cursor/commands`, `.cursor/skills` |
| Codex discovery | Root `AGENTS.md` managed block + physical `.agents/skills/<name>/SKILL.md` |

Operator commands (from this system repository, targeting a disposable or approved consumer path):

```bash
python3 scripts/ide-development.py plan --repo /path/to/consumer     # dry-run plan (no writes)
python3 scripts/ide-development.py install --repo /path/to/consumer
python3 scripts/ide-development.py update --repo /path/to/consumer
python3 scripts/ide-development.py drift --repo /path/to/consumer     # read-only drift report
python3 scripts/ide-development.py verify --repo /path/to/consumer
python3 scripts/ide-development.py version --repo /path/to/consumer
python3 scripts/ide-development.py rollback --repo /path/to/consumer
```

Every mutating operation plans first, is transactional, and records rollback information. Managed-file drift is hash-detected; unknown conflicts fail closed. GitHub App credentials, secrets, variables, Bugbot dashboard settings, and live repository protections stay **external** (plan/apply/verify with dry-run default — see repository-protection contract).

Protection of `development`, `staging`, and `main` is required managed-system behavior for every installed repository.

## Supported platforms (current v2)

| Platform | Status |
|---|---|
| **Cursor** | Supported — physical `.cursor` discovery adapters |
| **Codex** | Supported — `AGENTS.md` + `.agents/skills` |
| **Claude Code** | **Not** in current v2 support or roadmap. Historical `claude/` files may remain on disk; do not treat them as a supported runtime. |

## Layout

- `core/` — canonical portable knowledge asset (doctrine, skills, commands, templates, library client, …).
- `core/managed-core/` — package source for the v2 managed core (manifest, schemas, platform adapters).
- `.cursor/` — Cursor compatibility runtime in **this** system repo (adapters into `core/`, plus Cursor-only `rules/` and `mcp.json`).
- `scripts/ide-development.py` / `scripts/ide_development/` — portable installer engine.
- `codex/` — Codex-oriented system entrypoints (consumers also get native root/` .agents` adapters on install).
- `docs/archive/` — superseded descriptive docs; see `docs/archive/README.md`.

## Status

**Version `v2.0.0` (Wave 1).** Identified in `VERSION`; this wave does **not** create a Git tag or GitHub release.

Automated Stage 1 / system verification: `scripts/verify-ide-development.sh`. Portable v2 integration harness: `tests/test-portable-v2-integration.sh`.

**Deliberately not claimed here:** persistent autonomous orchestration, Principal phone dashboard, automatic product deploy past Module 6 Release OK, or Claude Code as a supported platform. See Technical PRD §9 and Operations Manual “Current status.”
