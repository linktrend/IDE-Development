# Lane D Result — deterministic release-candidate packaging

**Issue:** #67
**Branch:** `issue/67-work-packet-1-production-readiness-proof-and-rel`
**Lane:** D (deterministic release-candidate packaging)
**Model:** cursor-grok-4.5-high
**Package version target:** `2.0.0`
**No commit / push / PR / tag / GitHub release / credentials** (subagent constraint)

## Delivered

| Path | Role |
|---|---|
| `scripts/ide_development/release_candidate.py` | Stdlib RC create/verify |
| `scripts/ide_development/build_manifest.py` | Includes RC schemas in generated manifest |
| `scripts/ide_development/cli.py` | `release-candidate create\|verify` |
| `scripts/ide_development/constants.py` | RC constants + `PACKAGE_VERSION_TARGET` |
| `core/managed-core/schemas/release-candidate.schema.json` | RC metadata schema |
| `core/managed-core/schemas/release-candidate-checksums.schema.json` | Checksums schema |
| `scripts/ide_development_tests/test_release_candidate.py` | Gate/refusal/archive unit tests |
| `scripts/ide_development_tests/test_package_reproducibility.py` | Manifest byte-identical proof |
| `tests/packaging/test_release_candidate_integration.py` | Create/verify integration |
| `tests/packaging/LANE_D_RESULT.md` | This evidence |

Binary archives live only under ignored `build/` (`.gitignore` already covers `build/`).

## Commands

```bash
# Unit + packaging suites
PYTHONPATH=scripts python3 -m unittest discover -s scripts/ide_development_tests -v
PYTHONPATH=scripts python3 -m unittest discover -s tests/packaging -v

# Manifest regenerate + verify
PYTHONPATH=scripts python3 -m ide_development.build_manifest --write
PYTHONPATH=scripts python3 -m ide_development.build_manifest --verify

# Production RC (requires clean worktree + this evidence file)
PYTHONPATH=scripts python3 scripts/ide-development.py release-candidate create --json

# Local WP1 proof while other lanes dirty the tree
PYTHONPATH=scripts python3 scripts/ide-development.py release-candidate create \
  --allow-dirty --skip-evidence --json

# Module entry
PYTHONPATH=scripts python3 -m ide_development.release_candidate create --allow-dirty --skip-evidence --json

# Verify extracted install from archive
PYTHONPATH=scripts python3 scripts/ide-development.py release-candidate verify \
  --archive build/release-candidate/ide-development-managed-core-2.0.0.tar.gz --json
```

## Sample archives (local `build/`, not committed)

Recorded after final Lane D source freeze on this worktree tip:

| Field | Value |
|---|---|
| `sourceCommit` (HEAD at sample build) | `e804e6beafd76b45c609ae283b0a7477f2b8c27a` |
| `packageVersion` | `2.0.0` |
| `manifestHash` | `sha256:71ded557fd549149e5cc556d8713e05333c35dbb57d08583a5609fcaa2e62ab6` |
| tar.gz path | `build/release-candidate/ide-development-managed-core-2.0.0.tar.gz` |
| tar.gz sha256 | `sha256:3060a69b4ab3c4b54c4893a3b1d803dfe270743b1dd4c47af1e40e7bd25a65f7` |
| tar.gz bytes | `212896` |
| zip path | `build/release-candidate/ide-development-managed-core-2.0.0.zip` |
| zip sha256 | `sha256:4258285c574d47647293cce4f84b9df6ec51641cc1b928bc2131389307b30d2a` |
| zip bytes | `283013` |
| install verify | `installedVersion=2.0.0`, exit 0 |
| identities packaged | `137` repo-relative paths |

Metadata + checksums companions (also under `build/release-candidate/`):

- `release-candidate.json`
- `SHA256SUMS.json` (archives + metadata; not self-hashed)

## Reproducibility proof

1. **Manifest:** consecutive `write_manifest()` runs produce byte-identical `MANIFEST.json` (`test_package_reproducibility`).
2. **Within create:** consecutive tar.gz/zip builds from the same staging tree are byte-identical (enforced; create fails closed on drift).
3. **Across create (stable tree):** back-to-back `create_release_candidate(allow_dirty=True, skip_evidence=True, skip_install_verify=True)` produced identical tar.gz and zip digests (`repro True True` for the sample checksums above).
4. Archive members use fixed epoch `2026-08-01T00:00:00Z`, uid/gid 0, sorted paths, no symlinks.

Checksums change if package sources change (expected). Production RC must be rebuilt on a clean frozen SHA.

## Refusals tested

| Refusal | Result |
|---|---|
| Dirty worktree without `--allow-dirty` | exit `12`, error contains `dirty` |
| Missing evidence (`LANE_D_RESULT.md`) without `--skip-evidence` | exit `12` (mocked + gate) |
| Version ≠ `2.0.0` / root↔managed drift | exit `12` |
| Symlink package source | refused |
| Credential-like PEM/token material | refused |
| Absolute host checkout path in content | refused |
| Manifest hash drift after regenerate | refused (`verify_manifest` errors) |

## Packaging policy

Excluded from archives: credentials/secret values, `.git` metadata, absolute host paths, external symlinks, caches/temp, consumer data, Claude surfaces, `build/` artifacts.

Provenance identities are repository-relative only. Install + rollback instructions are embedded in metadata and synthesized as `INSTALL.md` / `ROLLBACK.md` inside the archive (not committed host paths).

## Test results (Lane D)

```text
PYTHONPATH=scripts python3 -m unittest discover -s scripts/ide_development_tests -v
→ Ran 71 tests — OK

PYTHONPATH=scripts python3 -m unittest discover -s tests/packaging -v
→ Ran 4 tests — OK
```

## Gaps / blockers for lead

1. **Clean-tree production RC not yet runnable in this concurrent WP1 worktree** — other lanes leave the tree dirty; sample used `--allow-dirty --skip-evidence`. After integration checkpoint is clean, re-run without those flags (this file now satisfies evidence).
2. **HEAD SHA above may lag the eventual Lane D commit** — sample bind is local tip at build time; lead should rebuild RC after the checkpoint commit that includes these sources and record the new digests in the WP1 evidence bundle.
3. **No tag / GitHub release / publish** performed (in scope for WP2 only).
4. **Cross-platform matrix CI** for archives is Lane A ownership; Lane D proved local extract+install on this host only.
5. **MANIFEST.json regenerates** when RC schemas / installer sources change — expect a managed-core manifest diff in the Lane D checkpoint.
