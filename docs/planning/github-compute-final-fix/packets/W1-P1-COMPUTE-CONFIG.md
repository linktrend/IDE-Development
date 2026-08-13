# W1-P1 — Compute Configuration and Hosted-Runner Routing

## Objective

Implement the configuration, validation, and routing foundation for GitHub-hosted
ARM64 compute. This packet must make self-hosted/Mac routing invalid in the new
profile without yet rewriting complete workflows.

## Dependencies and base

- Depends on Terra preflight and `FROZEN-INTERFACES.md`.
- Branch/worktree from immutable `B0`.
- May reuse and migrate current streamlined-delivery schemas and config loaders.

## Owned paths

- `core/managed-core/schemas/delivery-*.schema.json`
- managed default delivery configuration files discovered by preflight
- `scripts/gitops/coordinator/config.py` or its replacement config module
- `scripts/gitops/delivery_modes.py` only for configuration parsing/defaults
- configuration-focused tests under `scripts/tests/`
- corresponding source copies outside managed core when the repository convention
  requires mirrored authoritative files

Terra must remove a path from this packet if another packet owns it after live
inventory. Do not edit workflow YAML here.

## Required implementation

1. Add/migrate schema version for `github-hosted`, runner
   `ubuntu-24.04-arm`, checkpoint CI disabled, obsolete cancellation enabled,
   maximum two infrastructure attempts, maximum two sealed candidates, fast/full/
   release commands, and receipt-reuse identity fields.
2. Make the new profile the recommended/default new-install profile.
3. Reject unknown runner values and reject any `self-hosted`, Mac label, ephemeral
   runner label, or privileged runner selection in this profile.
4. Preserve explicit legacy-profile parsing only as a migration input; do not make
   it selectable after successful migration.
5. Preserve repository-owned command arrays exactly. Validate commands as arrays
   of non-empty strings and timeouts as bounded positive integers.
6. Produce deterministic normalized configuration and digest.
7. Give validation errors plain-English remediation without recommending the Mac
   runner or former custom App.

## Acceptance criteria

- Valid new config loads identically twice and produces the same digest.
- `ubuntu-24.04-arm` is rendered as a scalar hosted label, never a self-hosted
  label array.
- Checkpoint CI defaults false and cannot be silently enabled by a missing field.
- Tests reject self-hosted/Mac/ephemeral labels, more than two attempts, malformed
  commands, and receipt reuse without complete identity fields.
- Migration fixture maps current streamlined config to new hosted profile while
  preserving repository commands.
- No workflow, manifest, release, external GitHub setting, or consumer is changed.

## Validation

Run the existing config tests plus new focused tests. At minimum:

```bash
python3 -m unittest scripts.tests.test_streamlined_delivery_config
python3 -m compileall -q scripts/gitops
```

If module discovery differs, record and run the repository-equivalent command.

## Prohibited

- No PR, merge, promotion, workflow dispatch, runner registration, billing change,
  secret access, App change, host service change, installer/manifest/version edit,
  or consumer edit.
- Do not edit receipt/lifecycle behavior owned by W1-P2/W1-P3.

## Handoff

Commit one coherent change. Return the evidence record required by
`FROZEN-INTERFACES.md`, normalized config example, digest determinism proof, and
negative-test results.
