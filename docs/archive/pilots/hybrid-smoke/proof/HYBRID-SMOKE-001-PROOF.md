---
proof_id: "HYBRID-SMOKE-001-PROOF"
subject_type: "issue"
subject_id: "HYBRID-SMOKE-001"
issue_status_at_proof: "review_ready"
---

# Proof — HYBRID-SMOKE-001

## What changed

| File | Change |
|------|--------|
| `docs/LINKDEVELOPER-WORKSPACE-OPERATOR-GUIDE.md` | Added hybrid registry to Key docs; Section 7 rewritten to state gstack and mattpocock are installed/wired with local clone paths |

## Before / after

**Before:** Key docs lacked hybrid registry link. Section 7 cited deleted skills (`browser-qa`, `release-readiness`) and did not state clone paths.

**After:** Key docs includes `docs/HYBRID-SKILLS-REGISTRY.md`. Section 7 lists 40 local domain skills plus installed gstack and mattpocock clones with fork URLs.

## Verification method

1. Opened operator guide and confirmed Key docs entry.
2. Confirmed `docs/HYBRID-SKILLS-REGISTRY.md` exists.
3. Confirmed hybrid command entrypoints exist under `core/commands/hybrid-*.md`.
4. Issue status set to `review_ready` before review.

## Acceptance criteria check

| Criterion | Met |
|-----------|-----|
| Key docs lists hybrid registry | yes |
| Section 7 describes installed/wired hybrid | yes |

## Hybrid routing evidence

- PRD: `core/pilots/hybrid-smoke/PRD.md`
- Trigger 2 path: grill → approve → to-issues → small-change
- Registry: `docs/HYBRID-SKILLS-REGISTRY.md`
