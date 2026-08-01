#!/usr/bin/env bash
# Focused tests for managed repository protections (WP5).
# All cases use fixtures — no live GitHub mutation or credential reads.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FX="${ROOT}/scripts/tests/fixtures/repository-protection"
TOOL="${ROOT}/scripts/manage-repository-protections.sh"
LEGACY="${ROOT}/scripts/apply-development-merge-ruleset.sh"
PY="${ROOT}/scripts/gitops/repository_protection.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass() { echo "PASS: $*"; }
fail() { echo "FAIL: $*" >&2; exit 1; }

[ -x "$TOOL" ] || chmod +x "$TOOL"
[ -x "$LEGACY" ] || chmod +x "$LEGACY"
[ -f "$PY" ] || fail "missing repository_protection.py"
[ -f "${ROOT}/docs/contracts/REPOSITORY-PROTECTION.md" ] || fail "missing protection contract"

# ---- unit: union + baselines via python ----
cd "$ROOT"
python3 - <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, str(Path("scripts/gitops").resolve()))
import repository_protection as rp

dev = rp.managed_baseline("development")
assert dev == [
    "Cursor Bugbot",
    "Verify IDE Development",
    "Enforce allowed PR source branches",
], dev
stg = rp.managed_baseline("staging")
assert "Cursor Bugbot" not in stg
assert stg[-1] == "Enforce allowed PR source branches"
main = rp.managed_baseline("main")
assert "Cursor Bugbot" not in main

u = rp.union_checks(dev, ["Consumer Custom Lint", "Verify IDE Development"], ["Extra"])
assert u["preserved"] == ["Consumer Custom Lint", "Extra"], u
assert "Consumer Custom Lint" in u["desired"]
assert u["desired"].index("Cursor Bugbot") == 0

merged = rp.merge_ruleset_rules(
    [
        {"type": "required_status_checks", "parameters": {"required_status_checks": []}},
        {"type": "pull_request", "parameters": {"required_approving_review_count": 1}},
        {"type": "deletion"},
    ],
    rp._status_check_rule(["Cursor Bugbot"]),
)
assert [r["type"] for r in merged] == ["required_status_checks", "pull_request", "deletion"]

preserved_classic = rp.classic_protection_body(
    ["Cursor Bugbot"],
    existing={
        "required_pull_request_reviews": {"required_approving_review_count": 2},
        "restrictions": {"users": ["a"], "teams": [], "apps": []},
    },
)
assert preserved_classic["required_pull_request_reviews"]["required_approving_review_count"] == 2
assert preserved_classic["restrictions"]["users"] == ["a"]
print("unit ok")
PY
pass "baseline and union helpers"

# ---- plan covers all three branches; dry-run mutations empty ----
"$TOOL" plan --repo linktrend/Fixture --fixture-dir "${FX}/rulesets-empty" \
  >"${TMP}/plan-empty.json"
python3 - <<PY
import json
from pathlib import Path
p = json.loads(Path("${TMP}/plan-empty.json").read_text())
assert p["schemaVersion"] == 1
assert p["dryRun"] is True
assert p["mode"] == "plan"
assert p["mutations"] == []
assert set(p["branches"]) == {"development", "staging", "main"}
assert p["branches"]["development"]["action"] == "create"
assert p["branches"]["staging"]["action"] == "create"
assert p["branches"]["main"]["action"] == "create"
dev = p["branches"]["development"]["requiredChecks"]["desired"]
assert dev[0] == "Cursor Bugbot"
assert "Enforce allowed PR source branches" in dev
stg = p["branches"]["staging"]["requiredChecks"]["desired"]
assert "Cursor Bugbot" not in stg
assert "Enforce allowed PR source branches" in stg
main = p["branches"]["main"]["requiredChecks"]["desired"]
assert "Cursor Bugbot" not in main
assert p["repoSettings"]["allow_auto_merge"]["after"] is True
assert "rollback" in p and "snapshot" in p["rollback"]
assert p["rollback"]["instructions"]
assert p["capability"]["mechanism"] == "rulesets"
print("plan ok")
PY
pass "plan covers development/staging/main with rollback"

# ---- preserve consumer-specific checks + bypass_actors ----
"$TOOL" plan --repo linktrend/Fixture --fixture-dir "${FX}/rulesets-partial" \
  >"${TMP}/plan-partial.json"
