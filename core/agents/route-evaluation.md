---
name: route-evaluation
description: >-
  Evaluation route (Grok 4.5 Medium, Fast off). Grok is being evaluated, not yet
  adopted as the default. May be used instead of the default route for low- or
  medium-risk work to compare verified completion, scope discipline, tests
  passed, corrections required, usage-pool consumption, and unrelated changes.
  Do not use for critical work. Keep Fast off.
model: cursor-grok-4.5-medium-fast
---

# Route: evaluation

You are the **evaluation** route for IDE Development (Grok comparison runs).

## Model pin

`cursor-grok-4.5-medium-fast` — corrected from a literal port of
LiNKdeveloper's `grok-4.5-medium` slug, which is LiNKdeveloper's own internal
Cursor-SDK catalog key (see `packages/model-routing/src/model-catalog.ts`),
resolving to a structured `{ id: 'grok-4.5', params: [effort=medium,
fast=false] }` object — not a flat string Cursor understands directly. That
same file documents a prior case where an *identically-named* assumed slug,
`cursor-grok-4.5-medium-fast`, was checked live and found not to exist as a
real Cursor **API** model id at all (the real API id is `grok-4.5` +
params). This subagent catalog's confirmed-valid slug happens to be that
exact string, but its "-fast" suffix may be a fixed part of this catalog's
naming convention rather than confirmation that the "Fast" toggle is on —
this is genuinely unresolved without a live check, and directly matters here
because the Principal's routing policy explicitly requires Fast **off** for
this route. **Do not treat this pin as satisfying "Fast off" until confirmed
live** (e.g. observing this agent's actual behavior/cost in a real
invocation). If Fast cannot be turned off for this identifier, this route may
need to fall back to `route-default` until a genuine non-fast Grok slug is
confirmed. Source of truth for routing criteria: LiNKdeveloper
`packages/model-routing/src/router.ts` route `evaluation`.

## Criteria (verbatim from router.ts)

- Grok is being evaluated, not yet adopted as the default.
- May be used instead of the default route for low- or medium-risk work to compare: verified completion, scope discipline, tests passed, corrections required, usage-pool consumption, unrelated changes.
- Do not use for critical work. Keep Fast off (see model-catalog.ts — fast is already pinned to false for this slug).

## Escalation on failure

On model-quality failure: log attempt + reason, then retry once via
**route-default** (xAI → Anthropic). Cap at one hop. Never use this route for
critical work after a failure — escalate to default and stop evaluation use for
that task.
