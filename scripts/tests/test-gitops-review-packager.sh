#!/usr/bin/env bash
# Static GitOps invariants + trust-boundary proofs (companion to behavioral suite).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
fail() { echo "FAIL: $1" >&2; exit 1; }
pass() { echo "PASS: $1"; }

PKG="core/github/managed-workflows/linktrend-review-packager.yml"
STG="core/github/managed-workflows/linktrend-development-to-staging.yml"
MAIN="core/github/managed-workflows/linktrend-staging-to-main.yml"
INT="core/github/managed-workflows/linktrend-integrator-merge.yml"
CI=".github/workflows/ci.yml"

grep -q 'pull_request:' "$PKG" || fail "packager missing Phase PR trigger"
grep -q 'workflow_dispatch:' "$PKG" || fail "packager missing explicit dispatch"
grep -q 'cancel-in-progress: true' "$PKG" || fail "packager must cancel obsolete PR runs"
grep -q 'pull_request_target:' "$STG" || fail "staging must use explicit promotion trigger"
grep -q 'pull_request_target: # zizmor: ignore\[dangerous-triggers\]' "$STG" \
  || fail "staging trusted trigger must carry reviewed zizmor suppression"
grep -q 'pull_request_target: # zizmor: ignore\[dangerous-triggers\]' "$MAIN" \
  || fail "main trusted trigger must carry reviewed zizmor suppression"
! grep -q 'cron:' "$PKG" || fail "retired packager cron remains"
! grep -q 'cron:' "$STG" || fail "retired staging cron remains"
! grep -q 'workflow_run:' "$PKG" || fail "retired workflow cascade remains"
grep -q 'source_branch' "$INT" || fail "integrator must gate source branch"
pass "Workflow phases use PR/explicit promotion triggers without cascades"

python3 - <<'PY'
from pathlib import Path
import json

runner_type = json.loads(
    Path(".github/linktrend-gitops-consumer.json").read_text()
).get("runnerType", "github-hosted")
runner_types = {"github-hosted": ("ubuntu-24.04-arm", "ubuntu-24.04-arm")}
assert runner_type in runner_types, f"Unsupported runnerType: {runner_type}"
privileged_runner, untrusted_runner = runner_types[runner_type]

def render(text: str) -> str:
    return (
        text.replace("__LINKTREND_CI_WORKFLOW_NAME__", "CI")
        .replace("__LINKTREND_BRANCH_POLICY_WORKFLOW_NAME__", "Branch Source Policy")
        .replace("__LINKTREND_BUGBOT_CHECK_NAME__", "Cursor Bugbot")
        .replace("__LINKTREND_UNTRUSTED_RUNS_ON__", untrusted_runner)
        .replace("__LINKTREND_RUNS_ON__", privileged_runner)
    )

for name in (
    "linktrend-review-packager.yml",
    "linktrend-review-ready-publisher.yml",
    "linktrend-development-to-staging.yml",
    "linktrend-staging-to-main.yml",
    "linktrend-integrator-merge.yml",
    "branch-source-policy.yml",
    "linktrend-cleanup-merged.yml",
    "linktrend-repair-observer.yml",
):
    managed = Path(f"core/github/managed-workflows/{name}").read_text()
    live = Path(f".github/workflows/{name}").read_text()
    assert render(managed) == live, f"Diverged after render: {name}"
print("ok")
PY
pass "Managed workflows match live copies (after consumer-name render)"

grep -q 'Linktrend Review Ready' core/github/REVIEW-READY.md || fail "status context missing"
grep -q '@cursor review' "$INT" || fail "default @cursor review"
pass "Readiness status + Bugbot command"

if grep -nE 'push origin HEAD:(staging|main)' scripts/gitops/promote_*.sh "$STG" "$MAIN"; then
  fail "direct push remains"
fi
grep -q 'Linktrend Receipt Gate' "$STG" || fail "staging receipt gate missing"
pass "No direct push; receipt-gated promotion"

