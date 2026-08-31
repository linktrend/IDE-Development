# OpenClaw customization-scoped admission canary

**Combined canary: REJECT**  
**Requested probe matrix: PASS**  
**Live real-scanner admission: REJECT** (`new-skipped-input`)

This report is IDE evidence only. OpenClaw Prime was not modified, its full suite was not run, and nothing was merged or promoted.

Recorded 2026-08-31 13:08 Asia/Taipei.

## Identities

| Surface | Value |
| --- | --- |
| Protected IDE SHA | `e32b578e2d11dcdf6e24baa8022f577efa26da24` |
| IDE HEAD | `e32b578e2d11dcdf6e24baa8022f577efa26da24` (match) |
| IDE branch | `dev/cloudcursor/openclaw-scoped-canary-evidence-60dc` |
| IDE installer | `2.5.2` |
| OpenClaw `origin/development` | `95e0494c1f332fd33cea12152a07dd404c52bb07` |
| OpenClaw HEAD / tree | `95e0494c1f332fd33cea12152a07dd404c52bb07` / `dbeea3e695449c1a5e79962d772d1c0716f42fc5` |
| OpenClaw working tree | clean (unmodified) |
| Boundary kind | `openclaw-prime-customization-boundary` |
| Boundary prime pin | `ae397be1e601307b50d593c195ab9777c8400492` / `c5d6b6d75066915b433e6f92d223b7bcb821d6fc` |
| Upstream classification pin | `503b21dc6bfdea5e385ba3f85e81691cfc2a23c1` / `270f1c102caf961b69839fe04656aee4ea59ac8c` |

Admission used the protected IDE module `scripts/ide_development/openclaw_customization_admission.py` and the IDE secret scanner against the clean OpenClaw `development` tree. Scanner inputs were the admission `checkedPaths` only. Forbidden whole trees were never walked.

## Requested probes

| Probe | Verdict | Evidence |
| --- | --- | --- |
| Exact scoped paths | **PASS** | 1130 checked paths. SHA-256 of sorted POSIX paths: `6b00dfd477861cf9ecf50f9e431562b89b4412e421517d8e6493377315b879e8`. Zero forbidden-tree hits. Zero out-of-boundary paths. `noUpstreamScanOrMutation=true`. |
| Unchanged upstream findings allowed | **PASS** | Exact `credential_finding` on a scoped path with matching `baselineFindings` and `observed_upstream` admitted. |
| Declared-missing legacy paths omitted | **PASS** | `declaredMissingLocally=["core"]` and `omittedMissingPaths=["core"]`. Zero absent `core/` inventory files were scanned. |
| Synthetic new finding rejected | **PASS** | `OpenClawAdmissionError: new-or-changed-finding` |
| Synthetic new skipped input rejected | **PASS** | `OpenClawAdmissionError: new-skipped-input` |
| Synthetic timeout rejected | **PASS** | `errorType=timeout` and `TimeoutError` both raised `scanner-timeout` |

### Exact scoped paths

Checked paths were the union of:

- LiNKtrend-owned prefixes and exact paths from the live boundary
- present IDE `installed-state.json` destinations under declared IDE prefixes (package `2.5.2`)
- present overlay `AGENTS.md`
- present transaction-changed paths
- the boundary file itself under `.linktrend/openclaw-prime`

Forbidden whole trees (unscanned): `apps`, `config`, `deploy`, `examples`, `extensions`, `packages`, `qa`, `security`, `skills`, `src`, `test`, `ui`.

Sample (first 12 of 1130): `.agents/skills-loader.mjs`, `.agents/skills/action-queue/SKILL.md`, `.agents/skills/agentcomply/SKILL.md`, `.agents/skills/agentsetup/SKILL.md`, `.agents/skills/api-patterns/SKILL.md`, `.agents/skills/app-builder/SKILL.md`, `.agents/skills/architecture/SKILL.md`, `.agents/skills/bash-linux/SKILL.md`, `.agents/skills/ci-cd-and-automation/SKILL.md`, `.agents/skills/code-review-and-quality/SKILL.md`, `.agents/skills/code-simplification/SKILL.md`, `.agents/skills/context-engineering/SKILL.md`.

### Declared-missing `core`

The live boundary lists `core` under `ideManaged.declaredMissingLocally`. Admission omitted that declared token (`omittedMissingPaths=["core"]`).

The 2.5.2 inventory still declares 15 `core/` destinations. All 15 exist on this `development` tree and were therefore included as present inventory files (not as a forbidden upstream walk). That matches admission: missing declared paths are omitted; present inventory files remain in scope. The boundary uncertainty note that `core/` is absent from Prime is stale relative to `95e0494c1f332fd33cea12152a07dd404c52bb07`.

## Live real-scanner admission

**REJECT** — fail-closed `new-skipped-input`.

The scoped scanner returned `ok=false` with 6 scoped findings (kinds `skipped_input`, `stale_fixture_declaration`; rules `input.undecodable`, `assignment.secret`, `binding.candidate_tree`). Paths only (no secret values):

- `linkbots/lisa/Personality files/assets/lisa-avatar-original.jpg`
- `linkbots/lisa/Personality files/assets/lisa-avatar.png`
- `.github/linktrend-secret-scan-fixtures.json`
- `.ide-development/tests/test_gate_receipts.py`
- `.ide-development/tests/test_phase_packager_coordinator.py` (two findings)

Those live findings were **not** present as exact `preExistingFindings` on the boundary, so admission correctly refused. This is not a synthetic probe failure; it is the live `development` tree refusing admission until those scoped findings are baseline-bound or repaired in a later governed change.

## Focused IDE tests (protected SHA)

`python3 -m unittest tests.ide_development.test_openclaw_customization_admission -v`

13 tests, 0.042s, **OK**. Not an OpenClaw suite.

## Non-goals (honored)

- No OpenClaw file edits, commits, or pushes
- No OpenClaw full suite
- No merge into `development`
- No promotion to `staging` or `main`
- No implementer Phase packaging

## Combined verdict

**REJECT.** The protected IDE admission behavior at `e32b578e2d11dcdf6e24baa8022f577efa26da24` matches the requested probes against OpenClaw `development` `95e0494c1f332fd33cea12152a07dd404c52bb07`, but live real-scanner admission of that tree is not admitted.
