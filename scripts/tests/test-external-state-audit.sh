#!/usr/bin/env bash
# Contract tests for scripts/gitops/external_state_audit.py
# All cases use fixtures or dry-run — no live GitHub mutation or secret value reads.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PY="${ROOT}/scripts/gitops/external_state_audit.py"
CONTRACT="${ROOT}/docs/contracts/EXTERNAL-STATE-AUDIT.md"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass() { echo "PASS: $*"; }
fail() { echo "FAIL: $*" >&2; exit 1; }

[ -f "$PY" ] || fail "missing external_state_audit.py"
[ -f "$CONTRACT" ] || fail "missing EXTERNAL-STATE-AUDIT.md"
chmod +x "$PY" 2>/dev/null || true

write_fixture() {
  local dir="$1"
  mkdir -p "$dir"
  cat >"${dir}/state.json"
}

# ---- unit: dry-run default is unchecked, mutations empty, exit 0 ----
cd "$ROOT"
python3 "$PY" report --repo linktrend/Fixture --json-output "${TMP}/dry.json" >/dev/null
python3 - <<PY
import json
from pathlib import Path
p = json.loads(Path("${TMP}/dry.json").read_text())
assert p["schemaVersion"] == 1
assert p["dryRun"] is True
assert p["mode"] == "report"
assert p["mutations"] == []
assert p["source"] == "dry-run"
assert p["statusContext"] == "Linktrend Review Ready"
assert p["summary"]["ready"] is False
statuses = {c["id"]: c["status"] for c in p["checks"]}
assert statuses["github_auth.automation_token_secret"] == "unchecked"
assert statuses["bugbot.user_token_secret"] == "unchecked"
assert statuses["bugbot.manual_trigger_only"] == "unchecked"
assert statuses["protection.development_ruleset"] == "unchecked"
assert statuses["protection.staging_ruleset"] == "unchecked"
assert statuses["protection.main_ruleset"] == "unchecked"
assert statuses["protection.allow_auto_merge"] == "unchecked"
assert statuses["carlos.user_token_boundary"] in {"unchecked", "unknown"}
assert statuses["workflows.required_presence"] in {"unchecked", "unknown"}
assert statuses["completion.status_context"] == "ok"
assert "LINKTREND_AUTOMATION_TOKEN" in json.dumps(p["checklist"])
assert p.get("applyRefused") is True
assert p["mutations"] == []
assert p.get("humanSummary")
# Ensure no accidental secret-looking PEM blob markers in output
text = Path("${TMP}/dry.json").read_text()
assert "BEGIN PRIVATE KEY" not in text
assert "BEGIN RSA PRIVATE KEY" not in text
print("dry-run ok")
PY
pass "dry-run default report is unchecked with empty mutations"

# verify on dry-run must be not-ready (exit 3)
set +e
python3 "$PY" verify --repo linktrend/Fixture >"${TMP}/dry-verify.json" 2>"${TMP}/dry-verify.err"
rc=$?
set -e
[ "$rc" -eq 3 ] || fail "dry-run verify expected exit 3 got $rc"
pass "dry-run verify exits 3 (not ready)"

# ---- refuse --live with --fixture-dir ----
set +e
python3 "$PY" report --repo linktrend/Fixture --live --fixture-dir "$TMP" \
  >"${TMP}/refuse.out" 2>"${TMP}/refuse.err"
rc=$?
set -e
[ "$rc" -eq 5 ] || fail "live+fixture expected exit 5 got $rc"
pass "refuses --live combined with --fixture-dir"

# ---- mutate method refused ----
python3 - <<PY
import sys
from pathlib import Path
sys.path.insert(0, str(Path("${ROOT}/scripts/gitops").resolve()))
import external_state_audit as esa
client = esa.ReadOnlyGitHubClient("linktrend/Fixture")
try:
    client.mutate("POST", "/repos/x")
except esa.AuditError as e:
    assert e.exit_code == esa.EXIT_REFUSED
else:
    raise SystemExit("mutate POST should refuse")
for method in ("PUT", "PATCH", "DELETE"):
    try:
        client.mutate(method)
    except esa.AuditError as e:
        assert e.exit_code == esa.EXIT_REFUSED
    else:
        raise SystemExit(f"mutate {method} should refuse")
print("mutate refused")
PY
pass "mutating HTTP methods refused"

# ---- fixture: ready (full WP1 surface via shared matched fixture) ----
READY_FX="${ROOT}/scripts/tests/fixtures/external-state-wp1/matched"
[ -d "$READY_FX" ] || fail "missing WP1 matched fixture for ready case"

python3 "$PY" verify --repo linktrend/Fixture --fixture-dir "${READY_FX}" \
  --json-output "${TMP}/ready-out.json" >/dev/null
python3 - <<PY
import json
from pathlib import Path
p = json.loads(Path("${TMP}/ready-out.json").read_text())
assert p["dryRun"] is True
assert p["mutations"] == []
assert p["source"] == "fixture"
assert p["summary"]["ready"] is True
assert p["summary"]["missing"] == 0
assert p["summary"]["drift"] == 0
assert p["summary"]["unchecked"] == 0
for c in p["checks"]:
    assert c["status"] in {"ok", "matched"}, c
# Fixture must not have embedded private key material
text = Path("${READY_FX}/state.json").read_text()
assert "PRIVATE KEY" not in text
assert "ghs_" not in text
assert "github_pat_" not in text
print("ready ok")
PY
pass "fixture ready verify exits 0 with all ok"

# ---- fixture: missing secrets / installation / ruleset ----
CRED_FX="${ROOT}/scripts/tests/fixtures/external-state-wp1/credential-missing"
[ -d "$CRED_FX" ] || fail "missing WP1 credential-missing fixture"