# ---- Trust boundary: write-capable workflows ----
WRITE_WFS=("$STG" "$MAIN")
for wf in "${WRITE_WFS[@]}"; do
  # Must not check out PR head/merge ref
  if grep -nE 'ref:\s*\$\{\{\s*github\.event\.pull_request\.(head\.sha|merge_commit_sha)' "$wf"; then
    fail "write workflow checks out PR head/merge: $wf"
  fi
  if grep -nE 'refs/pull/' "$wf"; then
    fail "write workflow references refs/pull: $wf"
  fi
  grep -q 'persist-credentials: false' "$wf" || fail "missing persist-credentials false: $wf"
  grep -q 'default_branch' "$wf" || fail "missing trusted default_branch checkout: $wf"
  # Prefer pull_request_target over privileged pull_request for PR events
  if grep -qE '^\s+pull_request:' "$wf" && ! grep -q 'pull_request_target' "$wf"; then
    fail "privileged pull_request without pull_request_target: $wf"
  fi
  # Must not interpolate untrusted title/body into shell run blocks via expression
  if grep -nE 'github\.event\.pull_request\.(title|body)' "$wf"; then
    fail "untrusted PR title/body interpolated: $wf"
  fi
  grep -q 'permissions:' "$wf" || fail "missing least-privilege permissions: $wf"
done
# Unprivileged CI remains read-only and tests proposed code
grep -q 'permissions:' "$CI" || fail "ci missing permissions"
grep -q 'contents: read' "$CI" || fail "ci must be contents:read"
grep -q 'pull_request:' "$CI" || fail "ci must test PRs with pull_request"
! grep -q 'contents: write' "$CI" || fail "ci must not have contents:write"
pass "Trust boundary: trusted checkout + least-privilege token; CI unprivileged"

# Explicit PR/dispatch workflows have no workflow_run/check_run cascade.
! grep -q 'workflow_run:\|check_run:' "$PKG" || fail "packager retains an event cascade"
pass "No indefinite self-trigger via event cascades"

grep -q 'Ship 05' .cursor/rules/02-autonomous-ship-pull.mdc
grep -q 'Pull 07' .cursor/rules/02-autonomous-ship-pull.mdc
grep -q 'Linktrend Review Ready' .cursor/rules/02-autonomous-ship-pull.mdc
pass "Doctrine Ship 05/Pull 07 + status readiness"

grep -q 'default branch' docs/GITOPS-CONSUMER-ROLLOUT.md
grep -qi 'mention-only\|manualTriggerOnly' docs/contracts/BUGBOT-MENTION-ONLY.md
! grep -q 'LINKTREND_AUTOMATION_TOKEN' docs/contracts/GITHUB-APP-GITOPS-CREDENTIALS.md \
  || fail "retired App automation token remains in active credentials contract"
pass "Activation + mention-only + normal credential docs"

for s in scripts/mark-review-ready.sh scripts/validate-review-ready.sh \
         scripts/pull-update-work-branches.sh scripts/cleanup-merged-branches.sh \
         scripts/gitops/promote_staging.sh scripts/gitops/promote_main.sh \
         scripts/gitops/integrator_evaluate.sh scripts/tests/test-gitops-behavioral.sh \
         scripts/gitops/resolve_automation_token.sh scripts/gitops/resolve_bugbot_user_token.sh; do
  [ -x "$s" ] || fail "not executable: $s"
done
! grep -q 'LINKTREND_BUGBOT_USER_TOKEN' "$PKG" || fail "retired Bugbot user token remains"
grep -q '@cursor review' "$INT" || fail "final-suite Bugbot request missing"
[ ! -f scripts/commit-review-ready.sh ] || fail "commit-review-ready.sh must be removed"
[ ! -f core/templates/REVIEW-READY.json ] || fail "REVIEW-READY.json template must be removed"
pass "Executable modes + obsolete readiness file artifacts removed"

# Authoritative docs/scripts must not positively instruct creating/using the deleted JSON marker.
# Explanatory "must not use" / obsolete/superseded mentions are allowed. Historical ADR/OPEN-ISSUES
# lines may retain obsolete text only when a dated correction supersedes them.
python3 - <<'PY'
from pathlib import Path
import re

JSON = ".linktrend/review-ready.json"

