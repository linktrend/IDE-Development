# Lane D — Release Candidate Result (WP-01)

**Status:** RC created (not published)
**Package version target:** `2.1.0`
**Source commit:** `f15c8ec4dfc4fffc6b97eb25d6ad3fd99d4747a4`
**Generated (UTC):** 2026-08-02T09:04:59Z

## Commands

```bash
python3 scripts/ide-development.py release-candidate create --json
python3 scripts/ide-development.py release-candidate verify \
  --archive build/release-candidate/ide-development-managed-core-2.1.0.tar.gz --json
```

## Identity

| Field | Value |
|---|---|
| `packageVersion` | `2.1.0` |
| `manifestHash` | `sha256:3ff2178d434e7a61e4b152bda8991a71759be6c31da2a497246d003b398fc75f` |
| tar.gz path | `build/release-candidate/ide-development-managed-core-2.1.0.tar.gz` |
| tar.gz sha256 | `sha256:add0529545b504d42402f4c90f0273a0c5551399d34059e1e1dbc3b86831a501` |
| zip path | `build/release-candidate/ide-development-managed-core-2.1.0.zip` |
| zip sha256 | `sha256:7ac81dc416419cdade7d0bc3b7fb1438f7b45c5d5ade46adaef451b259847ccf` |
| install verify | `installedVersion=2.1.0`, exit 0 |

## Notes

- Archives live under ignored `build/release-candidate/` (not committed).
- Machine-readable copies under `docs/validation/wp01-phase-delivery/`.
- Publication is **not** performed by the implementer; authorized release mechanism only after independent PASS.
- Fail closed: Version ≠ `2.1.0` / root↔managed drift → exit `12`.
