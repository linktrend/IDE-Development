#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

python3 - <<'PY'
from pathlib import Path
import re

root = Path.cwd()
managed = root / "core/github/managed-workflows"
live = root / ".github/workflows"
owned = (
    "branch-source-policy.yml",
    "linktrend-review-packager.yml",
    "linktrend-integrator-merge.yml",
    "linktrend-development-to-staging.yml",
    "linktrend-staging-to-main.yml",
    "linktrend-cleanup-merged.yml",
    "linktrend-repair-observer.yml",
    "linktrend-review-ready-publisher.yml",
)

for name in owned:
    template = (managed / name).read_text(encoding="utf-8")
    counterpart = (live / name).read_text(encoding="utf-8")
    rendered = (
        template.replace("__LINKTREND_CI_WORKFLOW_NAME__", "CI")
        .replace("__LINKTREND_BRANCH_POLICY_WORKFLOW_NAME__", "Branch Source Policy")
        .replace("__LINKTREND_BUGBOT_CHECK_NAME__", "Cursor Bugbot")
        .replace("__LINKTREND_UNTRUSTED_RUNS_ON__", "ubuntu-24.04-arm")
        .replace("__LINKTREND_RUNS_ON__", "ubuntu-24.04-arm")
    )
    assert rendered == counterpart, f"managed/live parity mismatch: {name}"
    assert "ubuntu-24.04-arm" in template, f"hosted ARM runner missing: {name}"
    assert not re.search(r"self-hosted|macOS|ephemeral|create-github-app-token|LINKTREND_GITOPS_APP", template, re.I), name
    assert re.search(r"^permissions:\s*(?:\{\})?$", template, re.M), f"permissions missing: {name}"

fast = (managed / "linktrend-review-packager.yml").read_text(encoding="utf-8")
assert not re.search(r"^\s+push:", fast, re.M), "checkpoint push trigger reintroduced"
assert "name: Linktrend Fast Checks" in fast
assert "pull_request.number" in fast and "github.workflow" in fast
assert "cancel-in-progress: true" in fast
assert "timeout-minutes: 5" in fast

full = (managed / "linktrend-integrator-merge.yml").read_text(encoding="utf-8")
assert not re.search(r"^\s+push:", full, re.M), "full suite has a checkpoint trigger"
assert "name: Linktrend Full Suite" in full
for field in ("pr_number", "source_branch", "head_sha", "candidate_id", "seal_revision", "attempt"):
    assert f"{field}:" in full, field
assert "full-suite-receipt.json" in full
assert "retention-days: 30" in full
assert "@cursor review" in full
assert "linktrend-bugbot-requested" in full

for name in ("linktrend-development-to-staging.yml", "linktrend-staging-to-main.yml"):
    text = (managed / name).read_text(encoding="utf-8")
    assert "name: Linktrend Receipt Gate" in text
    assert "Linktrend Branch Source Policy" in text
    assert "gate_receipt.py" in text and "--gate full-gate" in text
    assert "download-artifact" in text
    assert "test-gitops-phase-delivery.sh" not in text
    assert not re.search(r"^\s+workflow_run:", text, re.M)

print("PASS: W2-P1 workflow names, events, runner, parity, and gate wiring")
PY

PYTHONPATH=scripts python3 - <<'PY'
from gitops.phase_integrator import phase_full_suite_dispatch_allowed

head = "a" * 40
record = {
    "sealed": True,
    "sealedSha": head,
    "sealRevision": 1,
    "phaseBranch": "phase/demo",
    "candidateId": "sha256:" + "b" * 64,
    "candidateIdentity": {"sourceSha": head},
    "fast": {"status": "passed", "sha": head},
    "bugbot": {"status": "not-run"},
    "full": {"status": "not-run"},
}
ok, detail, dispatch = phase_full_suite_dispatch_allowed(record, live_head_sha=head, pr_number=7)
assert ok and detail == "current_sealed_candidate"
assert dispatch == {
    "pr_number": "7",
    "source_branch": "phase/demo",
    "head_sha": head,
    "candidate_id": "sha256:" + "b" * 64,
    "seal_revision": "1",
    "attempt": "1",
}
blocked, reason, _ = phase_full_suite_dispatch_allowed(record, live_head_sha="c" * 40, pr_number=7)
assert not blocked and reason == "sealed_head_stale"
record["full"] = {"status": "requested", "sha": head}
blocked, reason, _ = phase_full_suite_dispatch_allowed(record, live_head_sha=head, pr_number=7)
assert not blocked and reason == "full_suite_already_requested"
record["full"] = {"status": "failed", "attempt": 2, "sha": head}
blocked, reason, _ = phase_full_suite_dispatch_allowed(record, live_head_sha=head, pr_number=7)
assert not blocked and reason == "full_suite_attempt_limit"
print("PASS: exact-head full-suite dispatch negative probes")
PY
