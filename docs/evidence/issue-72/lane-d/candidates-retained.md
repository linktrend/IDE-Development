# Lane D — candidates retained (not deleted)

Only **reference-proven** temporary/generated tracked junk may be removed. The following looked temporary by filename but are retained with reasons. Lane D did not delete them.

## Archive / evidence lookalikes (Lane B ownership)

Under `docs/archive/evidence/wp02/` (moved from `docs/evidence/wp02/` by Lane B during this issue):

| Pattern | Examples | Retain reason |
|---------|----------|---------------|
| `*.err` (often empty) | `lane-d/raw/actions-secrets.err`, `…/workflows-list.err` | WP02 live-probe stderr captures; empty = success/no stderr. Acceptance evidence. |
| `*.rc` (1–2 bytes, value `0`) | `lead/validation/*.rc` | Command exit-code proofs for validation matrix. |
| `*.stderr` / `*.stderr.txt` / `*.stdout.*` | `rc-create.stderr`, `external-state-*-live.stderr.txt` | Captured CLI streams for WP02 external-state / RC proof. |
| `*.jsonl` before-state | `before-state-*/commit-statuses.jsonl` | Snapshot evidence, not a temp log. |

**Lead note:** If a future pass wants to prune empty `*.err` companions, that is an archive/evidence policy decision (Lane B / lead), not blind temp deletion.

## Fixtures (must keep)

| Path | Reason |
|------|--------|
| `tests/fixtures/unification-e2e/.../proof-manifest.sha256` | Fixture checksum manifest |
| `tests/**/fixtures/**`, `scripts/ide_development_tests/fixtures/**` | Installer/migration/RC test payloads |
| `tests/platform_matrix/summaries/` (+ nested `.gitignore`) | Directory tracked; generated JSON ignored locally |

## Schemas / runbooks named “release-candidate” (not outputs)

| Path | Reason |
|------|--------|
| `core/managed-core/schemas/release-candidate*.schema.json` | Contracts |
| `docs/runbooks/release-candidate.md` | Operator runbook |
| `scripts/ide_development/release_candidate.py` + tests | Source + proof harness |
| Archived WP02 proposed copies under `docs/archive/evidence/wp02/lane-e/proposed/...` | Historical proposals (Lane B) |

## Adoption backups / transcripts

| Path | Reason |
|------|--------|
| `docs/adoption-backups/**` | Intentional consumer backup snapshots |
| `docs/archive/handoffs/transcripts/**` | Archived handoff transcripts (Lane B) |

## Suggest-only hygiene (not Lane D apply)

| Candidate | Why flagged | Action for lead / Lane E |
|-----------|-------------|---------------------------|
| Stale local worktrees for closed issues 23–68 | Disk / confusion risk | Cleanup after Issue #72 merge; do not touch from Lane D |
| `/private/tmp/issue-23-…` worktree marked **prunable** | Already flagged by git | `git worktree prune` (operator) |
| One local `git stash` entry | Unknown contents | Leave untouched unless Principal/operator inspects |
| GitHub branch/PR remote clutter | Out of scope | Lane E disposition only |

## Deletion ledger

| File | Deleted? | Proof |
|------|----------|-------|
| _(none)_ | — | Full-tree junk pattern search returned no trackable temp/generated files outside protected trees above |
