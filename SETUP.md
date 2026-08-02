# Setup Guide

## Purpose

This repository is **IDE Development** — the shared AI development core (version **v2.0.0**) used across **Cursor** and **Codex**.

The canonical knowledge asset lives in `core/`. The portable package source for consumers lives in `core/managed-core/`. GitHub is the source of truth.

**Claude Code is outside current v2 support and roadmap.** Historical Claude packaging files may exist under `claude/`; do not treat them as an active install path.

**New operators:** after cloning, start with the source-of-truth set:

- [docs/IDE-DEVELOPMENT-INTENT.md](docs/IDE-DEVELOPMENT-INTENT.md)
- [docs/IDE-DEVELOPMENT-TECHNICAL-PRD.md](docs/IDE-DEVELOPMENT-TECHNICAL-PRD.md)
- [docs/IDE-DEVELOPMENT-OPERATIONS-MANUAL.md](docs/IDE-DEVELOPMENT-OPERATIONS-MANUAL.md) — day-to-day instructions
- [docs/OPEN-ISSUES.md](docs/OPEN-ISSUES.md) — build log
- [docs/GITOPS-CONSUMER-ROLLOUT.md](docs/GITOPS-CONSUMER-ROLLOUT.md) — consumer rollout order and approval gates

Retired systems and historical evidence: [docs/ARCHIVE-INDEX.md](docs/ARCHIVE-INDEX.md) and [docs/archive/](docs/archive/README.md).

## Clone On Another Machine

Recommended target location:

```bash
mkdir -p ~/Projects
cd ~/Projects
git clone https://github.com/linktrend/IDE-Development.git "IDE Development"
cd "IDE Development"
```

After cloning, use this repository as the **system source** of the shared development core on that machine. It is for authoring, packaging, and self-verification — not a consumer rollout target.

## Mac Mini Setup

On the Mac Mini, clone into:

```bash
~/Projects/IDE Development
```

Commands:

```bash
mkdir -p ~/Projects
cd ~/Projects
git clone https://github.com/linktrend/IDE-Development.git "IDE Development"
cd "IDE Development"
git status
cat VERSION   # expect v2.0.0
```

## Pull Updates

Before using or editing the system on any machine:

```bash
git pull
git status
```

## Portable consumer install (v2)

Consumers install a **physical** managed core inside their own Git repository. There is no consumer-to-system `.cursor` symlink and no absolute external path dependency.

From this system repository:

```bash
# Plan only (no repository or Git-metadata writes)
python3 scripts/ide-development.py plan --repo /path/to/consumer

# Install or update (transactional; produces rollback info)
python3 scripts/ide-development.py install --repo /path/to/consumer
python3 scripts/ide-development.py update --repo /path/to/consumer

# Read-only checks
python3 scripts/ide-development.py drift --repo /path/to/consumer
python3 scripts/ide-development.py verify --repo /path/to/consumer
python3 scripts/ide-development.py version --repo /path/to/consumer

# Restore exact pre-change bytes from the last transaction
python3 scripts/ide-development.py rollback --repo /path/to/consumer
```

What a successful install leaves in the consumer:

- committed `.ide-development/` managed core
- physical Cursor discovery files under `.cursor/rules`, `.cursor/commands`, `.cursor/skills`
- Codex discovery via root `AGENTS.md` managed markers and physical `.agents/skills/`
- consumer-owned content outside managed ownership/markers preserved
- installed-state / transaction metadata under Git-local `.git/ide-development/` (not packaged secrets)

### Plain-English command meanings

| Command | Meaning |
|---|---|
| `plan` / dry-run | Show what would change; write nothing |
| `install` | First-time physical managed install |
| `update` | Bring an installed consumer up to the package version |
| `drift` | Read-only report of managed-file hash drift / conflicts |
| `verify` | Confirm install integrity against recorded state |
| `version` | Print package / installer version identity |
| `rollback` | Restore exact pre-change files and modes from the last transaction |

### Consumer rollout hard rules

1. Produce a **read-only drift report** for the target consumer first.
2. Obtain **separate Carlos (Principal) approval** before each consumer install/update.
3. Follow the locked order in [`docs/GITOPS-CONSUMER-ROLLOUT.md`](docs/GITOPS-CONSUMER-ROLLOUT.md).
4. Do **not** nest-install into IDE Development itself during Wave 1.
5. Do **not** apply live GitHub protections, secrets, variables, App, or Bugbot settings from Wave 1 automation without an explicit approved apply step (dry-run default).

Legacy `scripts/wire-repo.sh` / sync helpers remain for compatibility with the prior sparse GitOps wiring model until consumers migrate; they are **not** the v2 portable install path.

## Branch protection (standard system behavior)

Every installed consumer must protect `development`, `staging`, and `main`. Planning and verification tooling is dry-run by default; credentials are never packaged. See [`docs/contracts/REPOSITORY-PROTECTION.md`](docs/contracts/REPOSITORY-PROTECTION.md).

## Make Changes Safely

Use one working copy at a time for active edits to this system repository. Do not make overlapping manual changes on both the MacBook and Mac Mini and then try to reconcile them later.

Before letting Cursor, Codex, or another agent modify the system:

```bash
git status
```

If the working tree is clean, make the smallest useful change, then review the result before committing.

## MacBook Update Flow

Typical update flow for this system repository:

```bash
git pull
git status
git add README.md SETUP.md VERSION docs/
git commit -m "..."
git push
```

If other root files are intentionally changed, stage them explicitly rather than using broad adds by habit.

## Warning

- Do not copy `core/` or `.cursor/` manually into many repositories.
- Do not create consumer `.cursor` symlinks pointing at this checkout.
- Use Git and this repository as the source of truth for the package.
- Make major changes in small commits.
- Run `git status` before letting agents modify the system.
- Never commit secrets, App private keys, or live credential values into managed packages.
