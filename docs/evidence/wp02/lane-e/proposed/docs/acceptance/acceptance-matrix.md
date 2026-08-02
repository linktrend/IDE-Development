# Acceptance matrix — Work Packet 1 (production readiness proof)

**Issue:** #67
**Branch:** `issue/67-work-packet-1-production-readiness-proof-and-rel`
**Packet:** Work Packet 1 — production-readiness proof and release candidate
**Rule:** Do **not** claim production readiness when any required row is skipped, neutral, untested, or only inferred.

Evidence belongs with the lead’s WP1 evidence bundle. This matrix is the operator checklist of **what must be proven**.

---

## A. Source and checkpoint integrity

| ID | Gate | Pass criteria | Owner lane |
|---|---|---|---|
| A1 | Starting checkpoint | History contains exact `76d2aae1fbf0d497fbfb0e06181b3932660c96ce` without rewrite | Lead |
| A2 | Prior portable checkpoints | History contains #64 `44a26f0…` and portable v2 `0868c00…` | Lead |
| A3 | Clean tree / remote match | Worktree clean; local HEAD == `origin/<issue-branch>` after checkpoint push | Lead |
| A4 | Untouched protected lines | `origin/development`, `staging`, `main`, PR #49, consumers untouched | Lead |
| A5 | No forbidden artifacts | No secrets, caches, generated binary RC archives, or `.superpowers` committed | All |

## B. Installer and migration

| ID | Gate | Pass criteria | Owner lane |
|---|---|---|---|
| B1 | Unit suite | `PYTHONPATH=scripts python3 -m unittest discover -s scripts/ide_development_tests -v` | A/B |
| B2 | Live migration BB | `python3 tests/managed-core-migration-bb/run_tests.py --with-installer` — no skipped required scenarios | B |
| B3 | Clean-room install | Brand-new disposable repo install leaves physical `.ide-development/` + Cursor/Codex adapters | B |
| B4 | Idempotence | Repeat install/update byte-identical; no absolute source-checkout path in installed files/state | B |
| B5 | Sparse GitOps upgrade | Upgrade from prior sparse layout succeeds fail-closed on conflicts | B |
| B6 | External `.cursor` symlink | Physical migration; external target byte-identical; rollback exact | B |
| B7 | Consumer-owned preserve | Consumer rules/commands/skills and `AGENTS.md` outside markers byte-identical | B |
| B8 | Obsolete generic rules | Exact-known supersession removal only; modified/unknown refuse | B |
| B9 | Drift → repair | Drift detection then deterministic repair path proven | B |
| B10 | Interrupted txn | Recovery + byte/mode-exact rollback | B/E |
| B11 | Extracted RC install | Install from extracted archive with **no** IDE Development checkout access | B/D |

## C. Discovery and precedence

| ID | Gate | Pass criteria | Owner lane |
|---|---|---|---|
| C1 | Cursor discovery | Nested-directory discovery of physical `.cursor/{rules,commands,skills}` | B |
| C2 | Codex discovery | Nested-directory discovery via `AGENTS.md` managed block + `.agents/skills` | B |
| C3 | Precedence | Managed lifecycle wins when explicitly identified; consumer technical guidance preserved; unknown conflicts fail closed | Contract + B |
| C4 | Claude excluded | No Claude entrypoints, packaging, tests claiming support, or docs asserting Claude support | F + all |

## D. Cross-platform OS evidence

| ID | Gate | Pass criteria | Owner lane |
|---|---|---|---|
| D1 | macOS | Matrix job success on exact checkpoint SHA; record Python + OS versions | A |
| D2 | Ubuntu Linux | Same | A |
| D3 | Windows | Same; Windows-safe assertions (no fake POSIX mode/symlink privilege claims) | A |
| D4 | No silent skips | Required tests not skipped for symlink/FS/shell/permission differences; exclusions explicit + paired assertion | A |

**Expectation:** Evidence must identify platform + Python version per OS. Unavailable runners → record exact external blocker; do **not** mark the platform passed.

## E. External GitHub state (read-only)

