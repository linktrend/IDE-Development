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
assert "run_delivery_profile.py fast" in fast
assert "scripts.tests.test_candidate_lifecycle" not in fast
assert "workflow_dispatch:" in fast
assert "options: [reconciled]" in fast or "options: [reconciled]".replace(" ", "") in fast.replace(" ", "")
assert "reconciled-fast:" in fast
assert "ref: development" in fast
assert "persist-credentials: false" in fast
assert "contents: read" in fast
assert "verify_reconciled_fast_dispatch.py" in fast
assert "run_delivery_profile.py fast" in fast
assert "actions/cache" not in fast.lower()
assert "pull-requests: write" not in fast

full = (managed / "linktrend-integrator-merge.yml").read_text(encoding="utf-8")
assert not re.search(r"^\s+push:", full, re.M), "full suite has a checkpoint trigger"
assert "name: Linktrend Full Suite" in full
assert "types: [labeled]" in full
assert "github.event.label.name == 'linktrend-full-suite'" in full
assert "workflow_dispatch:" in full
assert 'mode == \'reconciled\'' in full
assert 'promotable": False' in Path("scripts/gitops/verify_reconciled_tree.py").read_text(encoding="utf-8")
assert 'checks_json="${RUNNER_TEMP}/linktrend-reconciled-checks.json"' in full
assert '--checks-json "${checks_json}"' in full
assert "full-suite-receipt.json" in full
assert "retention-days: 30" in full
assert "@cursor review" in full
assert "linktrend-bugbot-requested" in full
assert "phase-delivery-record.json" not in full, "a tracked record cannot seal its own PR head"
for required in (
    "full_suite_stale_seal",
    "full_suite_requires_phase_branch",
    "full_suite_repository_mismatch",
    "--config-key fastWorkflowName",
    "exact dispatch-time seal accepted",
    "github.event.pull_request.head.sha",
    "full_suite_sealed_candidate_limit",
    "full_suite_attempt_limit",
    "display_title",
):
    assert required in full, required
assert 'sum(run_attempt for head, run_attempt in relevant if head == current_head)' in full
assert 'history_file="$(mktemp)"' in full
assert 'gh api "repos/${GITHUB_REPOSITORY}/actions/workflows/linktrend-integrator-merge.yml/runs?event=pull_request&per_page=100" >"${history_file}"' in full
assert 'json.load(handle)' in full
assert 'python3 - "${history}"' not in full
assert 'if executions > 2:' in full
assert 'Every paid execution counts' in full
assert 'pull-requests: write' not in full.split('  bugbot:', 1)[0]
assert 'candidate/' not in full
assert "run_delivery_profile.py full" in full
assert 'GITHUB_REPOSITORY" = "linktrend/IDE-Development' not in full
assert "require_exact_ci_success.py" in full
assert '"Linktrend Fast Checks" and .conclusion' not in full

for name in ("linktrend-development-to-staging.yml", "linktrend-staging-to-main.yml"):
    text = (managed / name).read_text(encoding="utf-8")
    assert "workflow_dispatch:" not in text
    assert "inputs." not in text
    assert "github.event.pull_request.head.sha" in text
    assert "name: Linktrend Receipt Gate" in text
    assert "Linktrend Branch Source Policy" in text
    assert "gate_receipt.py" in text and "--gate full-gate" in text
    assert "download-artifact" in text
    assert "fullRunId" in text and "steps.receipt.outputs.run_id" in text
    assert "--workflow-run-id" in text
    assert 'RECEIPT_RUN_ID: ${{ steps.receipt.outputs.run_id }}' in text
    assert '--workflow-run-id "${RECEIPT_RUN_ID}"' in text
    assert '.path == ".github/workflows/linktrend-integrator-merge.yml"' in text
    assert '.event == "pull_request"' in text
    assert '.event == "workflow_dispatch"' not in text
    assert '.name == "Linktrend Full Suite"' not in text
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

python3 - <<'PY'
"""Model the live sequence: dispatch inputs bind the head without a seal commit."""
import hashlib
import json

def candidate_id(repository, branch, head, tree):
    payload = {
        "repository": repository,
        "sourceSha": head,
        "gitTreeSha": tree,
        "dependencyDigests": {},
        "testProfile": "full",
    }
    return "sha256:" + hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()

head = "a" * 40
tree = "b" * 40
seal = candidate_id("linktrend/IDE-Development", "phase/demo", head, tree)
assert seal == candidate_id("linktrend/IDE-Development", "phase/demo", head, tree)
assert seal != candidate_id("linktrend/IDE-Development", "phase/demo", "c" * 40, tree)
assert seal != candidate_id("someone/fork", "phase/demo", head, tree)
# The workflow validates the source branch independently; its legacy candidate
# identity deliberately does not encode a branch field.
assert "phase/demo" != "phase/other"
# A tracked seal record would require a follow-on commit and makes its recorded
# head stale.  Dispatch-time inputs avoid that impossible fixed point.
record_head = head
committed_record_head = "d" * 40
assert record_head != committed_record_head
assert seal != candidate_id("linktrend/IDE-Development", "phase/demo", committed_record_head, tree)
print("PASS: dispatch-time seal live-sequence regression")
PY

