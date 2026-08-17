#!/usr/bin/env bash
# Adversarial + static proofs for the normal-token Review Ready publisher.
# Ownership: this script + scripts/tests/fixtures/review-ready-publisher/**
# Does not mutate GitHub. Does not edit production workflow/scripts/docs.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

FIX="$ROOT/scripts/tests/fixtures/review-ready-publisher"
WF=".github/workflows/linktrend-review-ready-publisher.yml"
DISPATCH="scripts/gitops/review_ready_dispatch.py"
NEG_WF="$FIX/workflow/adversarial-untrusted-source.yml"
PATTERNS="$FIX/workflow/required-trust-patterns.txt"
CASES="$FIX/cases/dispatch-cases.json"
CONTRACT="$FIX/contract.json"

fail() { echo "FAIL: $1" >&2; exit 1; }
pass() { echo "PASS: $1"; }

[ -f "$CONTRACT" ] || fail "missing fixture contract: $CONTRACT"
[ -f "$CASES" ] || fail "missing cases: $CASES"
[ -f "$NEG_WF" ] || fail "missing adversarial workflow fixture: $NEG_WF"
[ -f "$PATTERNS" ] || fail "missing trust patterns: $PATTERNS"
[ -f "$WF" ] || fail "missing production workflow: $WF"
[ -f "$DISPATCH" ] || fail "missing dispatch validator: $DISPATCH"

# ---- 1) Negative fixture encodes forbidden trust failures ----
python3 - <<'PY' "$NEG_WF"
import re, sys
from pathlib import Path
text = Path(sys.argv[1]).read_text(encoding="utf-8")
checks = [
    ("untrusted PR head checkout", r"pull_request\.head\.sha"),
    ("persist-credentials true", r"persist-credentials:\s*true"),
    ("human Bugbot user token", r"LINKTREND_BUGBOT_USER_TOKEN"),
    ("github.token status path", r"github\.token"),
    ("private key leaked into consumer env", r"LINKTREND_GITOPS_APP_PRIVATE_KEY"),
    ("mutable HEAD status target", r"statuses/HEAD"),
]
missing = [name for name, pat in checks if not re.search(pat, text)]
if missing:
    raise SystemExit(f"adversarial fixture incomplete; missing markers: {missing}")
print("ok")
PY
pass "Adversarial untrusted-source fixture encodes forbidden patterns"

# ---- 2) Production workflow trusted-source / no human fallback ----
python3 - <<'PY' "$WF" "$NEG_WF" "$PATTERNS"
import re
import sys
from pathlib import Path

prod = Path(sys.argv[1]).read_text(encoding="utf-8")
neg = Path(sys.argv[2]).read_text(encoding="utf-8")
assert prod != neg, "production workflow must not equal adversarial fixture"

for raw in Path(sys.argv[3]).read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if not line or line.startswith("#"):
        continue
    kind, needle = line.split("|", 1)
    if kind == "must":
        if needle not in prod:
            raise SystemExit(f"workflow missing required trust marker: {needle}")
    elif kind == "must_not":
        if needle in prod:
            raise SystemExit(f"workflow contains forbidden marker: {needle}")
    else:
        raise SystemExit(f"unknown pattern kind: {kind}")

for banned_app_marker in (
    "create-github-app-token",
    "LINKTREND_GITOPS_APP_ID",
    "LINKTREND_GITOPS_APP_PRIVATE_KEY",
):
    if banned_app_marker in prod:
        raise SystemExit(f"obsolete GitHub App dependency present: {banned_app_marker}")

for banned in (
    "LINKTREND_BUGBOT_USER_TOKEN",
    "BUGBOT_USER_TOKEN",
    "resolve_bugbot_user_token",
):
    if banned in prod:
        raise SystemExit(f"human credential fallback present: {banned}")

