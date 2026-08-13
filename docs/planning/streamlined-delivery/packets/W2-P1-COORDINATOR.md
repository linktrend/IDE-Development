# W2-P1 — Mac Mini Coordinator Service

## Assignment

Implement the versioned local coordinator, queue, GitHub adapter, service lifecycle, CLI, and installer using integrated Wave 1 interfaces. Terra supplies verified `B1`. This packet may run with W2-P2 and W2-P3.

## Dependencies and reading

All Wave 1 packets must be integrated and passing. Read the implementation plan, frozen interfaces, Terra runbook, integrated Wave 1 modules, and `docs/contracts/GITHUB-APP-GITOPS-CREDENTIALS.md`.

## Owned paths

- new `host/coordinator/daemon.py`
- new `host/coordinator/github_client.py`
- new `host/coordinator/queue.py`
- new `host/coordinator/cli.py`
- new `host/coordinator/service.py`
- new `host/coordinator/__main__.py`
- new `host/macos/ai.linktrend.ide-coordinator.plist.template`
- new `scripts/host/install-ide-coordinator.py`
- new `scripts/host/uninstall-ide-coordinator.py`
- new `host/coordinator/tests/test_daemon.py`
- new `host/coordinator/tests/test_queue.py`
- new `host/coordinator/tests/test_github_client.py`
- new `host/coordinator/tests/test_installer.py`
- `docs/evidence/streamlined-delivery/W2-P1/**`

## Required implementation

1. One daemon manages an allowlisted repository registry.
2. Poll GitHub with ETags/conditional requests and bounded backoff.
3. Load execution policy only from protected default-branch content.
4. Persist queue, attempts, candidate identity, cancellation, and results in transactional SQLite with migrations.
5. Enqueue idempotently by repository/gate/candidate identity and use the frozen priority order without starvation.
6. Cancel work when a PR closes or identity changes.
7. Publish stable normal commit statuses; observe but never forge Cursor Bugbot.
8. Create/update one durable alert after attempt 2 failure and refuse attempt 3.
9. Recover truthful state after restart; distinguish jobs that started from those cancelled before start.
10. CLI: `status`, `pause`, `resume`, `enqueue`, `cancel`, `approve-main`, `doctor`.
11. Bind `approve-main` to exact staging source, current main base, PR head, and receipt.
12. Install versioned files atomically, retain one previous version, and render a secret-free launchd plist.
13. Rollback/uninstall affects only this service and scoped installation.

## Tests and negative probes

- Duplicate event produces one queue row.
- ETag not-modified performs no mutation.
- Rate limit/network/missing token backs off or fails closed without App fallback or attempt increment.
- Restart restores queue and terminal states.
- Stale/closed PR cancels.
- Second failure creates one alert; third attempt refused.
- Candidate cannot replace protected policy.
- Main approval rejects changed binding.
- Installer dry-run, atomic activation, rollback, and scoped uninstall pass.
- Logs contain no supplied test secret.

## Prohibited

No workflow YAML, Packager/Integrator/promotion changes, live installation, live GitHub mutation in tests, or version/manifest/release changes.

## Acceptance commands

```bash
python3 -m unittest discover -s host/coordinator/tests
python3 -m py_compile host/coordinator/*.py scripts/host/*.py
python3 -m host.coordinator --help
python3 scripts/host/install-ide-coordinator.py --help
git diff --check
```

## Handoff

Commit/push and report B1, exact SHA, files, migrations, tests, negative probes, installer dry-run, evidence, secret scan, clean state, and blocker or `none`. No live install, PR, review-ready, merge, or promotion.
