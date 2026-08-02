# Lane A Result — cross-platform installer matrix

**Issue:** #67 Work Packet 1
**Lane:** A (cross-platform installer matrix)
**Model:** cursor-grok-4.5-high
**Host:** Darwin arm64 (macOS-26.5.2), Python 3.9.6
**Date:** 2026-08-02 (Asia/Taipei session)

## Verdict

**PASS on this macOS host.** Authoritative command exited `0` with 59/59 tests passing (0 fail, 0 error, 0 skip).

## How to run

```bash
python3 scripts/run_cross_platform_matrix.py
```

Optional flags: `-q` (quiet), `--no-json`, `--summary PATH`, `--matrix-only`, `--existing-only`.

Machine-readable summaries: `tests/platform_matrix/summaries/matrix-<sys.platform>-latest.json` (JSON gitignored; see `summaries/README.md`).

CI: `.github/workflows/ide-development-cross-platform.yml` on push to `issue/**` (and `workflow_dispatch`) using `ubuntu-latest` / `macos-latest` / `windows-latest` only.

## Local Darwin run (recorded)

| Field | Value |
|---|---|
| Command | `python3 scripts/run_cross_platform_matrix.py` |
| Exit code | `0` |
| Tests run | 59 |
| Pass | 59 |
| Fail | 0 |
| Error | 0 |
| Skip | 0 |
| Duration | ~5.0s |
| Summary artifact | `tests/platform_matrix/summaries/matrix-darwin-latest.json` |

Quiet re-run confirmation:

```text
python3 scripts/run_cross_platform_matrix.py -q
EXIT:0
counts: pass=59 run=59 fail=0 error=0 skip=0
```

## Files changed (Lane A owned paths only)

| Path | Role |
|---|---|
| `scripts/run_cross_platform_matrix.py` | Authoritative one-command entrypoint |
| `.github/workflows/ide-development-cross-platform.yml` | Branch-safe CI matrix (issue/** push) |
| `tests/platform_matrix/__init__.py` | Package roots |
| `tests/platform_matrix/runner.py` | Discovery, exclusions, unittest runner |
| `tests/platform_matrix/summary.py` | JSON summary schema/helpers |
| `tests/platform_matrix/exclusions.py` | Explicit Windows symlink-privilege exclusions + equivalents |
| `tests/platform_matrix/platform_assertions.py` | Windows-safe mode/physical assertions |
| `tests/platform_matrix/test_cross_process_lock_matrix.py` | True cross-process lock on all platforms (incl. Windows msvcrt) |
| `tests/platform_matrix/test_unicode_paths.py` | Spaces + Unicode target paths |
| `tests/platform_matrix/test_windows_safe_contracts.py` | Portable modes, physical files, worktree meta equivalents |
| `tests/platform_matrix/summaries/.gitignore` | Ignore generated `*.json` |
| `tests/platform_matrix/summaries/README.md` | Summary artifact docs |
| `tests/platform_matrix/LANE_A_RESULT.md` | This handoff |

**Not edited:** `scripts/ide_development/**` (installer production), other lanes, PR #49, credentials, billing, live GitHub settings.

## Coverage mapping

Discovers existing `scripts/ide_development_tests` (install/update/plan/dry-run/drift/verify/version/rollback/locking/spaces/worktree/physical/symlink) and adds matrix supplements for:

- **Unicode + spaces** consumer roots and path join/backup encoding
- **Windows-safe modes** (no pretending POSIX mode bits on win32)
- **True cross-process contention on Windows** (existing suite skips win32 fcntl proof)
- **Physical-file / worktree** equivalents when symlink privilege is absent

## Platform exclusions (Windows without symlink privilege)

When `os.symlink` cannot create file symlinks on Windows, `exclusions.py` skips symlink-creation tests from `ide_development_tests` and pairs each with an equivalent in `test_windows_safe_contracts.py`. On this Darwin host, symlink privilege is available → **no exclusions applied** (`exclusions: []` in summary).

## Known gaps

1. **Ubuntu/Windows CI not executed from this lane session** — workflow is ready; lead push to `issue/**` must confirm `ubuntu-latest` / `windows-latest` green. Do not claim those platforms passed until CI artifacts exist.
2. **Shell suites** (bash verify scripts) are intentionally out of scope for this Python matrix entrypoint on Windows; macOS/Linux continue via other workflows (`ci.yml` / verify scripts).
3. **Existing `test_rollback_restores_bytes_and_modes`** still compares POSIX `stat.S_IMODE` inside `ide_development_tests` (cannot edit without leaving owned paths). Matrix adds portable equivalent; if Windows CI fails on the legacy assertion, lead should reassign a Track-2 hardening edit — Lane A did not modify installer or existing unit tests.
4. **No paid/self-hosted runners** used or configured.

## Blockers

None for Darwin local matrix. External: awaiting first CI matrix run on Ubuntu + Windows after lead checkpoints/pushes the issue branch.

## Exact commands / exit codes

```bash
# Primary
python3 scripts/run_cross_platform_matrix.py
# → exit 0; Ran 59 tests; OK

# Quiet confirmation
python3 scripts/run_cross_platform_matrix.py -q
# → exit 0

# Underlying discovery (also covered by entrypoint)
PYTHONPATH=scripts python3 -m unittest discover -s scripts/ide_development_tests -v
# → exit 0; Ran 46 tests; OK (pre-matrix baseline)
```
