#!/usr/bin/env bash
# WP1 Lane C fixture matrix for external-state plan/verify.
# Covers: matched, drifted, forbidden, unavailable, malformed, credential-missing.
# Read-only only — apply refused; no live mutations; no secret values.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FX="${ROOT}/scripts/tests/fixtures/external-state-wp1"
AUDIT="${ROOT}/scripts/gitops/external_state_audit.py"
PLAN="${ROOT}/scripts/gitops/external_state_plan.py"
VERIFY="${ROOT}/scripts/gitops/external_state_verify.py"
SCHEMA_PLAN="${ROOT}/core/managed-core/schemas/external-state-plan.schema.json"
SCHEMA_VERIFY="${ROOT}/core/managed-core/schemas/external-state-verify.schema.json"
RP_FX="${ROOT}/scripts/tests/fixtures/repository-protection"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass() { echo "PASS: $*"; }
fail() { echo "FAIL: $*" >&2; exit 1; }

[ -f "$AUDIT" ] || fail "missing external_state_audit.py"
[ -f "$PLAN" ] || fail "missing external_state_plan.py"
[ -f "$VERIFY" ] || fail "missing external_state_verify.py"
[ -f "$SCHEMA_PLAN" ] || fail "missing external-state-plan.schema.json"
[ -f "$SCHEMA_VERIFY" ] || fail "missing external-state-verify.schema.json"
[ -d "$FX/matched" ] || fail "missing matched fixture"
chmod +x "$AUDIT" "$PLAN" "$VERIFY" 2>/dev/null || true

cd "$ROOT"

# ---- schemas exist and mention required surface ----
grep -q 'humanSummary' "$SCHEMA_PLAN" || fail "plan schema missing humanSummary"
grep -q 'credential-missing' "$SCHEMA_PLAN" || fail "plan schema missing credential-missing"
grep -q 'applyRefused' "$SCHEMA_PLAN" || fail "plan schema missing applyRefused"
grep -q '"mode".*"verify"' "$SCHEMA_VERIFY" || grep -q 'const": "verify"' "$SCHEMA_VERIFY" \
  || fail "verify schema missing verify mode"
pass "schemas present"

# ---- apply refused ----
set +e
python3 "$AUDIT" apply --repo linktrend/Fixture >"${TMP}/apply.out" 2>"${TMP}/apply.err"
rc=$?
set -e
[ "$rc" -eq 5 ] || fail "apply expected exit 5 got $rc"
grep -q 'refused' "${TMP}/apply.err" || fail "apply stderr missing refused"
pass "apply mode refused (exit 5)"

# ---- plan wrapper defaults to plan ----
python3 "$PLAN" --repo linktrend/Fixture --fixture-dir "${FX}/matched" \
  --json-output "${TMP}/plan-matched.json" >/dev/null
python3 - <<PY
import json
from pathlib import Path
p = json.loads(Path("${TMP}/plan-matched.json").read_text())
assert p["mode"] == "plan"
assert p["dryRun"] is True
assert p["mutations"] == []
assert p["applyRefused"] is True
assert p["summary"]["ready"] is True
assert p["humanSummary"]
assert all(d["mutate"] is False for d in p["desired"])
assert "BEGIN PRIVATE KEY" not in Path("${TMP}/plan-matched.json").read_text()
print("plan wrapper ok")
PY
pass "plan wrapper matched fixture"

# ---- verify wrapper matched ----
python3 "$VERIFY" --repo linktrend/Fixture --fixture-dir "${FX}/matched" \
  --json-output "${TMP}/verify-matched.json" >/dev/null
