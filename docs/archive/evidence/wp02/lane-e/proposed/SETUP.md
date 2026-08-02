# Setup Guide

## Purpose

This repository is **IDE Development** — the shared AI development core (version **v2.0.0**) used across **Cursor** and **Codex**.

The canonical knowledge asset lives in `core/`. The portable package source for consumers lives in `core/managed-core/`. GitHub is the source of truth for this **system source** repository.

**Claude Code is outside current v2 support and roadmap** (excluded). Historical Claude packaging files may exist under `claude/`; do not treat them as an active install path.

**This checkout is not a consumer.** Do not nest-install `.ide-development/` into IDE Development during Wave 1 / Work Packet 1 / Work Packet 2. Consumer rollout is **deferred** and requires separate Principal (Carlos) approval per repo after Work Packet 3 publication decisions — see [`docs/GITOPS-CONSUMER-ROLLOUT.md`](docs/GITOPS-CONSUMER-ROLLOUT.md).

**New operators:** after cloning, start with:

- [docs/IDE-DEVELOPMENT-INTENT.md](docs/IDE-DEVELOPMENT-INTENT.md)
- [docs/IDE-DEVELOPMENT-TECHNICAL-PRD.md](docs/IDE-DEVELOPMENT-TECHNICAL-PRD.md)
- [docs/IDE-DEVELOPMENT-OPERATIONS-MANUAL.md](docs/IDE-DEVELOPMENT-OPERATIONS-MANUAL.md)
- [docs/OPEN-ISSUES.md](docs/OPEN-ISSUES.md) · [docs/BUILD-LOG.md](docs/BUILD-LOG.md)
- [docs/runbooks/release-candidate.md](docs/runbooks/release-candidate.md) · [docs/runbooks/rollback.md](docs/runbooks/rollback.md)
- [docs/acceptance/acceptance-matrix.md](docs/acceptance/acceptance-matrix.md)
- [docs/GITOPS-CONSUMER-ROLLOUT.md](docs/GITOPS-CONSUMER-ROLLOUT.md)

Retired systems: [docs/ARCHIVE-INDEX.md](docs/ARCHIVE-INDEX.md) and [docs/archive/](docs/archive/README.md).

## Clone On Another Machine

```bash
mkdir -p ~/Projects
cd ~/Projects
git clone https://github.com/linktrend/IDE-Development.git "IDE Development"
cd "IDE Development"
```

Use this repository for authoring, packaging, and self-verification — not as a consumer rollout target.

## Mac Mini Setup

```bash
mkdir -p ~/Projects
cd ~/Projects
git clone https://github.com/linktrend/IDE-Development.git "IDE Development"
cd "IDE Development"
git status
cat VERSION   # expect v2.0.0
```

## Pull Updates (system source)

```bash
git pull
git status
```

## Portable consumer install (v2)

Consumers install a **physical** managed core inside their own Git repository. There is no consumer-to-system `.cursor` symlink and no absolute external path dependency.

**WP1/WP2 policy:** use **disposable** repositories for proof. Real consumers wait for Principal approval after WP03 publication decisions — do not treat this section as rollout authorization.

### One-command paths

#### A. From system source checkout

```bash
python3 scripts/ide-development.py plan --repo /path/to/consumer
python3 scripts/ide-development.py install --repo /path/to/consumer
python3 scripts/ide-development.py update --repo /path/to/consumer
```

#### B. From extracted release candidate

```bash
python3 scripts/ide-development.py release-candidate create
python3 scripts/ide-development.py release-candidate verify --archive /path/to/archive.tar.gz
```

Or extract manually and install without the live checkout:

```bash
python3 /path/to/extracted-rc/.../ide-development.py install \
  --package /path/to/extracted-rc \
  --repo /path/to/disposable-consumer
```

Details: [`docs/runbooks/release-candidate.md`](docs/runbooks/release-candidate.md).

### Drift, verify, version, rollback

```bash
python3 scripts/ide-development.py drift --repo /path/to/consumer
python3 scripts/ide-development.py verify --repo /path/to/consumer
python3 scripts/ide-development.py version --repo /path/to/consumer
python3 scripts/ide-development.py rollback --repo /path/to/consumer
```

Flags: `--repo` / `--target` aliases · `--package` package root · `--json` · `--dry-run` (no writes).

### What a successful install leaves

