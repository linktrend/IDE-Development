#!/usr/bin/env bash
# Promote staging → main via temporary promote/main/* branch + PR.
# MODE=package|approve-merge|reevaluate
# approve-merge REQUIRES EXPECTED_STAGING_SHA and EXPECTED_PROMOTE_HEAD.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "FAIL: not a git repository" >&2
  exit 1
}
cd "$ROOT"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=work-branch-allowlist.sh
source "${SCRIPT_DIR}/work-branch-allowlist.sh"

MODE="${MODE:-package}"
RELEASE_GATE_CHECKS="${RELEASE_GATE_CHECKS:-Verify IDE Development}"
TIMEZONE_LABEL="${TIMEZONE_LABEL:-Asia/Taipei}"
EXPECTED_STAGING_SHA="${EXPECTED_STAGING_SHA:-}"
EXPECTED_PROMOTE_HEAD="${EXPECTED_PROMOTE_HEAD:-}"
REPO="${GH_REPO:-${GITHUB_REPOSITORY:-$(gh repo view --json nameWithOwner --jq .nameWithOwner)}}"

report() {
  local status="$1"
  local why="$2"
  {
    echo "## Main promote report"
    echo ""
    echo "- Mode: ${MODE}"
    echo "- Status: **${status}**"
    echo "- Reason: ${why}"
    echo "- staging: \`${STG_SHA:-unknown}\`"
    echo "- main: \`${MAIN_SHA:-unknown}\`"
    echo "- promote_branch: \`${PROMOTE_BRANCH:-none}\`"
    echo "- promote_head: \`${PROMOTE_HEAD:-none}\`"
  } | tee main-promote-report.md
  echo "MAIN_PROMOTE_STATUS=${status}"
}

conflict_upsert() {
  python3 "${SCRIPT_DIR}/conflict_task.py" upsert \
    --repo "${REPO}" \
    --stage main \
    --source-branch staging \
    --target-branch main \
    --source-sha "${STG_SHA}" \
    --target-sha "${MAIN_SHA}" \
    --promote-pr "${PROMOTE_PR:-}" \
    --status conflict_blocked \
    --next-action "$1" \
    --increment-attempt
}

git fetch origin main staging 2>/dev/null || true
STG_SHA="$(git rev-parse origin/staging)"
MAIN_SHA="$(git rev-parse origin/main)"
SHORT="$(echo "${STG_SHA}" | cut -c1-12)"
PROMOTE_BRANCH="promote/main/${SHORT}"

find_promote_pr() {
  local row
  row="$(gh pr list --base main --head "${PROMOTE_BRANCH}" --state open --json number,headRefOid,body --jq '.[0] // empty')"
  if [ -z "${row}" ] || [ "${row}" = "null" ]; then
    row="$(gh pr list --base main --state open --json number,headRefName,headRefOid,body \
      | python3 -c '
import json,sys
sha=sys.argv[1]
for r in json.load(sys.stdin):
    if str(r.get("headRefName","")).startswith("promote/main/") and sha in (r.get("body") or ""):
        print(json.dumps(r)); break
' "${STG_SHA}" || true)"
  fi
  echo "${row}"
}

if [ "${MODE}" = "reevaluate" ]; then
  row="$(find_promote_pr)"
  if [ -z "${row}" ]; then
    report "waiting" "no open main promote PR"
    exit 0
  fi
  PROMOTE_PR="$(echo "${row}" | python3 -c 'import json,sys; print(json.load(sys.stdin)["number"])')"
  PROMOTE_HEAD="$(echo "${row}" | python3 -c 'import json,sys; print(json.load(sys.stdin)["headRefOid"])')"
  report "waiting" "reevaluate only observes PR #${PROMOTE_PR}; merge requires approve-merge"
  exit 0
fi

if [ "${MODE}" = "package" ]; then
  if git merge-base --is-ancestor origin/staging origin/main; then
    report "skipped" "staging already in main"
    exit 0
  fi
  existing="$(gh pr list --base main --head "${PROMOTE_BRANCH}" --state open --json number --jq '.[0].number // empty' || true)"
  if [ -n "${existing}" ]; then
    PROMOTE_PR="${existing}"
    PROMOTE_HEAD="$(gh pr view "${PROMOTE_PR}" --json headRefOid --jq .headRefOid)"
    report "packaged" "promote PR #${PROMOTE_PR} already open at ${PROMOTE_HEAD} (no rebuild)"
    exit 0
  fi

  START_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
  START_SHA="$(git rev-parse HEAD)"
  WT="$(mktemp -d "${TMPDIR:-/tmp}/main-promote.XXXXXX")"
  cleanup() { git worktree remove --force "${WT}" >/dev/null 2>&1 || rm -rf "${WT}"; }
  trap cleanup EXIT
  git worktree add --detach "${WT}" origin/main >/dev/null
  git -C "${WT}" checkout -B "${PROMOTE_BRANCH}" >/dev/null
  if ! git -C "${WT}" merge --no-ff origin/staging -m "chore(promote): merge staging ${SHORT} into main candidate"; then
    git -C "${WT}" merge --abort 2>/dev/null || true
    conflict_upsert "Repair merge of staging into main on ${PROMOTE_BRANCH}."
    report "conflict_blocked" "merge conflict building main candidate — protected branches unchanged"
    exit 0
  fi
  PROMOTE_HEAD="$(git -C "${WT}" rev-parse HEAD)"
  git -C "${WT}" push -u origin "HEAD:refs/heads/${PROMOTE_BRANCH}"
  BODY="$(cat <<EOF
