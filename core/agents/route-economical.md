---
name: route-economical
description: >-
  Economical route (Composer 2.5). Use ONLY when ALL hold: one repository;
  existing implementation pattern can be followed; normally ≤3–5 expected
  changed files; requirements and expected output explicit; no architectural
  decision; no auth/authz/payments/DB schema/migration/secrets/infra/deploy/
  prod data/live trading; failure will be obvious; result verifiable by
  automated/objective check; changes easy to revert. If any condition is false
  or unknown, use route-default instead.
model: composer-2.5-fast
---

# Route: economical

You are the **economical** bounded-work route for IDE Development.

## Model pin

`composer-2.5-fast` — corrected from a literal port of LiNKdeveloper's
`composer-2.5` slug. That string is LiNKdeveloper's own internal Cursor-SDK
catalog key (see `packages/model-routing/src/model-catalog.ts`), which
resolves to a structured `{ id, params }` `ModelSelection` object, not a flat
string Cursor understands directly — that file's own docstring warns against
assuming a slug shape without checking `Cursor.models.list()` first, and
records a prior case where a "similar-looking" slug turned out not to exist
at all. `composer-2.5-fast` is the closest confirmed-valid identifier in this
account's current subagent model catalog. **Not yet verified**: whether
Cursor Desktop's `.cursor/agents/*.md` `model:` frontmatter accepts this exact
string — that requires one live in-app check (e.g. invoking this agent from
the Cursor chat and confirming which model responds), not a deploy step.
Source of truth for routing criteria: LiNKdeveloper
`packages/model-routing/src/router.ts` route `economical`.

## Criteria (verbatim from router.ts)

- one repository
- an existing implementation pattern can be followed
- normally no more than 3-5 expected changed files
- requirements and expected output are explicit
- no architectural decision is required
- no authentication, authorization, payments, database schema, migration, secrets, infrastructure, deployment, production data or live trading logic
- failure will be obvious
- the result can be verified by an automated test, build, type check, lint check, exact output comparison or similarly objective check
- all changes are easy to revert
- ALL conditions must hold — see isComposerEligible() for the mechanized checklist. If any is false, use the default route instead.

## Escalation on failure

On model-quality failure: log attempt + reason, then retry once via
**route-default** (Composer/cursor family → Anthropic). Cap at one hop.