# Built-in github.token must authorize only the trusted publish/withdraw step.
blocks = re.split(r"\n(?=      - name:)", prod)
publish_blocks = 0
for block in blocks:
    uses_github_token = bool(
        re.search(
            r"(AUTOMATION_TOKEN|GH_TOKEN|GITHUB_TOKEN):\s*\$\{\{\s*github\.token",
            block,
        )
    )
    publishes = bool(
        re.search(r"(publish_review_ready|withdraw_sha|readiness_status)", block)
    )
    has_flag = "LINKTREND_TRUSTED_REVIEW_READY_PUBLISHER" in block
    if publishes and "run:" in block:
        publish_blocks += 1
        if not uses_github_token:
            raise SystemExit("publish step must forward github.token")
        if not has_flag:
            raise SystemExit(
                "publish step must set LINKTREND_TRUSTED_REVIEW_READY_PUBLISHER=1"
            )
        if "AUTOMATION_TOKEN:" not in block:
            raise SystemExit("publish step must forward documented AUTOMATION_TOKEN")
    elif has_flag and "Validate dispatch inputs" in block:
        raise SystemExit("trusted flag must not sit on input validation")

if publish_blocks != 1:
    raise SystemExit(f"expected exactly one publish/withdraw step, got {publish_blocks}")

for key in ("branch", "sha", "dry_run", "action", "reason"):
    if not re.search(rf"^\s*{key}\s*:", prod, re.M):
        raise SystemExit(f"workflow_dispatch input missing: {key}")

# Trusted source + data-only tip checkout + immutable tip verify.
assert "github.event.repository.default_branch" in prod
assert "untrusted-branch-data" in prod
assert "sha_mismatch" in prod
assert "no human fallback" in prod.lower()
assert "completion_gate" in prod or "validate_evidence" in prod
assert "review_ready_dispatch.py" in prod
assert "withdraw_sha" in prod
assert "withdraw" in prod
assert "statuses: write" in prod
print("ok")
PY
pass "Production workflow trusted-source + flag on publish step + built-in token forwarding"

# ---- 3) Adversarial fixture fails the same must/must_not requirements ----
python3 - <<'PY' "$NEG_WF" "$PATTERNS"
import sys
from pathlib import Path
prod = Path(sys.argv[1]).read_text(encoding="utf-8")
violations = 0
for raw in Path(sys.argv[2]).read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if not line or line.startswith("#"):
        continue
    kind, needle = line.split("|", 1)
    if kind == "must" and needle not in prod:
        violations += 1
    if kind == "must_not" and needle in prod:
        violations += 1
assert "pull_request.head.sha" in prod
assert violations > 0
print("ok")
PY
pass "Adversarial fixture is rejected by trust requirements"

# ---- 4) Dispatch validator adversarial cases + self-test + CLI ----
python3 - <<'PY' "$ROOT" "$DISPATCH" "$FIX" "$CASES"
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1])
dispatch_path = root / sys.argv[2]
fix = Path(sys.argv[3])
cases_doc = json.loads(Path(sys.argv[4]).read_text(encoding="utf-8"))

# Register module name before exec so dataclasses work under importlib.
spec = importlib.util.spec_from_file_location("review_ready_dispatch", dispatch_path)
mod = importlib.util.module_from_spec(spec)
sys.modules["review_ready_dispatch"] = mod
assert spec.loader is not None
spec.loader.exec_module(mod)

validate = getattr(mod, "validate_dispatch_inputs", None)
err_cls = getattr(mod, "DispatchValidationError", None)
if validate is None or err_cls is None:
    raise SystemExit(
        "review_ready_dispatch.py must export validate_dispatch_inputs "
        "and DispatchValidationError"
    )

failures = []
for case in cases_doc["dispatchCases"]:
    cid = case["id"]
    kwargs = {
        "branch": case["branch"],
        "sha": case["sha"],
        "github_repository": case["github_repository"],
    }
    for key in ("repository", "issue_number", "evidence_path", "evidence_json", "dry_run", "action", "reason"):
        if key in case:
            kwargs[key] = case[key]
    try:
        result = validate(**kwargs)
        ok = True
        code = None
        sha_out = getattr(result, "sha", None)
    except err_cls as e:
        ok = False
        code = e.code
        sha_out = None
    if case.get("expectOk"):
        if not ok:
            failures.append(f"{cid}: expected ok, got {code}")
            continue
        if case.get("expectSha") and sha_out != case["expectSha"]:
            failures.append(f"{cid}: expected sha {case['expectSha']}, got {sha_out}")
    else:
        if ok:
            failures.append(f"{cid}: expected failure {case.get('errorCode')}, got ok")
        elif case.get("errorCode") and code != case["errorCode"]:
            failures.append(f"{cid}: expected {case['errorCode']}, got {code}")

