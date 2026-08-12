# IDE Development

IDE Development is LiNKtrend’s shared, human-assisted Application Factory operating system — version **v2.1.9**. It installs a portable managed core into product repositories as committed physical files (`.ide-development/` plus Cursor/Codex discovery adapters) so agents follow one doctrine, one six-Module pipeline, one hybrid skill surface, and fail-closed gates — with the Principal approving Intent and release, not day-to-day coding.

It is distinct from **LiNKdeveloper**, the separate VPS-hosted autonomous application-factory Program. LiNKdeveloper may be *authored* using this system’s guidance, but it does not depend on this repo at runtime.

**This repository** is the **system source** and internal self-verification target. It is **not** a consumer rollout entry and must not receive a nested installed copy of itself.

**Claude Code is excluded** from current v2 support and roadmap. Do not add Claude entrypoints or treat archived Claude packaging (`docs/archive/platform-entrypoints/claude/`) as an install path.

**Pre-rollout:** WP1 proved the RC on disposable targets; WP2 built canonical lineage + live readiness; WP03 integrated and promoted the v2.0 line; Issue #72 completed the pre-launch cleanup; and Issue #81 delivered the v2.1 phase-delivery release through PR #82 / #85 / #86. **Consumer rollout (WP04) is prepared and not executed** — Principal approval is still required. See [`docs/CURRENT-STATUS.md`](docs/CURRENT-STATUS.md) and [`docs/GITOPS-CONSUMER-ROLLOUT.md`](docs/GITOPS-CONSUMER-ROLLOUT.md).

## Start here (source of truth)

These documents are the current, authoritative description of this repository. If anything elsewhere (including older docs under `docs/archive/`) disagrees with them, **these win**:

- **[`docs/CURRENT-STATUS.md`](docs/CURRENT-STATUS.md)** — concise current status / launch readiness (start here for “what is true now”).
- **[`docs/IDE-DEVELOPMENT-INTENT.md`](docs/IDE-DEVELOPMENT-INTENT.md)** — why IDE Development exists, who it’s for, scope, and what “done” means.
- **[`docs/IDE-DEVELOPMENT-TECHNICAL-PRD.md`](docs/IDE-DEVELOPMENT-TECHNICAL-PRD.md)** — exhaustive technical reference: architecture, six-Module pipeline, doctrine, hybrid skills, model routing, hooks/CI, LiNKlibraries, and what is not built yet.
- **[`docs/IDE-DEVELOPMENT-OPERATIONS-MANUAL.md`](docs/IDE-DEVELOPMENT-OPERATIONS-MANUAL.md)** — plain-English handbook for the Principal.
- **[`docs/OPEN-ISSUES.md`](docs/OPEN-ISSUES.md)** — append-only engineering notes and open/deferred items.
- **[`docs/BUILD-LOG.md`](docs/BUILD-LOG.md)** — active Work Packet build log (starts with WP1).
- **[`docs/adr/0004-portable-managed-core-v2.md`](docs/adr/0004-portable-managed-core-v2.md)** — portable managed-core v2 decision.
- **[`docs/GITOPS-CONSUMER-ROLLOUT.md`](docs/GITOPS-CONSUMER-ROLLOUT.md)** — consumer inventory, drift posture, Principal gate; rollout = WP04 (approval pending).
- **[`docs/work-packets/2026-08-02-work-packet-04-consumer-rollout.md`](docs/work-packets/2026-08-02-work-packet-04-consumer-rollout.md)** — WP04 packet (prepared / not executed).

Live operational companions: [`SETUP.md`](SETUP.md) (clone / install / update), [`docs/runbooks/release-candidate.md`](docs/runbooks/release-candidate.md), [`docs/runbooks/rollback.md`](docs/runbooks/rollback.md), [`docs/acceptance/acceptance-matrix.md`](docs/acceptance/acceptance-matrix.md), [`docs/HYBRID-SKILLS-REGISTRY.md`](docs/HYBRID-SKILLS-REGISTRY.md), [`docs/ARCHIVE-INDEX.md`](docs/ARCHIVE-INDEX.md), [`docs/AUTONOMOUS-GIT-OPERATIONS.md`](docs/AUTONOMOUS-GIT-OPERATIONS.md), [`docs/contracts/REPOSITORY-PROTECTION.md`](docs/contracts/REPOSITORY-PROTECTION.md), [`docs/contracts/MANAGED-CORE-V2.md`](docs/contracts/MANAGED-CORE-V2.md), [`docs/contracts/EXTERNAL-STATE-AUDIT.md`](docs/contracts/EXTERNAL-STATE-AUDIT.md).

