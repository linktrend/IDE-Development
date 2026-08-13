# W1-P2 validation evidence

This evidence is sanitized: it contains no credentials, host secrets, GitHub
responses, or untrusted command output.

- Packet: W1-P2 exact-content gate receipts
- Immutable implementation base: `9d8ca8794ce1bee8e07e71826eaaccebffc650f2`
- Branch: `issue/214-w1-p2-streamlined-delivery-exact-content-gate-re`
- Scope: receipt schema, receipt library, CLI, and unit tests only

Validation performed locally:

- `python3 -m unittest scripts.tests.test_gate_receipts` — PASS, 9 tests
- `python3 -m py_compile scripts/gitops/coordinator/receipts.py scripts/gitops/gate_receipt.py` — PASS
- `python3 scripts/gitops/gate_receipt.py --help` — PASS; operations `identity`, `write`, and `verify` listed
- `git diff --check` — PASS

Negative probes covered by the unit tests:

- one-byte source change — `tree_mismatch`
- one-byte dependency change — `dependency_mismatch`
- repository, gate, and profile changes — stable mismatch codes
- failed status — `receipt_not_passed`
- evidence digest mutation — `evidence_mismatch`
- malformed SHA — `invalid_sha`
- path traversal and symlink escape — `invalid_path`
- corrupt JSON — `invalid_receipt`
- interrupted atomic replacement preserves the prior receipt

No GitHub API, Docker, workflow, promotion, installation, PR, merge, ruleset,
or live-host operation was used.
