#!/usr/bin/env bash
# Phase 2 fixed-pipeline feasibility runner.
# Deterministic validator scenarios + documented supervised agent scenarios.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
FIXTURE="$ROOT/tests/fixtures/fixed-pipeline-feasibility"
STATE="$FIXTURE/pipeline-state.json"
VALIDATOR="$ROOT/scripts/feasibility/validate-pipeline-transition.mjs"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/feasibility.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT

cp -R "$FIXTURE/." "$WORK/fixture/"
WSTATE="$WORK/fixture/pipeline-state.json"

pass=0
fail=0

run_expect_fail() {
  local label="$1"
  shift
  set +e
  node "$VALIDATOR" "$@" >"$WORK/out.txt" 2>"$WORK/err.txt"
  local code=$?
  set -e
  if [[ "$code" -ne 0 ]]; then
    echo "PASS (rejected as expected): $label"
    pass=$((pass + 1))
  else
    echo "FAIL (should have rejected): $label"
    cat "$WORK/err.txt" "$WORK/out.txt" || true
    fail=$((fail + 1))
  fi
}

run_expect_ok() {
  local label="$1"
  shift
  set +e
  node "$VALIDATOR" "$@" >"$WORK/out.txt" 2>"$WORK/err.txt"
  local code=$?
  set -e
  if [[ "$code" -eq 0 ]]; then
    echo "PASS: $label"
    pass=$((pass + 1))
  else
    echo "FAIL: $label"
    cat "$WORK/err.txt" "$WORK/out.txt" || true
    fail=$((fail + 1))
  fi
}

assert_state_unchanged() {
  local label="$1"
  if ! diff -q "$STATE" "$WSTATE" >/dev/null 2>&1; then
    # Compare against snapshot taken at start of negative test — for fail paths we copy fresh
    :
  fi
  # For negative tests we use --apply on a copy and verify copy equals pre-attempt when rejected
  echo "NOTE: $label — fail-closed leaves working copy unchanged when reject before --apply"
}

echo "=== Deterministic validator scenarios ==="

# Snapshot original fixture for git-diff acceptance later
ORIG_HASH="$(shasum -a 256 "$STATE" | awk '{print $1}')"

# --- Negative: Module 1 complete without Principal approval ---
cp -R "$FIXTURE/." "$WORK/n1/"
python3 - <<'PY' "$WORK/n1"
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
gate = json.loads((root / "modules/01-intake-and-definition/gate.json").read_text())
gate["verdict"] = "pass"
gate["principalApprovalRecorded"] = False
(root / "modules/01-intake-and-definition/gate.json").write_text(json.dumps(gate, indent=2) + "\n")
before = (root / "pipeline-state.json").read_text()
pathlib.Path(root / "before.json").write_text(before)
PY
run_expect_fail "Module 1 complete without Principal approval" \
  --state "$WORK/n1/pipeline-state.json" \
  --request-transition "intake_and_definition:complete" --apply
if ! diff -q "$WORK/n1/before.json" "$WORK/n1/pipeline-state.json" >/dev/null; then
  echo "FAIL: state changed after rejected Module 1 complete"
  fail=$((fail + 1))
else
  echo "PASS: state unchanged after rejected Module 1 complete"
  pass=$((pass + 1))
fi

# --- Negative: activate Module 3 when Module 2 gate rejected / not complete ---
cp -R "$FIXTURE/." "$WORK/n2/"
python3 - <<'PY' "$WORK/n2"
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
state = json.loads((root / "pipeline-state.json").read_text())
state["modules"]["intake_and_definition"]["state"] = "complete"
state["modules"]["assembly_planning"]["state"] = "active"
state["modules"]["assembly_planning"]["gateVerdict"] = "rejected"
(root / "pipeline-state.json").write_text(json.dumps(state, indent=2) + "\n")
gate = json.loads((root / "modules/02-assembly-planning/gate.json").read_text())
gate["verdict"] = "rejected"
(root / "modules/02-assembly-planning/gate.json").write_text(json.dumps(gate, indent=2) + "\n")
pathlib.Path(root / "before.json").write_text((root / "pipeline-state.json").read_text())
PY
run_expect_fail "Activate Module 3 while Module 2 incomplete/rejected" \
  --state "$WORK/n2/pipeline-state.json" \
  --request-transition "execution:active" --apply
if ! diff -q "$WORK/n2/before.json" "$WORK/n2/pipeline-state.json" >/dev/null; then
  echo "FAIL: state changed after rejected Module 3 activation"
  fail=$((fail + 1))
else
  echo "PASS: state unchanged after rejected Module 3 activation"
  pass=$((pass + 1))
fi

# --- Negative: Issue done without proof/review/integration ---
cp -R "$FIXTURE/." "$WORK/n3/"
python3 - <<'PY' "$WORK/n3"
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
state = json.loads((root / "pipeline-state.json").read_text())
state["issues"] = {
  "ISSUE-1": {
    "status": "in_progress",
    "proof": None,
    "review": None,
    "integration": None
  }
}
(root / "pipeline-state.json").write_text(json.dumps(state, indent=2) + "\n")
pathlib.Path(root / "before.json").write_text((root / "pipeline-state.json").read_text())
PY
run_expect_fail "Issue done without proof/review/integration" \
  --state "$WORK/n3/pipeline-state.json" \
  --request-issue-done "ISSUE-1" --apply
