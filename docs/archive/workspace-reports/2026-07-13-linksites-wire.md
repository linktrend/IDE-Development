# Workspace Adoption Report — LiNKsites

- **Date/time:** 2026-07-13, 19:41–20:05 (UTC+8)
- **Workspace root:** `/Users/linktrend/Projects`
- **System repository:** `IDE Development` (`/Users/linktrend/Projects/IDE Development`)

## Repository in scope

- **LiNKsites** — `/Users/linktrend/Projects/LiNKsites`

## Prior state (discovered)

LiNKsites had a fully embedded, separate agent framework called **LiNKdev** (`LiNKdev/` at repo root — factory, product, and `skills/gstack` trees, template-synced from `linktrend/LiNKdev` up to v1.2.4), plus repo-level wiring for it:

- `.cursor/rules/00-linkdev-bootstrap.mdc`, `.cursor/commands/linkdev-*.md` and `wire-linkdev.md`, `.cursor/agents/README.md` and `.cursor/skills/README.md` (both pointing into `LiNKdev/`)
- `.github/workflows/linkdev-guard.yml` (validated `LiNKdev/factory/STATE.md` and ran `LiNKdev/factory/scripts/verify.sh`)
- 15 GitHub labels (`linkdev:*`, `runtime:cursor`, `runtime:codex`, `tier:standard`, `tier:critical`) installed by `LiNKdev/factory/scripts/install-labels.sh`

LiNKdev's own wire session record (`LiNKdev/product/reports/wire/WIRE-SESSION.md`) showed Step A ("wire") complete as of 2026-05-31, with dispatch install (Step B) still pending. This is a **separate, unrelated prior system** — not LiNKdeveloper — that predated this adoption.

`.cursor/rules/` also carried 12 LiNKsites-local rule files (`00-identity`, `01`–`07`, `10`–`12`, `15`). On inspection, `00-identity` and `01`–`07` were verbatim/near-verbatim duplicates of LiNKdeveloper's own shared rules (identity, git branching, secrets, quality, testing, agent behavior, troubleshooting, cross-IDE handoff). `10`, `11`, `15` were short pointers that duplicated detail already documented in this repo's own `docs/` and `sites_specs/`. `12-linksites-ui-policy.mdc` contained the one genuinely unique, non-duplicated policy (the `packages/ui` vendor model and template UI conventions).

## Legacy cleanup actions taken (in LiNKsites)

1. Migrated the unique content of `12-linksites-ui-policy.mdc` into `docs/policies/UI_TEMPLATE_POLICY.md` (new file), with dangling `LiNKdev/`/LiNKaios-operator-UI references removed.
2. Folded the short pointers from `10-foundation.mdc` / `11-sites-apps.mdc` / `15-release-deploy.mdc` into root `README.md` under a new "Development Conventions" section.
3. Fixed `docs/BRANCHING_AND_DEPLOYMENT_POLICY.md` and `docs/README.md` to remove `LiNKdev/factory/SPEC.md` / `LiNKdev/factory/rules/*` citations (the branch model itself is unchanged — now cites the LiNKdeveloper-provided `.cursor/rules/01-git-branching.mdc`).
4. Deleted `LiNKdev/` (entire embedded framework) and `.github/workflows/linkdev-guard.yml`.
5. Deleted all 15 `linkdev:*` / `runtime:*` / `tier:*` GitHub labels from `linktrend/LiNKsites`.
6. Left untouched (out of scope — different repository): a fallback default path in `scripts/mvo-live-publish.sh` that points at a sibling repo's own `LiNKtrend-System/LiNKdev/...` report folder. That is a different repo's system, not LiNKsites'.

## Wiring performed

```
./scripts/wire-repo.sh /Users/linktrend/Projects/LiNKsites
```

- Backed up the pre-existing `.cursor/` to `LiNKsites/.cursor-backup-20260713-200111/` (20 files: the LiNKdev shim files from step 4 above, plus the 12 local rule files from step 1–2 above).
- Created `LiNKsites/.cursor` as a relative symlink to `../IDE Development/.cursor`.
- Verified `.cursor/README.md`, `.cursor/execution/INDEX.yaml`, `.cursor/templates/INDEX.yaml`, `.cursor/commands/INDEX.yaml`, and `.cursor/rules/00-bootstrap.mdc` all reachable from LiNKsites.
- Backup folder was reviewed file-by-file (see above) and then deleted — every file was either a removed LiNKdev shim or content already migrated into `docs/`/`README.md` in this same session, so nothing was lost by deleting it.

## Repositories skipped / left untouched

None in this session — only LiNKsites was in scope for this adoption.

## Verification results

- `git status --porcelain` in LiNKsites shows only the expected deletions (`LiNKdev/**`, `.github/workflows/linkdev-guard.yml`, old `.cursor/*` files replaced by the symlink) and additions (`docs/policies/UI_TEMPLATE_POLICY.md`, edits to `README.md`, `docs/README.md`, `docs/BRANCHING_AND_DEPLOYMENT_POLICY.md`).
- Repo-wide case-insensitive scan for `linkdev` in LiNKsites returns only the string "LiNKdeveloper" (the correct system name) in `docs/BRANCHING_AND_DEPLOYMENT_POLICY.md`, plus the one out-of-scope sibling-repo path noted above.
- `gh label list` on `linktrend/LiNKsites` shows zero `linkdev:*`/`runtime:*`/`tier:*` labels remaining.

## Rollback notes

- To roll back: `git checkout -- .` in LiNKsites restores all deleted/edited files from git history (LiNKdev was tracked in git prior to this session, so `git log` retains full history even though the working tree backup was deleted).
- The `.cursor` symlink can be removed and replaced by re-checking out the prior `.cursor/` tree from git history if LiNKdeveloper wiring ever needs to be reversed.
- GitHub labels are not recoverable via git; re-run `LiNKdev/factory/scripts/install-labels.sh` from a checked-out prior commit if ever needed (not expected).