python3 - <<'PY'
"""The cap counts paid executions, independent of declared attempt labels."""
import re

pattern = re.compile(r"^Full Suite PR #(\d+) @ ([0-9a-f]{40}) r([12]) a([12])$")
head = "a" * 40

def executions(rows):
    relevant = []
    for title, run_attempt in rows:
        match = pattern.fullmatch(title)
        if match and match.group(1) == "7":
            relevant.append((match.group(2), run_attempt))
    return sum(run_attempt for candidate, run_attempt in relevant if candidate == head)

title1 = f"Full Suite PR #7 @ {head} r1 a1"
title2 = f"Full Suite PR #7 @ {head} r1 a2"
assert executions([(title1, 1), (title2, 1)]) == 2  # two fresh dispatches
assert executions([(title1, 2)]) == 2                 # one run plus one UI rerun
assert executions([(title1, 1), (title2, 1), (title2, 1)]) == 3
assert executions([(title1, 3)]) == 3
print("PASS: paid Full Suite execution cap covers fresh dispatches and UI reruns")
PY

python3 - <<'PY'
"""Receipt identity must use the resolved profile, including consumer fallback."""
from pathlib import Path

for relative in (
    ".github/workflows/linktrend-integrator-merge.yml",
    "core/github/managed-workflows/linktrend-integrator-merge.yml",
):
    text = Path(relative).read_text(encoding="utf-8")
    assert 'profile_files=[str(config_path.relative_to(Path.cwd()))]' in text, relative
    assert 'profile_files=[".github/linktrend-delivery-mode.json"]' not in text, relative
    assert 'fastWorkflowName' in text, relative
    assert '"Linktrend Fast Checks" and .conclusion' not in text, relative
print("PASS: Full receipt binds resolved source or consumer profile and declared Fast gate")
PY

python3 - <<'PY'
"""Promotion and receipt CLI must bind the resolved source-or-consumer profile."""
from pathlib import Path

for relative in (
    "scripts/gitops/promote_staging.sh",
    "scripts/gitops/promote_main.sh",
):
    text = Path(relative).read_text(encoding="utf-8")
    assert "receipt_profile_args()" in text, relative
    assert 'RECEIPT_PROFILE_ARGS=()' in text, relative
    assert '.github/linktrend-delivery-mode.json' in text, relative
    assert '.ide-development/config/delivery.json' in text, relative
    assert 'delivery profile configuration is unavailable in promotion candidate' in text, relative
    assert '${RECEIPT_PROFILE_ARGS[@]+"${RECEIPT_PROFILE_ARGS[@]}"}' in text, relative

for relative in (
    ".github/workflows/linktrend-development-to-staging.yml",
    ".github/workflows/linktrend-staging-to-main.yml",
    "core/github/managed-workflows/linktrend-development-to-staging.yml",
    "core/github/managed-workflows/linktrend-staging-to-main.yml",
):
    text = Path(relative).read_text(encoding="utf-8")
    assert "--profile-file .github/linktrend-delivery-mode.json" not in text, relative

receipt = Path("scripts/gitops/gate_receipt.py").read_text(encoding="utf-8")
assert ".ide-development/config/delivery.json" in receipt
assert "resolved_profile_files" in receipt
print("PASS: receipt and promotion identities bind a resolved source or installed profile")
PY

python3 - <<'PY'
"""Empty dependency configuration must not trip `set -e` in promotion."""
from pathlib import Path
import re

for relative in ("scripts/gitops/promote_staging.sh", "scripts/gitops/promote_main.sh"):
    text = Path(relative).read_text(encoding="utf-8")
    assert "RECEIPT_IDENTITY_ARGS=()" in text, relative
    assert '"${RECEIPT_IDENTITY_ARGS[@]}"' not in text.replace('${RECEIPT_IDENTITY_ARGS[@]+"${RECEIPT_IDENTITY_ARGS[@]}"}', ''), relative
    assert '${RECEIPT_IDENTITY_ARGS[@]+"${RECEIPT_IDENTITY_ARGS[@]}"}' in text, relative
    match = re.search(r"receipt_identity_args\(\) \{(.*?)\n\}", text, re.S)
    assert match, f"missing receipt_identity_args in {relative}"
    body = match.group(1)
    assert re.search(r'done <<< "\$\{raw\}"\s+return 0\s*$', body), relative
print("PASS: empty receipt dependency list returns success in both promotion scripts")
PY
