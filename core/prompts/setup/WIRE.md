# Execute: Wire the Shared Cursor System

Use this prompt when installing or validating the shared `.cursor` system in a host repository.

## Goal

Confirm that the host repository has the local `.cursor` system in place, that the expected directories exist, and that setup evidence is recorded.

## Read First

1. `.cursor/README.md`
2. `.cursor/checklists/wire-checklist.md`
3. `.cursor/workflows/dispatch-v2.md`

## Rules

1. Work only on setup and verification artifacts unless the host repo explicitly asks for broader changes.
2. Do not depend on external factory directories.
3. Record blockers explicitly instead of silently skipping them.
4. Do not invent secrets or claim remote integrations are configured unless they were actually verified.

## Required Outcome

- `.cursor` exists with the expected top-level folders
- commands point to local prompts
- required rules, skills, prompts, templates, workflows, and checklists are present
- any GitHub or automation setup gaps are documented
