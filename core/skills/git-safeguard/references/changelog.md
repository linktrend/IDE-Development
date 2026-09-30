# Changelog

## v1.1.0 - 2026-07-15
- Adopted `format_profile: simple` (right-sized template, catalog-eval-telemetry-spec §5).
- Removed the persistence block and task-state machinery this stateless single-pass gate never used; replaced the full Decision Tree with a short Preconditions list.
- Kept the CLI-first tooling protocol, the mandatory safety checklist, input/output contracts, and the mandatory Phase 5 ledger/telemetry append.

## v1.0.0 - 2026-02-24
- Added mandatory pre-push safety checklist.
- Enforced `git status` and `git diff --cached` before push.