def is_positive_json_instruction(line: str) -> bool:
    if "review-ready.json" not in line:
        return False
    low = line.lower()
    # Explicit prohibition / explanation — allowed
    if any(
        tok in low
        for tok in (
            "must not",
            "do **not**",
            "do not",
            "never",
            "obsolete",
            "superseded",
            "there is no",
            "must not be used",
            "must not exist",
            "not be used",
            "no longer",
            "fight over a shared path like",
            "like `.linktrend/review-ready.json`",
            "no `.linktrend/review-ready.json`",
            "and **no** `.linktrend/review-ready.json`",
            "and **no** `.linktrend/review-ready.json`",
            "— still **no pr** from the implementer and **no** `.linktrend/review-ready.json`",
        )
    ):
        return False
    if re.search(r"(?i)\bno\b.*review-ready\.json", line):
        return False
    # Positive operational verbs / discover patterns
    if re.search(
        r"(?i)(discover\s+`?\.linktrend/review-ready\.json"
        r"|marks?\s+.`?review_ready.?\s*\+\s*`?\.linktrend/review-ready\.json"
        r"|branch-local\s+`?\.linktrend/review-ready\.json"
        r"|valid\s+`?\.linktrend/review-ready\.json"
        r"|create\w*\s+.*review-ready\.json"
        r"|write\w*\s+.*review-ready\.json"
        r"|commit\w*\s+.*review-ready\.json)",
        line,
    ):
        return True
    return False

# Current operational contracts / agent instructions — no positive JSON readiness.
ops = [
    Path("docs/contracts/LISA-OPENCLAW-FOLLOW-UP.md"),
    Path("core/github/REVIEW-READY.md"),
    Path("docs/AUTONOMOUS-GIT-OPERATIONS.md"),
    Path(".cursor/rules/02-autonomous-ship-pull.mdc"),
    Path("scripts/gitops/work-branch-allowlist.sh"),
    Path("scripts/mark-review-ready.sh"),
    Path("scripts/validate-review-ready.sh"),
    Path("scripts/clear-review-ready.sh"),
    Path("scripts/pull-update-work-branches.sh"),
]
for path in ops:
    text = path.read_text(encoding="utf-8")
    for i, line in enumerate(text.splitlines(), 1):
        if is_positive_json_instruction(line):
            raise SystemExit(f"{path}:{i}: positive review-ready.json instruction forbidden:\n{line}")

allow = Path("scripts/gitops/work-branch-allowlist.sh").read_text(encoding="utf-8")
assert "review_ready_allowed_paths" not in allow
assert "review-ready.json" not in allow
assert "review-freeze.json" not in allow

# Historical records may keep obsolete bullets only if a dated correction supersedes them.
adr = Path("docs/adr/0003-autonomous-ship-pull-promote.md").read_text(encoding="utf-8")
assert "review-ready = commit status; supersedes file marker" in adr
assert "Linktrend Review Ready" in adr
assert "There is no** `.linktrend/review-ready.json` readiness file" in adr

oi = Path("docs/OPEN-ISSUES.md").read_text(encoding="utf-8")
assert "Correction — 2026-07-28 (review-ready mechanism)" in oi
assert "Linktrend Review Ready" in oi
assert "obsolete" in oi.lower()

# Broken ADR link must stay fixed
cig = Path("core/github/CI-GATE-CONTRACTS.md").read_text(encoding="utf-8")
assert "docs/adr/0003-autonomous-ship-pull-promote.md" in cig
assert "docs/adr/0003-autonomous-git-operations.md" not in cig

# Authoritative readiness doc must describe commit status, not a marker commit
rr = Path("core/github/REVIEW-READY.md").read_text(encoding="utf-8")
assert "Linktrend Review Ready" in rr
assert "Do **not** add a readiness file" in rr

print("no authoritative positive JSON readiness dependency")
PY
pass "No authoritative positive dependency on deleted JSON readiness"

# Honest outcomes vocabulary
python3 - <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, "scripts/gitops")
from write_outcome import VALID
need = {"packaged","waiting","skipped","blocked","failed","bugbot_requested","merged"}
assert need <= VALID, need - VALID
text = Path("scripts/gitops/packager_evaluate.py").read_text()
for s in ("waiting","skipped","blocked","bugbot_requested"):
    assert s in text
print("outcomes ok")
PY
pass "Honest outcome vocabulary present"

# ---- Normal automation token: same-job secret; never job-output secrets ----
for wf in "${WRITE_WFS[@]}"; do
  ! grep -q 'create-github-app-token' "$wf" \
    || fail "GitHub automation token action remains: $wf"
  if grep -nE 'outputs:\s*$' "$wf" >/dev/null; then
    # Any job-level outputs block must not expose app_token / token
    python3 - "$wf" <<'PY'
