# W1-P3 executor and resource evidence

Date: 2026-08-13 (Asia/Taipei)
Immutable implementation base: `9d8ca8794ce1bee8e07e71826eaaccebffc650f2`
Branch: `issue/215-w1-p3-streamlined-delivery-isolated-executor-and`

This evidence is sanitized. It contains no credentials, host paths, candidate
source, GitHub mutations, or live service state.

## Implementation boundary

- Admission is a pure decision in `host/coordinator/resources.py`.
- Execution uses `subprocess.Popen` with `shell=False` and a Docker argv only.
- Docker argv includes explicit `linux/amd64` platform, CPU, memory,
  memory-swap, PID, stop-timeout, name, coordinator/job labels, scoped bind
  mount, read-only root, network isolation, and working directory.
- Cleanup uses exact coordinator and job labels plus the registered container
  name. Startup recovery inventories only the coordinator label.
- Temporary checkout removal requires an explicit job workspace root and an
  owned temporary-checkout flag. Broad targets fail closed.
- Nested Docker is accepted only with protected, positive image/memory/PID
  bounds; the host Docker socket is always rejected.

## Acceptance commands

| Command | Result |
| --- | --- |
| `python3 -m unittest discover -s host/coordinator/tests -p 'test_executor.py'` | PASS — 10 tests |
| `python3 -m unittest discover -s host/coordinator/tests -p 'test_resources.py'` | PASS — 5 tests |
| `python3 -m py_compile host/coordinator/executor.py host/coordinator/resources.py host/coordinator/cleanup.py` | PASS |
| `git diff --check` | PASS |

## Required negative probes

- Third fast admission refused after two active fast jobs.
- Overlapping heavy admission refused after one active full/release job.
- CPU, memory, disk, Docker-unavailable, and interactive-use pressure each
  pause admission.
- Shell-string candidate command rejected; an accepted command appears only
  after the Docker image in the argv.
- Checkout escape, broad cleanup target, invalid volume, and host Docker socket
  mount rejected.
- Cancellation and timeout terminate the fake container process.
- Startup recovery removes the labelled orphan but preserves the active job.
- Docker cleanup failure is returned and remains visible.
- Secret-like output is redacted before structured evidence.

## Bounded real smoke

- Image: `alpine:3.20`
- Candidate command: bounded `sh` printf probe inside the disposable container.
- Result: PASS, exit code `0`, structured cleanup `success=true`.
- Container name: unique explicit coordinator name for the run.
- Exact-name post-check: PASS — `docker ps -a` returned no matching name.
- Temporary checkout: removed only through the registered job workspace scope.

No GitHub API, status, PR, workflow, launchd, service, ruleset, promotion, or
Docker Desktop configuration operation was performed.
