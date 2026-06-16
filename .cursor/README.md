# AI Factory Core for Cursor

This `.cursor/` directory is the compatibility runtime surface for the shared development system used across the workspace.

The canonical portable knowledge asset now lives in `../core/`.

This adapter layer exists so existing `.cursor/...` paths, bootstrap behavior, rules, prompts, commands, templates, and examples continue to function without semantic change.

For a fresh repository or first-time operator, the recommended startup path is:

1. read this file
2. then immediately read `bootstrap/START-HERE.md`
3. if the work is greenfield or materially ambiguous, route into `discovery/INDEX.yaml`
4. only then continue into intent, doctrine, templates, commands, or deeper layers as directed

It remains operationally self-contained from the perspective of existing `.cursor/...` consumers:

- rules define operating constraints and standards
- execution defines doctrine and runtime semantics for autonomous work
- skills provide focused implementation guidance
- prompts drive setup, planning, and execution flows
- agents define reusable specialist roles and squad compositions
- templates provide structured artifacts
- workflows describe multi-step operating patterns
- checklists provide verification gates
- commands provide preferred execution wrappers and retained legacy compatibility entrypoints
- session defines natural-language session start, resume, shutdown, and handoff behavior
- workspace defines one-time workspace adoption and consumer repository wiring behavior

`LiNKdev` is legacy source material only. It is not a required runtime dependency for this system.

`core/` is canonical storage. `.cursor/` is the compatibility runtime surface.

## Directory Map

| Path | Purpose |
|------|---------|
| `rules/` | Always-on and situational rules kept under `.cursor/` |
| `bootstrap/` | Canonical onboarding, startup, and shutdown sequence |
| `discovery/` | Optional pre-intent discovery and interview guidance for greenfield or ambiguous work |
| `execution/` | Canonical execution doctrine and runtime model |
| `skills/` | Local skills catalog and focused skill documents |
| `prompts/` | Reusable execution prompts for setup, planning, and execution |
| `agents/` | Specialist role definitions, control roles, and squads |
| `templates/` | Canonical templates for plans, issues, reports, and intent docs |
| `workflows/` | End-to-end process definitions |
| `checklists/` | Verification and readiness checklists |
| `commands/` | Preferred execution command wrappers plus retained legacy compatibility commands |
| `session/` | Session lifecycle guidance for resume, close-out, and handoff behavior |
| `workspace/` | One-time workspace adoption, cleanup, and repository wiring behavior |
| `mcp.json` | Local machine MCP configuration kept under `.cursor/` |

## Operating Model

1. Read this file first.
2. If the repository or session is fresh, read `bootstrap/START-HERE.md` next.
3. If the work is greenfield, ambiguous, or under-specified, read `discovery/INDEX.yaml` before `INTENT.md`.
4. Use `bootstrap/QUICKSTART.md` only when the work level is already obvious.
5. Read `rules/00-linkdev-bootstrap.mdc`, then any other applicable rules.
6. For program, module, phase, issue, proof, review, and integration work, read `execution/INDEX.yaml`.
7. Use the execution doctrine files as the governing model:
   - `execution/CANONICAL-LAWS.md`
   - `execution/MINIMUM-RUNTIME-MODEL.md`
   - `execution/AUTONOMOUS-MODULE-EXECUTION.md`
8. Use `templates/INDEX.yaml` to select the minimum artifact needed.
9. Use `agents/INDEX.yaml` when the task needs a role, control function, or squad composition.
10. Use `commands/INDEX.yaml` when the task begins from a command-style invocation.
11. Use `session/INDEX.yaml` when the task is a natural-language resume or close-out request.
12. Use `workspace/INDEX.yaml` when the task is a one-time workspace adoption request.
13. Read `skills/SKILLS_CATALOG.md` before opening individual skills.
14. Open only the prompt, template, checklist, workflow, skill, agent, command, session, or workspace file required for the task.
15. Prefer revising existing assets over creating parallel copies.
16. Keep the system simple, modular, and maintainable.

## First Path

For most first-time use, the safest path is:

1. `bootstrap/START-HERE.md`
2. `discovery/INDEX.yaml` only if the work is greenfield or ambiguous
3. `commands/INDEX.yaml`
4. the one preferred command wrapper that matches the task
5. only the doctrine, templates, workflows, state, and contracts required by that command

For session resume or close-out requests, insert `session/INDEX.yaml` before selecting the next operational path.

For one-time workspace adoption requests, insert `workspace/INDEX.yaml` before selecting the adoption path.

## Optional Discovery

Use discovery only when needed.

- greenfield or ambiguous work: `DISCOVERY -> INTERVIEW -> INTENT`
- routine new work: `INTENT`
- bugfix or atomic operational work: `ISSUE`

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

The `.cursor/...` paths remain valid by design. Existing repositories that consume the shared system through `.cursor/` should continue functioning without modification.