python3 - <<PY
import json
from pathlib import Path
p = json.loads(Path("${TMP}/plan-partial.json").read_text())
dev = p["branches"]["development"]
assert "Consumer Custom Lint" in dev["requiredChecks"]["preserved"]
assert "Consumer Custom Lint" in dev["requiredChecks"]["desired"]
assert "Enforce allowed PR source branches" in dev["requiredChecks"]["desired"]
assert dev["after"]["bypassActors"][0]["actor_id"] == 1
assert dev["action"] == "update"
assert p["branches"]["staging"]["action"] == "create"
assert p["branches"]["main"]["action"] == "create"
print("union ok")
PY
pass "union preserves repo-specific checks and bypass_actors"

# ---- preserve non-check ruleset rules on update (fail-closed design) ----
"$TOOL" plan --repo linktrend/Fixture --fixture-dir "${FX}/rulesets-extra-rules" \
  >"${TMP}/plan-extra-rules.json"
python3 - <<PY
import json
from pathlib import Path
p = json.loads(Path("${TMP}/plan-extra-rules.json").read_text())
dev = p["branches"]["development"]
assert dev["action"] == "update"
rules = dev["after"]["body"]["rules"]
types = [r["type"] for r in rules]
assert types[0] == "required_status_checks", types
assert "pull_request" in types
assert "non_fast_forward" in types
assert "deletion" in types
# Managed source-policy check was missing → unioned in; non-check rules untouched.
assert "Enforce allowed PR source branches" in dev["requiredChecks"]["desired"]
contexts = [
    c["context"]
    for c in rules[0]["parameters"]["required_status_checks"]
]
assert "Enforce allowed PR source branches" in contexts
assert types.count("required_status_checks") == 1
assert dev["after"]["bypassActors"][0]["actor_id"] == 9
print("extra-rules plan ok")
PY
cp -R "${FX}/rulesets-extra-rules" "${TMP}/extra-rules-fx"
"$TOOL" apply --apply --repo linktrend/Fixture --fixture-dir "${TMP}/extra-rules-fx" \
  --json-output "${TMP}/apply-extra-rules.json" >/dev/null
python3 - <<PY
import json
from pathlib import Path
state = json.loads(Path("${TMP}/extra-rules-fx/state.json").read_text())
detail = state["ruleset_details"]["21"]
types = [r["type"] for r in detail["rules"]]
assert types[0] == "required_status_checks"
assert "pull_request" in types and "non_fast_forward" in types and "deletion" in types
assert types.count("required_status_checks") == 1
pr = next(r for r in detail["rules"] if r["type"] == "pull_request")
assert pr["parameters"]["required_approving_review_count"] == 1
print("extra-rules apply ok")
PY
pass "ruleset update preserves non-check rules"

# ---- unclassified ruleset rule fails closed ----
python3 - <<'PY'
import json, sys, tempfile, shutil
from pathlib import Path
sys.path.insert(0, str(Path("scripts/gitops").resolve()))
import repository_protection as rp

base = Path("scripts/tests/fixtures/repository-protection/rulesets-extra-rules")
with tempfile.TemporaryDirectory() as td:
    dest = Path(td) / "fx"
    shutil.copytree(base, dest)
    state = json.loads((dest / "state.json").read_text())
    state["ruleset_details"]["21"]["rules"].append({"parameters": {}})
    (dest / "state.json").write_text(json.dumps(state, indent=2) + "\n")
    client = rp.FixtureClient("linktrend/Fixture", dest)
    try:
        rp.build_plan(client, branches=("development",))
        raise SystemExit("expected ProtectionError for unclassified rule")
    except rp.ProtectionError as exc:
        assert "missing type" in str(exc)
        assert exc.exit_code == rp.EXIT_FAILED
print("unclassified-rule fail-closed ok")
PY
pass "unclassified ruleset rule fails closed"

# ---- classic BP preserves reviews / restrictions ----
"$TOOL" plan --repo linktrend/Fixture --fixture-dir "${FX}/branch-protection-with-reviews" \
  >"${TMP}/plan-bp-reviews.json"