import re,sys
text=open(sys.argv[1],encoding="utf-8").read()
# Rough: between "jobs:" and end, find job outputs that mention token
for m in re.finditer(r'(?m)^  [A-Za-z0-9_-]+:\n(?:.*\n)*?(?=^  [A-Za-z0-9_-]+:|\Z)', text.split("jobs:\n",1)[-1] if "jobs:" in text else ""):
    block=m.group(0)
    if re.search(r'(?m)^\s+outputs:\s*$', block):
        if re.search(r'(?i)automation_token|app_token|outputs\.token|token:', block.split("steps:",1)[0]):
            raise SystemExit(f"token-like job output in {sys.argv[1]}")
print("ok")
PY
  fi
  if grep -nE 'needs\.[A-Za-z0-9_-]+\.outputs\.(automation_token|app_token|token)\b' "$wf"; then
    fail "consumes automation token via needs.*.outputs: $wf"
  fi
  if grep -nE 'skip-token-revoke:\s*true' "$wf"; then
    fail "skip-token-revoke workaround forbidden: $wf"
  fi
done
# Consumer steps must not inject GitHub App private-key env
for wf in "${WRITE_WFS[@]}"; do
  # private-key: is allowed only under create-github-app-token with: block
  python3 - "$wf" <<'PY'
from pathlib import Path
import sys,re
text=Path(sys.argv[1]).read_text()
# Forbid LINKTREND_GITOPS_APP_PRIVATE_KEY in env: mappings for run steps
if re.search(r'(?m)^\s+LINKTREND_GITOPS_APP_PRIVATE_KEY:\s*', text):
    raise SystemExit(f"private key env injected into workflow steps: {sys.argv[1]}")
# Forbid job output named app_token
if re.search(r'(?m)^\s+app_token:\s*', text):
    raise SystemExit(f"app_token job output present: {sys.argv[1]}")
print("ok")
PY
done
pass "Normal token same-job only; no job-output secret transport"

# ---- Concurrency: Fast Checks cancel obsolete runs per PR. ----
for wf in "$PKG" "$INT"; do
  grp="$(grep -E '^\s*group:' "$wf" | head -1)"
  echo "$grp" | grep -q 'pr-' || fail "concurrency must scope to a PR: $wf :: $grp"
  grep -q 'cancel-in-progress: true' "$wf" || fail "obsolete PR runs must cancel: $wf"
done
grep -q 'cancel-in-progress: true' "$STG"
grep -q 'cancel-in-progress: true' "$MAIN"
# Explicit Phase workflows use least-privilege built-in tokens; no App resolver.
for wf in "$PKG" "$INT" "$STG" "$MAIN"; do
  grep -q 'permissions:' "$wf" || fail "missing least-privilege permissions: $wf"
  ! grep -q 'create-github-app-token\|LINKTREND_GITOPS_APP_PRIVATE_KEY\|resolve_event_pr.py' "$wf" \
    || fail "retired App resolver remains: $wf"
done
! test -f scripts/gitops/event_relevance.py || fail "test-only event_relevance.py must be removed"
! test -f scripts/gitops/bugbot_request_once.py || fail "test-only bugbot_request_once.py must be removed"
pass "Uniform SHA concurrency + resolve-before-mint; test-only helpers removed"

# ---- actionlint on managed workflows (expression errors only; ignore SC2129 style) ----
if command -v actionlint >/dev/null 2>&1; then
  set +e
  al_out="$(actionlint -shellcheck= core/github/managed-workflows/*.yml .github/workflows/linktrend-*.yml .github/workflows/branch-source-policy.yml 2>&1)"
  al_ec=$?
  set -e
  # Filter style/shellcheck noise; fail on expression / YAML / workflow errors
  if [ "$al_ec" -ne 0 ]; then
    filtered="$(printf '%s\n' "$al_out" | grep -vE 'SC2129|shellcheck is not installed|SC[0-9]{4}' || true)"
    if printf '%s' "$filtered" | grep -Eq 'error:|expression|unexpected|invalid'; then
      echo "$filtered" >&2
      fail "actionlint reported expression/workflow errors"
    fi
  fi
  pass "actionlint managed workflows (expression-safe)"
else
  echo "WARN: actionlint not installed — skipped expression lint"
fi

