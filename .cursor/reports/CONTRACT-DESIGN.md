# Contract Design

## Contract Architecture

The contract layer defines universal handoff rules across the system.

It sits between:

- artifacts
- workflows
- runtimes
- human and AI resources

It does not implement behavior. It defines what must be true for a handoff to be valid.

Core contract documents:

- `.cursor/contracts/INDEX.yaml`
- `.cursor/contracts/README.md`
- `.cursor/contracts/CONTRACT-MODEL.md`
- `.cursor/contracts/INPUT-CONTRACT.md`
- `.cursor/contracts/OUTPUT-CONTRACT.md`
- `.cursor/contracts/STATE-CONTRACT.md`
- `.cursor/contracts/SIDE-EFFECT-CONTRACT.md`
- `.cursor/contracts/VALIDATION-CONTRACT.md`

## Producer / Consumer Model

The universal producer / consumer pattern is:

- upstream stage produces an artifact or decision
- downstream stage consumes it only if contract conditions are satisfied

Examples:

- `INTENT.md` produces program eligibility for `PROGRAM.md`
- `ISSUE.md` produces executable scope for runtime execution
- `PROOF.md` produces evidence for `REVIEW.md`
- `REVIEW.md` produces authorization for `INTEGRATION.md`
- `INTEGRATION.md` produces dependency satisfaction for downstream issues

## Invariants

The contract layer preserves these invariants:

1. Issue remains the atomic executable unit.
2. Dependencies determine sequencing.
3. Proof precedes review.
4. Review precedes integration.
5. Integration precedes downstream dependency satisfaction.
6. Higher-level artifacts never bypass lower-level gate requirements.
7. Agents remain resources rather than the control structure.

## Remaining Work Required Before v1.0

1. Decide whether the contract layer should be wired explicitly into the top-level `.cursor` discovery path.

2. Validate the contract model against a supervised real module execution in a live repository.

3. Decide whether explicit contract examples are needed later for training and onboarding without bloating the canonical layer.

4. Decide whether compatibility and optional contract classes ever need separate dedicated documents or if the current layer is sufficient.

5. Determine whether future implementation tooling should read contract requirements directly from these documents or from a later machine-readable derivative.
