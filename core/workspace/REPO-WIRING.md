# Repo Wiring

## Purpose

Define how consumer repositories are attached to the shared runtime surface after safe discovery and cleanup review.

## Preferred Method — Deterministic Script

When the consumer repository path is known and legacy cleanup has already been reviewed, prefer the wiring script:

```bash
./scripts/wire-repo.sh /path/to/consumer-repo
```

From inside `IDE Development`, pass an absolute or relative path to the consumer repository root.

The script:

- verifies the target is a directory and is not the system repository itself
- preserves an existing physical `.cursor` tree and its consumer-owned files
- moves an existing `.cursor` symlink to a timestamped backup before creating a physical directory
- syncs managed Cursor rules, commands, and skills as regular files under `repo/.cursor` (**Layer A** — agent behavior)
- syncs managed GitHub workflows from `core/github/managed-workflows/` into `repo/.github/workflows/` (**Layer B** — robots; never overwrites `ci.yml`)
- verifies required runtime paths are reachable from the consumer repository
- prints next steps for verified Phase delivery and the designated project orchestrator under Eric

Agents receiving natural-language wiring requests should run this script and report its pass/fail output rather than improvising copy or symlink commands by hand.

Current delivery and orchestration instructions: `docs/runbooks/hosted-delivery-operations.md`. Backfill existing wired repos: `./scripts/backfill-managed-workflows.sh`.

## Manual Fallback

Use manual inspection only when judgment is required first — for example, when an existing `.cursor` contains mixed repository-specific rules and shared-system copies that must be inspected per `LEGACY-CLEANUP.md`. Preserve consumer-owned files, then use the wiring script to install the managed files physically.

## Resolution Chain

The package manifest resolves canonical content from `IDE Development/core` and installs the selected managed entrypoints as regular files under `repo/.cursor`.

## Preconditions

Before wiring:

- repository identity must be clear
- any existing `.cursor` state must be inspected
- uncertain material must be preserved
- backups must exist when replacement is safe but destructive

## Verification

After wiring, verify:

- `repo/.cursor` is a physical directory, not a symlink
- `.cursor/rules/cursor-gitops-bootstrap.mdc` and `.cursor/rules/linktrend-git-branching.mdc` exist as regular files
- `.cursor/commands/agentsetup.md`, `.cursor/commands/agentcomply.md`, and their managed skills exist as regular files
- managed workflow files are present under `repo/.github/workflows/`

## Backward Compatibility Rule

Consumer repositories should continue to see a normal `.cursor/...` runtime surface.

The consumer repository should not need to know that:

- `IDE Development/.cursor` is itself an adapter
- `IDE Development/core` is canonical storage

## Managed File Rule

Do not hand-copy managed `.cursor` entrypoints. Use the wiring script so the package manifest controls their physical contents and consumer-owned files remain intact.

Managed GitHub workflow YAML **must** be copied into each consumer. Prefer `scripts/sync-managed-workflows.sh` over hand copies.

## Post-wire checklist (Layer B completion)

1. Managed workflows present under `repo/.github/workflows/` (sync output PASS).
2. Use the combined Phase delivery flow in `docs/runbooks/hosted-delivery-operations.md`; require exact-head Verify evidence and independent review.
3. Use the designated project orchestrator under Eric and its verified IDE route, as documented in the hosted delivery runbook.
4. Merge the Phase PR to `development` only after required checks and review pass.
