# W1-P3 — Exact Receipts, Promotion Reuse, and Authentication Boundary

## Objective

Implement pure receipt creation/verification and promotion eligibility so one
successful full suite can be reused for identical staging/main content. Remove
custom-App assumptions from these modules without yet deleting all legacy files.

## Dependencies and base

- Depends on Terra preflight and frozen candidate/receipt/auth interfaces.
- Branch/worktree from immutable `B0`.
- Use W1-P1/W1-P2 fixtures until Wave 1 integration.

## Owned paths

- `scripts/gitops/gate_receipt.py`
- `scripts/gitops/promotion_receipt_gate.py`
- `scripts/gitops/coordinator/receipts.py`
- `core/managed-core/schemas/gate-receipt.schema.json`
- receipt/promotion/auth-boundary focused tests
- a new minimal authentication-policy helper if Terra assigns it

Do not edit workflow YAML, promotion shell orchestration, installer, or manifest.

## Required implementation

1. Create/validate the frozen FullSuiteReceipt fields and deterministic digest.
2. Calculate Git tree through Git, not a timestamp or branch-name shortcut.
3. Calculate dependency identity from declared lockfiles/manifests and profile/
   workflow identity from canonical bytes.
4. Bind receipt to repository and successful recognized workflow run/attempt.
5. Reject failure/cancelled/skipped conclusions, superseded heads, wrong repository,
   changed tree, changed dependency/profile/workflow digest, malformed schema,
   altered evidence, or unknown runner label.
6. Accept different merge commit SHAs only when every reusable identity input is
   equal; record both source and promotion commits for lineage.
7. Produce short machine-readable PASS/HOLD output for promotion workflows.
8. Remove calls that require minting the former custom App token. Pure receipt
   verification must require no privileged credential.
9. Document in code that GitHub's built-in `GITHUB_TOKEN` is permitted only at the
   later workflow boundary with explicit least privilege.
10. Preserve enough receipt retention/lookup metadata to complete main promotion.

## Acceptance criteria

- Exact identity passes at development, staging, and main fixtures.
- Different commit with identical tree and dependency identity passes.
- One-byte file change, lockfile change, profile change, workflow change, wrong
  repo, tampered digest, failed run, or superseded candidate fails closed.
- No custom App environment variable is needed by the receipt unit tests.
- Output never prints credentials or secret values.
- Existing receipt fixtures migrate or fail with an explicit unsupported-version
  message; they are never silently trusted.

## Validation

```bash
python3 -m unittest scripts.tests.test_gate_receipts
python3 -m unittest scripts.tests.test_promotion_receipt_gate
python3 -m compileall -q scripts/gitops
```

## Prohibited

- No workflow, PR, merge, promotion, billing, external secret/App, runner, Docker,
  host, installer, manifest, release, or consumer change.
- Do not weaken identity to commit-message, branch-name, or mutable artifact URL.

## Handoff

Return one exact commit, schema example, receipt digest example, positive and
negative matrix, and a list of remaining legacy App callers for W2-P2/W2-P3.