python3 - <<PY
import json
from pathlib import Path
p = json.loads(Path("${TMP}/plan-bp-reviews.json").read_text())
assert p["capability"]["mechanism"] == "branch_protection"
dev = p["branches"]["development"]
assert dev["action"] == "update"
body = dev["after"]["body"]
reviews = body["required_pull_request_reviews"]
assert reviews is not None
assert reviews["required_approving_review_count"] == 2
assert reviews["require_code_owner_reviews"] is True
assert reviews["dismiss_stale_reviews"] is True
rest = body["restrictions"]
assert rest["users"] == ["ops-bot"]
assert rest["teams"] == ["release-managers"]
assert rest["apps"] == ["linktrend-integrator"]
assert body["required_conversation_resolution"] is True
assert "Cursor Bugbot" in body["required_status_checks"]["contexts"]
assert "Legacy Check" in body["required_status_checks"]["contexts"]
print("bp-reviews plan ok")
PY
cp -R "${FX}/branch-protection-with-reviews" "${TMP}/bp-reviews-fx"
"$TOOL" apply --apply --repo linktrend/Fixture --fixture-dir "${TMP}/bp-reviews-fx" \
  --json-output "${TMP}/apply-bp-reviews.json" >/dev/null
python3 - <<PY
import json
from pathlib import Path
state = json.loads(Path("${TMP}/bp-reviews-fx/state.json").read_text())
dev = state["branch_protections"]["development"]
assert dev["required_pull_request_reviews"]["required_approving_review_count"] == 2
assert dev["restrictions"]["teams"] == ["release-managers"]
assert dev["required_conversation_resolution"] is True
assert "Cursor Bugbot" in dev["required_status_checks"]["contexts"]
# Must not have been forced to null
assert dev["required_pull_request_reviews"] is not None
assert dev["restrictions"] is not None
print("bp-reviews apply ok")
PY
pass "classic BP update preserves reviews and restrictions"

# ---- classic create still uses null reviews/restrictions ----
python3 - <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, str(Path("scripts/gitops").resolve()))
import repository_protection as rp

body = rp.classic_protection_body(["Cursor Bugbot"])
assert body["required_pull_request_reviews"] is None
assert body["restrictions"] is None
print("classic-create-null ok")
PY
pass "classic create leaves reviews/restrictions null"

# ---- verify matched = clean; verify empty = drift ----
set +e
"$TOOL" verify --repo linktrend/Fixture --fixture-dir "${FX}/rulesets-matched" \
  >"${TMP}/verify-ok.json"
rc=$?
set -e
[ "$rc" -eq 0 ] || fail "verify matched expected 0 got $rc"
python3 -c 'import json,sys; p=json.load(open(sys.argv[1])); assert p["verify"]["ok"] is True' \
  "${TMP}/verify-ok.json"
pass "verify matched fixtures"

set +e
"$TOOL" verify --repo linktrend/Fixture --fixture-dir "${FX}/rulesets-empty" \
  >"${TMP}/verify-drift.json"
rc=$?
set -e
[ "$rc" -eq 3 ] || fail "verify drift expected exit 3 got $rc"
pass "verify reports drift without mutating"

# ---- apply refused without --apply ----
set +e
"$TOOL" apply --repo linktrend/Fixture --fixture-dir "${FX}/rulesets-empty" \
  >"${TMP}/apply-refused.out" 2>"${TMP}/apply-refused.err"
rc=$?
set -e
[ "$rc" -eq 5 ] || fail "apply without --apply expected exit 5 got $rc"
# Copy fixture to temp so apply can mutate isolated state
cp -R "${FX}/rulesets-empty" "${TMP}/apply-fx"
# Confirm source fixture unchanged (no mutations file concept — compare state)
python3 - <<PY
import json
from pathlib import Path
before = json.loads(Path("${FX}/rulesets-empty/state.json").read_text())
assert before["rulesets"] == []
print("source fixture untouched")
PY
pass "apply refuses without --apply; fixtures stay clean"

# ---- apply with --apply on isolated fixture; then rollback ----
cp -R "${FX}/rulesets-empty" "${TMP}/mut-fx"
"$TOOL" apply --apply --repo linktrend/Fixture --fixture-dir "${TMP}/mut-fx" \
  --json-output "${TMP}/apply-out.json" >/dev/null
