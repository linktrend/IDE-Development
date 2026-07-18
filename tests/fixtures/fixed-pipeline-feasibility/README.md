# Fixed-pipeline feasibility fixture

Disposable fixture for Phase 2 of the IDE Development ↔ LiNKdeveloper unification PRD.

This is **not** production doctrine. It proves that a session-scoped Cursor orchestrator plus a deterministic repository-resident transition validator can enforce the six-Module application pipeline fail-closed.

## Module order

1. `intake_and_definition`
2. `assembly_planning`
3. `execution`
4. `verification_and_hardening`
5. `library_contribution`
6. `shipment`

## Runner

```bash
bash scripts/feasibility/run-fixed-pipeline-feasibility.sh
```

Negative scenarios must leave fixture state unchanged and exit non-zero.
