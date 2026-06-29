---
name: task-decomposition
description: Decompose complex or ambiguous work into atomic, dependency-aware issues with testable verification.
version: 1.0.0
status: active
tags: [planning, decomposition, issues, dependencies]
source_adapted_from:
  - LiNKskills/skills/task-decomposition
related_templates:
  - core/templates/PROGRAM.md
  - core/templates/MODULE.md
  - core/templates/PHASE.md
  - core/templates/ISSUE.md
---

# Task Decomposition

Use this skill when a request is too large, ambiguous, or multi-step to execute as one issue.

## Use When

- a feature spans multiple files, systems, or roles
- dependencies must be ordered before coding starts
- acceptance criteria are not yet atomic
- a module or phase needs issue-level execution structure

Do not use this skill for tiny low-risk changes that fit `small-change`.

## Output Shape

- objective
- scope and out-of-scope boundaries
- issue list
- dependency graph
- acceptance criteria per issue
- proof requirement per issue
- blockers or open decisions

## Decision Path

1. Identify the highest active artifact: intent, program, module, phase, or issue.
2. If the work can fit one small issue, stop and route to `small-change` or `execute-issue`.
3. Split the work into independently verifiable issue candidates.
4. Declare dependencies between issue candidates.
5. Confirm each issue has testable acceptance criteria.
6. Mark unresolved decisions as blockers rather than guessing.

## Rules

1. Issues must be atomic enough to prove and review.
2. Dependencies must be explicit and acyclic.
3. Every issue must state allowed work and out-of-scope work.
4. Every issue must include proof requirements before execution begins.
5. Do not decompose by agent role alone; decompose by deliverable and dependency.
6. Do not create vague issues such as "finish implementation" or "clean up code".

## Verification

A decomposition is ready when:

- every issue has a clear objective
- every issue has testable acceptance criteria
- dependencies identify what must be integrated first
- no issue requires hidden context from unrelated artifacts
- blocked items name the exact missing input or decision

## Progressive Disclosure

Read:

1. current program or module artifact
2. relevant phase artifacts
3. existing issue artifacts in the target scope
4. templates needed for the decomposition

Do not scan unrelated modules or historical reports unless the current artifact references them.
