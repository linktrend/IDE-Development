---
name: route-evaluation
description: >-
  Evaluation route (Grok 4.5 Medium, Fast off). Grok is being evaluated, not yet
  adopted as the default. May be used instead of the default route for low- or
  medium-risk work to compare verified completion, scope discipline, tests
  passed, corrections required, usage-pool consumption, and unrelated changes.
  Do not use for critical work. Keep Fast off.
model: grok-4.5[effort=medium,fast=false]
---

# Route: evaluation

You are the **evaluation** route for IDE Development (Grok comparison runs).

## Model pin

`grok-4.5[effort=medium,fast=false]` (Grok 4.5 Medium, Fast off). An earlier
version of this file pinned `grok-4.5-medium` and then "corrected" it to
`cursor-grok-4.5-medium-fast`, both wrong: the former is LiNKdeveloper's flat
internal routing-name (not a Cursor identifier); the latter came from
confusing a *different* system's (Task-tool subagent spawning) slug list with
this frontmatter's actual format, and its baked-in "-fast" suffix would have
directly violated the Principal's explicit Fast-off requirement for this
route. The real Cursor model id is `grok-4.5` with a separate `fast` boolean
param — LiNKdeveloper `packages/model-routing/src/model-catalog.ts`'s own
docstring documents this exact confusion happening once before and explicitly
warns against assuming a slug shape without a live `Cursor.models.list()`
check; its `grok-4.5-medium` entry (`{ id: 'grok-4.5', params: [effort=medium,
fast=false] }`) is that live-verified shape, transcribed above with `fast`
explicitly `false`. Source of truth for routing criteria: LiNKdeveloper
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
