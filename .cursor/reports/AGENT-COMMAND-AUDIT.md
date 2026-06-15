# Agent And Command Audit

## Scope

Reviewed only:

- `.cursor/agents/`
- `.cursor/commands/`
- `.cursor/agents/INDEX.yaml`
- `.cursor/commands/INDEX.yaml`

## Findings

### 1. Discoverability is mostly complete but not fully strict

The primary agent and command assets are indexed:

- all active structured agent roles are present in `.cursor/agents/INDEX.yaml`
- the squad file is present in `.cursor/agents/INDEX.yaml`
- all command wrapper files are present in `.cursor/commands/INDEX.yaml`
- legacy compatibility command wrappers are also present in `.cursor/commands/INDEX.yaml`

Strict gaps remain:

- `.cursor/agents/README.md` is not represented in `.cursor/agents/INDEX.yaml`
- `.cursor/commands/README.md` is not represented in `.cursor/commands/INDEX.yaml`

If the rule is interpreted literally as "every file must be discoverable through its index", both directories currently fail that requirement for their README files.

### 2. The control-versus-resource boundary is mostly correct

The newer execution-facing roles are correctly split into:

- control roles: `planner`, `orchestrator`, `reviewer`, `integrator`
- delivery roles: `product-owner`, `technical-lead`, `ui-ux-designer`, `frontend-developer`, `backend-developer`, `qa-automation-engineer`

This aligns with the doctrine that agents are resources while execution order comes from artifacts, dependencies, and gates.

The strongest supporting evidence is:

- `orchestrator` owns readiness and sequencing
- `reviewer` owns the independent gate
- `integrator` owns post-review incorporation
- specialist roles do not claim execution graph control

### 3. Legacy flat agents overlap with the newer structured roles

Two flat legacy agent documents remain:

- `.cursor/agents/project-planner.md`
- `.cursor/agents/architect-integrator.md`

They are indexed as compatibility roles, which is reasonable, but they still overlap conceptually with newer structured roles:

- `project-planner.md` overlaps with `planner/AGENT.md`
- `architect-integrator.md` overlaps partially with `technical-lead/AGENT.md` and `integrator/AGENT.md`, although its scope is `.cursor` system maintenance rather than product execution

This is not a runtime failure, but it does increase ambiguity during manual role selection.

### 4. Canonical command responsibilities align with the execution hierarchy

The preferred commands are coherent and map cleanly to the doctrine:

- `plan-program` → program level
- `plan-module` → module and phase decomposition
- `complete-module` → module-level recursive execution
- `execute-issue` → issue execution
- `review-issue` → issue review
- `integrate-issue` → issue integration

This respects:

- `Program -> Module -> Phase -> Issue`
- issue as the atomic executable unit

No preferred command was found that treats a higher-level artifact as the atomic execution unit.

### 5. Legacy commands sit outside the execution doctrine

The `linkdev-*` and `wire-linkdev` commands do not align to the canonical execution hierarchy. They are setup or compatibility entrypoints, not program/module/phase/issue execution commands.

This is acceptable only because they are explicitly marked:

- `compatibility-only`
- `legacy`
- `not-preferred`

They should not be treated as part of the canonical execution command surface.

### 6. Naming is partly inconsistent

The new command names are consistent and clear:

- verb-noun
- kebab-case
- doctrine-aligned

The legacy command names are inconsistent:

- `wire-linkdev` reverses the `linkdev-*` prefix pattern
- `linkdev-wire-post-ui` is an alias to another alias-oriented action and is less clear than the canonical execution commands
- `linkdev-go` is vague compared with `plan-program`

The agent directory also has naming style drift:

- newer roles use directory plus `AGENT.md`
- legacy roles are flat markdown files
- squad uses a flat markdown file under `squads/`

This is understandable historically but not fully normalized.

## Problems

### High

1. Strict discoverability is incomplete because the directory README files are not indexed.

