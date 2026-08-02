# Runbook — release candidate (Work Packet 1)

**Audience:** Operators packaging and verifying IDE Development portable managed-core **v2** for production readiness proof.
**Scope:** System repository only. No consumer install, no GitHub tag/release, no live settings apply.
**Related:** [`rollback.md`](./rollback.md) · [`../acceptance/acceptance-matrix.md`](../acceptance/acceptance-matrix.md) · [`../GITOPS-CONSUMER-ROLLOUT.md`](../GITOPS-CONSUMER-ROLLOUT.md) · Issue #67 / Work Packet 1

---

## Plain English

A **release candidate (RC)** is a reproducible archive of the managed package built from a clean worktree of this system repository. Operators use it to prove install/update/verify/rollback on disposable targets **without** needing the live IDE Development checkout next to the consumer.

Work Packet 1 **prepares and proves** the RC. Work Packet 2 handles integration into `development`, publication decisions, and (only after separate Principal approval) consumer rollout.

---

## What IDE Development installs (reminder)

Into an approved or disposable **consumer** Git repository (never nested into IDE Development itself during Wave 1 / WP1):

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
4. Package identity consistent: root `VERSION`, `core/managed-core/VERSION`, and `MANIFEST.json` `packageVersion` (target **2.0.0** / `v2.0.0`).
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

Outputs stay under an ignored build/artifact directory — **never** a GitHub tag or Release.

---

## One-command install / update paths

### A. From system source checkout

```bash
# Disposable or Principal-approved consumer only — never IDE Development itself in WP1
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

## Explicit non-goals (WP1)

| Action | Status in WP1 |
|---|---|
| Git tag / GitHub Release | **Forbidden** |
| Merge into `development` / promote | **Work Packet 2** |
| Real consumer install/update | **Deferred** — separately Principal-gated; see consumer rollout doc |
| Live GitHub App / secrets / Bugbot / ruleset apply | **Forbidden** (plan/verify read-only only) |
| Claude packaging or docs claiming Claude support | **Forbidden** |

---

## Work Packet 2 boundary

Work Packet 2 is the **integration and publication** stage: reconcile frozen PR #49 and intentional checkpoints, governed merge/promotion, and final publication/rollout decisions under **separate** Carlos approval. WP1 stops at a proven RC + evidence on the issue branch.
