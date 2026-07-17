# State Design

## State Architecture

The state layer provides a canonical state vocabulary shared across:

- commands
- workflows
- runtime
- contracts
- agents

It centralizes:

- artifact states
- transition rules
- readiness conditions
- blocked and failure semantics
- retry behavior
- terminal stop rules

Core state documents:

- `.cursor/state/INDEX.yaml`
- `.cursor/state/README.md`
- `.cursor/state/STATE-MODEL.md`
- `.cursor/state/STATE-TRANSITIONS.md`
- `.cursor/state/READY-STATES.md`
- `.cursor/state/BLOCKED-STATES.md`
- `.cursor/state/FAILURE-STATES.md`
- `.cursor/state/RETRY-STATES.md`
- `.cursor/state/TERMINAL-STATES.md`

## Transition Model

The state system distinguishes:

- planning formation states
- execution readiness states
- execution-progress states
- review and integration gate states
- blocked and failure states
- terminal completion states

Issue remains the normative atomic state machine:

- `draft -> planned -> ready -> in_progress -> review_ready -> done`

Higher-level work units use roll-up-oriented states such as:

- `draft`
- `planned`
- `active`
- `blocked`
- `review_ready`
- `complete`

## Invariants

The state layer preserves these invariants:

1. Issue remains the atomic executable unit.
2. Dependencies determine sequencing.
3. Proof precedes review.
4. Review precedes integration.
5. Integration precedes downstream dependency satisfaction.
6. Higher-level completion never weakens lower-level gate requirements.
7. Agents remain resources, not the control structure.
8. Blocked state always requires an explicit visible reason.

## Cross-Layer Relationships

### Commands

Commands use the state layer to determine:

- when work may start
- when a handoff occurs
- when a stop is legitimate

### Workflows

Workflows use the state layer to:

- define entry and exit conditions
- express stage progression
- distinguish rework from completion

### Runtime

Runtime uses the state layer to:

- compute readiness
- progress issue execution
- handle blocked, retry, and terminal conditions

### Contracts

Contracts use the state layer to:

- validate legal transitions
- determine whether handoffs are complete and valid

### Agents

Agents use the state layer as a shared vocabulary, but do not own the control structure.

## Remaining Work Before v1.0

1. Wire the state layer explicitly into top-level discovery if broader root entrypoint routing is desired.

2. Align older runtime and contract state references to point more explicitly at this new canonical state layer in a future reconciliation pass.

3. Validate the state model against a supervised real module execution in a live repository.

4. Decide whether a dedicated blocker artifact is ever needed or whether blocker evidence should remain embedded in existing artifacts.

5. Decide whether program, module, and phase state vocabularies should eventually be made machine-readable in addition to document-based.
