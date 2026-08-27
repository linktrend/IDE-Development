# Module: scripts/ide_development

[← Back to INDEX](../../INDEX.md)

**Type:** python | **Files:** 20

**Entry point:** `scripts/ide_development/__init__.py`

## Files

| File | Lines | Large |
| ---- | ----- | ----- |
| `scripts/ide_development/__init__.py` | 9 |  |
| `scripts/ide_development/__main__.py` | 10 |  |
| `scripts/ide_development/app_canary.mjs` | 167 |  |
| `scripts/ide_development/build_manifest.py` | 1360 | 📊 |
| `scripts/ide_development/cli.py` | 310 |  |
| `scripts/ide_development/constants.py` | 114 |  |
| `scripts/ide_development/engine.py` | 586 | 📊 |
| `scripts/ide_development/errors.py` | 38 |  |
| `scripts/ide_development/hashing.py` | 118 |  |
| `scripts/ide_development/io_atomic.py` | 105 |  |
| `scripts/ide_development/lock.py` | 144 |  |
| `scripts/ide_development/manifest.py` | 334 |  |
| `scripts/ide_development/markers.py` | 97 |  |
| `scripts/ide_development/paths.py` | 175 |  |
| `scripts/ide_development/plan.py` | 857 | 📊 |
| `scripts/ide_development/release_candidate.py` | 1025 | 📊 |
| `scripts/ide_development/resolution.py` | 278 |  |
| `scripts/ide_development/state.py` | 131 |  |
| `scripts/ide_development/symlink_migrate.py` | 154 |  |
| `scripts/ide_development/transaction.py` | 680 | 📊 |

## Documentation

- [outline.md](outline.md) - Symbol maps for large files
- [imports.md](imports.md) - Dependencies

---

| High 🔴 | Medium 🟡 | Low 🟢 |
| 1 | 0 | 0 |

## 🔴 High Priority

### `RULE` (scripts/ide_development/io_atomic.py:45)

> refuses overwriting symlink paths (even though replace would not follow).
