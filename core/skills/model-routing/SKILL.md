---
name: model-routing
description: >-
  Select and spawn the correct IDE Development model-routing subagent for a
  task. Selects the founder-approved implementation, independent-review, and
  checkpoint-verifier routes.
version: 2.0.0
status: active
tags: [routing, models, subagents, escalation]
source_of_truth: coding-execution-protocol
---

# Model routing (Cursor Desktop)

IDE Development has no persistent Ledger process. Model routing is enforced by
**pinned custom subagents** under `.cursor/agents/route-*.md` plus this skill's
agent-followed doctrine.

## Founder-approved routes

| Route ID | Subagent file | Exact model | Use |
|---|---|---|
| `bounded_simple_implementation` | `.cursor/agents/route-default.md` | `composer-2.5` | bounded/simple implementation |
| `complex_long_implementation` | `.cursor/agents/route-escalation.md` | `cursor-grok-4.6-medium` | complex/long implementation |
| `independent_review` | `.cursor/agents/route-independent-review.md` | `cursor-grok-4.6-high` (Fast off) | separate semantic/code review |
| `checkpoint_verifier` | `.cursor/agents/route-checkpoint-verifier.md` | `gpt-5.6-luna-high` | separate exact checkpoint/evidence/scope/protocol verification |

Spawn the matching subagent (Task tool / `/route-*`) rather than doing the work
on an unpinned parent model when a route clearly applies. Review and verifier
routes are always separate from implementation.

Opus and Terra are retired as default or required routes for undispatched work.
Completed evidence recorded under those identities remains valid. Specialist
routes are selectable only with an explicit founder exception recorded in the
manifest.

## Route selection (criteria verbatim from router.ts)

### bounded_simple_implementation — Composer 2.5

- one repository and an existing implementation pattern
- bounded/simple implementation with explicit requirements
- normally no more than 3–5 changed files, objective validation, and easy rollback
- no architecture, authentication, secrets, infrastructure, deployment, or production-data decision

### complex_long_implementation — cursor-grok-4.6-medium

- complex, long-running, multi-file, architectural, difficult-debugging, or cross-system implementation
- the bounded route is not eligible or has failed one structured correction
- keep work packet-scoped and do not use this route as the reviewer or verifier

### independent_review — cursor-grok-4.6-high (Fast off)

- Run as a separate semantic/code review after implementation.
- Provide the original request, approved scope, complete diff, focused tests, and known risks.
- Fast must be explicitly false; silence or substitution is not clean.

### checkpoint_verifier — gpt-5.6-luna-high

- Run as a separate exact verifier for checkpoint commit/tree, evidence, scope, and protocol compliance.
- It must not implement the packet or replace the independent semantic/code review.
- Read back the exact model identity with Fast=false.

### Specialist exception routes

- Bulk-document, evaluation, and other specialist routes are not in the default matrix.
- They require an explicit founder exception with evidence of the capability, security, independence, or context need.

## Escalation-on-failure protocol (Principal-approved)

When a route's model fails with a **model-quality** signal
(`code_defect`, `quality_gate_failed`, or a **recurring** `timeout_uncertain`):

1. **Log** the attempt: route id, model slug, failure class/reason, timestamp —
   into the active Issue proof artifact or session note (no silent skip).
2. **Retry once** with the paired different-family route:

| Failed route | Retry route |
|---|---|---|---|
| `bounded_simple_implementation` | `complex_long_implementation` |
| `complex_long_implementation` | *(none — surface to repair)* |
| `independent_review` | *(none — surface to repair)* |
| `checkpoint_verifier` | *(none — surface to repair)* |

3. Cap at **one hop**. A second failure surfaces to the Principal / repair —
   do not keep trying models until one works.
4. Infrastructure/input failures (not model-quality) use same-model retry rules
   instead of this pairing table.

This protocol is agent-followed doctrine (IDE Development has no Ledger process
to mechanize it). Skipping the log step or the different-family retry is a
routing violation.