## What it installs

| Surface | What a consumer receives |
|---|---|
| Managed core | Committed physical `.ide-development/` tree |
| Cursor discovery | Physical `.cursor/rules`, `.cursor/commands`, `.cursor/skills` |
| Codex discovery | Root `AGENTS.md` managed block + physical `.agents/skills/<name>/SKILL.md` |

**Precedence:** Shared managed lifecycle rules win when explicitly identified in the package. Legitimate repository-specific technical guidance outside managed ownership/markers is **preserved**. Unknown conflicts and modified obsolete generics **fail closed**. External `.cursor` symlinks are migrated to physical files without reading/writing the external target.

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

Or extract manually and install with `--package` pointed at the extracted package root (**no** dependency on this checkout):

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

GitHub App credentials, secrets, variables, Bugbot dashboard settings, and live branch protections stay **outside** the package. WP1 proved **read-only plan/verify**; WP2 closed IDE Development live readiness under its packet. **Consumer** settings apply and installs remain Principal-gated (WP04). See [`docs/contracts/EXTERNAL-STATE-AUDIT.md`](docs/contracts/EXTERNAL-STATE-AUDIT.md) and [`docs/contracts/REPOSITORY-PROTECTION.md`](docs/contracts/REPOSITORY-PROTECTION.md).

Protection of `development`, `staging`, and `main` remains required managed-system behavior for every installed repository once apply is separately approved.

## Supported platforms

| Platform | Status |
|---|---|
| **Cursor** | Supported — physical `.cursor` discovery adapters |
| **Codex** | Supported — `AGENTS.md` + `.agents/skills` |
| **Claude Code** | **Excluded** — not in current v2 support or roadmap |

### Host OS evidence (WP1)

WP1 production-readiness proof required **macOS, Ubuntu Linux, and Windows** matrix evidence on the exact checkpoint SHA, with Python and OS versions recorded. Skipped or unavailable runners are blockers, not silent passes. See [`docs/acceptance/acceptance-matrix.md`](docs/acceptance/acceptance-matrix.md).

## Layout

- `core/` — canonical portable knowledge asset (doctrine, skills, commands, templates, library client, …).
- `core/managed-core/` — package source for the v2 managed core (manifest, schemas, platform adapters).
- `.cursor/` — Cursor compatibility runtime in **this** system repo (adapters into `core/`, plus Cursor-only `rules/` and `mcp.json`).
- `scripts/ide-development.py` / `scripts/ide_development/` — portable installer engine.
- `codex/` — Codex-oriented system entrypoints (consumers also get native root/`.agents` adapters on install).
- `docs/CURRENT-STATUS.md` · `docs/runbooks/` · `docs/acceptance/` · `docs/BUILD-LOG.md` — operator status and handoff.
- `docs/archive/` — superseded descriptive docs; see `docs/archive/README.md`.

## Status

**Version `v2.1.9`.** Identified in `VERSION`. This patch release resolves real filesystem paths before managed Library containment checks, closing both intermediate-symlink and Windows cross-drive escapes. Version identity still does **not** by itself create a Git tag or GitHub Release. See [`docs/CURRENT-STATUS.md`](docs/CURRENT-STATUS.md).

Automated Stage 1 / system verification: `scripts/verify-ide-development.sh`. Portable v2 integration harness: `tests/test-portable-v2-integration.sh`.

**Deliberately not claimed here:** persistent autonomous orchestration, Principal phone dashboard, automatic product deploy past Module 6 Release OK, Claude Code support, or **executed** consumer rollout (WP04 approval pending). See Technical PRD §9, Operations Manual “Current status,” and the WP04 packet.