if failures:
    print("\n".join(failures), file=sys.stderr)
    raise SystemExit(1)

# Built-in self-test
st = subprocess.run(
    [sys.executable, str(dispatch_path), "self-test"],
    cwd=str(root),
    text=True,
    capture_output=True,
)
if st.returncode != 0:
    raise SystemExit(f"self-test failed: {st.stdout}\n{st.stderr}")

# CLI: valid ok; cross-repo fails closed
valid = next(c for c in cases_doc["dispatchCases"] if c["id"] == "valid_issue_branch_exact_sha")
bad = next(c for c in cases_doc["dispatchCases"] if c["id"] == "reject_cross_repository_publish")

def cli(case):
    cmd = [
        sys.executable,
        str(dispatch_path),
        "validate",
        "--branch", case["branch"],
        "--sha", case["sha"],
        "--github-repository", case["github_repository"],
    ]
    if case.get("repository"):
        cmd.extend(["--repository", case["repository"]])
    return subprocess.run(cmd, cwd=str(root), text=True, capture_output=True)

v = cli(valid)
if v.returncode != 0:
    raise SystemExit(f"CLI valid failed rc={v.returncode} out={v.stdout} err={v.stderr}")
payload = json.loads(v.stdout)
assert payload.get("ok") is True
b = cli(bad)
if b.returncode == 0:
    raise SystemExit(f"CLI cross-repo unexpectedly succeeded: {b.stdout}")
bp = json.loads(b.stdout)
assert bp.get("ok") is False
assert bp.get("error") == "repository_mismatch"

print(f"ok dispatchCases={len(cases_doc['dispatchCases'])}")
PY
pass "Dispatch validator adversarial cases (branch/SHA/repo/issue)"

# ---- 5) Immutable evidence validation (completion_gate schema on fixtures) ----
python3 - <<'PY' "$ROOT" "$FIX" "$CASES"
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
fix = Path(sys.argv[2])
cases_doc = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
sys.path.insert(0, str(root / "scripts/gitops"))
import completion_gate as cg

failures = []
for case in cases_doc["evidenceCases"]:
    evidence = json.loads((fix / case["evidence"]).read_text(encoding="utf-8"))
    missing = cg.validate_evidence(evidence, case["sha"])
    ok = not missing
    if case.get("expectOk"):
        if not ok:
            failures.append(f"{case['id']}: expected ok, got {missing}")
        continue
    if ok:
        failures.append(f"{case['id']}: expected failure, got ok")
        continue
    blob = ",".join(missing)
    for needle in case.get("errorSubstrings") or []:
        if needle not in blob:
            failures.append(f"{case['id']}: missing {needle} in {missing}")
            break

if failures:
    print("\n".join(failures), file=sys.stderr)
    raise SystemExit(1)
print(f"ok evidenceCases={len(cases_doc['evidenceCases'])}")
PY
pass "Evidence fixtures fail closed on SHA/schema/command mismatches"

# ---- 6) Remote tip immutability comparison (workflow contract + pure cases) ----
python3 - <<'PY' "$WF" "$CASES"
import sys
from pathlib import Path

wf = Path(sys.argv[1]).read_text(encoding="utf-8")
# Workflow must independently compare remote tip to requested immutable SHA.
for needle in (
    "Verify remote tip equals immutable SHA",
    "sha_mismatch",
    "branches/",
    "commit",
):
    if needle not in wf:
        raise SystemExit(f"workflow missing remote-tip proof marker: {needle}")

cases = __import__("json").loads(Path(sys.argv[2]).read_text(encoding="utf-8"))

