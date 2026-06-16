# AI Factory Core for Cursor

This `.cursor/` directory is the active source of truth for the shared development system used across the workspace.

For a fresh repository or first-time operator, the recommended startup path is:

1. read this file
2. then immediately read `bootstrap/START-HERE.md`
3. only then continue into doctrine, templates, commands, or deeper layers as directed

It is intentionally self-contained:

- rules define operating constraints and standards
- execution defines doctrine and runtime semantics for autonomous work
- skills provide focused implementation guidance
- prompts drive setup, planning, and execution flows
- agents define reusable specialist roles and squad compositions
- templates provide structured artifacts
- workflows describe multi-step operating patterns
- checklists provide verification gates
- commands provide preferred execution wrappers and retained legacy compatibility entrypoints

`LiNKdev` is legacy source material only. It is not a required runtime dependency for this system.

## Directory Map

| Path | Purpose |
|------|---------|
| `rules/` | Always-on and situational rules |
| `bootstrap/` | Canonical onboarding, startup, and shutdown sequence |
| `execution/` | Canonical execution doctrine and runtime model |
| `skills/` | Local skills catalog and focused skill documents |
| `prompts/` | Reusable execution prompts for setup, planning, and execution |
| `agents/` | Specialist role definitions, control roles, and squads |
| `templates/` | Canonical templates for plans, issues, reports, and intent docs |
| `workflows/` | End-to-end process definitions |
| `checklists/` | Verification and readiness checklists |
| `commands/` | Preferred execution command wrappers plus retained legacy compatibility commands |
| `mcp.json` | Local machine MCP configuration |

## Operating Model

1. Read this file first.
2. If the repository or session is fresh, read `bootstrap/START-HERE.md` next.
3. Use `bootstrap/QUICKSTART.md` only when the work level is already obvious.
4. Read `rules/00-linkdev-bootstrap.mdc`, then any other applicable rules.
5. For program, module, phase, issue, proof, review, and integration work, read `execution/INDEX.yaml`.
6. Use the execution doctrine files as the governing model:
   - `execution/CANONICAL-LAWS.md`
   - `execution/MINIMUM-RUNTIME-MODEL.md`
   - `execution/AUTONOMOUS-MODULE-EXECUTION.md`
7. Use `templates/INDEX.yaml` to select the minimum artifact needed.
8. Use `agents/INDEX.yaml` when the task needs a role, control function, or squad composition.
9. Use `commands/INDEX.yaml` when the task begins from a command-style invocation.
10. Read `skills/SKILLS_CATALOG.md` before opening individual skills.
11. Open only the prompt, template, checklist, workflow, skill, agent, or command file required for the task.
12. Prefer revising existing assets over creating parallel copies.
13. Keep the system simple, modular, and maintainable.

## First Path

For most first-time use, the safest path is:

1. `bootstrap/START-HERE.md`
2. `commands/INDEX.yaml`
3. the one preferred command wrapper that matches the task
4. only the doctrine, templates, workflows, state, and contracts required by that command

## Execution Doctrine

Execution doctrine governs autonomous module execution.

When asked to complete a module or issue, agents should:

1. use `execution/INDEX.yaml` as the entrypoint
2. load only the doctrine files relevant to the task
3. use progressive disclosure rather than scanning the entire repository
4. use `templates/INDEX.yaml` to determine which execution artifacts to read next
5. use `agents/INDEX.yaml` and `commands/INDEX.yaml` to select the minimum role or command entrypoint needed

For fresh repositories, do not skip the bootstrap layer. It is the intended bridge from zero context into the execution doctrine.

## Compatibility

Some command names still include `linkdev` for continuity with older workflows. Their implementation now lives entirely in this repository.