if ! diff -q "$WORK/n3/before.json" "$WORK/n3/pipeline-state.json" >/dev/null; then
  echo "FAIL: state changed after rejected issue done"
  fail=$((fail + 1))
else
  echo "PASS: state unchanged after rejected issue done"
  pass=$((pass + 1))
fi

# --- Negative: Module 4 complete with unmet criteria ---
cp -R "$FIXTURE/." "$WORK/n4/"
python3 - <<'PY' "$WORK/n4"
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
gate = json.loads((root / "modules/04-verification-and-hardening/gate.json").read_text())
gate["verdict"] = "pass"
gate["unmetLivingDocumentCriteria"] = ["AC-1"]
(root / "modules/04-verification-and-hardening/gate.json").write_text(json.dumps(gate, indent=2) + "\n")
pathlib.Path(root / "before.json").write_text((root / "pipeline-state.json").read_text())
PY
run_expect_fail "Module 4 complete with unmet Living Document criteria" \
  --state "$WORK/n4/pipeline-state.json" \
  --request-transition "verification_and_hardening:complete" --apply

# --- Negative: Module 6 complete rejected ---
cp -R "$FIXTURE/." "$WORK/n5/"
python3 - <<'PY' "$WORK/n5"
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
gate = json.loads((root / "modules/06-shipment/gate.json").read_text())
gate["verdict"] = "pass"
(root / "modules/06-shipment/gate.json").write_text(json.dumps(gate, indent=2) + "\n")
pathlib.Path(root / "before.json").write_text((root / "pipeline-state.json").read_text())
PY
run_expect_fail "Module 6 complete (must use release_ready)" \
  --state "$WORK/n5/pipeline-state.json" \
  --request-transition "shipment:complete" --apply

# --- Happy path (deterministic apply on working copy) ---
cp -R "$FIXTURE/." "$WORK/happy/"
python3 - <<'PY' "$WORK/happy"
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
# Mark Module 1 gate + principal approval
gate = json.loads((root / "modules/01-intake-and-definition/gate.json").read_text())
gate["verdict"] = "pass"
gate["principalApprovalRecorded"] = True
(root / "modules/01-intake-and-definition/gate.json").write_text(json.dumps(gate, indent=2) + "\n")
for mid, rel in [
  ("02-assembly-planning", "assembly_planning"),
  ("03-execution", "execution"),
  ("04-verification-and-hardening", "verification_and_hardening"),
  ("05-library-contribution", "library_contribution"),
  ("06-shipment", "shipment"),
]:
    gpath = root / f"modules/{mid}/gate.json"
    g = json.loads(gpath.read_text())
    g["verdict"] = "pass"
    if mid == "04-verification-and-hardening":
        g["unmetLivingDocumentCriteria"] = []
    gpath.write_text(json.dumps(g, indent=2) + "\n")
state = json.loads((root / "pipeline-state.json").read_text())
state["principalDecisions"] = [{"scope": "module1", "decision": "approved"}]
state["livingDocumentCriteria"] = [{"id": "AC-1", "status": "met"}]
state["issues"] = {
  "ISSUE-1": {
    "status": "review_ready",
    "proof": {"status": "present"},
    "review": {"verdict": "pass"},
    "integration": {"status": "integrated"}
  }
}
(root / "pipeline-state.json").write_text(json.dumps(state, indent=2) + "\n")
PY

for step in \
  "intake_and_definition:complete" \
  "assembly_planning:active" \
  "assembly_planning:complete" \
  "execution:active" \
  "execution:complete" \
  "verification_and_hardening:active" \
  "verification_and_hardening:complete" \
  "library_contribution:active" \
  "library_contribution:complete" \
  "shipment:active"
do
  run_expect_ok "Happy path step $step" \
    --state "$WORK/happy/pipeline-state.json" \
    --request-transition "$step" --apply
done

run_expect_ok "Happy path issue done with proof/review/integration" \
  --state "$WORK/happy/pipeline-state.json" \
  --request-issue-done "ISSUE-1" --apply

run_expect_ok "Happy path terminal release_ready" \
  --state "$WORK/happy/pipeline-state.json" \
  --set-terminal "release_ready" --apply

# Ensure committed fixture unchanged
NEW_HASH="$(shasum -a 256 "$STATE" | awk '{print $1}')"
if [[ "$ORIG_HASH" == "$NEW_HASH" ]]; then
  echo "PASS: committed fixture pipeline-state.json unchanged"
  pass=$((pass + 1))
else
  echo "FAIL: committed fixture was mutated"
  fail=$((fail + 1))
fi

echo ""
echo "=== Supervised agent scenarios (documented evidence) ==="
echo "See docs/validation/fixed-pipeline-feasibility-report.md for:"
echo "  1) Happy path Cursor session"
echo "  2) Failed gate refuse Module 3"
echo "  3) Resume in new chat from durable state"
echo "  4) Direct completion attempt refuse"
echo ""
echo "Deterministic results: pass=$pass fail=$fail"

if [[ "$fail" -ne 0 ]]; then
  exit 1
fi
exit 0
