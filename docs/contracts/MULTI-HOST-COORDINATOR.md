# W4 multi-host coordinator contract

W4 makes Streamlined Delivery multi-host-capable while keeping the current Mac
Mini as the only enabled production worker. The coordinator owns one global
SQLite queue and worker registry. A worker is a capacity-bearing, isolated
candidate executor; it is not a GitHub authority, a promotion actor, or a
privileged coordinator.

## Worker registry

Every worker has a stable `workerId`, platform, architecture, exact
`isolated-candidate` trust, explicit capabilities (`fast`, `heavy`, and only
when deliberately enabled `nestedDocker`), concurrency/resource limits,
heartbeat interval, enabled/draining/offline state, and an owner repository
allowlist. A registration carrying `privileged`, `coordinator`, `admin`, or
`root` trust/role is rejected. That rule also applies to Linux/VPS
registrations; VPS status cannot escalate trust.

The committed fixture at
`host/coordinator/fixtures/current-mac-mini-workers.json` contains exactly one
enabled worker: `mac-mini-primary` (`macos/arm64`). It is a registration
fixture, not a launchd instruction and not live-state evidence. The worker must
heartbeat before dispatch; three missed heartbeat intervals classify it as
offline.

Safe local commands use the coordinator database selected by `--db`:

```text
python3 -m host.coordinator --db PATH worker register --definition worker.json
python3 -m host.coordinator --db PATH worker inspect
python3 -m host.coordinator --db PATH worker drain WORKER_ID
python3 -m host.coordinator --db PATH worker disable WORKER_ID
python3 -m host.coordinator --db PATH worker enable WORKER_ID
python3 -m host.coordinator --db PATH worker heartbeat WORKER_ID
python3 -m host.coordinator --db PATH worker remove WORKER_ID
```

These commands edit only the selected local registry. They do not install or
load launchd, change GitHub rules, create credentials, or touch live candidate
checkouts. Drain stops new leases and allows existing work to finish; disable
also prevents new heartbeats from making the worker eligible; remove is for a
worker with no active lease and is reversible only by re-registering the same
stable identity and exact allowlist.

## Queue, leases, and fairness

All repositories and priorities share the coordinator queue. The queue first
selects the highest-priority eligible band, then rotates repositories within
that band so one repository cannot monopolize equal-priority capacity. A job
is eligible only when its repository is allowlisted, its required capability
matches, the worker has capacity, and host pressure is below configured
thresholds. `nestedDocker` is never inferred from `heavy`.

Claiming a job creates one central lease token and starts the candidate's
global attempt. Renewal is accepted only from the current worker and token.
An expired lease marks the in-flight assignment lost, returns the same job to
the queue, and reuses the same attempt number on reassignment. A late result
from the old token is rejected, so loss recovery cannot produce duplicate
completion. A completed lease clears the token atomically.

## Trust and receipts

Candidate commands pass only through the existing disposable Linux-container
executor. The host Docker socket, broad mounts, host shell, credentials, and
privileged coordinator operations remain outside candidate execution. Worker
receipt provenance records worker ID, capabilities, isolated trust,
coordinator identity/version, and execution environment. Candidate reuse still
requires the exact repository, Git tree SHA, dependency digest set, and test
profile; worker changes do not weaken that identity rule.

## Future Mac/Linux/VPS rollout and rollback

To add a future machine, prepare a no-secret JSON definition, register it in a
disposable or operator-selected database, heartbeat it, and run the focused W4
tests before enabling it. Start with `drain` and inspect active leases before
maintenance. Marking a machine offline or allowing its lease to expire causes
central reassignment; it does not create a second queue.

Rollback is local and bounded: drain or disable the new worker, wait for
active leases to finish or expire, inspect that the Mac Mini is the sole
enabled worker, and restore the previous coordinator/package version using the
existing transaction journal. Do not delete the SQLite database during
rollback, because it contains exact attempts, leases, receipts, and alerts.
No VPS deployment, launchd mutation, GitHub ruleset/secret change, PR, merge,
promotion, tag, or release is part of this packet.
