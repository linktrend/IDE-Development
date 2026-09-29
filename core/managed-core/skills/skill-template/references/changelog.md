# Skill Changelog

## v1.3.0 - 2026-02-22
- Migrated template location to `/skills/skill-template`.
- Added global tool dependency rule: if required tool is missing, route creation to `/skills/tool-architect`.

## v1.2.0 - 2026-02-20
- Added mandatory `tooling` frontmatter block for CLI-first protocol.
- Switched default persistence checkpoint path to `.workdir/tasks/{{task_id}}/state.jsonl`.
- Added specialist/generalist profiling and conditional JIT loading workflow.
- Added mandatory `get_tool_details` usage for Generalist/JIT profile.

## v1.1.0 - 2026-02-20
- Added required `engine` frontmatter block for intelligence-floor requirements.
- Added Decision Tree intelligence-floor fail-fast checkpoint.

## v1.0.0 - 2026-02-20
- Initial Golden Template baseline.
- Includes 5-phase workflow, persistence, contracts, and self-correction loop.
