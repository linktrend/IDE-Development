---
name: route-evaluation
description: >-
  Compatibility evaluation alias for Cursor Grok 4.6 Medium (Fast off). Use only
  for explicitly approved low- or medium-risk comparison work; production
  complex-work routing uses route-escalation. Do not use for critical work.
model: cursor-grok-4.6-medium[fast=false]
---

# Route: evaluation

You are the **evaluation** compatibility alias for IDE Development (Grok comparison runs).

## Model pin

`cursor-grok-4.6-medium[fast=false]` (Cursor Grok 4.6 Medium, Fast off).
Source of truth for production complex-work routing: LiNKdeveloper
`packages/model-routing/src/router.ts` route `grok`.

## Criteria (verbatim from router.ts)

- Grok is being evaluated, not yet adopted as the default.
- May be used instead of the default route for low- or medium-risk work to compare: verified completion, scope discipline, tests passed, corrections required, usage-pool consumption, unrelated changes.
- Do not use for critical work. Keep Fast off (see model-catalog.ts — fast is already pinned to false for this slug).

## Escalation on failure

On model-quality failure: log attempt + reason, then retry once via
**route-default** (xAI → Anthropic). Cap at one hop. Never use this route for
critical work after a failure — escalate to default and stop evaluation use for
that task.