python3 - <<PY
import json
from pathlib import Path
p = json.loads(Path("${TMP}/verify-matched.json").read_text())
assert p["mode"] == "verify"
assert p["summary"]["ready"] is True
by = {c["id"]: c for c in p["checks"]}
assert by["github_app.authority_scope"]["status"] in {"ok", "matched"}
assert by["carlos.user_token_boundary"]["status"] in {"ok", "matched"}
assert by["protection.staging_ruleset"]["status"] == "ok"
assert by["protection.main_ruleset"]["status"] == "ok"
assert by["protection.promotion_source_policy"]["status"] in {"ok", "matched"}
assert by["protection.repo_specific_checks_preserved"]["status"] in {"ok", "matched"}
assert by["workflows.required_presence"]["status"] in {"ok", "matched"}
assert "Consumer Staging Lint" in json.dumps(
    (p.get("protectionPlan") or {}).get("branches") or {}
) or by["protection.repo_specific_checks_preserved"]["status"] in {"ok", "matched"}
print("verify matched ok")
PY
pass "verify matched → ready"

# ---- drifted ----
set +e
python3 "$VERIFY" --repo linktrend/Fixture --fixture-dir "${FX}/drifted" \
  --json-output "${TMP}/verify-drifted.json" >/dev/null
rc=$?
set -e
[ "$rc" -eq 3 ] || fail "drifted verify expected exit 3 got $rc"
python3 - <<PY
import json
from pathlib import Path
p = json.loads(Path("${TMP}/verify-drifted.json").read_text())
assert p["summary"]["ready"] is False
by = {c["id"]: c for c in p["checks"]}
assert by["github_app.app_id_variable"]["status"] == "drift"
assert by["bugbot.check_name"]["status"] == "drift"
assert by["protection.development_ruleset"]["status"] == "drift"
assert by["protection.promotion_source_policy"]["status"] == "drift"
assert by["protection.allow_auto_merge"]["status"] == "drift"
assert by["workflows.required_presence"]["status"] == "drift"
assert p["mutations"] == []
print("drifted ok")
PY
pass "drifted fixture verify exits 3"

# ---- forbidden ----
set +e
python3 "$VERIFY" --repo linktrend/Fixture --fixture-dir "${FX}/forbidden" \
  --json-output "${TMP}/verify-forbidden.json" >/dev/null
rc=$?
set -e
[ "$rc" -eq 3 ] || fail "forbidden verify expected exit 3 got $rc"
python3 - <<PY
import json
from pathlib import Path
p = json.loads(Path("${TMP}/verify-forbidden.json").read_text())
by = {c["id"]: c for c in p["checks"]}
assert by["github_app.authority_scope"]["status"] == "forbidden"
assert by["carlos.user_token_boundary"]["status"] == "forbidden"
assert by["workflows.permissions_posture"]["status"] == "forbidden"
assert p["mutations"] == []
print("forbidden ok")
PY
pass "forbidden fixture reports forbidden statuses"

# ---- unavailable ----
set +e
python3 "$VERIFY" --repo linktrend/Fixture --fixture-dir "${FX}/unavailable" \
  --json-output "${TMP}/verify-unavailable.json" >/dev/null
rc=$?
set -e
[ "$rc" -eq 4 ] || fail "unavailable verify expected exit 4 got $rc"
python3 - <<PY
import json
from pathlib import Path
p = json.loads(Path("${TMP}/verify-unavailable.json").read_text())
by = {c["id"]: c for c in p["checks"]}
assert by["protection.development_ruleset"]["status"] == "unavailable"
assert by["protection.staging_ruleset"]["status"] == "unavailable"
assert by["protection.main_ruleset"]["status"] == "unavailable"
assert p["summary"]["ready"] is False
assert p["mutations"] == []
print("unavailable ok")
PY
pass "unavailable fixture verify exits 4"

# ---- malformed ----
set +e
python3 "$PLAN" --repo linktrend/Fixture --fixture-dir "${FX}/malformed" \
  >"${TMP}/malformed.out" 2>"${TMP}/malformed.err"
rc=$?
set -e
[ "$rc" -eq 1 ] || fail "malformed expected exit 1 got $rc"
grep -qi 'malformed' "${TMP}/malformed.err" || fail "malformed stderr missing marker"
pass "malformed fixture refused"

# ---- credential-missing ----
set +e
python3 "$VERIFY" --repo linktrend/Fixture --fixture-dir "${FX}/credential-missing" \
  --json-output "${TMP}/verify-cred.json" >/dev/null