set +e
python3 "$PY" verify --repo linktrend/Fixture --fixture-dir "${CRED_FX}" \
  --json-output "${TMP}/missing-out.json" >/dev/null
rc=$?
set -e
[ "$rc" -eq 3 ] || fail "missing fixture verify expected exit 3 got $rc"
python3 - <<PY
import json
from pathlib import Path
p = json.loads(Path("${TMP}/missing-out.json").read_text())
assert p["summary"]["ready"] is False
by = {c["id"]: c for c in p["checks"]}
assert by["github_auth.automation_token_secret"]["status"] == "credential-missing"
assert by["bugbot.user_token_secret"]["status"] == "credential-missing"
assert p["mutations"] == []
print("missing ok")
PY
pass "missing/credential-missing fixture verify exits 3"

# ---- fixture: drift on ruleset checks ----
DRIFT_FX="${ROOT}/scripts/tests/fixtures/external-state-wp1/drifted"
[ -d "$DRIFT_FX" ] || fail "missing WP1 drifted fixture"

set +e
python3 "$PY" verify --repo linktrend/Fixture --fixture-dir "${DRIFT_FX}" \
  --json-output "${TMP}/drift-out.json" >/dev/null
rc=$?
set -e
[ "$rc" -eq 3 ] || fail "drift fixture verify expected exit 3 got $rc"
python3 - <<PY
import json
from pathlib import Path
p = json.loads(Path("${TMP}/drift-out.json").read_text())
by = {c["id"]: c for c in p["checks"]}
assert by["bugbot.check_name"]["status"] == "drift"
assert by["protection.development_ruleset"]["status"] == "drift"
assert "Linktrend Review Gate" in by["protection.development_ruleset"]["detail"]
assert p["mutations"] == []
print("drift ok")
PY
pass "drift fixture reports non-numeric app id and incomplete ruleset"

# ---- secret name present even if fixture wrongly includes a value key ----
# Build from matched fixture but inject ignored secret value keys.
python3 - <<PY
import json, shutil
from pathlib import Path
src = Path("${ROOT}/scripts/tests/fixtures/external-state-wp1/matched/state.json")
dest = Path("${TMP}/secret-value-ignored")
dest.mkdir(parents=True, exist_ok=True)
state = json.loads(src.read_text())
state.pop("actions_secret_names", None)
state["actions_secrets"] = [
    {"name": "LINKTREND_AUTOMATION_TOKEN", "value": "SHOULD_NEVER_APPEAR_IN_OUTPUT"},
    {"name": "LINKTREND_BUGBOT_USER_TOKEN", "value": "ALSO_SHOULD_NEVER_APPEAR"},
]
(dest / "state.json").write_text(json.dumps(state, indent=2) + "\n")
print("wrote secret-value-ignored fixture")
PY

python3 "$PY" report --repo linktrend/Fixture --fixture-dir "${TMP}/secret-value-ignored" \
  --json-output "${TMP}/secret-out.json" >/dev/null
python3 - <<PY
import json
from pathlib import Path
text = Path("${TMP}/secret-out.json").read_text()
assert "SHOULD_NEVER_APPEAR_IN_OUTPUT" not in text
assert "ALSO_SHOULD_NEVER_APPEAR" not in text
p = json.loads(text)
by = {c["id"]: c for c in p["checks"]}
assert by["github_auth.automation_token_secret"]["status"] == "ok"
assert by["bugbot.user_token_secret"]["status"] == "ok"
assert by["github_auth.automation_token_secret"]["observed"] == "name_present"
print("secret values ignored")
PY
pass "fixture secret values never appear in report output"

# ---- process-env secret presence warns without printing value ----
SECRET_VAL="pem-material-MUST-NOT-LEAK-into-json-output-$$"
export LINKTREND_AUTOMATION_TOKEN="${SECRET_VAL}"
python3 "$PY" report --repo linktrend/Fixture --json-output "${TMP}/leak-warn.json" >/dev/null
python3 - <<PY
import json
from pathlib import Path
text = Path("${TMP}/leak-warn.json").read_text()
assert "pem-material-MUST-NOT-LEAK-into-json-output" not in text
p = json.loads(text)
assert any(("LINKTREND_AUTOMATION_TOKEN" in w and "present_in_process_env" in w) for w in p["warnings"])
print("env warn ok")
PY
unset LINKTREND_AUTOMATION_TOKEN
pass "secret env presence warns without leaking value"

# ---- contract doc mentions hard rules ----
grep -q 'dry-run' "$CONTRACT" || fail "contract missing dry-run"
grep -q 'Never' "$CONTRACT" || fail "contract missing Never prohibition language"
grep -q 'LINKTREND_AUTOMATION_TOKEN' "$CONTRACT" || fail "contract missing automation token name"
grep -q 'manualTriggerOnly' "$CONTRACT" || fail "contract missing manualTriggerOnly"
grep -q 'development-autonomous-merge' "$CONTRACT" || fail "contract missing ruleset name"
grep -q 'Linktrend Review Ready' "$CONTRACT" || fail "contract missing status context"
grep -q 'mutations' "$CONTRACT" || fail "contract missing mutations empty guarantee"
pass "contract documents automation/Bugbot/protection audit surface"

# ---- default argv (no mode) equals report ----
python3 "$PY" --repo linktrend/Fixture >"${TMP}/default-mode.json"
python3 -c 'import json,sys; p=json.load(open(sys.argv[1])); assert p["mode"]=="report"' \
  "${TMP}/default-mode.json"
pass "default mode is report"

echo "PASS: all external-state audit contract tests"