| ID | Gate | Pass criteria | Owner lane |
|---|---|---|---|
| E1 | Fixture matrix | plan/verify matched, drifted, forbidden, unavailable, malformed, credential-missing | C |
| E2 | Live audit | Optional read-only audit of `linktrend/IDE-Development`; no secret values recorded | C |
| E3 | Unknown/blocked | Unverifiable settings reported `unknown`/`blocked`, never assumed compliant | C |
| E4 | No apply | Zero live App/secret/variable/Bugbot/ruleset mutations in WP1 | C |

Tooling note: existing `scripts/gitops/external_state_audit.py` is read-only (`report`/`verify`). WP1 Lane C expands inventory/planner/verifier coverage; **apply remains out of WP1**.

## F. Package and release candidate

| ID | Gate | Pass criteria | Owner lane |
|---|---|---|---|
| F1 | Manifest regen | Deterministic; second run byte-identical | D |
| F2 | Archives | Reproducible portable archives + SHA-256; no credentials/host paths/symlinks/Git metadata | D |
| F3 | CLI RC command | `release-candidate create|verify` present; create refuses dirty tree / hash drift / missing evidence for production-grade runs | D |
| F4 | Extract + install | Clean temp extract installs successfully | B/D |
| F5 | No publish | No tag, GitHub Release, or registry publish | D + Lead |

## G. Security / fail-closed

| ID | Gate | Pass criteria | Owner lane |
|---|---|---|---|
| G1 | Path/link attacks | Traversal, absolute injection, symlink/junction escapes refused | E |
| G2 | Malformed package | Bad manifest/hash/mode/partial archive fail closed with deterministic JSON | E |
| G3 | Concurrency / corruption | Locks, interrupted writes, corrupt journals fail closed | E |
| G4 | Evidence hygiene | No credentials, tokens, private keys, local usernames, or absolute checkout paths in packages/evidence | E |

## H. Full system regression (minimum)

| ID | Command | Notes |
|---|---|---|
| H1 | `PYTHONPATH=scripts python3 -m unittest discover -s scripts/ide_development_tests -v` | Required |
| H2 | `python3 tests/managed-core-migration-bb/run_tests.py --with-installer` | Required |
| H3 | `python3 -m pytest tests/adapters -q` | Required when adapters present |
| H4 | `bash scripts/tests/test-repository-protection.sh` | macOS/Linux |
| H5 | `bash scripts/tests/test-stale-cleanup-controls.sh` | **ABSENT on WP1 starting checkpoint** (`76d2aae`); lives on unrelated cleanup issue lineage (e.g. #63). Do not import that lineage in WP1. Partial coverage: `test-gitops-behavioral.sh` cleanup dry-run cases. |
| H6 | `bash scripts/tests/test-gitops-behavioral.sh` | macOS/Linux |
| H7 | `bash scripts/tests/test-gitops-lifecycle.sh` | macOS/Linux |
| H8 | `bash scripts/tests/test-gitops-review-packager.sh` | macOS/Linux |
| H9 | `bash tests/test-portable-v2-integration.sh` | Required |
| H10 | `bash scripts/verify-platform-adoption.sh` | Required |
| H11 | `SKIP_LOCAL_ARCHIVE_CHECKS=1 bash scripts/verify-ide-development.sh` | Required |

Windows: cross-platform runner executes equivalent Python-owned contract tests and documents the shell-suite division; required macOS/Linux shell suites must still pass on those platforms.

## I. Process / publication exclusions (must remain true)

| ID | Exclusion | WP1 value |
|---|---|---|
| I1 | PR / Bugbot / review-ready / merge | Not performed by this packet |
| I2 | Promote to staging/main | Not performed |
| I3 | Consumer rollout | **Deferred** — separately Principal approval-gated; remains deferred through WP2; WP03 publication decisions + rollout doc |
| I4 | Tag / GitHub Release | Not performed |
| I5 | Claude support claims | Absent |

---

## Work Packet 2 / Work Packet 3 hand-off

When every required row above is green (or explicitly blocked with external cause), WP1 may checkpoint. **WP2** (Issue #68) owns canonical lineage construction (including proving frozen PR #49 content while preserving frozen heads), stale-cleanup hardening (plan only), and IDE Development live readiness — checkpoint only; no merge/promote/tag/consumer. **WP3** owns integration into `development` / promotion and publication/rollout **decisions** under separate Principal approval — not automatic consumer mutation.
