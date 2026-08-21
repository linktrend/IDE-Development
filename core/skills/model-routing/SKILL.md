---
name: model-routing
description: >-
  Select and spawn the correct IDE Development model-routing subagent for a
  task. Ports LiNKdeveloper packages/model-routing router.ts route criteria and
  escalation pairing so the two systems cannot drift.
version: 2.5.1
status: active
tags: [routing, models, subagents, escalation]
source_of_truth: LiNKdeveloper/packages/model-routing/src/router.ts
---

# Model routing (Cursor Desktop)

This skill restores/backfills an original mandatory Coding Execution Protocol
requirement omitted or incorrectly implemented in the prior routing baseline;
it is not a new feature, optional improvement, or rollout-created policy.

IDE Development has no persistent Ledger process. Model routing is enforced by
**pinned custom subagents** under `.cursor/agents/route-*.md` plus this skill's
agent-followed doctrine.

## Subagents (one per route)

| Route ID | Subagent file | Model slug |
|---|---|---|
| `auto_cost` | `.cursor/agents/route-default.md` | `cursor-auto-cost` (`auto-smart`, `optimize_for=cost`) |
| `composer` | `.cursor/agents/route-economical.md` | `composer-2.5` (Fast=false) |
| `grok` | `.cursor/agents/route-escalation.md` | `cursor-grok-4.6-medium` (Fast=false) |
| `specialist` | `.cursor/agents/route-specialist.md` | `gpt-5.6-sol-medium` (Fast=false) |
| `independent_review` | `.cursor/agents/route-independent-review.md` | `claude-opus-4-8-thinking-medium` |
| `bulk_documents` | `.cursor/agents/route-bulk-documents.md` | `gemini-3.7-flash-medium` (Fast=false) |

Spawn the matching subagent (Task tool / `/route-*`) rather than doing the work
on an unpinned parent model when a route clearly applies.

## Route selection (criteria verbatim from router.ts)

### auto_cost — Cursor Auto Cost

- normal coding, repository analysis, debugging, refactoring, testing, documentation, plans and ordinary research
- use only when `optimize_for=cost` (or an equivalent account/team Auto Cost setting) is explicitly selectable and independently read back
- retain the effective model id, display name, params and usage pool returned by Cursor
- Cloud API `id=default`, `displayName=Auto` without mode proof is generic Auto and is not accepted as Auto Cost

### composer — Composer 2.5

Use only for fully bounded, objectively verifiable, easy-to-revert work meeting every Composer checklist condition. Simple work must not select an expensive third-party route.

### grok — Cursor Grok 4.6 Medium

- new architecture, difficult/ambiguous planning, cross-system investigation or long-running/context-heavy work
- sensitive-domain analysis (auth, payments, migrations, infrastructure, deployment, financial or trading logic)
- use as the deterministic direct Cursor route when Auto Cost cannot be expressed or independently proven
- Fast must be false

### specialist — documented third-party exception

Use Sol or another third-party model only when the packet records a specific capability, security, independence or actual 1M-context requirement that Auto Cost/Composer/Grok cannot satisfy. Record the reason, exact selection and readback; availability alone is not a reason.

### independent_review — Opus 4.8 Medium

- security review
- authorization and authentication review
- final review of consequential changes
- migration, payment, infrastructure or trading-risk review
- independent challenge of an architecture or large implementation
- Run as a SEPARATE review task. The reviewer must receive the original request, approved scope, plan, complete diff, tests and known risks.

### bulk_documents — Gemini 3.7 Flash Medium

- large-volume classification or extraction
- very large document collections
- PDF, image or multimodal classification
- repetitive structured synthesis across many files
- use only for a task-justified bulk-document role with the exact selector `gemini-3.7-flash-medium`; Fast must be false
- Require a representative sample review before processing the full collection. Never move, rename or delete files based solely on unreviewed classification output.

## Escalation-on-failure protocol (Principal-approved)

When a route's model fails with a **model-quality** signal
(`code_defect`, `quality_gate_failed`, or a **recurring** `timeout_uncertain`):

1. **Log** the attempt: route id, model slug, failure class/reason, timestamp —
   into the active Issue proof artifact or session note (no silent skip).
2. **Retry once** with the paired different-family route:

| Failed route | Retry route |
|---|---|
| `auto_cost` | `grok` |
| `composer` | `auto_cost` (only if Auto Cost can be attested) |
| `grok` | `specialist` only with a documented exception |
| `bulk_documents` | `auto_cost` (only if Auto Cost can be attested) |
| `specialist` | *(none — surface to repair)* |
| `independent_review` | *(none — surface to repair)* |

3. Cap at **one hop**. A second failure surfaces to the Principal / repair —
   do not keep trying models until one works.
4. Infrastructure/input failures (not model-quality) use same-model retry rules
   instead of this pairing table.

This protocol is agent-followed doctrine (IDE Development has no Ledger process
to mechanize it). Skipping the log step or the different-family retry is a
routing violation.