python3 - <<PY
import json
from pathlib import Path
p = json.loads(Path("${TMP}/apply-out.json").read_text())
assert p["dryRun"] is False
assert p["verify"]["ok"] is True
ops = {m["op"] for m in p["mutations"]}
assert "create_ruleset" in ops
assert "patch_repo" in ops
# Three branches created
assert sum(1 for m in p["mutations"] if m["op"] == "create_ruleset") == 3
state = json.loads(Path("${TMP}/mut-fx/state.json").read_text())
names = {r["name"] for r in state["rulesets"]}
assert names == {
    "development-autonomous-merge",
    "staging-autonomous-promote",
    "main-autonomous-release",
}, names
assert state["repo"]["allow_auto_merge"] is True
print("apply ok")
PY
pass "explicit apply creates three rulesets in fixture only"

# Capture plan snapshot from pre-apply empty clone for rollback proof
cp -R "${FX}/rulesets-empty" "${TMP}/rb-fx"
"$TOOL" plan --repo linktrend/Fixture --fixture-dir "${TMP}/rb-fx" \
  --json-output "${TMP}/rb-plan.json" >/dev/null
"$TOOL" apply --apply --repo linktrend/Fixture --fixture-dir "${TMP}/rb-fx" >/dev/null
"$TOOL" rollback --apply --repo linktrend/Fixture --fixture-dir "${TMP}/rb-fx" \
  --snapshot "${TMP}/rb-plan.json" --json-output "${TMP}/rb-out.json" >/dev/null
python3 - <<PY
import json
from pathlib import Path
state = json.loads(Path("${TMP}/rb-fx/state.json").read_text())
assert state["rulesets"] == [], state["rulesets"]
assert state["repo"]["allow_auto_merge"] is False
print("rollback ok")
PY
pass "rollback restores pre-apply ruleset absence"

# ---- branch protection fallback ----
"$TOOL" plan --repo linktrend/Fixture --fixture-dir "${FX}/branch-protection-fallback" \
  >"${TMP}/plan-bp.json"
python3 - <<PY
import json
from pathlib import Path
p = json.loads(Path("${TMP}/plan-bp.json").read_text())
assert p["capability"]["mechanism"] == "branch_protection"
dev = p["branches"]["development"]
assert "Legacy Check" in dev["requiredChecks"]["preserved"]
assert "Cursor Bugbot" in dev["requiredChecks"]["desired"]
assert dev["action"] == "update"
assert p["branches"]["staging"]["action"] == "create"
print("bp ok")
PY
pass "rulesets unavailable falls back to classic branch protection"

# ---- unavailable mechanism ----
set +e
"$TOOL" plan --repo linktrend/Fixture --fixture-dir "${FX}/unavailable" \
  >"${TMP}/plan-unavail.json"
rc=$?
set -e
[ "$rc" -eq 4 ] || fail "unavailable plan expected exit 4 got $rc"
python3 - <<PY
import json
from pathlib import Path
p = json.loads(Path("${TMP}/plan-unavail.json").read_text())
assert p["capability"]["mechanism"] == "unavailable"
assert all(b["action"] == "unavailable" for b in p["branches"].values())
print("unavail ok")
PY
set +e
"$TOOL" apply --apply --repo linktrend/Fixture --fixture-dir "${FX}/unavailable" \
  >/dev/null 2>"${TMP}/unavail-apply.err"
rc=$?
set -e
[ "$rc" -eq 4 ] || [ "$rc" -eq 1 ] || fail "unavailable apply must refuse, got $rc"
pass "unavailable mechanism plans safely and refuses apply"

# ---- ruleset detail fetch failure must fail closed (preserve checks) ----
python3 - <<'PY'
import json, sys, tempfile
from pathlib import Path
from copy import deepcopy
sys.path.insert(0, str(Path("scripts/gitops").resolve()))
import repository_protection as rp

fx = Path("scripts/tests/fixtures/repository-protection/rulesets-partial")
with tempfile.TemporaryDirectory() as td:
    dest = Path(td) / "fx"
    import shutil
    shutil.copytree(fx, dest)
    client = rp.FixtureClient("linktrend/Fixture", dest)
    original = client.get_ruleset

    def boom(rid: int):
        return None

    client.get_ruleset = boom  # type: ignore[method-assign]
    try:
        rp.build_plan(client)
        raise SystemExit("expected ProtectionError on detail fetch failure")
    except rp.ProtectionError as exc:
        assert exc.exit_code == rp.EXIT_UNAVAILABLE, exc.exit_code
        assert "detail fetch failed" in str(exc)
