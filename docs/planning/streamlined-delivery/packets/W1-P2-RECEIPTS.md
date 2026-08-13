# W1-P2 — Exact-Content Gate Receipts

## Assignment

Implement deterministic creation and verification of test receipts so staging and main reuse a full-suite result only for identical content and dependencies. Terra supplies immutable `B0`. This packet may run with W1-P1 and W1-P3.

## Required reading

- `../IMPLEMENTATION-PLAN.md`
- `../FROZEN-INTERFACES.md`
- `core/github/CI-GATE-CONTRACTS.md`
- existing exact-SHA and release-candidate helpers under `scripts/gitops/`

## Owned paths

- new `core/managed-core/schemas/gate-receipt.schema.json`
- new `scripts/gitops/coordinator/receipts.py`
- new `scripts/gitops/gate_receipt.py`
- new `scripts/tests/test_gate_receipts.py`
- `docs/evidence/streamlined-delivery/W1-P2/**`

W1-P1 owns `scripts/gitops/coordinator/__init__.py`; do not create or modify it.

## Required implementation

1. Implement the frozen Candidate Identity and Receipt shapes.
2. Compute the Git tree through Git, never by assuming commit identity.
3. Hash every configured dependency file after proving it is relative, present, regular, and not a symlink escape.
4. Canonically order dependency entries and JSON.
5. Create a receipt only for a completed successful result.
6. Write atomically.
7. Verify repository, gate, tree, dependencies, profile, passed status, evidence digests, and full SHAs.
8. Accept different commit SHAs only when complete tree and dependency identity match.
9. Return stable rejection codes: `repository_mismatch`, `gate_mismatch`, `tree_mismatch`, `dependency_mismatch`, `profile_mismatch`, `receipt_not_passed`, `evidence_mismatch`, `invalid_sha`, `invalid_path`, and `invalid_receipt`.
10. CLI operations: `identity`, `write`, and `verify`.

## Tests and negative probes

- Exact identity and different-commit/same-tree cases pass.
- One-byte source, dependency, repository, gate, profile, failed status, evidence, malformed SHA, path escape, and corrupt JSON cases fail.
- Canonical output is byte-stable.
- Interrupted atomic write preserves the previous receipt.

## Prohibited

No GitHub API, Docker, workflows, promotion, package/version/manifest changes, PR, merge, ruleset, or installation.

## Acceptance commands

```bash
python3 -m unittest scripts.tests.test_gate_receipts
python3 -m py_compile scripts/gitops/coordinator/receipts.py scripts/gitops/gate_receipt.py
python3 scripts/gitops/gate_receipt.py --help
git diff --check
```

## Handoff

Commit/push checkpoint and report immutable base, exact pushed SHA, owned-path diff, tests, negative probes, evidence, clean state, and blocker or `none`. No PR and no review-ready.

