# W1-P1 — Delivery Configuration and Lifecycle State

## Assignment

Implement the versioned configuration and deterministic state-transition foundation used by every later packet. Terra supplies immutable Wave base `B0`. This packet may run with W1-P2 and W1-P3.

## Required reading

- `../IMPLEMENTATION-PLAN.md`
- `../FROZEN-INTERFACES.md`
- `docs/contracts/DELIVERY-MODES.md`
- `core/managed-core/schemas/delivery-modes.schema.json`
- `scripts/gitops/delivery_modes.py`
- `scripts/tests/test-gitops-phase-delivery.sh`

## Owned paths

- `core/managed-core/schemas/delivery-modes.schema.json`
- new `core/managed-core/schemas/delivery-runtime.schema.json`
- `scripts/gitops/delivery_modes.py`
- new `scripts/gitops/coordinator/__init__.py`
- new `scripts/gitops/coordinator/config.py`
- new `scripts/gitops/coordinator/state.py`
- new `scripts/tests/test_streamlined_delivery_config.py`
- `docs/evidence/streamlined-delivery/W1-P1/**`

## Required implementation

1. Preserve existing version-1 configuration.
2. Add version 2 exactly as specified in `FROZEN-INTERFACES.md`.
3. Reject unknown properties and unsafe commands.
4. Normalize relative command paths without allowing repository escape.
5. Enforce two attempts, two sealed revisions, fast target no more than 300 seconds, one or two fast jobs, and one heavy job.
6. Model every lifecycle state listed in the implementation plan.
7. Implement a pure transition function that rejects illegal order, stale identities, terminal-state mutation, and a third sealed candidate.
8. Implement atomic JSON state serialization for tests and later coordinator import. SQLite is out of scope here.
9. Passive observation, deduplication, and pre-start cancellation must not increment attempts.
10. Return structured results, not human-text parsing.

## Tests and negative probes

- Existing v1 fixture loads unchanged.
- Complete v2 fixture normalizes deterministically.
- Unknown field, absolute/outside command, invalid limits, stale SHA, promotion before gates, and third seal are rejected.
- `stopped`, `blocked`, and `main-promoted` cannot auto-transition.
- Interrupted atomic write preserves the previous valid state.
- Existing Phase delivery tests pass.

## Prohibited

No GitHub requests, workflow YAML, host executor/service, PR, merge, promotion, ruleset, installation, VERSION, INDEX, or MANIFEST change.

## Acceptance commands

```bash
python3 -m unittest scripts.tests.test_streamlined_delivery_config
bash scripts/tests/test-gitops-phase-delivery.sh
python3 -m py_compile scripts/gitops/coordinator/config.py scripts/gitops/coordinator/state.py
git diff --check
```

If module discovery is incompatible, use discovery scoped to the exact test file and record the replacement command.

## Handoff

Commit and push the packet branch. Report base SHA, branch, final local/remote SHA, changed files, commands and exit codes, negative probes, evidence directory, clean status, and blocker or `none`. Do not open a PR or mark review-ready.

