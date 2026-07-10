# LiNKdeveloper Stage 1 — Declaration

**Status:** Stage 1a (Define Workflow) complete, pending Carlos/Lisa review.
**Date:** 2026-07-10

## This repository IS LiNKdeveloper Stage 1

This repository (`IDE Development`) is **LiNKdeveloper Stage 1**: a semi-manual application factory operating system. It provides the common workflow blueprint — doctrine, artifacts, workflows, contracts, and state model — that governs how any LiNKtrend factory (Website, Application, Automation, Content) turns an intent into an integrated, proven, released piece of work.

Stage 1 does not replace this repository's existing identity. It is a role this repository plays: the governed execution core for semi-manual, human-supervised factory work, as already described in `README.md` and `SETUP.md`.

## Naming stays unchanged

- The local folder name stays `IDE Development`.
- The GitHub repository stays `linktrend/IDE-Development`.
- No rename, no new repository, no new root-level system name is introduced by Stage 1.
- Internally, the canonical knowledge asset remains `core/` and the Cursor-compatible runtime surface remains `.cursor/`, exactly as `README.md` already states.

## Relationship to LiNKdeveloper Stage 2

`LiNKdeveloper` (as a separate repository at `/Users/linktrend/Projects/LiNKdeveloper`) is **Stage 2**: a fully autonomous orchestrator runtime — LiNKdeveloper's own docs describe an "autonomous, continuous lifecycle" driven by an internal orchestrator, executor routing policy, and issue/work-packet schema (see `LiNKdeveloper/docs/SOFTWARE_DEVELOPMENT_LIFECYCLE_MODEL.md`, `EXECUTOR_ROUTING_POLICY.md`).

Stage 2 is **read-only reference** for Stage 1 work. It is not built, extended, wired, or depended upon during Stage 1. It exists to show where the semi-manual workflow defined here is eventually headed once autonomy is added. Stage 1 borrows *concepts* (lifecycle stage names, governance gates, work-packet shape) from Stage 2's docs for the Application Factory variant mapping — it does not borrow code, infrastructure, or runtime behavior.

## LiNKdev is legacy and excluded

`LiNKdev` — the standalone repository at `/Users/linktrend/Projects/LiNKdev` and the embedded `LiNKdev/` folders inside `LiNKsites`, `LiNKtrend-System`, `LiNKautowork`, and `LiNKbot-core` — is **abandoned**. Carlos tried it once; it failed; he stopped using it.

This repository's own doctrine already treats LiNKdev as legacy, not active:

- `.cursor/rules/00-linkdev-bootstrap.mdc` (alwaysApply: true) states: *"Do not depend on `LiNKdev`, chat memory, IDE memory, or unstated assumptions."*
- `core/workspace/WORKSPACE-ADOPTION.md` lists "legacy LiNKdev remnants" as something to inspect and clean up during workspace adoption, not something to install.
- `core/checklists/wire-checklist.md` requires confirming "no required runtime dependency on `LiNKdev`" before a repo is considered wired.
- `core/skills/SKILLS_CATALOG.md` and `core/reports/SKILL-MIGRATION-PASS-1.md` reference `LiNKtrend-System/LiNKdev/skills/gstack` only as a **historical content source to mine selectively**, not as an active dependency.

Stage 1 does not change this posture. LiNKdev appears in the Stage 1a spec only under legacy-to-migrate notes — never as an active system, dependency, or parallel workflow. See the Stage 1a spec, Section D, for the full legacy-exclusion treatment, including a naming collision this audit surfaced between LiNKdev's internal legacy `gstack` folder and the external `garrytan/gstack` Layer 2 skill source.

## Three autonomy stages

| Stage | Name | Handoff model | Status |
|---|---|---|---|
| **1a** | Define Workflow | Human defines; spec produced | **Complete — this deliverable set** |
| **1b** | Semi-manual development | Human approves; agent assists inside issues | Begins after 1a is approved by Carlos and Lisa |
| **2** | Mostly/fully autonomous | LiNKdeveloper orchestrator + OpenClaw dispatch | Future — out of scope for this repository today |

Full detail on blueprint verification, the Application Factory variant, the skills architecture, and acceptance criteria is in `docs/LINKDEVELOPER-STAGE1A-SPEC.md`. Execution evidence for this audit is in `docs/LINKDEVELOPER-STAGE1A-REPORT.md`.
