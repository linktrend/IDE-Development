---
name: intelligent-routing
description: Select the smallest appropriate command, skill, artifact path, and agent role for a task.
version: 1.0.0
status: active
tags: [routing, skills, commands, agents]
source_adapted_from:
  - link-antigravity-kit/.codex/skills/intelligent-routing
---

# Intelligent Routing

Use this skill when deciding how the system should handle a request.

## Routing Order

1. Determine whether the request is discovery, planning, execution, review, integration, session, or workspace adoption.
2. Select the smallest command path.
3. Select only relevant skills.
4. Select agent roles only as resources, not as the control structure.
5. Load only required artifacts.

## Common Routes

- ambiguous greenfield: discovery and interview
- significant new work: `plan-program` or `plan-module`
- tiny bounded work: `small-change`
- ready issue: `execute-issue`
- evidence check: `review-issue`
- accepted work: `integrate-issue`
- resume: session lifecycle
- workspace wiring: workspace adoption

## Rules

- Do not over-plan trivial work.
- Do not skip proof, review, or integration for speed.
- Do not choose multiple overlapping skills when one is enough.
- Do not treat specialist agents as sequence drivers.
- Record blockers when routing cannot proceed.

## Output

- selected command
- selected skill or skills
- active artifact level
- required reads
- reason for route

## Progressive Disclosure

Read indexes first. Stop once the correct route is clear.
