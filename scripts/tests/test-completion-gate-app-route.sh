#!/usr/bin/env bash
# Narrow tests for App-only privileged Review Ready publish + gate diagnostics.
# Does not mutate live GitHub; uses file backend + mocked github backend token rules.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/cg-app-route.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

pass() { echo "PASS: $*"; }
fail() { echo "FAIL: $*" >&2; exit 1; }

# ---------------------------------------------------------------------------
# 1) readiness_status: ambient GH/GITHUB tokens never authorize publish
# ---------------------------------------------------------------------------
python3 - "$ROOT" "$TMP" <<'PY'
import json, os, sys, tempfile
from pathlib import Path
from unittest import mock

root = Path(sys.argv[1])
tmp = Path(sys.argv[2])
sys.path.insert(0, str(root / "scripts" / "gitops"))
import readiness_status as rs

# Clear App tokens; leave ambient human/workflow tokens.
for k in ("AUTOMATION_TOKEN", "LINKTREND_APP_TOKEN"):
    os.environ.pop(k, None)
os.environ["GH_TOKEN"] = "ghs_FAKE_HUMAN_MUST_NOT_PUBLISH"
os.environ["GITHUB_TOKEN"] = "ghs_FAKE_WORKFLOW_MUST_NOT_PUBLISH"
os.environ["GITHUB_REPOSITORY"] = "linktrend/IDE-Development"
os.environ.pop("LINKTREND_STATUS_BACKEND", None)
os.environ.pop("LINKTREND_STATUS_DIR", None)

assert rs.resolve_app_publish_token() == ""
assert "ghs_FAKE_HUMAN_MUST_NOT_PUBLISH" in rs._gh_token()  # reads may use ambient
route = rs.app_backed_review_ready_route(
    branch="issue/44-add-app-backed-review-ready-publisher-and-produc",
    sha="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
)
assert route.startswith("gh workflow run linktrend-review-ready-publisher.yml ")
assert "-f branch=issue/44-add-app-backed-review-ready-publisher-and-produc" in route
assert "-f sha=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" in route
assert "-f dry_run=false" in route

posted = []

def fake_api(method, url, token, body=None):
    posted.append({"method": method, "url": url, "token": token, "body": body})
    if method == "GET":
        return []
    return {}

with mock.patch.object(rs, "_api", side_effect=fake_api):
    backend = rs.GitHubStatusBackend(repo="linktrend/IDE-Development")
    try:
        backend.post(
            "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "success",
            "issue=44",
            branch="issue/44-add-app-backed-review-ready-publisher-and-produc",
        )
        raise SystemExit("expected publish to fail closed without App token")
    except RuntimeError as exc:
        msg = str(exc)
        assert "privileged_publish_requires_github_app" in msg, msg
        assert "no GH_TOKEN/GITHUB_TOKEN fallback" in msg, msg
        assert "linktrend-review-ready-publisher.yml" in msg, msg
        assert "issue/44-add-app-backed-review-ready-publisher-and-produc" in msg, msg

assert posted == [], f"no API publish calls allowed, got {posted}"

# App token present → publish uses App token only (not ambient).
os.environ["AUTOMATION_TOKEN"] = "ghs_APP_PUBLISH_TOKEN_ONLY"
posted.clear()
with mock.patch.object(rs, "_api", side_effect=fake_api):
    st = rs.publish_review_ready(
        "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        "44",
        "gate-test",
        branch="issue/44-x",
    )
assert st.state == "success"
assert any(p["method"] == "POST" for p in posted), posted
for p in posted:
    if p["method"] == "POST":
        assert p["token"] == "ghs_APP_PUBLISH_TOKEN_ONLY", p
        assert p["token"] != "ghs_FAKE_HUMAN_MUST_NOT_PUBLISH"
        assert p["token"] != "ghs_FAKE_WORKFLOW_MUST_NOT_PUBLISH"
        assert p["body"]["context"] == "Linktrend Review Ready"
        assert p["body"]["state"] == "success"

