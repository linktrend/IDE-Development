# Lane E Result — security / fail-closed / recovery acceptance

**Issue:** #67 Work Packet 1
**Lane:** E
**Model:** cursor-grok-4.5-high
**Date:** 2026-08-02
**Scope:** disposable fixtures only; no live deletion/cleanup apply/GitHub mutation/credentials

## Runner

```bash
python3 tests/security_acceptance/run_tests.py
# unittest discover:
PYTHONPATH=scripts:tests/security_acceptance python3 -m unittest discover -s tests/security_acceptance -p 'test_*.py'
# bridge suite:
PYTHONPATH=scripts python3 -m unittest scripts.ide_development_tests.test_security_adversarial
```

## Summary

| Metric | Value |
|--------|------:|
| Primary suite tests | 58 |
| Passed | 57 (+ lead fixes → 57 pass / 1 skip) |
| Failed | 0 |
| Errors | 0 |
| Skipped | 1 (Windows junction — Darwin runner) |
| Adversarial bridge | 10/10 pass |
| Production code patched by Lane E | **No** (owned paths only) |
| Production defects fixed by lead | DEFECT-E1, E2, E3 |

**Verdict:** Lane E acceptance suite **PASS** with 1 platform skip. Lead reproduced and fixed three must-fix installer defects after integration; security suite re-run OK.

## Exit-code contract exercised

| Code | Constant | Refusal class |
|-----:|----------|---------------|
| 0 | `EXIT_OK` | success |
| 1 | `EXIT_ERROR` | unexpected / corrupt journal JSON |
| 10 | `EXIT_DRIFT` | managed drift |
| 11 | `EXIT_CONFLICT` | symlink / unknown content / path escape / lock / markers |
| 12 | `EXIT_INVALID_PACKAGE` | malformed manifest / hash / traversal / invalid mode / self-install |
| 13 | `EXIT_ROLLBACK_FAILURE` | missing tx / incomplete journal / missing backups |

## Case matrix (post-lead-fix expectations)

| ID | Case | Expected exit | Result | Notes |
|----|------|--------------:|--------|-------|
| P01–P10 | Path/symlink escapes | fail-closed | PASS | P07 now InvalidPackage 12 |
| P11 | Windows junction escape | — | SKIP | win32-only |
| M01–M09, M12 | Manifest adversarial | fail-closed | PASS | |
| M10 | Mode `rwxr` | 12 | PASS | lead fix E2 |
| M11 | Mode `999` | InvalidPackage | PASS | lead fix E2 |
| R01–R06 | Lock/recovery | fail-closed | PASS | |
| C01–C04 | Consumer/markers | fail-closed | PASS | |
| S01–S04 | Repo-scope evidence | refuse/mismatch | PASS | no live apply |
| N01–N05 | No secrets/host paths | clean/detect | PASS | |
| J01–J05 | CLI JSON refusals | deterministic | PASS | J04 includes exitCode (E1) |

## Lead-resolved defects

1. **E1** — `run_rollback` failure payload now includes `exitCode`.
2. **E2** — `normalize_mode` refuses non-octal modes as `InvalidPackageError`.
3. **E3** — package source symlink checked via `join_under_nofollow` before resolve → `InvalidPackageError` (12).

## Owned paths written

- `tests/security_acceptance/**`
- `scripts/ide_development_tests/test_security_adversarial.py`
- `scripts/ide_development_tests/fixtures/security/**`

## Explicit non-actions (Lane E)

- No commit / push / PR
- No live GitHub/cleanup apply
- No credentials used or created
