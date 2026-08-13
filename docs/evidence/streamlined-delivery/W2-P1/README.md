# W2-P1 coordinator evidence

This evidence is sanitized and records local, non-live verification of the
Mac Mini coordinator packet. No GitHub mutation, service activation, launchd
load, ruleset change, PR, merge, promotion, or installation was performed.

## Base

- Worktree branch: `issue/216-w2-p1-streamlined-delivery-coordinator`
- Integrated checkout base: `9e9abf4da7361e765f8c276d708035be261f8359`
- Requested B1 in the dispatch text: `9e9abf4da7361e765f8c276d708035be261f835a`
- The requested ending-`a` object is not present locally; the worktree is
  based on the integrated ending-`9` commit above.

## Acceptance and negative probes

Correction attempt 2 closes the launchd canary defect: the rendered
`ProgramArguments` now ends with the required safe-by-default `run` command.
The service loop performs bounded local poll/status passes, remains healthy
without `LINKTREND_AUTOMATION_TOKEN`, handles `SIGINT`, and does not enable
candidate execution from the launchd template.

| Probe | Result |
| --- | --- |
| `python3 -m unittest discover -s host/coordinator/tests` | PASS, 39 tests |
| `python3 -m py_compile host/coordinator/*.py scripts/host/*.py` | PASS |
| `python3 -m host.coordinator --help` | PASS |
| `python3 scripts/host/install-ide-coordinator.py --help` | PASS |
| `python3 scripts/host/uninstall-ide-coordinator.py --help` | PASS |
| `git diff --check` | PASS |
| Duplicate queue event | PASS: one request row |
| Conditional ETag 304 | PASS: no queue/candidate mutation |
| Rate limit and missing credential | PASS: bounded fail-closed; no attempt increment |
| Restart recovery | PASS: queued and interrupted states remain truthful |
| Closed/stale PR and identity change | PASS: obsolete work is cancelled |
| Second failure / third attempt | PASS: one durable local alert; third start refused |
| Candidate execution policy replacement | PASS: candidate command ignored |
| Changed main approval binding | PASS: rejected |
| Installer dry-run, atomic activation, rollback, scoped uninstall | PASS |
| Bugbot behavior | PASS: observation uses GET only; no review/status is forged |
| Secret scan of test output and rendered plist | PASS: no supplied test secret |

## Owned implementation

- `host/coordinator/daemon.py`
- `host/coordinator/github_client.py`
- `host/coordinator/queue.py`
- `host/coordinator/cli.py`
- `host/coordinator/service.py`
- `host/coordinator/__main__.py`
- `host/macos/ai.linktrend.ide-coordinator.plist.template`
- `scripts/host/install-ide-coordinator.py`
- `scripts/host/uninstall-ide-coordinator.py`
- `host/coordinator/tests/`

The SQLite migration is schema version 2 and includes repositories, jobs,
attempts, alerts, conditional-poll state, exact-bound approvals, and persisted
pause state. The
installer retains `current` and one `previous` version using scoped atomic
filesystem replacement. The launchd template contains no credential fields.

## Scope and blocker

No unrelated paths were changed. The only noted issue is the dispatch/base
identity discrepancy recorded above; no blocker was found in the implementation
or local acceptance probes.