# File backend still publishes without App token (local/unit path).
os.environ.pop("AUTOMATION_TOKEN", None)
os.environ["LINKTREND_STATUS_BACKEND"] = "file"
os.environ["LINKTREND_STATUS_DIR"] = str(tmp / "status")
sha = "cccccccccccccccccccccccccccccccccccccccc"
rs.mark_sha(sha, "44", "file-backend")
ok, detail = rs.is_sha_review_ready(sha)
assert ok, detail
print("readiness_status app-only publish ok")
PY
pass "readiness_status rejects human/GITHUB_TOKEN publish; App route diagnostic exact"

# ---------------------------------------------------------------------------
# 2) completion_gate review-ready: github backend without App → fail + route
# ---------------------------------------------------------------------------
python3 - "$ROOT" "$TMP" <<'PY'
import json, os, subprocess, sys, tempfile
from pathlib import Path

root = Path(sys.argv[1])
tmp = Path(sys.argv[2])

# Tiny git worktree with allowed branch + evidence + origin tip match.
repo = tmp / "repo"
repo.mkdir()
subprocess.check_call(["git", "init", "-q", "-b", "issue/44-app-route-diag"], cwd=repo)
subprocess.check_call(["git", "config", "user.email", "t@example.com"], cwd=repo)
subprocess.check_call(["git", "config", "user.name", "t"], cwd=repo)
subprocess.check_call(["git", "commit", "-q", "--allow-empty", "-m", "tip"], cwd=repo)
# Keep .linktrend/ out of porcelain status (matches production gitignore).
exclude = repo / ".git" / "info" / "exclude"
exclude.parent.mkdir(parents=True, exist_ok=True)
exclude.write_text(exclude.read_text(encoding="utf-8") + "\n.linktrend/\n" if exclude.is_file() else ".linktrend/\n", encoding="utf-8")
# File-backend-style origin tip without network: set remote + remote-tracking ref.
subprocess.check_call(["git", "remote", "add", "origin", str(repo)], cwd=repo)
sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
branch = subprocess.check_output(
    ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo, text=True
).strip()
subprocess.check_call(["git", "update-ref", f"refs/remotes/origin/{branch}", sha], cwd=repo)

ev = repo / ".linktrend" / "completion-evidence.json"
ev.parent.mkdir(parents=True, exist_ok=True)
ev.write_text(
    json.dumps(
        {
            "schemaVersion": 1,
            "headSha": sha,
            "classification": "tests",
            "acceptance": "app-route diagnostic proof",
            "commands": [{"cmd": "true", "exitCode": 0}],
        }
    )
    + "\n",
    encoding="utf-8",
)

env = os.environ.copy()
# Force GitHub backend; strip App tokens; leave ambient tokens that must not publish.
env.pop("AUTOMATION_TOKEN", None)
env.pop("LINKTREND_APP_TOKEN", None)
env["GITHUB_TOKEN"] = "ghs_FAKE_AMBIENT"
env["GH_TOKEN"] = "ghs_FAKE_AMBIENT"
env["GITHUB_REPOSITORY"] = "linktrend/IDE-Development"
env["LINKTREND_STATUS_BACKEND"] = "github"
env.pop("LINKTREND_STATUS_DIR", None)

# Avoid real network: patch via PYTHONPATH helper is heavy; instead unit-check
# publish_ready diagnostic by importing gate with mocked readiness mark.
sys.path.insert(0, str(root / "scripts" / "gitops"))
import completion_gate as cg
import readiness_status as rs

# Direct helper: missing App token message includes route for this branch/sha.
err = rs.missing_app_publish_token_error(branch=branch, sha=sha)
assert "privileged_publish_requires_github_app" in err
assert "linktrend-review-ready-publisher.yml" in err
assert branch in err and sha in err

# completion_gate.publish_ready surfaces the error (mocked mark_sha).
class Boom(Exception):
    pass

def boom_mark(*a, **k):
    raise RuntimeError(rs.missing_app_publish_token_error(branch=branch, sha=sha))

orig = rs.mark_sha
rs.mark_sha = boom_mark  # type: ignore
try:
    ok, detail = cg.publish_ready(sha, "44", "notes", branch=branch)
finally:
    rs.mark_sha = orig  # type: ignore