## Main promote package (awaiting Principal Approve)

- staging SHA (source): \`${STG_SHA}\`
- previous main SHA: \`${MAIN_SHA}\`
- promote candidate SHA: \`${PROMOTE_HEAD}\`
- Approve must bind **both** \`expected_sha=${STG_SHA}\` and \`expected_promote_head=${PROMOTE_HEAD}\`.
- release-gate must pass on **this PR head**.
EOF
)"
  URL="$(gh pr create --base main --head "${PROMOTE_BRANCH}" \
    --title "chore(promote): staging → main (awaiting Approve ${SHORT})" \
    --body "${BODY}")"
  PROMOTE_PR="$(gh pr view "${URL}" --json number --jq .number)"
  report "packaged" "opened main promote PR #${PROMOTE_PR} head ${PROMOTE_HEAD}"
  [ "$(git rev-parse --abbrev-ref HEAD)" = "${START_BRANCH}" ]
  [ "$(git rev-parse HEAD)" = "${START_SHA}" ]
  exit 0
fi

if [ "${MODE}" != "approve-merge" ]; then
  report "failed" "unknown MODE=${MODE}"
  exit 1
fi

if [ -z "${EXPECTED_STAGING_SHA}" ] || [ -z "${EXPECTED_PROMOTE_HEAD}" ]; then
  report "failed" "approve-merge requires both EXPECTED_STAGING_SHA and EXPECTED_PROMOTE_HEAD"
  exit 1
fi

if [ "${EXPECTED_STAGING_SHA}" != "${STG_SHA}" ]; then
  report "failed" "expected_sha ${EXPECTED_STAGING_SHA} != staging tip ${STG_SHA}"
  exit 1
fi

row="$(find_promote_pr)"
if [ -z "${row}" ]; then
  report "failed" "no open main promote PR for staging ${STG_SHA}"
  exit 1
fi
PROMOTE_PR="$(echo "${row}" | python3 -c 'import json,sys; print(json.load(sys.stdin)["number"])')"
PROMOTE_HEAD="$(echo "${row}" | python3 -c 'import json,sys; print(json.load(sys.stdin)["headRefOid"])')"
BODY="$(echo "${row}" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("body") or "")')"

if [ "${EXPECTED_PROMOTE_HEAD}" != "${PROMOTE_HEAD}" ]; then
  report "failed" "expected_promote_head ${EXPECTED_PROMOTE_HEAD} != PR head ${PROMOTE_HEAD}"
  exit 1
fi

if ! echo "${BODY}" | grep -q "${STG_SHA}"; then
  report "failed" "promote PR body does not reference staging SHA ${STG_SHA}"
  exit 1
fi

base="$(gh pr view "${PROMOTE_PR}" --json baseRefName,headRefName --jq .baseRefName)"
head_branch="$(gh pr view "${PROMOTE_PR}" --json headRefName --jq .headRefName)"
if [ "${base}" != "main" ] || ! is_main_promote_branch "${head_branch}"; then
  report "failed" "PR #${PROMOTE_PR} is not main <- promote/main/*"
  exit 1
fi

if ! python3 "${SCRIPT_DIR}/wait_named_gate.py" \
    --pr "${PROMOTE_PR}" \
    --required "${RELEASE_GATE_CHECKS}" \
    --timeout-seconds "${GATE_WAIT_SECONDS:-300}" \
    --poll-seconds 15 \
    --report-file release-gate-wait.json; then
  report "blocked" "release-gate not green on PR #${PROMOTE_PR} head ${PROMOTE_HEAD}"
  exit 1
fi

head_now="$(gh pr view "${PROMOTE_PR}" --json headRefOid --jq .headRefOid)"
if [ "${head_now}" != "${EXPECTED_PROMOTE_HEAD}" ]; then
  report "failed" "promote head changed during gate wait"
  exit 1
fi

if gh pr merge "${PROMOTE_PR}" --merge; then
  tid="$(python3 -c 'import hashlib; print(hashlib.sha256(f"'"${REPO}"'|main|'"${STG_SHA}"'|'"${MAIN_SHA}"'".encode()).hexdigest()[:16])')"
  python3 "${SCRIPT_DIR}/conflict_task.py" resolve --repo "${REPO}" --id "${tid}" >/dev/null 2>&1 || true
  report "promoted" "merged main promote PR #${PROMOTE_PR}"
  exit 0
fi
conflict_upsert "Merge failed for main promote PR #${PROMOTE_PR}"
report "failed" "merge failed — no direct push to main"
exit 1