def tip_ok(requested: str, remote_tip: str) -> bool:
    tip = (remote_tip or "").lower()
    sha = (requested or "").lower()
    if not tip or len(tip) != 40:
        return False
    return tip == sha

failures = []
for case in cases["remoteTipCases"]:
    ok = tip_ok(case["requested"], case["remote_tip"])
    if bool(ok) != bool(case["expectOk"]):
        failures.append(f"{case['id']}: expected ok={case['expectOk']} got {ok}")
if failures:
    print("\n".join(failures), file=sys.stderr)
    raise SystemExit(1)
print(f"ok remoteTipCases={len(cases['remoteTipCases'])}")
PY
pass "Immutable remote tip mismatch fails closed"

# ---- 7) No token leakage / human fallback in dispatch validator source ----
python3 - <<'PY' "$DISPATCH"
from pathlib import Path
import sys
text = Path(sys.argv[1]).read_text(encoding="utf-8")
for b in (
    "print(os.environ",
    "print(token",
    "print(AUTOMATION",
    "print(GITHUB_TOKEN",
    "print(GH_TOKEN",
    "LINKTREND_GITOPS_APP_PRIVATE_KEY",
    "BUGBOT_USER_TOKEN",
    "LINKTREND_BUGBOT_USER_TOKEN",
):
    if b in text:
        raise SystemExit(f"dispatch validator forbidden reference: {b}")
print("ok")
PY
pass "Dispatch validator has no token leakage / human fallback references"

# ---- 8) Fixture contract matches readiness_status normal-token route ----
python3 - <<'PY' "$ROOT" "$CONTRACT"
import json
import sys
from pathlib import Path
root = Path(sys.argv[1])
contract = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
sys.path.insert(0, str(root / "scripts/gitops"))
import readiness_status as rs
assert contract["productionPaths"]["workflow"].endswith(rs.REVIEW_READY_PUBLISHER_WORKFLOW)
route = rs.app_backed_review_ready_route(
    branch="issue/44-add-app-backed-review-ready-publisher-and-produc",
    sha="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    dry_run=False,
)
assert "linktrend-review-ready-publisher.yml" in route
assert "-f branch=issue/44-add-app-backed-review-ready-publisher-and-produc" in route
assert "-f sha=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" in route
assert "-f action=publish" in route
assert "-f dry_run=false" in route
withdraw = rs.app_backed_review_ready_route(
    branch="issue/44-add-app-backed-review-ready-publisher-and-produc",
    sha="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    action="withdraw",
    reason="rollback",
    dry_run=False,
)
assert "-f action=withdraw" in withdraw
assert "-f reason=rollback" in withdraw
assert contract["statusContext"] == rs.CONTEXT
assert "withdrawRoute" in contract
assert "-f action=withdraw" in contract["withdrawRoute"]
print("ok")
PY
pass "Fixture contract matches readiness_status normal-token route"

# ---- 9) Structural flag placement vs defective predecessor ----
python3 - <<'PY' "$ROOT" "$WF" "$FIX"
import sys
from pathlib import Path
root = Path(sys.argv[1])
sys.path.insert(0, str(root / "scripts/gitops"))
import review_ready_publisher_bootstrap as boot

prod = Path(sys.argv[2]).read_text(encoding="utf-8")
fix = Path(sys.argv[3])
defective = (fix / "workflow/defective-v238-flag-on-validate.yml").read_text(encoding="utf-8")
neg = (fix / "workflow/adversarial-untrusted-source.yml").read_text(encoding="utf-8")

prod_info = boot.publisher_defect(prod)
bad_info = boot.publisher_defect(defective)
neg_info = boot.publisher_defect(neg)
assert prod_info["corrected"] and not prod_info["defective"], prod_info
assert prod_info["flagOnPublish"] and not prod_info["flagOnUnrelatedSteps"], prod_info
assert bad_info["defective"] and not bad_info["corrected"], bad_info
assert bad_info["flagOnUnrelatedSteps"] and not bad_info["flagOnPublish"], bad_info
assert not neg_info["corrected"], neg_info
print("ok")
PY
pass "Structural parse: trusted flag on publication step only; defective predecessor detected"

