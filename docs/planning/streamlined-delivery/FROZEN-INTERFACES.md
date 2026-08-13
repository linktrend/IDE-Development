# Frozen Interfaces for Parallel Execution

These interfaces are fixed before Wave 1 dispatch. A Luna executor must implement against them and must not rename, broaden, or redesign them. If an interface is impossible, the executor reports a blocker; Terra decides whether to revise the plan before integration.

## 1. Configuration file

Repository path: `.github/linktrend-delivery-mode.json`.

Version 1 remains readable. Version 2 adds:

```json
{
  "schemaVersion": 2,
  "deliveryMode": "phase-integration",
  "phaseBranchPrefix": "phase/",
  "orchestrationMode": "local-coordinator",
  "fastTargetSeconds": 300,
  "maxAttemptsPerCandidate": 2,
  "maxSealedCandidateRevisions": 2,
  "maxFastJobs": 2,
  "maxHeavyJobs": 1,
  "stagingPromotion": "automatic",
  "mainPromotion": "principal-approval",
  "testProfiles": {
    "fast": {"commands": [], "timeoutSeconds": 300},
    "full": {"required": false, "commands": [], "timeoutSeconds": 3600},
    "release": {"commands": [], "timeoutSeconds": 300}
  },
  "dependencyFiles": [],
  "resourceLimits": {
    "fastCpus": 1.0,
    "fastMemoryMiB": 2048,
    "heavyCpus": 2.0,
    "heavyMemoryMiB": 4096,
    "pidsLimit": 768,
    "pauseCpuPercent": 80,
    "pauseMemoryPercent": 80,
    "minimumFreeDiskGiB": 20
  }
}
```

Commands are relative executable paths or argument arrays validated from the protected default-branch policy. Candidate branches cannot introduce or alter the policy used to execute themselves.

## 2. Coordinator package API

Python package roots:

- shared installed/consumer logic: `scripts/gitops/coordinator/`;
- host-only daemon/execution logic: `host/coordinator/`.

Required callable boundaries:

```python
load_delivery_config(repo_root_or_payload) -> DeliveryConfig
load_state(state_id) -> DeliveryState | None
transition(state, event) -> DeliveryState

compute_candidate_identity(repo_path, dependency_files) -> CandidateIdentity
write_receipt(result, output_path) -> GateReceipt
verify_receipt(receipt, candidate_identity, required_gate) -> ReceiptVerdict

admit_job(request, host_snapshot, running_jobs) -> AdmissionVerdict
run_job(job, limits, cancellation) -> ExecutionResult
cleanup_job(job_id) -> CleanupResult

enqueue(request) -> QueueResult
cancel_obsolete(repository, pr_number, live_identity) -> list[str]
publish_status(repository, sha, context, state, description, target_url) -> None
```

Exact class internals are packet-owned, but the behavior and semantic arguments above are fixed.

## 3. Candidate identity

Identity is not merely a commit SHA:

```json
{
  "repository": "owner/name",
  "sourceSha": "40 lowercase hex",
  "gitTreeSha": "40 lowercase hex",
  "dependencyDigests": {
    "relative/path": "sha256:64 lowercase hex"
  },
  "testProfile": "fast|full|release"
}
```

Promotion may have a different commit SHA. Reuse is allowed only when Git tree, dependency digests, repository, and required test profile match.

## 4. Receipt

Required fields:

```json
{
  "schemaVersion": 1,
  "status": "passed",
  "repository": "owner/name",
  "gate": "fast-gate|full-gate|staging-gate|release-gate",
  "sourceSha": "40 lowercase hex",
  "testedCheckoutSha": "40 lowercase hex",
  "gitTreeSha": "40 lowercase hex",
  "dependencyDigests": {},
  "testProfile": "fast|full|release",
  "attempt": 1,
  "coordinatorVersion": "released semantic version",
  "startedAt": "RFC3339 UTC",
  "completedAt": "RFC3339 UTC",
  "evidenceDigests": {},
  "github": {"pullRequest": null, "runUrl": null}
}
```

Only `passed` receipts are reusable. Receipt writes are atomic.

## 5. State and attempt keys

State identity:

`repository | phaseBranch | phaseId`

Attempt identity:

`repository | gate | gitTreeSha | canonical dependency digest set`

Attempt increments only after execution starts. Cancellation before execution does not increment it.

Terminal automatic states:

- `main-promoted`
- `stopped`
- `blocked`
- `cancelled`

## 6. Status contexts

These names are stable:

- `Linktrend Fast Gate`
- `Linktrend Full Suite`
- `Linktrend Phase Ready`
- `Linktrend Staging Gate`
- `Linktrend Release Gate`
- `Linktrend Coordinator`
- external unchanged: `Cursor Bugbot`

Branch rules require only the contexts appropriate to that target branch. Statuses bind to the exact candidate SHA and include a target URL to sanitized evidence or coordinator status.

## 7. Queue priorities

Lower number is higher priority:

1. Explicit manual urgent request.
2. Active Phase fast gate.
3. Staging/main receipt verification and short release gate.
4. Active Phase full suite.
5. Background cleanup or compatibility work.

Priority never overrides resource admission, trust boundaries, two-attempt stops, or exact identity.

## 8. Phase record additions

The Phase record must include:

- phase ID and branch;
- immutable base SHA;
- accepted Issue branch and exact SHA entries;
- proof each Issue SHA is included;
- draft PR identity when created;
- seal revision 1 or 2;
- sealed SHA and candidate identity;
- fast, Bugbot, full, staging, and release results;
- merge and promotion SHAs;
- stop/block reason when applicable.

## 9. Alerts

After the second failure, create exactly one durable GitHub Issue/update keyed by repository, phase, gate, and candidate identity. It must report attempts, failure category, sanitized command result, evidence location, and required human action. Re-observation must update the same record, not create duplicates.

## 10. Main approval

- `principal-approval`: coordinator creates/verifies the main PR and waits for `approve-main` bound to exact staging SHA, main base SHA, PR head SHA, and receipt identity.
- `automatic`: coordinator may merge after all exact gates pass.

The implementation must support both. Default is `principal-approval`.

