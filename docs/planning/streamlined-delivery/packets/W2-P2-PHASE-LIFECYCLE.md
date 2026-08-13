# W2-P2 — Phase Aggregation and Sealed PR Lifecycle

## Assignment

Implement the normal flow in which many verified Issue branches become one draft and later sealed Phase PR. Terra supplies verified `B1`. This packet may run with W2-P1 and W2-P3.

## Dependencies and reading

All Wave 1 packets must be integrated. Read the implementation plan, frozen interfaces, `docs/contracts/DELIVERY-MODES.md`, `docs/contracts/AGENT-COMPLETION.md`, and current Packager/Integrator scripts.

## Owned paths

- `scripts/gitops/completion_gate.py`
- `scripts/gitops/delivery_modes.py`
- `scripts/gitops/packager_discover.py`
- `scripts/gitops/packager_evaluate.py`
- `scripts/gitops/packager_logic.py`
- `scripts/gitops/integrator_evaluate.sh`
- new `scripts/gitops/phase_integrator.py`
- new `scripts/tests/test_phase_batch_lifecycle.py`
- new `scripts/tests/test_phase_concurrent_feature.py`
- `docs/evidence/streamlined-delivery/W2-P2/**`

## Required implementation

1. Recommend/default Phase integration for new v2 installs while honoring explicit `issue-pr` configuration.
2. Checkpointing an Issue creates no PR and calls no Bugbot.
3. Record independent Issue acceptance against exact pushed SHA.
4. Only the Integrator may mutate Phase branch/record.
5. Prove every accepted Issue SHA is an ancestor of Phase head.
6. Reject duplicate Issues, stale tips, missing acceptance, wrong base, and unproven inclusion.
7. Permit one early draft Phase PR for visibility; unsealed updates do not request Bugbot/full suite.
8. Seal exact Phase head/candidate identity and allow only revisions 1 and 2.
9. Any head change invalidates prior candidate gates.
10. Request Bugbot exactly once after current sealed candidate's fast success.
11. Merge eligibility requires current seal, fast success, Bugbot success, full success/not-required, no conflict, and unchanged live head.
12. Preserve risk-based standalone Issue PR exceptions.
13. Concurrent development movement requires explicit Phase synchronization and fresh seal.
14. Maintain all frozen Phase record fields.

## Tests and negative probes

- Three Issue tips yield one draft Phase PR and no normal Issue PR.
- Explicit issue-pr behavior remains.
- Duplicate/stale/unaccepted/unincluded Issue rejected.
- Non-Integrator mutation rejected.
- Bugbot absent before seal/fast success and invoked once after.
- Head change invalidates gates.
- Revision 2 allowed and revision 3 rejected.
- Concurrent feature commit survives synchronization.
- Merge conflict blocks without side preference.
- Valid risk exception remains supported.

## Prohibited

No workflow YAML, host daemon/executor, promotion scripts, live GitHub mutations in tests, or VERSION/INDEX/MANIFEST/generated-copy changes.

## Acceptance commands

```bash
python3 -m unittest scripts.tests.test_phase_batch_lifecycle scripts.tests.test_phase_concurrent_feature
bash scripts/tests/test-gitops-phase-delivery.sh
bash scripts/tests/test-gitops-review-packager.sh
bash scripts/tests/test-integrator-bugbot-gate.sh
git diff --check
```

## Handoff

Commit/push and report B1, exact SHA, files, tests, negative probes, three-Issue/one-PR proof, concurrent-feature proof, clean state, and blocker or `none`. No live PR, merge, review-ready, or promotion.