# ---- 10) Token forwarding, precedence, and no disclosure ----
python3 - <<'PY' "$ROOT"
import os
import sys
from pathlib import Path
from unittest import mock

root = Path(sys.argv[1])
sys.path.insert(0, str(root / "scripts/gitops"))
import readiness_status as rs

secret = "ghs_DOCUMENTED_AUTOMATION_TOKEN_VALUE_NEVER_LOG"
human = "ghs_FAKE_HUMAN_MUST_NOT_WIN"
workflow = "ghs_FAKE_WORKFLOW_ALIAS"

def clear_tokens():
    for k in (*rs.PUBLISH_TOKEN_ENVS, rs.TRUSTED_PUBLISHER_FLAG):
        os.environ.pop(k, None)

# Missing flag: AUTOMATION_TOKEN must not silently authorize publish.
clear_tokens()
os.environ["AUTOMATION_TOKEN"] = secret
os.environ["GH_TOKEN"] = human
os.environ["GITHUB_TOKEN"] = workflow
assert rs.resolve_app_publish_token() == ""
assert rs.automation_token_present() is True
fwd = rs.forward_automation_token({"AUTOMATION_TOKEN": secret, "GH_TOKEN": human})
assert fwd["GH_TOKEN"] == secret
assert fwd["GITHUB_TOKEN"] == secret
assert fwd["AUTOMATION_TOKEN"] == secret
# Silent-loss probe: documented token is not dropped when GH_TOKEN was absent.
fwd2 = rs.forward_automation_token({"AUTOMATION_TOKEN": secret})
assert fwd2.get("GH_TOKEN") == secret
assert fwd2.get("GITHUB_TOKEN") == secret

# Trusted flag + documented token: AUTOMATION_TOKEN precedes aliases.
os.environ[rs.TRUSTED_PUBLISHER_FLAG] = "1"
assert rs.resolve_app_publish_token() == secret

# Alias-only trusted path (built-in github.token forwarded as GH_TOKEN).
clear_tokens()
os.environ[rs.TRUSTED_PUBLISHER_FLAG] = "1"
os.environ["GH_TOKEN"] = workflow
assert rs.resolve_app_publish_token() == workflow

# Missing flag + aliases: fail closed.
clear_tokens()
os.environ["GH_TOKEN"] = human
os.environ["GITHUB_TOKEN"] = workflow
assert rs.resolve_app_publish_token() == ""

# Diagnostics never disclose token values.
clear_tokens()
os.environ["AUTOMATION_TOKEN"] = secret
os.environ["GH_TOKEN"] = human
msg = rs.missing_app_publish_token_error(
    branch="issue/44-add-app-backed-review-ready-publisher-and-produc",
    sha="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
)
assert "AUTOMATION_TOKEN" in msg
assert secret not in msg
assert human not in msg
assert "forward_automation_token" in msg
assert "linktrend-review-ready-publisher.yml" in msg

# Publish/withdraw exact SHA with trusted built-in token (mocked GitHub).
clear_tokens()
os.environ[rs.TRUSTED_PUBLISHER_FLAG] = "1"
os.environ["AUTOMATION_TOKEN"] = secret
os.environ["GH_TOKEN"] = human
os.environ["GITHUB_REPOSITORY"] = "linktrend/IDE-Development"
sha = "dddddddddddddddddddddddddddddddddddddddd"
posted = []

def fake_api(method, url, token, body=None):
    posted.append({"method": method, "url": url, "token": token, "body": body})
    if method == "GET":
        mine = [p for p in posted if p["method"] == "POST"]
        if not mine:
            return []
        last = mine[-1]["body"]
        return [{"context": rs.CONTEXT, "state": last["state"], "description": last["description"]}]
    if method == "POST" and "/statuses/" in url:
        if token != secret:
            raise RuntimeError("insufficient permission: 403")
        return {}
    raise RuntimeError(f"unexpected {method} {url}")