2. Legacy agent overlap can create role-selection ambiguity between:
   - `project-planner.md`
   - `planner/AGENT.md`

### Medium

1. Legacy commands remain in the same command surface as canonical execution commands, which dilutes clarity for users and agents even though the index classifies them correctly.

2. Agent file naming conventions are mixed:
   - flat markdown legacy files
   - structured role directories with `AGENT.md`
   - squad markdown file

3. `architect-integrator.md` uses the word `integrator`, which is easy to confuse with the canonical execution control role `integrator/AGENT.md`.

### Low

1. `.cursor/commands/README.md` and `.cursor/agents/README.md` are useful but currently depend on direct file browsing rather than index-driven discovery.

2. There is no phase-specific command surface. This is not a doctrine violation, but it means the hierarchy is operationally exposed most strongly at program, module, and issue levels rather than equally at all layers.

## Recommended Changes

### High Value

1. Add index entries for:
   - `.cursor/agents/README.md`
   - `.cursor/commands/README.md`

2. Clarify in the agent index that:
   - `planner/AGENT.md` is the canonical planning control role
   - `project-planner.md` is compatibility-only and not preferred for new execution work

### Medium Value

1. Reduce naming ambiguity between:
   - `architect-integrator.md`
   - `integrator/AGENT.md`

This can be done later through clearer descriptions or compatibility labeling without deleting either file.

2. Make command-surface separation more visible inside `.cursor/commands/INDEX.yaml` by grouping or tagging:
   - canonical execution commands
   - legacy compatibility commands

3. Consider whether `wire-linkdev` should eventually adopt a naming pattern consistent with the other legacy commands, while retaining compatibility.

### Low Value

1. Decide whether a phase-level command is intentionally unnecessary or should exist later as a thin wrapper.

2. Normalize long-term file layout under `agents/` if and only if compatibility concerns no longer require the legacy flat files.

## Files Affected

Reviewed files:

- `.cursor/agents/INDEX.yaml`
- `.cursor/agents/README.md`
- `.cursor/agents/architect-integrator.md`
- `.cursor/agents/project-planner.md`
- `.cursor/agents/planner/AGENT.md`
- `.cursor/agents/orchestrator/AGENT.md`
- `.cursor/agents/reviewer/AGENT.md`
- `.cursor/agents/integrator/AGENT.md`
- `.cursor/agents/product-owner/AGENT.md`
- `.cursor/agents/technical-lead/AGENT.md`
- `.cursor/agents/ui-ux-designer/AGENT.md`
- `.cursor/agents/frontend-developer/AGENT.md`
- `.cursor/agents/backend-developer/AGENT.md`
- `.cursor/agents/qa-automation-engineer/AGENT.md`
- `.cursor/agents/squads/autonomous-development-squad.md`
- `.cursor/commands/INDEX.yaml`
- `.cursor/commands/README.md`
- `.cursor/commands/complete-module.md`
- `.cursor/commands/execute-issue.md`
- `.cursor/commands/integrate-issue.md`
- `.cursor/commands/linkdev-dispatch.md`
- `.cursor/commands/linkdev-go.md`
- `.cursor/commands/linkdev-ui-automations.md`
- `.cursor/commands/linkdev-wire-post-dispatch.md`
- `.cursor/commands/linkdev-wire-post-ui.md`
- `.cursor/commands/plan-module.md`
- `.cursor/commands/plan-program.md`
- `.cursor/commands/review-issue.md`
- `.cursor/commands/wire-linkdev.md`

Report created:

- `.cursor/reports/AGENT-COMMAND-AUDIT.md`

## Summary Verdict

The active agent and command layer is structurally usable and broadly aligned with the execution doctrine.

The main stabilization issues are not doctrinal failures. They are:

- incomplete strict discoverability for directory READMEs
- overlap between legacy and canonical planning roles
- naming drift in legacy compatibility assets

No immediate evidence was found that the preferred execution commands violate the canonical hierarchy or that specialist agents have been turned into the execution control structure.
