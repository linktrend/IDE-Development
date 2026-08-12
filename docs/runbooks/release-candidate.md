# Runbook — release candidate (Work Packet 1)

**Audience:** Operators packaging and verifying IDE Development portable managed-core **v2** for production readiness proof.
**Scope:** System repository only. No consumer install, no GitHub tag/release, no live consumer settings apply.
**Related:** [`rollback.md`](./rollback.md) · [`../acceptance/acceptance-matrix.md`](../acceptance/acceptance-matrix.md) · [`../GITOPS-CONSUMER-ROLLOUT.md`](../GITOPS-CONSUMER-ROLLOUT.md) · [`../CURRENT-STATUS.md`](../CURRENT-STATUS.md) · Issue #67 / Work Packet 1
**Status boundary (2026-08-03):** WP1 RC proof, WP2 lineage/live readiness, WP03 integration/promotion, Issue #72 cleanup, and Issue #81 v2.1 phase delivery are **complete**. WP04 consumer rollout is **prepared / not executed**. This runbook remains the RC operator procedure; it does not authorize consumer mutation.

---

## Plain English

A **release candidate (RC)** is a reproducible archive of the managed package built from a clean worktree of this system repository. Operators use it to prove install/update/verify/rollback on disposable targets **without** needing the live IDE Development checkout next to the consumer.

Work Packet 1 **prepared and proved** the RC. Work Packet 2 built canonical lineage + live readiness. Work Packet 03 integrated/promoted the system line. **Work Packet 04** (consumer rollout) remains Principal-gated and is **not** authorized by this runbook.

---

## What IDE Development installs (reminder)

Into an approved or disposable **consumer** Git repository (never nested into IDE Development itself):

| Surface | Result |
|---|---|
| Managed core | Committed physical `.ide-development/` |
| Cursor discovery | Physical `.cursor/rules`, `.cursor/commands`, `.cursor/skills` |
| Codex discovery | Root `AGENTS.md` managed marker block + physical `.agents/skills/<name>/SKILL.md` |

Claude Code is **excluded** — not a supported platform and not packaged as an install target.

---

## Prerequisites

1. Clean git worktree on the Work Packet 1 issue branch (or the exact checkpoint SHA under test).
2. Python 3 available (`python3`).
3. Installer entrypoint present: `scripts/ide-development.py`.
4. Package identity consistent: root `VERSION`, `core/managed-core/VERSION`, and `MANIFEST.json` `packageVersion` (target **2.1.6** / `v2.1.6`).
5. Required acceptance evidence for this SHA exists or will be attached (see acceptance matrix). Do **not** claim production readiness when a required platform gate is skipped, neutral, or untested.

---

## Command inventory (accurate as of WP1 docs)

### Installer / lifecycle

From the IDE Development repository root:

```bash
python3 scripts/ide-development.py plan --repo /path/to/target
python3 scripts/ide-development.py install --repo /path/to/target
python3 scripts/ide-development.py update --repo /path/to/target
python3 scripts/ide-development.py drift --repo /path/to/target
python3 scripts/ide-development.py verify --repo /path/to/target
python3 scripts/ide-development.py version --repo /path/to/target
python3 scripts/ide-development.py rollback --repo /path/to/target
python3 scripts/ide-development.py release-candidate create
python3 scripts/ide-development.py release-candidate verify --archive /path/to/archive.tar.gz
```

Notes:

- `--repo` and `--target` are aliases. `--package` points at the package/system root (defaults to detecting this checkout).
- `--dry-run` / `plan` guarantee no repository or Git-metadata writes.
- `--json` emits machine-readable output.

### `release-candidate` (Lane D — present on this branch)

```bash
# Build RC archives (default output: build/release-candidate/)
python3 scripts/ide-development.py release-candidate create
python3 scripts/ide-development.py release-candidate create --json

# Extract an archive and install into a clean temp repo (proof)
python3 scripts/ide-development.py release-candidate verify --archive /path/to/archive.tar.gz
```

`create` options (operator-facing):

| Flag | Meaning |
|---|---|
| `--output-dir DIR` | Output directory (default `build/release-candidate`) |
| `--allow-dirty` | Allow dirty worktree for **local proofs only** — production RC must be clean |
| `--skip-install-verify` | Skip extract+install verification |
| `--skip-evidence` | Skip lane evidence path checks (packaging unit tests still required) |

Hard refusals (fail closed) for production-grade create:

