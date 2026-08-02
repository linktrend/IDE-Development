# WP02 Lane F — Portable-system regression review (#3)

| Field | Value |
|---|---|
| Reviewer | Lane F reviewer #3 (PORTABLE-SYSTEM REGRESSION) |
| Model | cursor-grok-4.5-high |
| Repo | linktrend/IDE-Development |
| Branch | `issue/68-work-packet-02-integration-lineage-stale-cleanup` |
| Tip SHA reviewed | `3c21bb8493a795aa6e46e0eb8a31b2fcd6c15a96` |
| Reviewed at | 2026-08-02T03:25:00Z (approx.) |
| Scope | Read-only verification; review artifact only under `docs/evidence/wp02/lane-f/` |
| Product edits | None |
| Commit/push | None |

## Verdict

**PASS_WITH_PENDING_CI**

Installer, managed-core package, Cursor/Codex adapters, manifests, docs, and recorded local suite exits remain intact on the WP01+cleanup integrated tip. Three-OS matrix is **not** fully evidenced green on this tip — do not invent green; CI pending.

## Checks performed

### 1. Managed-core VERSION / MANIFEST

| Check | Result |
|---|---|
| `core/managed-core/MANIFEST.json` present | PASS — `schemaVersion=1`, `packageVersion=2.0.0`, 227 `files` entries |
| `core/managed-core/VERSION` present | PASS — content `2.0.0` |
| Root `VERSION` present | PASS — content `v2.0.0` (2.0.0 identity) |
| MANIFEST lists VERSION file | PASS — id `core-version` → `core/managed-core/VERSION` ⇒ `.ide-development/VERSION` |
| `core/managed-core/INDEX.yaml` | PASS — `version: "2.0.0"`, Cursor/Codex platforms noted |
| Installer constants | PASS — `INSTALLER_VERSION` / `PACKAGE_VERSION_TARGET` = `2.0.0` |

### 2. Release-candidate evidence

| Artifact | Result |
|---|---|
| `docs/evidence/wp02/lead/validation/rc-create-final.json` | PASS — `ok=true`, package/installer `2.0.0`, `installVerify.ok=true`, `installExitCode=0`, reproducible archives |
| `rc-verify-tar.json` | PASS — `ok=true`, tar.gz checksum matches create |
| `rc-verify-zip.json` | PASS — `ok=true`, zip checksum matches create |
| `rc-SHA256SUMS.json` | PASS — tar/zip/release-candidate.json digests bound |
| RC `sourceCommit` | `7e441faba1a6c61d9f3d3c75842610044fc40104` — ancestor of tip (`merge-base --is-ancestor` OK). Tip includes later WP02 evidence-binding commits only; package bytes intentionally bound to RC source. |

### 3. Required local suites (evidence-recorded exits)

Authoritative record: `docs/evidence/wp02/WORK-PACKET-02-EVIDENCE.json` → `validation` (all required packet suites **0**):

| Suite | Recorded exit |
|---|---|
| `test-stale-cleanup-controls.sh` | 0 |
| `test-cleanup-wp01-lineage-coexistence.sh` | 0 |
| `test-external-state-wp1.sh` | 0 |
| `test-external-state-audit.sh` | 0 |
| `test-repository-protection.sh` | 0 |
| `test-gitops-behavioral.sh` | 0 |
| `test-gitops-lifecycle.sh` | 0 |
| `test-gitops-review-packager.sh` | 0 |
| `test-portable-v2-integration.sh` | 0 |
| `verify-ide-development.sh` | 0 |
| `rcCreate` / `rcVerifyTar` / `rcVerifyZip` / `rcReproducible` | true |

Supporting logs: `portable-v2.rc=0`; r4 logs end with PASS for portable, lifecycle, verify-ide, coexistence, external-state, packager, stale-cleanup, repository-protection, behavioral.

Note: early `*.rc` snapshots still show intermediate failures (`gitops-lifecycle.rc=1`, `verify-ide.rc=127`) from pre-repair runs. Final bound evidence and r4 logs supersede those; not treated as current FAIL.

### 4. Portable harness / adapters / docs

| Surface | Result |
|---|---|
| `tests/test-portable-v2-integration.sh` | PASS — present, executable; harness ALL CHECKS PASSED (default mode) |
| `scripts/ide-development.py` | PASS — present |
| `AGENTS.md` | PASS — system-source + managed markers; agentsetup/agentcomply discovery |
| `.agents/skills/agentsetup` + `agentcomply` | PASS — physical SKILL.md present |
| `.agents/skills-manifest.json` | PASS — agentsetup/agentcomply referenced |
| `.cursor/commands/agentsetup.md` + `agentcomply.md` | PASS |
| `.cursor/skills/agentsetup` + `agentcomply` | PASS |
| Managed-core Cursor/Codex platform skills | PASS — both platforms have agentsetup/agentcomply |
| `platforms/cursor/materialization-manifest.json` | PASS |
| `platforms/codex/skills-manifest.json` | PASS |
| Operator docs | PASS — `README.md`, `SETUP.md`, `docs/contracts/MANAGED-CORE-V2.md`, `docs/runbooks/release-candidate.md`, `docs/acceptance/acceptance-matrix.md` present |
| Lane E SUMMARY | Reviewed — pre-combine blockers noted as historical lane output; tip now carries integrated managed-core + docs |

### 5. Three-OS expectation / CI

| Item | Result |
|---|---|
| Workflow present | PASS — `.github/workflows/ide-development-cross-platform.yml` matrices `ubuntu-latest` / `macos-latest` / `windows-latest` |
| Evidence `threeOsCi` | **pending_dispatch** (`WORK-PACKET-02-EVIDENCE.json`) — not claimed green |
| Live observation on tip `3c21bb8` | Run `30730574939` (`workflow_dispatch`): ubuntu **success**, macOS **success**, windows **in_progress**; overall run **in_progress**. Prior push run `30730570333` **cancelled**. Commit status state **pending**. |

**No invented green.** Three-OS full matrix success on this exact tip is **not** evidenced at review time → drives `PASS_WITH_PENDING_CI`.

## Findings

### Non-blocking observations

1. **Three-OS CI pending** — required for full portable closure; ubuntu/macOS already green on the active dispatch; Windows still running. Bind final run URL/conclusion when complete.
2. **Portable harness MANIFEST verify warn-only** — `portable-r4.log` still reports hash mismatches for `scripts/cleanup-merged-branches.sh` and `scripts/gitops/repair_task.py` under default skip/warn mode. RC create/verify on `7e441fa` succeeded with `ok=true`; treat as residual harness noise unless a post-tip `--write` drift reappears.
3. **`rc-rebuild-r4.log` ImportError** — attempted `verify_release_candidate` import failed; superseded by successful `rc-create-final.json` + `rc-verify-*.json` artifacts. No FAIL on final package path.
4. **Tip ≠ RC `sourceCommit`** — expected per evidence `bindingRule` (docs commits after package bind). Ancestry OK.

### Blocking regressions

None observed for portable installer/package/adapters/manifests/docs relative to WP01+cleanup integration.

## Explicit non-claims

- Three-OS CI green on tip `3c21bb8` — **not claimed**
- WP03 tag/release/publication — **not claimed**
- Consumer rollout / live external-state apply — **not claimed** (Lane D apply remains blocked per evidence)
- Review Ready / PR / Bugbot / promote — **not claimed**

## Return line

`PASS_WITH_PENDING_CI` — portable surfaces intact; required local suites exit 0 in evidence; three-OS CI pending (windows in progress).