with mock.patch.object(rs, "_api", side_effect=fake_api):
    st = rs.publish_review_ready(sha, "308", notes="exact-tip", branch="issue/308-x")
    assert st.state == "success"
    ok, detail = rs.is_sha_review_ready(sha)
    assert ok, detail
    wd = rs.withdraw_sha(sha, "rollback", branch="issue/308-x")
    assert wd.state == "failure"
    ok2, detail2 = rs.is_sha_review_ready(sha)
    assert not ok2

assert any(p["method"] == "POST" and p["token"] == secret for p in posted)
assert all(p["token"] != human for p in posted if p.get("token"))
blob = repr(posted) + msg
assert secret not in msg
print("ok")
PY
pass "AUTOMATION_TOKEN forwarding, alias precedence, publish/withdraw exact tip, no disclosure"

# ---- 11) Fail closed: missing flag, wrong SHA/evidence, untrusted source, 403 ----
python3 - <<'PY' "$ROOT" "$FIX" "$NEG_WF"
import json
import os
import sys
from pathlib import Path
from unittest import mock

root = Path(sys.argv[1])
fix = Path(sys.argv[2])
neg = Path(sys.argv[3]).read_text(encoding="utf-8")
sys.path.insert(0, str(root / "scripts/gitops"))
import completion_gate as cg
import readiness_status as rs
import review_ready_publisher_bootstrap as boot

# Missing flag
for k in (*rs.PUBLISH_TOKEN_ENVS, rs.TRUSTED_PUBLISHER_FLAG):
    os.environ.pop(k, None)
os.environ["GH_TOKEN"] = "ghs_AMBIENT"
os.environ["GITHUB_REPOSITORY"] = "linktrend/IDE-Development"
posted = []

def fake_api(method, url, token, body=None):
    posted.append({"method": method, "url": url, "token": token, "body": body})
    return []

with mock.patch.object(rs, "_api", side_effect=fake_api):
    try:
        rs.publish_review_ready(
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "1",
            branch="issue/1-x",
        )
        raise SystemExit("missing flag must fail closed")
    except RuntimeError as exc:
        assert "privileged_publish_requires_github_token" in str(exc)
assert posted == []

# Wrong SHA / stale evidence
sha = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
other = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
evidence = json.loads((fix / "evidence/valid.json").read_text(encoding="utf-8"))
assert cg.validate_evidence(evidence, sha) == []
stale = json.loads((fix / "evidence/sha-mismatch.json").read_text(encoding="utf-8"))
assert cg.validate_evidence(stale, sha)
assert cg.validate_evidence(evidence, other)

# Untrusted workflow source is not corrected
assert not boot.publisher_defect(neg)["corrected"]
assert "pull_request.head.sha" in neg
assert "LINKTREND_BUGBOT_USER_TOKEN" in neg

# Insufficient permission
os.environ[rs.TRUSTED_PUBLISHER_FLAG] = "1"
os.environ["AUTOMATION_TOKEN"] = "ghs_TRUSTED_BUT_FORBIDDEN"

def deny(method, url, token, body=None):
    raise RuntimeError(f"{method} {url} -> 403: Resource not accessible by integration")

with mock.patch.object(rs, "_api", side_effect=deny):
    try:
        rs.publish_review_ready(
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "1",
            branch="issue/1-x",
        )
        raise SystemExit("403 must fail closed")
    except RuntimeError as exc:
        assert "403" in str(exc)
print("ok")
PY
pass "Missing flag, stale evidence, untrusted source, and insufficient permission fail closed"

# ---- 12) Bootstrap positive + negatives ----
python3 - <<'PY' "$ROOT" "$WF" "$FIX"
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1])
boot_path = root / "scripts/gitops/review_ready_publisher_bootstrap.py"
st = subprocess.run(
    [sys.executable, str(boot_path), "self-test"],
    cwd=str(root),
    text=True,
    capture_output=True,
)
if st.returncode != 0:
    raise SystemExit(f"bootstrap self-test failed: {st.stdout}\n{st.stderr}")