- dirty worktree (unless `--allow-dirty` for local proofs)
- manifest hash drift / inconsistent `VERSION`
- missing required tests or evidence for the claimed SHA (unless explicitly skipped for local proofs)
- packaging credentials, host absolute paths, external symlinks, or Git metadata into the archive

Outputs stay under an ignored build/artifact directory — **never** a GitHub tag or Release from this runbook alone.

---

## Immutable publication (WP-01B — normal-token Mac Mini publisher)

Tag and GitHub Release creation for managed-core **v2.1.6** is owned by the system-repository workflow `.github/workflows/linktrend-managed-core-release-publisher.yml` (not consumer-synced).

Hard rules:

- Workflow YAML and publish helpers execute from the protected **default branch (`main`)** only.
- Requested `source_sha` must equal the remote `main` tip; the SHA is checked out as **data only**.
- Archives are **rebuilt and verified** from that source before any tag/Release mutation.
- Privileged identity is the repository's configured **normal automation token** on the Mac Mini — no workflow `GITHUB_TOKEN` fallback.
- Tag/release/checksum conflicts and publication replays **fail closed**.
- Operators may use `dry_run=true` or `action=verify-only` to rebuild/verify without creating a tag or Release.

Helpers:

- `scripts/gitops/managed_core_release_dispatch.py` — input validation
- `scripts/gitops/managed_core_release_publish.py` — rebuild/verify/bind/publish
- Evidence schema: `core/managed-core/schemas/managed-core-release.schema.json`
- Contract tests: `scripts/tests/test-managed-core-release-publisher.sh`

This implementer path does **not** trigger live publication. Live tag/Release follows the governed PR + promotion sequence, then an authorized normal-token Mac Mini publication.

---

## One-command install / update paths

### A. From system source checkout

```bash
# Disposable or Principal-approved consumer only — never IDE Development itself
python3 scripts/ide-development.py install --repo /path/to/consumer
python3 scripts/ide-development.py update --repo /path/to/consumer
```

### B. From extracted release candidate

After Lane D produces a verified archive:

1. Extract the RC into a temporary directory that is **not** the live IDE Development checkout.
2. Point `--package` at that extracted package root (the directory that contains the managed-core package layout / installer entry the RC documents).
3. Install into a disposable consumer with **no** access to the system checkout:

```bash
python3 /path/to/extracted-rc/.../ide-development.py install \
  --package /path/to/extracted-rc \
  --repo /path/to/disposable-consumer
```

Exact archive layout and entrypoint path are defined by Lane D packaging output; this runbook requires that extraction + install work without the source checkout on `PATH` or disk.

---

## Operator sequence (RC proof)

1. Confirm clean tree and record `git rev-parse HEAD`.
2. Run required local suites listed in the acceptance matrix (or note exact external blockers).
3. `python3 scripts/ide-development.py release-candidate create` — record archive checksums under `build/release-candidate/` (or `--output-dir`).
4. `python3 scripts/ide-development.py release-candidate verify --archive <archive>` and/or manual extract + `install --package …` into a disposable Git repo; run installer `verify`, `drift`, `version`.
5. Exercise `rollback` after a deliberate mutating install/update (see rollback runbook).
6. Confirm no tag, GitHub Release, consumer mutation, or live GitHub settings apply occurred.
7. Append evidence pointers to [`../BUILD-LOG.md`](../BUILD-LOG.md).

---

## Explicit non-goals (WP1 historical; still binding for this runbook)

| Action | Status |
|---|---|
| Git tag / GitHub Release from this RC procedure | **Forbidden** unless separately approved |
| Merge into `development` / promote | **WP03 complete** — not part of RC create/verify |
| Real consumer install/update | **WP04** — deferred until Principal approval; see consumer rollout doc |
| Live GitHub App / secrets / Bugbot / ruleset apply on consumers | **Forbidden** without separate approval |
| Claude packaging or docs claiming Claude support | **Forbidden** |

---

## Work Packet boundaries (pre-rollout)

- **WP1:** RC proof on disposable targets (this runbook).
- **WP2:** Lineage + IDE Development live readiness (checkpoint).
- **WP03:** Integrated/promoted the v2.0 line.
- **Issue #81:** v2.1 phase delivery promoted through PR #82/#85/#86.
- **WP04:** Consumer rollout — prepared / **not executed**; Principal approval required (`docs/work-packets/2026-08-02-work-packet-04-consumer-rollout.md`).
