# Core Migration Assessment

## Executive Verdict

Migration is feasible, but not as a pure rename.

The repository can move toward a portable `core/` knowledge asset with zero doctrinal or architectural change only if `.cursor/` remains a compatibility runtime surface.

Recommended adapter model: `C. Partial adapter`

- `core/` becomes the canonical content location for portable knowledge assets.
- `.cursor/` remains present for backward compatibility and tool integration.
- `.cursor/` should expose the existing paths expected by current consumers, preferably through symlinked directories or equivalent adapter files.
- Cursor-specific files should remain under `.cursor/`.

## Feasibility

### Can `.cursor` become `core/`?

Yes, but only in stages.

The contents are portable in principle, but the current implementation is deeply path-bound to `.cursor/`. A direct move from `.cursor/` to `core/` would break discovery, read orders, command wrappers, bootstrap rules, examples, reports, and compatibility assumptions across the system.

### Can migration happen with zero semantic changes?

Yes, if the first migration is packaging-only:

- move portable directories into `core/`
- preserve `.cursor/` as a compatibility layer
- keep internal references unchanged during v1.0.1
- avoid rewriting doctrine, command semantics, workflow rules, or template responsibilities

If the goal includes changing internal references from `.cursor/...` to `core/...`, that is no longer packaging-only. That becomes a broader documentation and compatibility refactor and belongs to a later release.

## Path Assumptions Discovered

The current system assumes `.cursor/` in multiple structural ways.

### 1. Root and bootstrap identity

- `README.md` says the active system lives in `.cursor/`
- `.cursor/README.md` says `.cursor/` is the active source of truth
- `.cursor/rules/00-linkdev-bootstrap.mdc` declares `.cursor/` as the source of truth and hard-codes `.cursor/...` read order
- bootstrap documents route operators to `.cursor/bootstrap/START-HERE.md`, `.cursor/commands/INDEX.yaml`, `.cursor/execution/INDEX.yaml`, and `.cursor/templates/INDEX.yaml`

### 2. Indexes encode `.cursor` paths

The following layers publish explicit `.cursor/...` paths in `path`, `dependencies`, `required_doctrine`, `required_templates`, `required_agents`, and related fields:

- `agents`
- `bootstrap`
- `commands`
- `contracts`
- `discovery`
- `examples`
- `execution`
- `runtime`
- `state`
- `system`
- `templates`
- `workflows`

### 3. Commands and prompts are hard-linked to `.cursor`

Command wrappers and prompt files explicitly reference:

- `.cursor/prompts/...`
- `.cursor/execution/...`
- `.cursor/templates/...`
- `.cursor/agents/...`
- `.cursor/checklists/...`
- `.cursor/workflows/...`

### 4. Templates, examples, and pilot artifacts embed `.cursor` paths

Canonical templates and examples reference `.cursor/...` in fields such as:

- `read_first`
- `dependencies`
- artifact relationships
- example walkthrough references

This means a physical move without compatibility paths would invalidate example and template guidance.

### 5. Setup and validation material assume `.cursor` exists

- `SETUP.md` treats `.cursor/` as the active system
- wire/setup prompts and checklists validate presence of `.cursor/`
- reports and validation history describe the system as a `.cursor` operating model

## Risks

### High risk

- Directly renaming `.cursor` to `core` would break most indexed paths immediately.
- Cursor bootstrap behavior currently depends on `.cursor/rules/` and `.cursor/README.md`.
- Existing consumer repositories that copied `.cursor/` would lose compatibility if the `.cursor` surface disappears.

### Medium risk

- Symlink behavior may not be equally well supported by every editor, tool, or OS combination.
- `.cursor/mcp.json` is tool-specific and should not move into a tool-neutral core without a compatibility plan.
- Legacy commands and setup flows still reference `.cursor` explicitly.

### Low risk

- Reports and examples that mention `.cursor` are historically path-specific but not runtime-critical.
- Root Markdown links use absolute local file paths; this is already a portability smell, but it does not block the migration strategy itself.

## Recommended Target Structure

The candidate structure is directionally correct but incomplete.

### Recommended structure

```text
core/
    bootstrap/
    discovery/
    execution/
    templates/
    agents/
    commands/
    prompts/
    skills/
    checklists/
    runtime/
    workflows/
    contracts/
    state/
    system/
    examples/
    reports/
    pilots/               # keep only if retained as first-class historical material

.cursor/
    README.md
    INDEX.yaml
    import-core.md
    mcp.json
    rules/
    bootstrap/            -> adapter or symlink to ../core/bootstrap
    discovery/            -> adapter or symlink to ../core/discovery
    execution/            -> adapter or symlink to ../core/execution
    templates/            -> adapter or symlink to ../core/templates
    agents/               -> adapter or symlink to ../core/agents
    commands/             -> adapter or symlink to ../core/commands
    prompts/              -> adapter or symlink to ../core/prompts
    skills/               -> adapter or symlink to ../core/skills
    checklists/           -> adapter or symlink to ../core/checklists
    runtime/              -> adapter or symlink to ../core/runtime
    workflows/            -> adapter or symlink to ../core/workflows
    contracts/            -> adapter or symlink to ../core/contracts
    state/                -> adapter or symlink to ../core/state
    system/               -> adapter or symlink to ../core/system
    examples/             -> adapter or symlink to ../core/examples
    reports/              -> adapter or symlink to ../core/reports
    pilots/               -> adapter or symlink to ../core/pilots

codex/
    AGENTS.md
    README.md

claude/
    CLAUDE.md

README.md
```