sys.path.insert(0, str(root / "scripts/gitops"))
import review_ready_publisher_bootstrap as boot

prod = Path(sys.argv[2]).read_text(encoding="utf-8")
defective = (
    Path(sys.argv[3]) / "workflow/defective-v238-flag-on-validate.yml"
).read_text(encoding="utf-8")
sha = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
req = boot.BootstrapRequest(
    actor_role="integrator",
    requested_head_sha=sha,
    evidence_head_sha=sha,
    installed_workflow=defective,
    corrected_workflow=prod,
    pr={"number": 99, "head_sha": sha, "head_branch": "issue/99-fix", "state": "open"},
    required_checks=["Linktrend Fast Checks"],
    passing_checks=["Linktrend Fast Checks"],
    required_contexts=["Linktrend Fast Checks"],
)
plan = boot.evaluate_bootstrap(req)
assert plan["ok"] is True
assert plan["callPublisher"] is False
assert plan["installViaExistingPr"] is True
assert plan["rerunUnchangedFull"] is False
assert plan["markDraftReady"] is True

for code, kwargs in (
    ("worker_self_use", {"actor_role": "worker"}),
    ("new_pr_forbidden", {"create_new_pr": True}),
    ("direct_protected_push", {"direct_protected_push": True}),
    ("missing_required_checks", {"passing_checks": []}),
    (
        "changed_head",
        {
            "pr": {
                "number": 99,
                "head_sha": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
                "head_branch": "issue/99-fix",
                "state": "open",
            }
        },
    ),
    (
        "founder_authorization_required",
        {"required_contexts": ["Linktrend Review Ready"], "founder_authorized": False},
    ),
    ("stale_evidence", {"evidence_head_sha": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}),
    ("defective_publisher_forbidden", {"call_publisher": True}),
):
    data = {**req.__dict__, **kwargs}
    try:
        boot.evaluate_bootstrap(boot.BootstrapRequest(**data))
        raise SystemExit(f"expected {code}")
    except boot.BootstrapError as exc:
        if exc.code != code:
            raise SystemExit(f"expected {code}, got {exc.code}")
print("ok")
PY
pass "Bootstrap positive Integrator exact-head path and negative probes"

# ---- 13) Installed workflow equals managed source / package manifest ----
python3 - <<'PY' "$ROOT"
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(sys.argv[1])
managed = (root / "core/github/managed-workflows/linktrend-review-ready-publisher.yml").read_bytes()
live = (root / ".github/workflows/linktrend-review-ready-publisher.yml").read_bytes()
assert managed == live, "live workflow must equal managed source"

manifest = json.loads((root / "core/managed-core/MANIFEST.json").read_text(encoding="utf-8"))
entry = next(
    f for f in manifest["files"] if f["id"] == "workflow-linktrend-review-ready-publisher-yml"
)
digest = "sha256:" + hashlib.sha256(managed).hexdigest()
assert entry["sourceHash"] == digest, f"manifest hash {entry['sourceHash']} != {digest}"
assert entry["source"] == "core/github/managed-workflows/linktrend-review-ready-publisher.yml"

tmp = Path(tempfile.mkdtemp(prefix="rr-publisher-install."))
try:
    (tmp / ".github").mkdir()
    shutil.copyfile(
        root / ".github/linktrend-gitops-consumer.json",
        tmp / ".github/linktrend-gitops-consumer.json",
    )
    r = subprocess.run(
        ["bash", str(root / "scripts/sync-managed-workflows.sh"), str(tmp)],
        cwd=str(root),
        text=True,
        capture_output=True,
    )
    if r.returncode != 0:
        raise SystemExit(f"sync failed: {r.stdout}\n{r.stderr}")
    installed = (tmp / ".github/workflows/linktrend-review-ready-publisher.yml").read_bytes()
    assert installed == managed, "disposable-consumer install must match managed source"
finally:
    shutil.rmtree(tmp, ignore_errors=True)
print("ok")
PY
pass "Installed/live workflow equals managed source and package manifest hash"

echo "PASS: review-ready publisher adversarial/static suite"
