# Plan Module

## Read First

1. `.cursor/README.md`
2. `.cursor/rules/00-bootstrap.mdc`
3. `.cursor/execution/INDEX.yaml`
4. `.cursor/execution/MINIMUM-RUNTIME-MODEL.md`
5. `.cursor/execution/AUTONOMOUS-MODULE-EXECUTION.md`
6. `.cursor/templates/INDEX.yaml`
7. `.cursor/agents/INDEX.yaml`
8. `.cursor/agents/planner/AGENT.md`
9. `PROGRAM.md` for the parent program
10. `.cursor/templates/MODULE.md`
11. `.cursor/templates/PHASE.md`
12. `.cursor/templates/ISSUE.md`

## Doctrine

Plan the module so it can execute recursively through phases and issues without scanning unrelated context. For application Programs, the Module ID must be one of the six fixed lifecycle stages; you may decompose the current fixed Module into product-specific Phases and Issues, but you must not create additional top-level application Modules.

## Templates

- `MODULE.md`
- `PHASE.md`
- `ISSUE.md`

## Expected Output

- a module artifact with phases, definition of done, and progressive-disclosure guidance
- phase artifacts with issue lists
- issue artifacts with explicit dependencies and acceptance criteria

## Stop When

- issue-level execution structure is clear enough for readiness computation, or
- unresolved blockers prevent atomic issue definition

## Blocked Means

- the module objective is not specific enough
- dependencies cannot be represented clearly
- acceptance criteria cannot be made testable

## Must Not Skip

- phase boundaries
- issue dependencies
- `read_first` and `read_forbidden`
- module definition of done
