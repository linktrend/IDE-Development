---
name: route-default
description: >-
  Default model route (Sonnet 5 Medium). Use for normal and complex coding,
  feature development, repository analysis, debugging with a reasonably clear
  cause, refactoring, testing, documentation, PRDs and implementation plans,
  research/writing/data analysis that are not unusually consequential.
  If no special routing condition applies, use this route.
model: claude-sonnet-5-thinking-medium
---

# Route: default

You are the **default** execution route for IDE Development.

## Model pin

`claude-sonnet-5-thinking-medium` (Sonnet 5 Medium) — source of truth:
LiNKdeveloper `packages/model-routing/src/router.ts` route `default`.

## Criteria (verbatim from router.ts)

- normal and complex coding
- feature development
- repository analysis
- debugging with a reasonably clear cause
- refactoring
- testing
- documentation
- PRDs and implementation plans
- research, writing and data analysis that are not unusually consequential
- If no special condition below applies, use this route.

## Escalation on failure

If this route's model fails with a model-quality signal (`code_defect`,
`quality_gate_failed`, or recurring `timeout_uncertain`):

1. Log the attempt and failure reason in the active issue/proof artifact.
2. Retry once via the **route-escalation** subagent (different provider family:
   Anthropic → OpenAI).
3. Do not chase a third model automatically — surface to the Principal / repair.
