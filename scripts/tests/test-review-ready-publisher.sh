#!/usr/bin/env bash
# Adversarial + static proofs for App-backed Review Ready publisher (Issue #44 Wave 2).
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

if "create-github-app-token" not in prod:
    raise SystemExit("missing create-github-app-token mint step")

for i, ln in enumerate(prod.splitlines(), 1):
    if "LINKTREND_GITOPS_APP_PRIVATE_KEY" not in ln:
        continue
    stripped = ln.strip()
    if stripped.startswith("#"):
        continue
    if "private-key:" in ln:
        continue
    raise SystemExit(
        f"private key appears outside mint private-key input at line {i}: {stripped}"
    )

for banned in (
    "LINKTREND_BUGBOT_USER_TOKEN",
    "BUGBOT_USER_TOKEN",
    "resolve_bugbot_user_token",
):
    if banned in prod:
        raise SystemExit(f"human credential fallback present: {banned}")

# github.token must not authorize status publication.
blocks = re.split(r"\n(?=      - name:)", prod)
for block in blocks:
    uses_github_token = bool(
        re.search(r"(GH_TOKEN|GITHUB_TOKEN):\s*\$\{\{\s*github\.token", block)
    )
    publishes = bool(
        re.search(
            r"(statuses/|readiness_status|publish_review_ready|Linktrend Review Ready)",
            block,
            re.I,
        )
    )
    if uses_github_token and publishes and "run:" in block:
        raise SystemExit(
            "github.token bound in a block that also publishes/readiness statuses"
        )

for key in ("branch", "sha", "dry_run"):
    if not re.search(rf"^\s*{key}\s*:", prod, re.M):
        raise SystemExit(f"workflow_dispatch input missing: {key}")

# Trusted source + data-only tip checkout + immutable tip verify.
assert "github.event.repository.default_branch" in prod
assert "untrusted-branch-data" in prod
assert "sha_mismatch" in prod
assert "refuse GITHUB_TOKEN publish fallback" in prod or "no human fallback" in prod.lower()
assert "completion_gate" in prod or "validate_evidence" in prod
assert "review_ready_dispatch.py" in prod
assert "automation_credentials_blocked" in prod
assert "resolve_automation_token" in prod
print("ok")
PY
pass "Production workflow trusted-source + no human/token-fallback static checks"

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
    for key in ("repository", "issue_number", "evidence_path", "evidence_json", "dry_run"):
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

# ---- 8) Fixture contract matches readiness_status App-backed route ----
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
assert "-f dry_run=false" in route
assert contract["statusContext"] == rs.CONTEXT
print("ok")
PY
pass "Fixture contract matches readiness_status App-backed route"

echo "PASS: review-ready publisher adversarial/static suite"
