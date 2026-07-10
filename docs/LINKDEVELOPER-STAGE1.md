# LiNKdeveloper Stage 1 — Declaration

**Status:** **Complete** — see `docs/LINKDEVELOPER-STAGE1-CLOSURE.md`  
**Date:** 2026-07-10

## This repository IS LiNKdeveloper Stage 1

This repository (`IDE Development`) is **LiNKdeveloper Stage 1**: the semi-manual **Application Factory** operating system.

It provides the **development workflow blueprint** — doctrine, artifacts, workflows, contracts, and state model — for building venture applications:

```
Intent → Program → Module → Phase → Issue → Proof → Review → Integration → Complete
```

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
| **Blueprint** | Factory operations common blueprint | **Complete** |
| **2** | Mostly/fully autonomous (LiNKdeveloper + OpenClaw) | Future |

Full detail:

- Application Factory: `docs/LINKDEVELOPER-STAGE1A-SPEC.md`
- Stage 1b: `docs/LINKDEVELOPER-STAGE1B-REPORT.md`
- Operations factories: `docs/FACTORY-OPERATIONS-BLUEPRINT.md`
- Closure: `docs/LINKDEVELOPER-STAGE1-CLOSURE.md`

## Next work

Finish **Website Factory** under the operations blueprint — first product build for LiNKdeveloper Stage 1. See `docs/LINKSITES-FACTORY-SETUP-REPORT.md` for setup status and open items.
