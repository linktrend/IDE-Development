# Lane D — `.gitignore` diff notes

**Before:** 15-line ignore covering OS/env/node build basics, `__pycache__/`, `.linktrend/`, and `core/library/.cache/`.

**After:** Grouped, explicit ignore set aligned with RC packager exclusions and acceptance A5.

## Kept (already present)

- `.DS_Store`, `.env`, `.env.*`, `node_modules/`, `dist/`, `build/`, `.next/`, `.cache/`
- `.vscode/`, `.idea/`, `*.log`
- `__pycache__/`, `.linktrend/`, `core/library/.cache/`

`build/` continues to cover release-candidate outputs (`build/release-candidate/` per `RC_BUILD_DIR_REL`).

## Added

| Category | Patterns | Why |
|----------|----------|-----|
| OS | `Thumbs.db`, `ehthumbs.db`, `Desktop.ini` | Windows junk not previously listed |
| Env exceptions | `!.env.example`, `!.env.*.example` | Prior `.env.*` blocked committing env *examples* (LiNKsites pattern) |
| Frontend caches | `.turbo/`, `.parcel-cache/`, `.vercel/` | Common generated tooling dirs |
| Python bytecode/packaging | `*.py[cod]`, `*$py.class`, `*.egg`, `*.egg-info/`, `.eggs/`, `.Python`, `pip-wheel-metadata/` | Match RC exclude + std packaging debris |
| Venvs | `.venv/`, `venv/`, `ENV/` | Local interpreters must not ship |
| Test/type/lint/coverage | `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `.tox/`, `.nox/`, `.hypothesis/`, `.coverage`, `.coverage.*`, `coverage/`, `coverage.xml`, `htmlcov/`, `.dmypy.json`, `dmypy.json` | Mission-listed gaps; were absent |
| Editor temp | `*.swp`, `*.swo`, `*~` | Vim/emacs scratch |
| File junk | `*.tmp`, `*.temp`, `*.bak`, `*.orig`, `*.rej` | Patch/merge/temp debris; RC already excludes `.tmp`/`.swp` |
| A5 | `.superpowers/` | Acceptance matrix forbidden artifact |

## Intentionally not ignored

| Path / pattern | Reason |
|----------------|--------|
| `docs/archive/**`, `docs/evidence/**` | Legitimate evidence (Lane B / historical WP packets) |
| `tests/**/fixtures/**`, `scripts/**/fixtures/**` | Required test payloads |
| `core/managed-core/**` | Package source |
| `tests/platform_matrix/summaries/.gitignore` | Nested rule already ignores generated `*.json` while keeping `README.md` |
| `*.rc` under evidence | Exit-code proof files, not shell rc configs |

## Validation

`git check-ignore -v` confirmed intended ignores for representative paths; `.env.example` / `.env.*.example` negate correctly; **0** currently tracked files flagged as newly ignore-matched junk.
