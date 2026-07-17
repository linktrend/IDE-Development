# Hybrid Feature — Minimal PRD (Smoke Test)

**Product:** LiNKdeveloper hybrid skills verification pilot  
**Author:** Carlos (simulated)  
**Date:** 2026-07-10  
**Status:** Approved for smoke execution

## Problem

Operators need a single place to discover that hybrid gstack and mattpocock skills are installed, not reference-only.

## Solution

Add the hybrid skills registry to the operator guide Key docs list so Carlos can find fork URLs and trigger routing from the primary operator entrypoint.

## Acceptance criteria

- Operator guide Key docs section includes `docs/HYBRID-SKILLS-REGISTRY.md`
- Change is doc-only, low risk
- Full gate discipline: issue → proof → review → integration

## Out of scope

- Code changes
- Factory infrastructure
- LiNKdev restoration

## Routing (Trigger 2 simulation)

1. `/grill-with-docs` — no gaps; PRD is complete
2. Carlos approves (simulated)
3. `/to-issues` — one issue: HYBRID-SMOKE-001
4. Execute doc change with Layer 1 SMALL-CHANGE path
