#!/usr/bin/env bash
# GATE-STOP-001: behavioral fail-closed gate test (negative + positive control).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NEG="$ROOT/tests/fixtures/gate-stop-progression/negative"
POS="$ROOT/tests/fixtures/gate-stop-progression/positive"
VALIDATOR="$ROOT/core/runtime/validate-application-pipeline.mjs"

fail() { echo "FAIL: $*" >&2; exit 1; }
pass() { echo "PASS: $*"; }

echo "=== GATE-STOP-001 negative scenario ==="

# 1-3: criterion required verified; executor wrote unverified; proof falsely claims pass
grep -q 'unverified' "$NEG/output.txt" || fail "negative fixture missing unverified content"
grep -q 'verified' "$NEG/PROOF.md" || fail "negative proof missing false claim"
# 4: independent review must fail and cite mismatch
grep -qi 'fail' "$NEG/REVIEW.md" || fail "review must fail"
grep -qi 'unverified' "$NEG/REVIEW.md" || fail "review must cite mismatch"
# 5: integration refused
grep -qi 'refused' "$NEG/INTEGRATION.md" || fail "integration must refuse"
# 6: issue must not be done
if grep -Eq 'status:[[:space:]]*done' "$NEG/ISSUE.md"; then
  fail "negative issue must not be done"
fi
grep -Eq 'status:[[:space:]]*(in_progress|review_ready)' "$NEG/ISSUE.md" \
  || fail "negative issue must remain in_progress or review_ready"
# 7: dependent blocked
grep -Eq 'status:[[:space:]]*blocked' "$NEG/dependent-ISSUE.md" || fail "dependent must remain blocked"
# 8: module gate fail
python3 - <<'PY' "$NEG/module-gate.json"
import json, pathlib, sys
g = json.loads(pathlib.Path(sys.argv[1]).read_text())
assert g.get("verdict") in ("rejected", "fail"), g
print("module gate rejected OK")
PY
# 9: orchestrator continue-anyway refused by validator (Module complete with rejected gate)
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
cp -R "$ROOT/tests/fixtures/fixed-pipeline-feasibility/." "$WORK/"
python3 - <<'PY' "$WORK"
import json, pathlib, sys
root = pathlib.Path(sys.argv[1])
gate = json.loads((root / "modules/03-execution/gate.json").read_text())
gate["verdict"] = "rejected"
(root / "modules/03-execution/gate.json").write_text(json.dumps(gate, indent=2) + "\n")
state = json.loads((root / "pipeline-state.json").read_text())
state["modules"]["intake_and_definition"]["state"] = "complete"
state["modules"]["assembly_planning"]["state"] = "complete"
state["modules"]["execution"]["state"] = "active"
(root / "pipeline-state.json").write_text(json.dumps(state, indent=2) + "\n")
pathlib.Path(root / "before.json").write_text((root / "pipeline-state.json").read_text())
PY
set +e
node "$VALIDATOR" --state "$WORK/pipeline-state.json" --request-transition "execution:complete" --apply \
  >"$WORK/out.txt" 2>"$WORK/err.txt"
code=$?
set -e
[[ "$code" -ne 0 ]] || fail "continue-anyway Module complete must be rejected"
diff -q "$WORK/before.json" "$WORK/pipeline-state.json" >/dev/null || fail "state changed after rejected continue-anyway"
pass "orchestrator refuse continue-anyway (validator non-zero, state unchanged)"
# 10: waiver without authority/reason/scope/expiry fails
python3 - <<'PY' "$NEG/waiver-attempt.json"
import json, pathlib, sys
w = json.loads(pathlib.Path(sys.argv[1]).read_text())
for k in ("authority", "reason", "scope", "expiry"):
    if w.get(k):
        raise SystemExit(f"waiver field {k} unexpectedly set")
if w.get("result") != "rejected":
    raise SystemExit("waiver must be rejected")
print("waiver rejected OK")
PY
pass "negative scenario"

echo "=== GATE-STOP-001 positive control ==="
grep -qx 'verified' "$POS/output.txt" || fail "positive output must be exact verified"
grep -Eq 'verdict:[[:space:]]*pass' "$POS/PROOF.md" || fail "positive proof pass"
grep -Eq 'verdict:[[:space:]]*pass' "$POS/REVIEW.md" || fail "positive review pass"
grep -Eq 'status:[[:space:]]*integrated' "$POS/INTEGRATION.md" || fail "positive integration"
grep -Eq 'status:[[:space:]]*done' "$POS/ISSUE.md" || fail "positive issue done"
grep -Eq 'status:[[:space:]]*ready' "$POS/dependent-ISSUE.md" || fail "dependent readiness recomputed"
pass "positive control"

echo "GATE-STOP-001: ALL CHECKS PASSED"
exit 0
