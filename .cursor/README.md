# AI Factory Core for Cursor

This `.cursor/` directory is the active source of truth for the shared development system used across the workspace.

It is intentionally self-contained:

- rules define operating constraints and standards
- execution defines doctrine and runtime semantics for autonomous work
- skills provide focused implementation guidance
- prompts drive setup, planning, and execution flows
- agents define reusable specialist roles and squad compositions
- templates provide structured artifacts
- workflows describe multi-step operating patterns
- checklists provide verification gates
- commands are compatibility entrypoints that route into local prompts

`LiNKdev` is legacy source material only. It is not a required runtime dependency for this system.

## Directory Map

| Path | Purpose |
|------|---------|
| `rules/` | Always-on and situational rules |
| `execution/` | Canonical execution doctrine and runtime model |
| `skills/` | Local skills catalog and focused skill documents |
| `prompts/` | Reusable execution prompts for setup, planning, and execution |
| `agents/` | Specialist role definitions, control roles, and squads |
| `templates/` | Canonical templates for plans, issues, reports, and intent docs |
| `workflows/` | End-to-end process definitions |
| `checklists/` | Verification and readiness checklists |
| `commands/` | Command entrypoints that reference local prompts |
| `mcp.json` | Local machine MCP configuration |

## Operating Model

1. Read this file first.
2. Read `rules/00-linkdev-bootstrap.mdc`, then any other applicable rules.
3. For program, module, phase, issue, proof, review, and integration work, read `execution/INDEX.yaml`.
4. Use the execution doctrine files as the governing model:
   - `execution/CANONICAL-LAWS.md`
   - `execution/MINIMUM-RUNTIME-MODEL.md`
   - `execution/AUTONOMOUS-MODULE-EXECUTION.md`
5. Use `templates/INDEX.yaml` to select the minimum artifact needed.
6. Use `agents/INDEX.yaml` when the task needs a role, control function, or squad composition.
7. Use `commands/INDEX.yaml` when the task begins from a command-style invocation.
8. Read `skills/SKILLS_CATALOG.md` before opening individual skills.
9. Open only the prompt, template, checklist, workflow, skill, agent, or command file required for the task.
10. Prefer revising existing assets over creating parallel copies.
11. Keep the system simple, modular, and maintainable.

## Execution Doctrine

Execution doctrine governs autonomous module execution.

When asked to complete a module or issue, agents should:

1. use `execution/INDEX.yaml` as the entrypoint
2. load only the doctrine files relevant to the task
3. use progressive disclosure rather than scanning the entire repository
4. use `templates/INDEX.yaml` to determine which execution artifacts to read next
5. use `agents/INDEX.yaml` and `commands/INDEX.yaml` to select the minimum role or command entrypoint needed

## Compatibility

Some command names still include `linkdev` for continuity with older workflows. Their implementation now lives entirely in this repository.