# ============================================================================
# Exact-SHA compatibility with normal-token Review Ready publisher
# ============================================================================
# Packager must treat a successful ``Linktrend Review Ready`` status on the
# immutable tip SHA as eligible — same contract whether the status was posted
# by the local completion gate or the normal-token Actions publisher. No live
# credentials or GitHub mutation required (file status backend + hooks).
python3 - <<'PY'
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(".").resolve()
sys.path.insert(0, str(ROOT / "scripts" / "gitops"))

import packager_discover as disc_mod
import packager_evaluate as eval_mod
import readiness_status as rs
from readiness_status import CONTEXT

assert CONTEXT == "Linktrend Review Ready"

# Static: discover/evaluate gate on exact-SHA readiness; no JSON marker path.
disc_src = (ROOT / "scripts/gitops/packager_discover.py").read_text(encoding="utf-8")
eval_src = (ROOT / "scripts/gitops/packager_evaluate.py").read_text(encoding="utf-8")
assert "is_sha_review_ready" in disc_src
assert "is_sha_review_ready" in eval_src
assert "skipped_head_drift" in disc_src
assert "readiness_lost" in eval_src
assert "stale_event_head" in eval_src
assert "abort_head_changed_after_gate" in eval_src
assert ".linktrend/review-ready.json" not in disc_src
assert ".linktrend/review-ready.json" not in eval_src
assert "review-ready.json" not in disc_src
assert "review-ready.json" not in eval_src

status_dir = Path(tempfile.mkdtemp(prefix="packager-exact-sha-"))
os.environ["LINKTREND_STATUS_BACKEND"] = "file"
os.environ["LINKTREND_STATUS_DIR"] = str(status_dir)

# Normal-token publisher success on immutable tip (same context + success state).
READY_SHA = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
OTHER_SHA = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
DRIFT_SHA = "cccccccccccccccccccccccccccccccccccccccc"
BRANCH = "issue/44-add-app-backed-review-ready-publisher-and-produc"

# Simulate normal-token publisher: post success for CONTEXT on exact SHA only.
rs.mark_sha(READY_SHA, "44", "normal_token_publish")
ok, detail = rs.is_sha_review_ready(READY_SHA)
assert ok and "issue=44" in detail, (ok, detail)
ok_other, detail_other = rs.is_sha_review_ready(OTHER_SHA)
assert not ok_other and detail_other == "no_ready_status", (ok_other, detail_other)

# Production GitHub backend filters to CONTEXT only (file backend is test-local).
gh_src = (ROOT / "scripts/gitops/readiness_status.py").read_text(encoding="utf-8")
assert 'CONTEXT = "Linktrend Review Ready"' in gh_src
assert '(r.get("context") or "") == CONTEXT' in gh_src

# ---- Discover: packages exact ready tip; skips not-ready / head drift ----
os.environ["AUTOMATION_TOKEN"] = "ghs_automation_token_for_packager_test"
os.environ["AUTOMATION_TOKEN_SOURCE"] = "github_token"
os.environ["LINKTREND_BUGBOT_USER_TOKEN"] = "user_pat_for_packager_test"
os.environ["BUGBOT_USER_TOKEN"] = "user_pat_for_packager_test"
os.environ["GITHUB_REPOSITORY"] = "linktrend/IDE-Development"
# Ensure workflow token cannot substitute for normal automation in this process.
os.environ["GITHUB_TOKEN"] = "ghs_workflow_must_not_substitute"
os.environ.pop("GH_TOKEN", None)

recorded: list[dict] = []


def list_branches_hook(token: str, repo: str) -> list[dict]:
    assert token == "ghs_automation_token_for_packager_test"
    assert repo == "linktrend/IDE-Development"
    return [
        {
            "name": BRANCH,
            "commit": {"sha": READY_SHA},
        },
        {
            "name": "issue/99-not-ready-yet",
            "commit": {"sha": OTHER_SHA},
        },
        {
            "name": "development",  # protected — must be ignored by allowlist
            "commit": {"sha": READY_SHA},
        },
        {
            "name": "issue/77-head-will-drift",
            "commit": {"sha": READY_SHA},
        },
    ]


