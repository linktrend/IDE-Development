# Copy-First UI Reskin Policy

**Status:** Active for LiNKdeveloper Stage 1 (semi-manual)  
**Date:** 2026-07-10  
**Authority:** Carlos/Lisa locked decision (Stage 1b)  
**Applies to:** Application Factory and other factories using LiNKapps starter kits in Stage 1

## Policy statement

Application Factory UI work **clones proven app UI/UX from an approved reference** and changes **look and feel only**. Greenfield AI codegen of UI/UX per app is **prohibited** in Stage 1 semi-manual operation.

## What this means

### Required approach

1. **Start from an approved reference** — typically the LiNKapps starter kit (`starter_linkapps_fullstack` or another kit explicitly approved in architecture/reuse decisions).
2. **Preserve structure** — navigation patterns, page layout, component hierarchy, and interaction flows come from the reference implementation.
3. **Reskin, don't reinvent** — apply branding through:
   - design tokens (color, typography, spacing)
   - theme variables and CSS/Tailwind configuration
   - media assets (logos, icons, imagery)
   - copy and content within existing layout slots
4. **Document the reference** — record which starter kit or proven app UI was cloned and what was changed in the module/issue artifacts (per IDE Development proof and review gates).

### Prohibited in Stage 1

- Generating a new UI layout, component tree, or interaction model from scratch via AI for each app
- Replacing the starter kit's proven UX with an agent-invented alternative without documented Principal approval
- Shipping UI that cannot trace back to an approved reference surface

### Allowed deviations

Deviations from the default starter kit UI source require **documented approval** before implementation issues enter `ready` state:

- Principal or designated approver records the exception in architecture or module artifacts
- The replacement reference (another proven app, pattern extract, or approved design spec) is named explicitly
- Proof for UI work includes comparison to the approved reference, not only agent confidence

## Default UI source

**LiNKapps starter kit** is the default UI source for Application Factory builds. Clone mechanics use `LiNKapps/scripts/create-app-repo.sh` per `STARTER_KIT_AND_REUSE_POLICY.md` (LiNKdeveloper Stage 2 reference).

Reuse decisions allowed by that policy include *use starter kit* and *extract pattern only* — this document makes the Stage 1 interpretation explicit: extract pattern means copy structure and reskin, not regenerate.

## Relationship to IDE Development gates

This policy does not override canonical workflow gates. UI work still flows through:

`Issue → Proof → Review → Integration → Complete`

Reviewers should reject UI proof that shows greenfield codegen without an approved reference trail.

## Stage 2 revision

LiNKdeveloper Stage 2 (autonomous orchestrator) may revise this policy with updated governance. Any Stage 2 change must remain explicit, approved, and documented — not implied by tooling defaults.

## Quick reference (quotable)

> Clone proven UI. Change look and feel. Do not greenfield AI-codegen UI per app in Stage 1.
