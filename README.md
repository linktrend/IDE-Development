# IDE Development

IDE Development **v3.0.0** is LiNKtrend’s shared development operating **System** (a System now, Program-ready). It installs one shared way of building software into every repo: a managed core at `.ide-development/` plus Cursor and Codex discovery adapters.

v3 runs that system with one AI orchestrator per repo. The orchestrator is a Cursor Project on the cursor-001 account, running a frontier model. It plans Phases and Issues, dispatches Issues to workers, packages branches into pull requests into `development`, merges when CI is green and one independent review has passed, and promotes `development` to `main`. Cheap helper subagents do its routine jobs.

Workers are Codex CLI on the orchestrator VM (Luna High for everyday work, Sol Medium for hard work, used while more than 25% of the allowance remains in every reported window) and the cursor-002 Cursor account via API (Grok 4.7 Medium everyday, Opus 5.5 Medium hard). Workers use `issue/<PREFIX>-<n>-<slug>` branches, commit and push often, and never open pull requests.

Checks are fast checks on each branch, one Full CI run per pull request, and one exact-head review by a different model family (Bugbot is optional). The repair ladder is Luna/Grok three times, then Sol/Opus once, then — if the work started on Sol/Opus — the other hard route once, then flag Carlos.

The ledger is the Supabase schema `ide_ledger` in the LiNKplatform project. Only the orchestrator writes it, through RPC. Until that ledger is live, the pilot run log stays in the Project store. Work IDs look like `IDE-<n>`. One GitHub Issue per Phase is the readable summary.

Long-lived branches are `development` and `main` only. Deploys after `main` are automatic GitHub Actions jobs. The deploy standard is owned by the LiNKops repo, and each deploy includes a health check and a rollback.

Carlos (the Principal) gives intent and answers questions. He does not approve merges or releases.

IDE Development is distinct from **LiNKdeveloper**, the separate autonomous application-factory Program. LiNKdeveloper may be authored using this system, and it does not depend on this repo at runtime.

**This repository** (`linktrend/IDE-Development`) is the **system source** and internal self-verification target. It is not a consumer rollout entry and must not receive a nested installed copy of itself. In other repos the same system is installed under `.ide-development/`.

**Claude Code is excluded** from current support. Do not add Claude entrypoints or treat archived Claude packaging (`docs/archive/platform-entrypoints/claude/`) as an install path.

How a repo’s Cursor Project is set up: [`docs/runbooks/project-setup-checklist.md`](docs/runbooks/project-setup-checklist.md). What is true right now: [`docs/CURRENT-STATUS.md`](docs/CURRENT-STATUS.md).

## Start here

- **[`docs/CURRENT-STATUS.md`](docs/CURRENT-STATUS.md)** — concise current status.
- **[`docs/IDE-DEVELOPMENT-OPERATIONS-MANUAL.md`](docs/IDE-DEVELOPMENT-OPERATIONS-MANUAL.md)** — plain-English handbook for the Principal.
- **[`docs/runbooks/project-setup-checklist.md`](docs/runbooks/project-setup-checklist.md)** — how a repo’s Project is set up.
- **[`docs/IDE-DEVELOPMENT-INTENT.md`](docs/IDE-DEVELOPMENT-INTENT.md)** — why IDE Development exists, who it is for, and what “done” means.
- **[`docs/IDE-DEVELOPMENT-TECHNICAL-PRD.md`](docs/IDE-DEVELOPMENT-TECHNICAL-PRD.md)** — technical reference for architecture, doctrine, skills, and checks.
- **[`SETUP.md`](SETUP.md)** — clone, install, and update.
- **[`docs/runbooks/release-candidate.md`](docs/runbooks/release-candidate.md)** · **[`docs/runbooks/rollback.md`](docs/runbooks/rollback.md)** · **[`docs/acceptance/acceptance-matrix.md`](docs/acceptance/acceptance-matrix.md)**.

Older notes under `docs/archive/` are historical. When they disagree with this README, current status, or the operations manual, those current pages win.