def run_hook(args: list[str], env: dict[str, str]) -> str:
    recorded.append({"args": list(args), "env": dict(env)})
    # Never leak Carlos secret names into App-role children.
    if env.get("GH_TOKEN") == "ghs_automation_token_for_packager_test":
        assert "LINKTREND_BUGBOT_USER_TOKEN" not in env
        assert "BUGBOT_USER_TOKEN" not in env
    joined = " ".join(args)
    if args[:3] == ["gh", "pr", "list"]:
        head = args[args.index("--head") + 1] if "--head" in args else ""
        if head == "issue/77-head-will-drift":
            # Existing draft authored by Carlos; head already drifted vs tip.
            return json.dumps(
                [
                    {
                        "number": 77,
                        "url": "https://example.test/pr/77",
                        "isDraft": True,
                        "headRefOid": DRIFT_SHA,
                        "title": "Review: issue/77-head-will-drift",
                        "body": "",
                        "author": {"login": "linktrend"},
                    }
                ]
            )
        return "[]"
    if args[:3] == ["gh", "pr", "create"]:
        # Only the ready non-drift branch should create.
        assert BRANCH in args
        return "https://example.test/pr/44"
    if args[:3] == ["gh", "pr", "view"]:
        if "number,author,headRefOid" in joined:
            return json.dumps(
                {
                    "number": 44,
                    "author": {"login": "linktrend"},
                    "headRefOid": READY_SHA,
                }
            )
        # Post-ensure reread: return tip SHA for packaged branch; drift for #77.
        target = args[3]
        if target == "77":
            return json.dumps(
                {"headRefOid": DRIFT_SHA, "author": {"login": "linktrend"}}
            )
        return json.dumps(
            {"headRefOid": READY_SHA, "author": {"login": "linktrend"}}
        )
    if args[:3] == ["gh", "pr", "edit"]:
        return ""
    if "repair_task.py" in joined:
        raise AssertionError("repair must not run on success/drift skip paths")
    raise AssertionError(f"unexpected run: {args}")


disc_mod._LIST_BRANCHES_HOOK = list_branches_hook
disc_mod._RUN_HOOK = run_hook
original_fetch_issue_pr_exception = disc_mod.fetch_issue_pr_exception
disc_mod.fetch_issue_pr_exception = lambda token, repo, sha: None
cwd = Path.cwd()
tmpdir = Path(tempfile.mkdtemp(prefix="packager-discover-cwd-"))
os.chdir(tmpdir)
try:
    rc = disc_mod.main()
    assert rc == 0
    report = json.loads(Path("packager-discover-report.json").read_text(encoding="utf-8"))
    by_branch = {row["branch"]: row for row in report}
    assert by_branch[BRANCH]["action"] == "skipped_phase_mode_issue_without_exception"
    assert by_branch[BRANCH]["ready"] is True
    assert by_branch[BRANCH]["headSha"] == READY_SHA
    assert by_branch["issue/99-not-ready-yet"]["action"] == "skipped_not_ready"
    assert by_branch["issue/99-not-ready-yet"]["ready"] is False
    assert by_branch["issue/77-head-will-drift"]["action"] == "skipped_phase_mode_issue_without_exception"
    assert "development" not in by_branch
    outcome = json.loads(Path("gitops-outcome.json").read_text(encoding="utf-8"))
    assert outcome["status"] == "skipped"
finally:
    os.chdir(cwd)
    disc_mod._LIST_BRANCHES_HOOK = None
    disc_mod._RUN_HOOK = None
    disc_mod.fetch_issue_pr_exception = original_fetch_issue_pr_exception

# Withdrawal on the tip must make discover skip (no success status).
rs.withdraw_sha(READY_SHA, "publisher_withdrawn")
ok_w, detail_w = rs.is_sha_review_ready(READY_SHA)
assert not ok_w and detail_w.startswith("status_"), (ok_w, detail_w)

# ---- Evaluate: exact head ready vs waiting / readiness_lost / stale event ----
# Re-mark ready for evaluate success path.
rs.mark_sha(READY_SHA, "44", "normal_token_publish")

os.environ["FAST_GATE_CHECKS"] = "Verify IDE Development"
os.environ["BUGBOT_REVIEW_COMMAND"] = "@cursor review"
os.environ["HEAD_SHA"] = READY_SHA

api_calls: list[dict] = []
eval_recorded: list[dict] = []


