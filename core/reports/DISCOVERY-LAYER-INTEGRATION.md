# Discovery Layer Integration

## Purpose

This pass introduces an optional discovery and interview layer that strengthens greenfield and ambiguous project startup without changing the existing execution doctrine.

## What Was Adapted From `agent-skills`

Adapted concepts from [addyosmani/agent-skills](https://github.com/addyosmani/agent-skills), especially:

- the `interview-me` pattern of one question at a time with explicit uncertainty tracking
- the idea that ambiguous work should be clarified before planning or implementation
- the anti-rationalization stance that confidence is not evidence and assumptions should be surfaced early
- the planning discipline that structured work should begin only after requirements are concrete enough to support it

Relevant source references:

- the `interview-me` skill emphasizes one-question-at-a-time interviewing until roughly 95% confidence and warns against guessing on underspecified asks ([interview-me](https://github.com/addyosmani/agent-skills/blob/main/skills/interview-me/SKILL.md))
- the `using-agent-skills` meta-skill routes unclear work into interview before spec and planning ([using-agent-skills](https://github.com/addyosmani/agent-skills/blob/main/skills/using-agent-skills/SKILL.md))
- the `spec-driven-development` skill emphasizes surfacing assumptions before proceeding and not silently filling in ambiguous requirements ([spec-driven-development](https://github.com/addyosmani/agent-skills/blob/main/skills/spec-driven-development/SKILL.md))
- the skill anatomy guidance emphasizes evidence over assumption, anti-rationalization, progressive disclosure, and token-conscious process docs ([skill-anatomy](https://github.com/addyosmani/agent-skills/blob/main/docs/skill-anatomy.md))
- the `doubt-driven-development` overview reinforces the principle that confident output is not automatically correct ([doubt-driven-development](https://github.com/addyosmani/agent-skills/blob/main/skills/doubt-driven-development/SKILL.md))

## What Was Intentionally Rejected

The following ideas were intentionally not adopted:

- the external repository's lifecycle architecture and command system
- any replacement of `INTENT -> PROGRAM -> MODULE -> PHASE -> ISSUE`
- any mandatory interview requirement
- any framework-specific or tool-specific orchestration model
- any redesign of runtime, workflow, contract, state, or system layers

The local system remains the source of truth.

## How The Interview Model Fits The Doctrine

The interview model is positioned before intent, not inside execution.

Resulting optional startup path:

- `DISCOVERY -> INTERVIEW -> INTENT`

After intent is formed, the canonical flow remains unchanged:

- `INTENT -> PROGRAM -> MODULE -> PHASE -> ISSUE -> PROOF -> REVIEW -> INTEGRATION`

This preserves:

- issue as the atomic executable unit
- dependency-driven execution ordering
- proof, review, and integration as completion gates
- the current doctrine and runtime semantics

## Why It Is Optional

Discovery is intentionally optional because it is useful only when ambiguity is real.

It should help with:

- completely new projects
- greenfield products
- ambiguous requests
- under-specified ideas

It should be skipped for:

- bug fixes
- routine work
- existing modules with clear scope
- small self-contained features

Making discovery optional preserves execution speed and avoids adding ceremony to work that is already clear.

## Risks Introduced

1. Operators may overuse discovery and add unnecessary questioning to routine work.

2. Confidence numbers may become performative if they are not tied to actual unresolved uncertainty.

3. Interview could drift into planning if the boundary with `INTENT.md` is not respected.

4. Discovery could become a delay tactic if operators keep questioning after uncertainty is already sufficiently reduced.

These risks are addressed directly in:

- `DISCOVERY.md`
- `CONFIDENCE-THRESHOLDS.md`
- `ANTI-RATIONALIZATION.md`

## Expected Benefits

1. Fewer silent assumptions at the start of greenfield or ambiguous work.

2. Better intent quality before program and module structure begins to harden.

3. Less premature planning on under-specified requests.

4. Better alignment between what the user actually wants and what the execution system later decomposes.

5. A stronger bridge between fresh-repository onboarding and the existing intent-driven operating model.

## Files Added

- `.cursor/discovery/INDEX.yaml`
- `.cursor/discovery/README.md`
- `.cursor/discovery/DISCOVERY.md`
- `.cursor/discovery/INTERVIEW.md`
- `.cursor/discovery/QUESTIONING-GUIDELINES.md`
- `.cursor/discovery/CONFIDENCE-THRESHOLDS.md`
- `.cursor/discovery/ANTI-RATIONALIZATION.md`
- `.cursor/reports/DISCOVERY-LAYER-INTEGRATION.md`

## Files Updated

- `.cursor/README.md`
- `.cursor/bootstrap/INDEX.yaml`
- `.cursor/bootstrap/README.md`
- `.cursor/bootstrap/START-HERE.md`
- `.cursor/bootstrap/PROJECT-BOOTSTRAP.md`
- `.cursor/bootstrap/SESSION-STARTUP.md`

## Summary

This integration adapts useful discovery concepts from `agent-skills` without importing its architecture.

The result is:

- optional
- lightweight
- bootstrap-aware
- doctrine-compatible
- intent-feeding rather than intent-replacing
