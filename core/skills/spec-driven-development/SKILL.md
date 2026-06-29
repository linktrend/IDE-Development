---
name: spec-driven-development
description: Convert unclear or significant work into a concise specification before planning or coding.
version: 1.0.0
status: active
tags: [spec, intent, requirements, planning]
source_adapted_from:
  - addyosmani/agent-skills/skills/spec-driven-development
---

# Spec Driven Development

Use this skill when work needs clearer requirements before it can be safely planned or executed.

## Use When

- starting a new project or major feature
- requirements are unclear
- multiple interpretations exist
- acceptance criteria are missing
- scope boundaries are not yet stable

## Spec Contents

- objective
- user or operator
- problem being solved
- in-scope work
- out-of-scope work
- constraints
- acceptance criteria
- definition of done
- risks and open questions

## IDE Development Mapping

- greenfield or ambiguous work produces or refines `INTENT.md`
- accepted intent can become `PROGRAM.md`
- module-level detail becomes `MODULE.md`, `PHASE.md`, and `ISSUE.md`

## Rules

- Do not code before the spec is clear enough to define acceptance criteria.
- Do not ask many questions at once; use focused discovery when needed.
- Do not turn a spec into implementation detail too early.
- Record blockers when user input is required.

## Output

- concise spec or intent-ready content
- acceptance criteria
- open questions
- recommended next artifact

## Progressive Disclosure

Read discovery guidance and relevant templates. Do not read execution layers until the work is ready to plan or execute.
