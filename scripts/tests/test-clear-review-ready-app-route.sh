#!/usr/bin/env bash
# App-backed clear/rollback (withdraw) must never use GH_TOKEN/GITHUB_TOKEN.
# Local clear-review-ready fails closed with exact App workflow_dispatch route.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/clear-rr-app.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

pass() { echo "PASS: $*"; }
fail() { echo "FAIL: $*" >&2; exit 1; }

# ---------------------------------------------------------------------------
# 1) readiness_status withdraw: ambient tokens never authorize; route uses action=withdraw
# ---------------------------------------------------------------------------
python3 - "$ROOT" "$TMP" <<'PY'
import os
import sys
from pathlib import Path
from unittest import mock

root = Path(sys.argv[1])
sys.path.insert(0, str(root / "scripts" / "gitops"))
import readiness_status as rs

for k in ("AUTOMATION_TOKEN", "LINKTREND_APP_TOKEN"):
    os.environ.pop(k, None)
os.environ["GH_TOKEN"] = "ghs_FAKE_HUMAN_MUST_NOT_WITHDRAW"
os.environ["GITHUB_TOKEN"] = "ghs_FAKE_WORKFLOW_MUST_NOT_WITHDRAW"
os.environ["GITHUB_REPOSITORY"] = "linktrend/IDE-Development"
os.environ.pop("LINKTREND_STATUS_BACKEND", None)

branch = "issue/44-add-app-backed-review-ready-publisher-and-produc"
sha = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
reason = "bugbot-rollback-test"

route = rs.app_backed_review_ready_route(
    branch=branch, sha=sha, action="withdraw", reason=reason
)
assert "linktrend-review-ready-publisher.yml" in route
assert "-f action=withdraw" in route
assert f"-f branch={branch}" in route
assert f"-f sha={sha}" in route
assert f"-f reason={reason}" in route
assert "-f dry_run=false" in route

posted = []

def fake_api(method, url, token, body=None):
    posted.append({"method": method, "url": url, "token": token, "body": body})
    if method == "GET":
        return [{"context": rs.CONTEXT, "state": "success", "description": "issue=44"}]
    return {}

with mock.patch.object(rs, "_api", side_effect=fake_api):
    try:
        rs.withdraw_sha(sha, reason, branch=branch)
        raise SystemExit("expected withdraw to fail closed without App token")
    except RuntimeError as exc:
        msg = str(exc)
        assert "privileged_publish_requires_github_app" in msg or "privileged_withdraw_requires_github_app" in msg, msg
        assert "no GH_TOKEN/GITHUB_TOKEN fallback" in msg, msg
        assert "linktrend-review-ready-publisher.yml" in msg, msg
        assert "-f action=withdraw" in msg, msg
        assert branch in msg and sha in msg

assert posted == [], f"no API status writes allowed, got {posted}"

# App token present → withdraw posts failure with App token only.
os.environ["LINKTREND_APP_TOKEN"] = "ghs_APP_WITHDRAW_TOKEN_ONLY"
posted.clear()
with mock.patch.object(rs, "_api", side_effect=fake_api):
    st = rs.withdraw_sha(sha, reason, branch=branch)
assert st.state == "failure"
assert any(p["method"] == "POST" for p in posted), posted
for p in posted:
    if p["method"] == "POST":
        assert p["token"] == "ghs_APP_WITHDRAW_TOKEN_ONLY", p
        assert p["body"]["state"] == "failure"
        assert p["body"]["context"] == rs.CONTEXT
print("withdraw app-only ok")
PY
pass "readiness_status withdraw rejects human tokens; App withdraw route exact"

# ---------------------------------------------------------------------------
# 2) clear-review-ready.sh fails closed with App-backed withdraw route JSON
# ---------------------------------------------------------------------------
python3 - "$ROOT" "$TMP" <<'PY'
import json
import os
import subprocess
import sys
from pathlib import Path

root = Path(sys.argv[1])
tmp = Path(sys.argv[2])
repo = tmp / "repo"
repo.mkdir()
subprocess.check_call(["git", "init", "-q", "-b", "issue/44-clear-withdraw-route"], cwd=repo)
subprocess.check_call(["git", "config", "user.email", "t@example.com"], cwd=repo)
subprocess.check_call(["git", "config", "user.name", "t"], cwd=repo)
subprocess.check_call(["git", "commit", "-q", "--allow-empty", "-m", "tip"], cwd=repo)
sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
branch = subprocess.check_output(
    ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo, text=True
).strip()

