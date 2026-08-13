# W1-P3 — Isolated Executor and Resource Governor

## Assignment

Implement host-side admission, disposable container execution, cancellation, and scoped cleanup without GitHub orchestration. Terra supplies immutable `B0`. This packet may run with W1-P1 and W1-P2.

## Required reading

- `../IMPLEMENTATION-PLAN.md`
- `../FROZEN-INTERFACES.md`
- `docs/contracts/ACTIONS-COST-CONTROLS.md`
- `scripts/tests/test-managed-runner-routing.sh`

## Owned paths

- new `host/coordinator/__init__.py`
- new `host/coordinator/executor.py`
- new `host/coordinator/resources.py`
- new `host/coordinator/cleanup.py`
- new `host/coordinator/tests/__init__.py`
- new `host/coordinator/tests/test_executor.py`
- new `host/coordinator/tests/test_resources.py`
- `docs/evidence/streamlined-delivery/W1-P3/**`

## Required implementation

1. Separate admission from execution.
2. Admit at most two fast jobs and one heavy job; heavy jobs never overlap.
3. Pause admission when CPU, memory, disk, Docker, or interactive-use pressure exceeds configured limits.
4. Build Docker invocations with explicit platform, CPU, memory, memory-swap, PID, timeout, name, mount, and working-directory limits.
5. Candidate commands run in disposable Linux containers only, never through the host shell.
6. Validate every checkout, volume, and cleanup target against the job identity.
7. Cancel and remove timed-out, cancelled, or obsolete work.
8. Startup recovery removes only coordinator-labelled orphan resources.
9. Nested Docker requires protected configuration and a separately bounded disposable environment; never mount the host Docker socket into candidate code.
10. Sanitize logs and return structured execution/cleanup results.

## Tests and negative probes

- Two fast admitted and third refused.
- One heavy admitted and overlap refused.
- Host pressure and interactive-use pause admission.
- Candidate command appears only in Docker arguments.
- Path escape/broad cleanup rejected.
- Cancellation and timeout terminate fake containers.
- Startup removes labelled orphan only.
- Cleanup failure remains visible.
- One optional bounded real smoke container exits and disappears.

## Prohibited

No GitHub API/status/PR code, launchd installer, workflows, delivery modes, receipts, version/manifest files, runner removal, or Docker Desktop configuration change.

## Acceptance commands

```bash
python3 -m unittest discover -s host/coordinator/tests -p 'test_executor.py'
python3 -m unittest discover -s host/coordinator/tests -p 'test_resources.py'
python3 -m py_compile host/coordinator/executor.py host/coordinator/resources.py host/coordinator/cleanup.py
git diff --check
```

The real smoke must use a unique explicit container name and prove that exact name is absent afterward.

## Handoff

Commit/push and report base, branch, exact SHA equality, files, tests, negative probes, live smoke/cleanup, resource invocation, clean state, and blocker or `none`. No PR or review-ready.
