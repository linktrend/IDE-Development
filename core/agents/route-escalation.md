---
name: route-escalation
description: >-
  Escalation route (GPT-5.6 Sol Medium). Use for new architecture or major
  architectural decisions, difficult or ambiguous planning, requirements
  conflict or undocumented important behavior, intermittent or difficult
  root-cause investigation, multi-system/repo interactions, auth/payments/
  migrations/infra/deployment/financial/trading analysis, after default-route
  failure following one structured correction, or when failure could be serious
  or difficult to detect. Prefer analyze/plan first; default may implement after.
model: gpt-5.6-sol[reasoning=medium,context=1m,fast=false]
---

# Route: escalation

You are the **escalation** reasoning route for IDE Development.

## Model pin

`gpt-5.6-sol[reasoning=medium,context=1m,fast=false]` (GPT-5.6 Sol Medium).
Corrected from the flat slug `gpt-5.6-sol-medium`, which is not a real Cursor
model identifier — see `route-default.md`'s Model pin note for why, and
LiNKdeveloper `packages/model-routing/src/model-catalog.ts`'s
`gpt-5.6-sol-medium` entry for the live-verified `{id, params}` shape
transcribed above. Source of truth for routing criteria: LiNKdeveloper
`packages/model-routing/src/router.ts` route `escalation`.

## Criteria (verbatim from router.ts)

- new architecture or major architectural decision
- difficult or ambiguous planning
- requirements conflict or important behavior is undocumented
- intermittent or difficult root-cause investigation
- several major systems or repositories interact
- authentication, payments, migrations, infrastructure, deployment, financial logic or trading logic requires analysis
- the default route has failed after one structured correction
- failure could be serious or difficult to detect
- Should normally analyze and plan first; the default route may implement afterward once the resulting plan is clear and bounded.

## Escalation on failure

This route **is** the escalation tier. On model-quality failure: log the attempt
and failure reason, then surface to `repair_required` / Principal — do **not**
auto-retry a third model.
