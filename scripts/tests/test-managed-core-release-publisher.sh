#!/usr/bin/env bash
# Static + adversarial proofs for App-backed managed-core release publisher (WP-01B).
# Does not mint tokens, create tags, or mutate GitHub.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

FIX="$ROOT/scripts/tests/fixtures/managed-core-release-publisher"
WF=".github/workflows/linktrend-managed-core-release-publisher.yml"
DISPATCH="scripts/gitops/managed_core_release_dispatch.py"
PUBLISH="scripts/gitops/managed_core_release_publish.py"
NEG_WF="$FIX/workflow/adversarial-untrusted-source.yml"
PATTERNS="$FIX/workflow/required-trust-patterns.txt"
CONTRACT="$FIX/contract.json"

fail() { echo "FAIL: $1" >&2; exit 1; }
pass() { echo "PASS: $1"; }

[ -f "$CONTRACT" ] || fail "missing fixture contract: $CONTRACT"
[ -f "$NEG_WF" ] || fail "missing adversarial workflow fixture: $NEG_WF"
[ -f "$PATTERNS" ] || fail "missing trust patterns: $PATTERNS"
[ -f "$WF" ] || fail "missing production workflow: $WF"
[ -f "$DISPATCH" ] || fail "missing dispatch validator: $DISPATCH"
[ -f "$PUBLISH" ] || fail "missing publish helper: $PUBLISH"
[ -f "core/managed-core/schemas/managed-core-release.schema.json" ] || fail "missing release schema"

# ---- 1) Negative fixture encodes forbidden trust failures ----
python3 - <<'PY' "$NEG_WF"
import re, sys
from pathlib import Path
text = Path(sys.argv[1]).read_text(encoding="utf-8")
checks = [
    ("untrusted PR head checkout", r"pull_request\.head\.sha"),
    ("persist-credentials true", r"persist-credentials:\s*true"),
    ("human Bugbot user token", r"LINKTREND_BUGBOT_USER_TOKEN"),
    ("github.token mutation path", r"github\.token"),
    ("private key leaked into consumer env", r"LINKTREND_GITOPS_APP_PRIVATE_KEY"),
    ("personal PAT fallback", r"ghp_"),
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
if "fee1f7d63c2ff003460e3d139729b119787bc349" not in prod:
    raise SystemExit("mint action pin missing/wrong")

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
    "github_pat_",
    "ghp_",
):
    if banned in prod:
        raise SystemExit(f"human/PAT credential fallback present: {banned}")

# github.token must not authorize tag/release publication.
blocks = re.split(r"\n(?=      - name:)", prod)
for block in blocks:
    uses_github_token = bool(
        re.search(r"(GH_TOKEN|GITHUB_TOKEN):\s*\$\{\{\s*github\.token", block)
    )
    if uses_github_token:
        raise SystemExit("github.token wired as mutation credential")

if "sync-managed-workflows.sh" in prod and "Not synced" not in prod.split("\n", 20).__repr__():
    pass  # header comment covers system-only; enforced below via sync list check

print("ok")
PY
pass "Production workflow enforces trusted default-branch + App-only mint"

# ---- 3) Must not be consumer-synced ----
if grep -q 'linktrend-managed-core-release-publisher.yml' scripts/sync-managed-workflows.sh; then
  fail "release publisher must not be in consumer managed workflow sync list"
fi
pass "Release publisher excluded from consumer workflow sync"

# ---- 4) Dispatch self-test + fixture cases ----
python3 "$DISPATCH" self-test >/dev/null
pass "Dispatch validator self-test"

python3 - <<'PY' "$DISPATCH" "$FIX/cases/dispatch-cases.json"
import json, subprocess, sys
from pathlib import Path

dispatch = Path(sys.argv[1])
cases = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))["cases"]
for case in cases:
    cmd = [
        sys.executable,
        str(dispatch),
        "validate",
        "--source-sha", case["source_sha"],
        "--version", case["version"],
        "--tag", case["tag"],
        "--action", case["action"],
        "--dry-run", "true" if case["dry_run"] else "false",
        "--github-repository", "linktrend/IDE-Development",
        "--default-branch", case["default_branch"],
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    payload = json.loads(proc.stdout or "{}")
    expect = case["expect"]
    if expect == "ok":
        if proc.returncode != 0 or not payload.get("ok"):
            raise SystemExit(f"case {case['id']}: expected ok, got {payload}")
    else:
        if proc.returncode == 0 or payload.get("error") != expect:
            raise SystemExit(
                f"case {case['id']}: expected error {expect}, got rc={proc.returncode} {payload}"
            )
print("ok")
PY
pass "Dispatch fixture cases"

# ---- 5) Publish helper unit tests (conflict/replay/token) ----
python3 "$ROOT/scripts/tests/test_managed_core_release_publish.py"
pass "Publish helper conflict/replay/token unit tests"

# ---- 6) Schema present and loadable ----
python3 - <<'PY'
import json
from pathlib import Path
schema = json.loads(Path("core/managed-core/schemas/managed-core-release.schema.json").read_text())
assert schema["properties"]["kind"]["const"] == "ide-development-managed-core-release"
assert "locator" in schema["required"]
print("ok")
PY
pass "Release evidence schema loads"

echo "ALL PASS: managed-core release publisher contract"
