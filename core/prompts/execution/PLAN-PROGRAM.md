# Plan Program

## Read First

1. `.cursor/README.md`
2. `.cursor/rules/00-bootstrap.mdc`
3. `.cursor/execution/INDEX.yaml`
4. `.cursor/execution/CANONICAL-LAWS.md`
5. `.cursor/execution/MINIMUM-RUNTIME-MODEL.md`
6. `.cursor/templates/INDEX.yaml`
7. `.cursor/agents/INDEX.yaml`
8. `.cursor/agents/planner/AGENT.md`
9. `.cursor/templates/INTENT.md`
10. `.cursor/templates/PROGRAM.md`

## Doctrine

Use execution doctrine to keep planning dependency-aware, gate-aware, and minimal.

## Templates

- `INTENT.md`
- `PROGRAM.md`
- `MODULE.md` when module structure must be declared

## Expected Output

- a validated or revised intent
- a program artifact with scope, modules, constraints, and definition of done
- for **application Programs**: instantiate the six fixed Modules (see APPLICATION-PIPELINE.md); do not invent an open module structure
- for **non-application governed work**: define modules as needed under generic Module semantics
- explicit blockers where program creation is not yet justified

## Stop When

- the program artifact is coherent and reviewable, or
- intent cannot yet pass program-creation readiness

## Blocked Means

- intent verdict is not `pass`
- for non-application work: scope or value is too ambiguous to define modules
- for application work: unable to instantiate the six fixed Modules or PIPELINE-STATE.json
- required constraints or owners are unknown

## Must Not Skip

- intent validation
- for application Programs: the six fixed Modules in order (never “identify/define an open module structure”)
- for non-application work: explicit module structure
- program definition of done
- progressive disclosure guidance via `read_first` and `read_forbidden`
