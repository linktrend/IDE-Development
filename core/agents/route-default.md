---
name: route-default
description: >-
  Default model route (Sonnet 5 Medium). Use for normal and complex coding,
  feature development, repository analysis, debugging with a reasonably clear
  cause, refactoring, testing, documentation, PRDs and implementation plans,
  research/writing/data analysis that are not unusually consequential.
  If no special routing condition applies, use this route.
model: claude-sonnet-5[thinking=true,effort=medium,context=1m]
---

# Route: default

You are the **default** execution route for IDE Development.

## Model pin

`claude-sonnet-5[thinking=true,effort=medium,context=1m]` (Sonnet 5 Medium).
Per [Cursor's subagent docs](https://cursor.com/docs/subagents), the `model:`
field takes a base model ID plus `[id=value,...]` bracket parameters — flat
suffixed strings like `claude-sonnet-5-thinking-medium` are not a format
Cursor's frontmatter (or its SDK) understands; that flat form is
LiNKdeveloper's own internal routing-policy naming convention (its *route
name* for readability), not a real model identifier anywhere. The bracket
params above are transcribed directly from LiNKdeveloper
`packages/model-routing/src/model-catalog.ts`'s `claude-sonnet-5-thinking-medium`
entry, which that file's own docstring says was ground-truth-checked against
a live `Cursor.models.list()` call for this account on 2026-07-16 — trust
that file's `{id, params}` shape over any flat slug seen elsewhere. Source of
truth for routing *criteria*: LiNKdeveloper
`packages/model-routing/src/router.ts` route `default`.

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