## What it installs

| Surface | What a consumer receives |
|---|---|
| Managed core | Committed physical `.ide-development/` tree |
| Cursor discovery | Physical `.cursor/rules`, `.cursor/commands`, `.cursor/skills` |
| Codex discovery | Root `AGENTS.md` managed block + physical `.agents/skills/<name>/SKILL.md` |

**Precedence:** Shared managed lifecycle rules win when explicitly identified in the package. Legitimate repository-specific technical guidance outside managed ownership/markers is preserved. Unknown conflicts and modified obsolete generics fail closed. External `.cursor` symlinks are migrated to physical files without reading or writing the external target.

## One-command install / update

### From this system source checkout

```bash
python3 scripts/ide-development.py plan --repo /path/to/consumer     # dry-run (no writes)
python3 scripts/ide-development.py install --repo /path/to/consumer
python3 scripts/ide-development.py update --repo /path/to/consumer
```

### From an extracted release candidate

```bash
# Build portable archives (default: build/release-candidate/)
python3 scripts/ide-development.py release-candidate create

# Prove extract+install into a clean temp repo
python3 scripts/ide-development.py release-candidate verify --archive /path/to/archive.tar.gz
```

Or extract manually and install with `--package` pointed at the extracted package root (no dependency on this checkout):

```bash
python3 /path/to/extracted-rc/.../ide-development.py install \
  --package /path/to/extracted-rc \
  --repo /path/to/disposable-consumer
```

See [`docs/runbooks/release-candidate.md`](docs/runbooks/release-candidate.md).

### Drift, verify, version, rollback

```bash
python3 scripts/ide-development.py drift --repo /path/to/consumer
python3 scripts/ide-development.py verify --repo /path/to/consumer
python3 scripts/ide-development.py version --repo /path/to/consumer
python3 scripts/ide-development.py rollback --repo /path/to/consumer
```

`--repo` / `--target` are aliases. `--package` selects the package root. `--json` for machine-readable output. `--dry-run` guarantees no repository or Git-metadata writes.

Every mutating operation plans first, is transactional, and records rollback information under `.git/ide-development/`.

## External GitHub state

GitHub App credentials, secrets, variables, Bugbot dashboard settings, and live branch protections stay outside the package. See [`docs/contracts/EXTERNAL-STATE-AUDIT.md`](docs/contracts/EXTERNAL-STATE-AUDIT.md) and [`docs/contracts/REPOSITORY-PROTECTION.md`](docs/contracts/REPOSITORY-PROTECTION.md).

Protection of `development` and `main` remains required for every installed repository.

## Supported platforms

| Platform | Status |
|---|---|
| **Cursor** | Supported — physical `.cursor` discovery adapters |
| **Codex** | Supported — `AGENTS.md` + `.agents/skills` |
| **Claude Code** | **Excluded** — not in current support |

## Layout

- `core/` — canonical portable knowledge asset (doctrine, skills, commands, templates, library client).
- `core/managed-core/` — package source for the managed core (manifest, schemas, platform adapters).
- `.cursor/` — Cursor compatibility runtime in **this** system repo (adapters into `core/`, plus Cursor-only `rules/` and `mcp.json`).
- `scripts/ide-development.py` / `scripts/ide_development/` — portable installer engine.
- `codex/` — Codex-oriented system entrypoints (consumers also get native root/`.agents` adapters on install).
- `chatgpt/` — ChatGPT / work-agent entrypoint.
- `docs/CURRENT-STATUS.md` · `docs/runbooks/` · `docs/acceptance/` — operator status and handoff.
- `docs/archive/` — superseded descriptive docs; see `docs/archive/README.md`.

## Status

**Version `v3.0.0`.** Wave 0 of the v3 pilot is done. Wave 1 content is complete and waits for merge to `development` and promotion to `main`. See [`docs/CURRENT-STATUS.md`](docs/CURRENT-STATUS.md).

Automated system verification: `scripts/verify-ide-development.sh`.
