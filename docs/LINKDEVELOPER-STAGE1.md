# LiNKdeveloper Stage 1 — Declaration

**Status:** **Complete — verified for use (hybrid skills installed)** — see [`docs/LINKDEVELOPER-STAGE1-VERIFICATION-REPORT.md`](LINKDEVELOPER-STAGE1-VERIFICATION-REPORT.md), [`docs/LINKDEVELOPER-STAGE1-HYBRID-REPORT.md`](LINKDEVELOPER-STAGE1-HYBRID-REPORT.md), and [`docs/LINKDEVELOPER-STAGE1-CLOSURE.md`](LINKDEVELOPER-STAGE1-CLOSURE.md)  
**Date:** 2026-07-10

## This repository IS LiNKdeveloper Stage 1

This repository (`IDE Development`) is **LiNKdeveloper Stage 1**: the semi-manual **Application Factory** operating system.

It provides the **development workflow blueprint** — doctrine, artifacts, workflows, contracts, and state model — for building venture applications:

```
Intent → Program → Module → Phase → Issue → Proof → Review → Integration → Complete
```

## Carlos operating model — three triggers + hybrid skills

Carlos starts every session with one of three triggers (see `docs/LINKDEVELOPER-WORKSPACE-OPERATOR-GUIDE.md`):

1. **New idea** — interview → spec/PRD → approve → app or factory → develop
2. **PRD in hand** — clarify gaps → approve → develop
3. **Existing software** — assess → plan → develop

**Hybrid skills are required**, not optional reference:

- **gstack** (macro) — https://github.com/linktrend/gstack, local `/Users/linktrend/Projects/gstack`
- **mattpocock/skills** (micro) — https://github.com/linktrend/skills, local `/Users/linktrend/Projects/skills`

Registry and routing: `docs/HYBRID-SKILLS-REGISTRY.md`, `core/skills/intelligent-routing/SKILL.md`. Eight superseded local skills were deleted (no wrappers) — see `docs/LINKDEVELOPER-STAGE1-HYBRID-REPORT.md`.

**This is not the operations workflow** for Website, Automation, or Content factories. Those factories use the **Factory Operations Common Blueprint** in `docs/FACTORY-OPERATIONS-BLUEPRINT.md` (Program → Module → Stage → Issue → Run → Gate, factory controller trigger, shared internal data architecture).

IDE Development is also the **tool** used to finish factory implementation gaps in other repos — it is not copied into each factory folder.

## Naming stays unchanged

- The local folder name stays `IDE Development`.
- The GitHub repository stays `linktrend/IDE-Development`.
- No rename, no new repository, no new root-level system name is introduced by Stage 1.
- Internally, the canonical knowledge asset remains `core/` and the Cursor-compatible runtime surface remains `.cursor/`, exactly as `README.md` already states.

## Relationship to LiNKdeveloper Stage 2

`LiNKdeveloper` (as a separate repository at `/Users/linktrend/Projects/LiNKdeveloper`) is **Stage 2**: a fully autonomous orchestrator runtime — LiNKdeveloper's own docs describe an "autonomous, continuous lifecycle" driven by an internal orchestrator, executor routing policy, and issue/work-packet schema (see `LiNKdeveloper/docs/SOFTWARE_DEVELOPMENT_LIFECYCLE_MODEL.md`, `EXECUTOR_ROUTING_POLICY.md`).

Stage 2 is **read-only reference** for Stage 1 work. It is not built, extended, wired, or depended upon during Stage 1. Stage 1 borrows *concepts* (lifecycle stage names, governance gates, work-packet shape) from Stage 2's docs for the Application Factory mapping — it does not borrow code, infrastructure, or runtime behavior.

## LiNKdev is legacy and excluded

`LiNKdev` — the standalone repository at `/Users/linktrend/Projects/LiNKdev` and the embedded `LiNKdev/` folders inside `LiNKsites`, `LiNKtrend-System`, `LiNKautowork`, and `LiNKbot-core` — is **abandoned**. Carlos tried it once; it failed; he stopped using it.

This repository's own doctrine already treats LiNKdev as legacy, not active:

- `.cursor/rules/00-bootstrap.mdc` states: *"Do not depend on `LiNKdev`, chat memory, IDE memory, or unstated assumptions."*
- `core/workspace/WORKSPACE-ADOPTION.md` lists "legacy LiNKdev remnants" as something to inspect and clean up during workspace adoption, not something to install.
- `core/checklists/wire-checklist.md` requires confirming "no required runtime dependency on `LiNKdev`" before a repo is considered wired.

See the Stage 1a spec, Section D, for the full legacy-exclusion treatment.

## Stage 1 deliverables

| Phase | Name | Status |
|---|---|---|
| **1a** | Define Application Factory workflow + skills | **Complete** |
| **1b** | Semi-manual OS (bootstrap, equivalence, policies) | **Complete** |
| **1c** | Hybrid skills install (gstack + mattpocock) | **Complete** |
| **Blueprint** | Factory operations common blueprint | **Complete** |
| **2** | Mostly/fully autonomous (LiNKdeveloper + OpenClaw) | Future |

Full detail:

- Application Factory: `docs/LINKDEVELOPER-STAGE1A-SPEC.md`
- Stage 1b: `docs/LINKDEVELOPER-STAGE1B-REPORT.md`
- Operations factories: `docs/FACTORY-OPERATIONS-BLUEPRINT.md`
- Closure: `docs/LINKDEVELOPER-STAGE1-CLOSURE.md`

## Next work

**Carlos develops using the LiNKdeveloper workspace;** factory operations implementation is deferred. See [`docs/LINKDEVELOPER-STAGE1-VERIFICATION-REPORT.md`](LINKDEVELOPER-STAGE1-VERIFICATION-REPORT.md) for the verified readiness verdict and [`docs/LINKDEVELOPER-WORKSPACE-OPERATOR-GUIDE.md`](LINKDEVELOPER-WORKSPACE-OPERATOR-GUIDE.md) for day-to-day operation.