assert ok is False
assert "privileged_publish_requires_github_app" in detail
assert "linktrend-review-ready-publisher.yml" in detail
assert cg.app_backed_route(branch, sha) in detail or "gh workflow run" in detail

# Full CLI path with file backend still succeeds (no App token needed offline).
env_file = env.copy()
env_file["LINKTREND_STATUS_BACKEND"] = "file"
env_file["LINKTREND_STATUS_DIR"] = str(tmp / "cli-status")
r = subprocess.run(
    [
        sys.executable,
        str(root / "scripts/gitops/completion_gate.py"),
        "review-ready",
        "--workdir",
        str(repo),
        "--evidence-file",
        str(ev),
    ],
    capture_output=True,
    text=True,
    env=env_file,
)
assert r.returncode == 0, r.stdout + r.stderr
payload = json.loads(r.stdout)
assert payload.get("published") is True
assert payload.get("state") == "review_ready"

# CLI github-backend path: mock by monkeypatching via env LINKTREND_STATUS_BACKEND
# already covered above; simulate failed publish payload fields via gate function.
from argparse import Namespace
# Use file backend but force publish_ready failure through temporary patch.
os.environ["LINKTREND_STATUS_BACKEND"] = "file"
os.environ["LINKTREND_STATUS_DIR"] = str(tmp / "cli-status-2")

def fail_publish(sha_, issue_id, notes, *, branch=""):
    return False, rs.missing_app_publish_token_error(branch=branch, sha=sha_)

orig_pub = cg.publish_ready
cg.publish_ready = fail_publish  # type: ignore
try:
    args = Namespace(
        workdir=str(repo),
        evidence_file=str(ev),
        issue_id="44",
        notes="diag",
        tests_ok=False,
    )
    import io
    from contextlib import redirect_stdout
    buf = io.StringIO()
    with redirect_stdout(buf):
        code = cg.cmd_review_ready(args)
    out = buf.getvalue()
finally:
    cg.publish_ready = orig_pub  # type: ignore
assert code == cg.EXIT_FAILED
payload = json.loads(out)
assert payload.get("published") is False
assert payload.get("appBackedRoute")
assert "linktrend-review-ready-publisher.yml" in payload["appBackedRoute"]
assert "privileged_publish_requires_github_app" in payload.get("error", "")
print("completion_gate diagnostics ok")
PY
pass "completion_gate fail-closed diagnostics include exact App-backed route"

# ---------------------------------------------------------------------------
# 3) Static: no ambient publish fallback in readiness_status source
# ---------------------------------------------------------------------------
python3 - "$ROOT" <<'PY'
from pathlib import Path
import sys
src = Path(sys.argv[1], "scripts/gitops/readiness_status.py").read_text(encoding="utf-8")
start = src.index("def resolve_app_publish_token")
end = src.index("\ndef ", start + 1)
body = src[start:end]
assert 'os.environ.get("GH_TOKEN")' not in body
assert "os.environ.get('GH_TOKEN')" not in body
assert 'os.environ.get("GITHUB_TOKEN")' not in body
assert "os.environ.get('GITHUB_TOKEN')" not in body
assert "AUTOMATION_TOKEN" in body or "APP_PUBLISH_TOKEN_ENVS" in body
assert "resolve_app_publish_token()" in src
assert "missing_app_publish_token_error" in src
assert "linktrend-review-ready-publisher.yml" in src
# post must not authorize via self.token / ambient for publish
post_start = src.index("def post(")
# GitHubStatusBackend.post is the first post with branch kw after class GitHubStatusBackend
gh_start = src.index("class GitHubStatusBackend")
post_start = src.index("def post(", gh_start)
post_end = src.index("\n    def ", post_start + 1) if "\n    def " in src[post_start + 1 : post_start + 800] else src.index("\ndef get_backend", post_start)
# simpler: slice until next top-level def get_backend
post_end = src.index("\ndef get_backend", gh_start)
post_body = src[post_start:post_end]
assert "resolve_app_publish_token()" in post_body
assert "missing_app_publish_token_error" in post_body
print("static no-fallback ok")
PY
pass "static: App publish token resolver has no human/GITHUB_TOKEN fallback"

echo "ALL PASS: completion-gate app-route diagnostics"