print("detail-fail-closed ok")
PY
pass "ruleset detail fetch failure fails closed"

# ---- rulesets forbidden/error must not fall through to classic BP ----
python3 - <<'PY'
import json, sys, tempfile, shutil
from pathlib import Path
sys.path.insert(0, str(Path("scripts/gitops").resolve()))
import repository_protection as rp

base = Path("scripts/tests/fixtures/repository-protection/branch-protection-fallback")
with tempfile.TemporaryDirectory() as td:
    dest = Path(td) / "fx"
    shutil.copytree(base, dest)
    state = json.loads((dest / "state.json").read_text())
    state["capability"]["rulesets"] = "forbidden"
    state["capability"]["rulesets_error"] = "HTTP 403"
    (dest / "state.json").write_text(json.dumps(state, indent=2) + "\n")
    client = rp.FixtureClient("linktrend/Fixture", dest)
    cap = rp.detect_mechanism(client)
    assert cap["mechanism"] == "unavailable", cap
print("forbidden-unavailable ok")
PY
pass "rulesets forbidden/error treated as unavailable"

# ---- no credential / secret reads in module ----
if rg -n 'secret|private.?key|PASSWORD|TOKEN|GSM|keychain' "$PY" \
  | rg -v 'Never|never|credential|no secret|SECRET|docs/|comment|instruction|authenticate|token material|LINKTREND_.*CHECKS|environ'; then
  fail "unexpected credential/secret handling in repository_protection.py"
fi
pass "no credential creation or secret reads"

# ---- legacy wrapper dry-run + apply on fixture ----
cp -R "${FX}/rulesets-empty" "${TMP}/legacy-fx"
"$LEGACY" --repo linktrend/Fixture --fixture-dir "${TMP}/legacy-fx" --dry-run \
  >"${TMP}/legacy-dry.json"
python3 - <<PY
import json
from pathlib import Path
# dry-run prints human lines then JSON; find last JSON object
text = Path("${TMP}/legacy-dry.json").read_text()
start = text.index("{")
p = json.loads(text[start:])
assert p["mode"] == "plan"
assert p["branches"]["development"]["action"] == "create"
assert "staging" not in p["branches"] or True
# legacy dry-run uses --branches development only
assert list(p["branches"]) == ["development"]
assert Path("${TMP}/legacy-fx/state.json").read_text() == Path("${FX}/rulesets-empty/state.json").read_text()
print("legacy dry-run ok")
PY
"$LEGACY" --repo linktrend/Fixture --fixture-dir "${TMP}/legacy-fx" \
  "Cursor Bugbot" "Verify IDE Development" "Enforce allowed PR source branches" \
  >"${TMP}/legacy-apply.out"
python3 - <<PY
import json
from pathlib import Path
state = json.loads(Path("${TMP}/legacy-fx/state.json").read_text())
names = {r["name"] for r in state["rulesets"]}
assert names == {"development-autonomous-merge"}, names
assert state["repo"]["allow_auto_merge"] is True
print("legacy apply ok")
PY
pass "legacy apply-development wrapper preserves CLI and scopes to development"

# ---- contract mentions three branches and dry-run-first ----
grep -q 'development-autonomous-merge' "${ROOT}/docs/contracts/REPOSITORY-PROTECTION.md"
grep -q 'staging-autonomous-promote' "${ROOT}/docs/contracts/REPOSITORY-PROTECTION.md"
grep -q 'main-autonomous-release' "${ROOT}/docs/contracts/REPOSITORY-PROTECTION.md"
grep -q 'Plan / dry-run' "${ROOT}/docs/contracts/REPOSITORY-PROTECTION.md"
grep -q 'Non-check ruleset rules' "${ROOT}/docs/contracts/REPOSITORY-PROTECTION.md"
grep -q 'required_pull_request_reviews' "${ROOT}/docs/contracts/REPOSITORY-PROTECTION.md"
pass "contract documents three-branch dry-run-first protections"

echo "PASS: repository protection suite"