### Why the candidate structure needs adjustment

The originally proposed `core/` omitted several directories that are part of the long-term knowledge asset:

- `prompts/`
- `skills/`
- `checklists/`
- `pilots/` if retained

These are not Cursor-only implementation details today. They are content and guidance assets that other runtimes can consume or adapt.

## Compatibility Strategy

Backward compatibility is mandatory, so `.cursor/` should not become a minimal stub in v1.0.1.

### Recommended strategy

1. Introduce `core/` as canonical storage for portable content.
2. Keep `.cursor/` present as the compatibility entrypoint for existing repositories and Cursor-native behaviors.
3. Preserve current `.cursor/...` paths by mapping most content directories back into `core/`.
4. Keep Cursor-specific files physically under `.cursor/`:
   - `rules/`
   - `mcp.json`
   - adapter entry files such as `.cursor/README.md`
5. Add tool-specific entrypoints outside `.cursor/`:
   - `codex/AGENTS.md`
   - `claude/CLAUDE.md`
6. Defer internal path-neutral rewrites until a later release.

### Why thin adapter only is not enough

Option `A. Thin adapter only` is too aggressive for v1.0.1.

The current system does not merely mention `.cursor/`; it operationally depends on it. A tiny `.cursor/README.md` plus `INDEX.yaml` would not preserve:

- rule loading
- command-to-prompt routing
- template path references
- bootstrap read orders
- setup checks
- examples and reports

### Why compatibility mirror is not ideal

Option `B. Compatibility mirror` preserves behavior but risks long-term duplication and drift if `.cursor/` and `core/` both contain real copies.

That model is safe short-term but weak as a source-of-truth model.

### Why partial adapter is the best fit

Option `C. Partial adapter` keeps:

- `core/` as the long-term knowledge asset
- `.cursor/` as a stable compatibility surface
- Cursor-only files local to `.cursor/`
- portable knowledge shared from one canonical location

This is the smallest change that preserves semantics and consumers.

## Existing Consumer Repository Strategy

Repositories that already use `.cursor/` should continue functioning unchanged.

Recommended compatibility promise:

- existing consumers may continue reading `.cursor/...`
- no required command names change in v1.0.1
- no required doctrine paths change in v1.0.1
- no required bootstrap path changes in v1.0.1
- Codex and Claude entrypoints are additive, not replacements

For downstream repositories, the migration should feel like:

- same `.cursor/` surface
- same behavior
- new optional tool-neutral `core/` location for maintainers and future adapters

## Breakage Risks to Test Before Any Move

1. Cursor rule loading from `.cursor/rules/*.mdc`
2. Access to symlinked directories inside `.cursor/`
3. Command wrappers resolving prompt paths under `.cursor/prompts/`
4. Index-driven discovery using `.cursor/...` `path` values
5. Consumer-repository installation flows that validate `.cursor/` presence
6. GitHub rendering and local editor behavior for adapter-linked files

## Rollback Strategy

Because this is packaging, rollback is straightforward if staged carefully.

1. Create a release branch from `v1.0.0`.
2. Introduce `core/` without deleting `.cursor/`.
3. Validate discovery and command entrypoints locally.
4. If any tool fails, revert the packaging commit or remove the adapter layer and return to the `v1.0.0` layout.

No doctrinal data migration is required, so rollback risk is low if the move is isolated to filesystem layout and references.

## Release Fit

### Belongs to v1.0.1?

Yes, if scoped narrowly to:

- canonicalizing portable content into `core/`
- preserving `.cursor/` compatibility
- adding tool-specific adapter entrypoints
- avoiding semantic rewrites

### Belongs to v1.1?

Yes, for the broader follow-up work:

- rewriting internal references from `.cursor/...` to path-neutral or `core/...` language
- reducing `.cursor` wording throughout doctrine and examples
- deciding whether pilots remain first-class
- rationalizing tool-specific materials further

## Confidence Level

Confidence: medium-high

Reasoning:

- feasibility is clear
- the main risks are operational rather than conceptual
- backward compatibility is achievable
- the largest unknown is tool behavior around symlinked or adapter-backed `.cursor/` paths

## Recommendation

Proceed only if the migration is framed as:

`core becomes canonical storage, .cursor remains the compatibility runtime surface`

Do not proceed if the goal is:

`rename .cursor to core and update everything later`

That would create immediate breakage and would not satisfy the zero-semantic-change constraint.