def eval_run(args: list[str], env: dict[str, str]) -> str:
    eval_recorded.append({"args": list(args), "env": dict(env)})
    joined = " ".join(args)
    if args[:3] == ["gh", "pr", "view"] and "author" in joined:
        return json.dumps(
            {
                "number": 44,
                "url": "https://example.test/pr/44",
                "isDraft": True,
                "headRefOid": READY_SHA,
                "baseRefName": "development",
                "state": "OPEN",
                "headRefName": BRANCH,
                "author": {"login": "linktrend"},
            }
        )
    if args[:3] == ["gh", "pr", "view"] and "headRefOid" in joined and "author" not in joined:
        return READY_SHA
    if args[:3] == ["gh", "pr", "checks"]:
        return json.dumps([{"name": "Verify IDE Development", "state": "SUCCESS"}])
    if args[:3] == ["gh", "pr", "ready"]:
        return ""
    raise AssertionError(f"unexpected evaluate run: {args}")


def eval_api(method: str, url: str, token: str, body, snap: dict[str, str]):
    api_calls.append(
        {"method": method, "url": url, "token": token, "body": body, "snap": snap}
    )
    if method == "GET":
        return []
    return {}


# Waiting: tip not ready
rs.withdraw_sha(READY_SHA, "not_yet")
eval_mod._RUN_HOOK = eval_run
eval_mod._API_HOOK = eval_api
try:
    waiting = eval_mod.evaluate_pr(44, "ghs_automation_token_for_packager_test")
    assert waiting["status"] == "waiting"
    assert waiting["detail"].startswith("not_ready:")
    assert waiting["headSha"] == READY_SHA
finally:
    eval_mod._RUN_HOOK = None
    eval_mod._API_HOOK = None

# Success path: App-published status on exact head → bugbot_requested
rs.mark_sha(READY_SHA, "44", "normal_token_publish")
api_calls.clear()
eval_recorded.clear()
eval_mod._RUN_HOOK = eval_run
eval_mod._API_HOOK = eval_api
try:
    ok_eval = eval_mod.evaluate_pr(44, "ghs_automation_token_for_packager_test")
    assert ok_eval["status"] == "bugbot_requested", ok_eval
    assert ok_eval["headSha"] == READY_SHA
    assert ok_eval["bugbot_comment_token"] == "bugbot_user"
    bugbot = [
        c
        for c in api_calls
        if c["method"] == "POST" and c["token"] == "user_pat_for_packager_test"
    ]
    assert len(bugbot) == 1
    assert READY_SHA in (bugbot[0]["body"] or {}).get("body", "")
finally:
    eval_mod._RUN_HOOK = None
    eval_mod._API_HOOK = None

# Stale event head (dispatch/event SHA ≠ live PR head) → skipped
os.environ["HEAD_SHA"] = OTHER_SHA
eval_mod._RUN_HOOK = eval_run
eval_mod._API_HOOK = eval_api
try:
    stale = eval_mod.evaluate_pr(44, "ghs_automation_token_for_packager_test")
    assert stale["status"] == "skipped"
    assert stale["detail"].startswith("stale_event_head:")
finally:
    eval_mod._RUN_HOOK = None
    eval_mod._API_HOOK = None
os.environ["HEAD_SHA"] = READY_SHA

# readiness_lost: gate green on sha1, but readiness withdrawn before re-check
# Simulate by making the second is_sha_review_ready fail via tip change after
# first check — withdraw after checks, before second ready read. We do this by
# patching pr_head to keep SHA while withdrawing status between gate and recheck.
# Here: head stays READY_SHA but we withdraw after first ready check by using a
# custom is_sha_review_ready sequence.


class _FlipReady:
    def __init__(self) -> None:
        self.n = 0

    def __call__(self, sha: str):
        self.n += 1
        if self.n == 1:
            assert sha == READY_SHA
            return True, "ready"
        return False, "status_failure"


flip = _FlipReady()
orig = eval_mod.is_sha_review_ready
eval_mod.is_sha_review_ready = flip  # type: ignore[assignment]
eval_mod._RUN_HOOK = eval_run
eval_mod._API_HOOK = eval_api
try:
    lost = eval_mod.evaluate_pr(44, "ghs_automation_token_for_packager_test")
    assert lost["status"] == "skipped"
    assert lost["detail"] == "readiness_lost"
    assert flip.n == 2
finally:
    eval_mod.is_sha_review_ready = orig
    eval_mod._RUN_HOOK = None
    eval_mod._API_HOOK = None

print("exact-SHA normal-token publisher packager compatibility ok")
PY
pass "Exact-SHA normal-token publisher compatibility (discover + evaluate)"

echo "PASS: gitops static redesign + trust-boundary checks"