- committed `.ide-development/` managed core
- physical Cursor discovery under `.cursor/rules`, `.cursor/commands`, `.cursor/skills`
- Codex discovery via root `AGENTS.md` managed markers and physical `.agents/skills/`
- consumer-owned content outside managed ownership/markers **preserved**
- obsolete generic rules removed only on **exact** supersession identity+hash match; otherwise refuse
- external `.cursor` symlink migrated to physical files without touching the outside target
- installed-state / transaction metadata under Git-local `.git/ide-development/` (not packaged secrets)

### Plain-English command meanings

| Command | Meaning |
|---|---|
| `plan` / `--dry-run` | Show what would change; write nothing |
| `install` | First-time physical managed install |
| `update` | Bring an installed consumer up to the package version |
| `drift` | Read-only report of managed-file hash drift / conflicts |
| `verify` | Confirm install integrity against package + installed-state |
| `version` | Print package / installer version identity |
| `rollback` | Restore exact pre-change files and modes from the last transaction |
| `release-candidate create` | Build reproducible portable archives + checksums (default `build/release-candidate/`; no tag/Release) |
| `release-candidate verify` | Extract an RC archive and install into a clean temp repo |

### Cursor and Codex discovery / precedence

- **Cursor** loads physical `.cursor/{rules,commands,skills}` from the consumer (works from nested directories under the repo).
- **Codex** loads the managed block in root `AGENTS.md` plus physical `.agents/skills/*/SKILL.md`.
- **Managed lifecycle** guidance wins when the package explicitly owns it.
- **Repository-specific technical guidance** outside managed ownership remains authoritative for that product.
- Conflicts that are unknown or that would overwrite modified consumer material **fail closed**.

### Consumer rollout hard rules

1. Produce a **read-only drift report** first.
2. Obtain **separate Carlos (Principal) approval** before each real consumer install/update.
3. Follow the locked order in [`docs/GITOPS-CONSUMER-ROLLOUT.md`](docs/GITOPS-CONSUMER-ROLLOUT.md).
4. Do **not** nest-install into IDE Development itself during Wave 1 / WP1.
5. Do **not** apply live GitHub protections, secrets, variables, App, or Bugbot settings from WP1 (plan/verify read-only only).
6. Work Packet 1 does **not** authorize real consumer mutation; rollout remains deferred.

Legacy `scripts/wire-repo.sh` / sync helpers remain for compatibility with the prior sparse GitOps wiring model until consumers migrate; they are **not** the v2 portable install path and must not create consumer-to-system `.cursor` symlinks for new installs.

## External GitHub state (read-only in WP1)

```bash
# Existing read-only audit helper (never mutates; never prints secret values)
python3 scripts/gitops/external_state_audit.py report --repo linktrend/IDE-Development
python3 scripts/gitops/external_state_audit.py verify --repo linktrend/IDE-Development --live
```

WP1 Lane C expands plan/verify inventory coverage. There is **no apply** in Work Packet 1. See [`docs/contracts/EXTERNAL-STATE-AUDIT.md`](docs/contracts/EXTERNAL-STATE-AUDIT.md).

## Branch protection (standard system behavior)

Every installed consumer must protect `development`, `staging`, and `main`. Planning and verification tooling is dry-run by default; credentials are never packaged. Live apply for **IDE Development** may occur in Work Packet 2 only via the authorized GitHub App path with a restorable before-state snapshot. Consumer protection apply and consumer installs remain separately approval-gated (WP03+). See [`docs/contracts/REPOSITORY-PROTECTION.md`](docs/contracts/REPOSITORY-PROTECTION.md).

## Host OS support evidence

WP1 production-readiness proof expects passing evidence on **macOS**, **Ubuntu Linux**, and **Windows** for the exact checkpoint SHA, with Python and OS versions recorded. See [`docs/acceptance/acceptance-matrix.md`](docs/acceptance/acceptance-matrix.md). Do not claim a platform passed if the runner was unavailable.

## Make Changes Safely (system source)

Use one working copy at a time for active edits. Before letting agents modify the system:

```bash
git status
```

If the working tree is clean, make the smallest useful change, then review before committing.

## Warning

- Do not copy `core/` or `.cursor/` manually into many repositories.
- Do not create consumer `.cursor` symlinks pointing at this checkout.
- Do not claim Claude Code support.
- Do not install real consumers during WP1/WP2 without Principal approval (rollout deferred; WP02 does not authorize consumer mutation).
- Never commit secrets, App private keys, or live credential values into managed packages or RC archives.
- Generated RC binary archives belong in ignored build/CI artifact dirs — not committed source.
