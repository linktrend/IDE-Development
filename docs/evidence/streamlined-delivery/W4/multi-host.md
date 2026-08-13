# W4 multi-host correction evidence

## Scope and authority

- Repository: `linktrend/IDE-Development`
- Worktree: `issue/221-w4-multi-host-coordinator-capacity`
- Implementation base: `d6ca472e809766304c1e891b1d44cdf7b84eb865`
- Current Mac Mini production posture: the committed fixture contains exactly
  one enabled `mac-mini-primary` worker; no service or live registry was
  installed or changed.
- No launchd, live coordinator database, GitHub ruleset/secret, PR, merge,
  promotion, tag, release, or unrelated repository was touched.

## Implemented proof surfaces

- `host/coordinator/workers.py`: stable worker identity, platform/arch,
  isolated trust, explicit fast/heavy/nestedDocker capability, resource and
  concurrency limits, heartbeat and enabled/draining/offline lifecycle,
  allowlist, and safe registry commands.
- `host/coordinator/queue.py` and `host/coordinator/multihost.py`: one durable
  queue, priority/repository fairness, capability and pressure admission,
  atomic leases, renewal, expiry recovery, fenced stale results, and global
  attempt preservation across reassignment.
- `host/coordinator/executor.py`: candidate execution rejects privileged trust,
  requires explicit isolated worker identity/capability metadata, and retains
  disposable Linux-container/socket/mount protections.
- `scripts/gitops/coordinator/receipts.py` plus the gate-receipt schema:
  worker ID/capabilities/trust, coordinator identity/version, and execution
  environment metadata are carried without changing exact repository/tree/
  dependency/profile reuse rules; legacy v1 receipts remain readable.
- `.github/linktrend-delivery-mode.json`: complete frozen schema v2
  `phase-integration` / `local-coordinator` policy with repository-relative
  fast/full/release commands.

## Focused validation

Passing commands:

```text
python3 -m unittest discover -s host/coordinator/tests -v       # 45 tests
env PYTHONPATH=scripts python3 -m unittest discover -s scripts/tests -p 'test_*.py' -v  # 55 tests
env PYTHONPATH=scripts python3 -m unittest discover -s scripts/ide_development_tests -v  # 73 tests
env PYTHONPATH=scripts python3 -m ide_development.build_manifest --verify
bash scripts/tests/test_local_coordinator_workflow_profile.sh
bash scripts/tests/test-gitops-phase-delivery.sh
bash tests/test-portable-v2-integration.sh
bash scripts/verify-ide-development.sh
git diff --check
```

The focused W4 tests exercise second Mac/Linux registration, capability
matching, nestedDocker explicitness, fairness, pressure, drain, stale
heartbeat/offline, duplicate pickup fencing, lease expiry, in-flight
reassignment with unchanged attempt `1`, no privileged/VPS escalation, exact
receipt reuse, and policy validation.

## Negative probes

- Privileged/coordinator/admin/root worker trust is rejected, including a
  Linux/VPS registration.
- A worker without the required heavy or nestedDocker capability cannot claim
  that job.
- Draining/offline workers cannot claim new work.
- CPU pressure pauses admission.
- A second worker cannot claim an already leased job.
- A late result from an expired lease is rejected as stale/duplicate.
- Lease reassignment preserves the candidate identity and attempt number.
- Candidate-provided command payload does not replace protected execution
  policy; existing daemon test remains passing.
- Existing socket, broad mount, shell-string, and scoped cleanup rejection
  probes remain passing.

## Known unrelated validation hold

`bash tests/test-portable-v2-integration.sh --full` reaches the historical
`scripts/tests/test-managed-core-release-publisher.sh` fixture and fails before
W4 code is exercised because that fixture expects package version `2.1.3`,
while this repository is intentionally and independently verified at `2.2.0`.
The default portable harness and the direct correctly configured 73-test
managed-core suite pass. This stale fixture is not changed by W4.