rc=$?
set -e
[ "$rc" -eq 3 ] || fail "credential-missing verify expected exit 3 got $rc"
python3 - <<PY
import json
from pathlib import Path
p = json.loads(Path("${TMP}/verify-cred.json").read_text())
by = {c["id"]: c for c in p["checks"]}
assert by["github_app.private_key_secret"]["status"] == "credential-missing"
assert by["bugbot.user_token_secret"]["status"] == "credential-missing"
assert by["github_app.app_id_variable"]["status"] == "missing"
assert by["github_app.installation"]["status"] == "missing"
text = Path("${TMP}/verify-cred.json").read_text()
assert "BEGIN PRIVATE KEY" not in text
assert "ghs_" not in text
assert "github_pat_" not in text
print("credential-missing ok")
PY
pass "credential-missing fixture"

# ---- repository_protection read_only refuses mutate ----
python3 - <<PY
import sys
from pathlib import Path
sys.path.insert(0, str(Path("${ROOT}/scripts/gitops").resolve()))
import repository_protection as rp

client = rp.FixtureClient(
    "linktrend/Fixture",
    Path("${RP_FX}/read-only-plan"),
    read_only=True,
)
plan = rp.build_plan(client)
assert plan["mutations"] == []
ok, problems = rp.verify_plan(plan)
assert ok, problems
try:
    client.create_ruleset({"name": "x"})
except rp.ProtectionError as e:
    assert e.exit_code == rp.EXIT_REFUSED
else:
    raise SystemExit("read_only create_ruleset should refuse")
for op in ("update_ruleset", "delete_ruleset", "put_branch_protection", "patch_repo"):
    try:
        if op == "update_ruleset":
            client.update_ruleset(1, {"name": "x"})
        elif op == "delete_ruleset":
            client.delete_ruleset(1)
        elif op == "put_branch_protection":
            client.put_branch_protection("development", {})
        else:
            client.patch_repo({"allow_auto_merge": False})
    except rp.ProtectionError as e:
        assert e.exit_code == rp.EXIT_REFUSED, op
    else:
        raise SystemExit(f"read_only {op} should refuse")
print("read_only protection ok")
PY
pass "repository_protection read_only plan/verify; mutate refused"

# ---- mutate methods on audit client refused ----
python3 - <<PY
import sys
from pathlib import Path
sys.path.insert(0, str(Path("${ROOT}/scripts/gitops").resolve()))
import external_state_audit as esa
client = esa.ReadOnlyGitHubClient("linktrend/Fixture")
for method in ("POST", "PUT", "PATCH", "DELETE"):
    try:
        client.mutate(method)
    except esa.AuditError as e:
        assert e.exit_code == esa.EXIT_REFUSED
    else:
        raise SystemExit(f"mutate {method} should refuse")
try:
    client.apply()
except esa.AuditError as e:
    assert e.exit_code == esa.EXIT_REFUSED
else:
    raise SystemExit("apply() should refuse")
print("audit mutate/apply refused")
PY
pass "audit mutate/apply helpers refuse"

# ---- dry-run plan never assumes compliant ----
python3 "$PLAN" --repo linktrend/Fixture --json-output "${TMP}/dry-plan.json" >/dev/null
python3 - <<PY
import json
from pathlib import Path
p = json.loads(Path("${TMP}/dry-plan.json").read_text())
assert p["source"] == "dry-run"
assert p["summary"]["ready"] is False
assert p["mutations"] == []
unproven = set(p["summary"].get("unproven") or [])
assert unproven, "dry-run must list unproven checks"
# Never treat unknown as ready
for c in p["checks"]:
    if c["id"] != "completion.status_context":
        assert c["status"] in {
            "unchecked", "unknown", "ok", "matched"
        } or c["id"] == "completion.status_context"
print("dry-run plan ok")
PY
pass "dry-run plan leaves observations unproven"

echo "PASS: all external-state WP1 Lane C tests"