# Install clear script + readiness_status into temp repo layout.
scripts = repo / "scripts"
gitops = scripts / "gitops"
gitops.mkdir(parents=True)
(scripts / "clear-review-ready.sh").write_text(
    (root / "scripts" / "clear-review-ready.sh").read_text(encoding="utf-8"),
    encoding="utf-8",
)
(gitops / "readiness_status.py").write_text(
    (root / "scripts" / "gitops" / "readiness_status.py").read_text(encoding="utf-8"),
    encoding="utf-8",
)
subprocess.check_call(["chmod", "+x", str(scripts / "clear-review-ready.sh")])

env = os.environ.copy()
env.pop("AUTOMATION_TOKEN", None)
env.pop("LINKTREND_APP_TOKEN", None)
env["GH_TOKEN"] = "ghs_FAKE_AMBIENT"
env["GITHUB_TOKEN"] = "ghs_FAKE_AMBIENT"
env["GITHUB_REPOSITORY"] = "linktrend/IDE-Development"
env["LINKTREND_STATUS_BACKEND"] = "github"
env.pop("LINKTREND_STATUS_DIR", None)

r = subprocess.run(
    ["bash", str(scripts / "clear-review-ready.sh"), sha, "rollback-test"],
    cwd=repo,
    capture_output=True,
    text=True,
    env=env,
)
assert r.returncode != 0, f"expected fail-closed, got rc=0 out={r.stdout} err={r.stderr}"
blob = (r.stdout or "") + (r.stderr or "")
assert "linktrend-review-ready-publisher.yml" in blob, blob
assert "-f action=withdraw" in blob, blob
assert branch in blob or f"-f branch={branch}" in blob, blob
assert sha in blob, blob
# Prefer machine-readable payload when present
for line in (r.stdout or "").splitlines():
    line = line.strip()
    if not line.startswith("{"):
        continue
    try:
        payload = json.loads(line)
    except json.JSONDecodeError:
        continue
    assert payload.get("ok") is False
    route = payload.get("appBackedRoute") or ""
    assert "-f action=withdraw" in route
    assert "linktrend-review-ready-publisher.yml" in route
    break
print("clear-review-ready fail-closed ok")
PY
pass "clear-review-ready.sh fails closed with App-backed withdraw route"

# ---------------------------------------------------------------------------
# 3) Static: workflow + docs bind withdraw to App route (not ambient gh token)
# ---------------------------------------------------------------------------
python3 - "$ROOT" <<'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1])
wf = (root / ".github/workflows/linktrend-review-ready-publisher.yml").read_text(encoding="utf-8")
managed = (root / "core/github/managed-workflows/linktrend-review-ready-publisher.yml").read_text(
    encoding="utf-8"
)
assert wf == managed, "live workflow must match managed template"
for text in (wf, managed):
    assert "action:" in text
    assert "withdraw" in text
    assert "withdraw_sha" in text or 'action == "withdraw"' in text or "action=withdraw" in text
    assert "refuse GITHUB_TOKEN" in text or "no human fallback" in text.lower()
    # must not teach GITHUB_TOKEN publish/withdraw fallback
    assert "LINKTREND_BUGBOT_USER_TOKEN" not in text

clear_src = (root / "scripts/clear-review-ready.sh").read_text(encoding="utf-8")
assert "GH_TOKEN" not in clear_src or "must not" in clear_src.lower() or "never" in clear_src.lower()
assert "readiness_status" in clear_src

docs = (root / "core/github/REVIEW-READY.md").read_text(encoding="utf-8")
assert "action=withdraw" in docs or "action: withdraw" in docs or "`withdraw`" in docs
assert "clear-review-ready" in docs
# Rollback must point at App-backed route, not imply ambient PAT works.
assert "App" in docs and ("workflow_dispatch" in docs or "linktrend-review-ready-publisher" in docs)
print("static withdraw binding ok")
PY
pass "workflow/docs bind clear/rollback withdraw to App-backed route"

echo "ALL PASS: clear-review-ready App-backed withdraw route"
