# Issue #72 validation checklist (lead)

Run after A–E integration; no silent required skips.

## Structural

- [ ] `git diff --check`
- [ ] Every moved/deleted path audited for inbound refs (`rg`)
- [ ] Lane B move-map applied; Lane A link-fix requests resolved
- [ ] `docs/CURRENT-STATUS.md` (or LAUNCH-READINESS) present and linked from README
- [ ] WP04 packet present, prepared/not-executed
- [ ] `docs/handoff/README.md` + `_TEMPLATE.md` still active
- [ ] Claude exclusion preserved; no consumer mutation claims of completion

## Tooling

- [ ] Manifest verify (and regenerate only via official tooling if needed)
- [ ] Documentation/reference checks used by verify
- [ ] `bash scripts/verify-ide-development.sh` (full)
- [ ] Portable v2 integration harness
- [ ] Relevant installer / adapters / gitops / cleanup tests
- [ ] Any new cleanup-specific tests

## Reviews (Lane F)

- [ ] Fresh Grok High review: docs truth
- [ ] Fresh Grok High review: dead-code safety
- [ ] Fresh Grok High review: Git hygiene disposition
- [ ] Repair valid findings ≤3 cycles

## Delivery (checkpoint only)

- [ ] Conventional commits on `issue/72-pre-launch-ide-development-codebase-cleanup-arch`
- [ ] Push branch; HEAD == origin/branch
- [ ] NO review-ready / Packager / PR / Bugbot / merge / promote / tag / consumer / GitHub cleanup apply
