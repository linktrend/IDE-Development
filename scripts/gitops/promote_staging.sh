#!/usr/bin/env bash
# Promote development → staging via temporary promote/staging/* branch + PR.
#
# MODE:
#   build          — schedule/manual only: create candidate once
#   reevaluate     — PR/check only: inspect existing PR; never checkout/merge/push
#   repair-resume  — same as reevaluate for a repaired existing head
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "FAIL: not a git repository" >&2
  exit 1
}
cd "$ROOT"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=work-branch-allowlist.sh
source "${SCRIPT_DIR}/work-branch-allowlist.sh"

MODE="${MODE:-build}"
STAGING_GATE_CHECKS="${STAGING_GATE_CHECKS:-Verify IDE Development}"
TIMEZONE_LABEL="${TIMEZONE_LABEL:-Asia/Taipei}"
REPO="${GH_REPO:-${GITHUB_REPOSITORY:-$(gh repo view --json nameWithOwner --jq .nameWithOwner)}}"
DRY_RUN="${DRY_RUN:-0}"

report() {
  local status="$1"
  local why="$2"
  {
    echo "## Staging promote report"
    echo ""
    echo "- Mode: ${MODE}"
    echo "- Status: **${status}**"
    echo "- Reason: ${why}"
    echo "- development: \`${DEV_SHA:-unknown}\`"
    echo "- staging: \`${STG_SHA:-unknown}\`"
    echo "- promote_branch: \`${PROMOTE_BRANCH:-none}\`"
    echo "- promote_head: \`${PROMOTE_HEAD:-none}\`"
  } | tee staging-promote-report.md
  echo "STAGING_PROMOTE_STATUS=${status}"
}

conflict_upsert() {
  python3 "${SCRIPT_DIR}/conflict_task.py" upsert \
    --repo "${REPO}" \
    --stage staging \
    --source-branch development \
    --target-branch staging \
    --source-sha "${DEV_SHA}" \
    --target-sha "${STG_SHA}" \
    --promote-pr "${PROMOTE_PR:-}" \
    --status conflict_blocked \
    --next-action "$1" \
    --increment-attempt
}

git fetch origin development staging 2>/dev/null || true
DEV_SHA="$(git rev-parse origin/development)"
STG_SHA="$(git rev-parse origin/staging)"
SHORT="$(echo "${DEV_SHA}" | cut -c1-12)"
PROMOTE_BRANCH="promote/staging/${SHORT}"

reevaluate_existing() {
  local pr head
  pr="$(gh pr list --base staging --head "${PROMOTE_BRANCH}" --state open --json number,headRefOid --jq '.[0] | "\(.number) \(.headRefOid)"' || true)"
  if [ -z "${pr}" ]; then
    # any open promote/staging/* for this development sha in body
    pr="$(gh pr list --base staging --state open --json number,headRefName,headRefOid,body \
      | python3 -c '
import json,sys
sha=sys.argv[1]
for r in json.load(sys.stdin):
    if str(r.get("headRefName","")).startswith("promote/staging/") and sha in (r.get("body") or ""):
        print(r["number"], r["headRefOid"]); break
' "${DEV_SHA}" || true)"
  fi
  if [ -z "${pr}" ]; then
    report "waiting" "no open staging promote PR to reevaluate"
    exit 0
  fi
  PROMOTE_PR="$(echo "${pr}" | awk '{print $1}')"
  PROMOTE_HEAD="$(echo "${pr}" | awk '{print $2}')"
  echo "Reevaluate PR #${PROMOTE_PR} head=${PROMOTE_HEAD} (no rebuild/push)"

  if ! python3 "${SCRIPT_DIR}/wait_named_gate.py" \
      --pr "${PROMOTE_PR}" \
      --required "${STAGING_GATE_CHECKS}" \
      --timeout-seconds "${GATE_WAIT_SECONDS:-120}" \
      --poll-seconds 10 \
      --report-file staging-gate-wait.json; then
    # unsuccessful gate / still pending — if conflicting mergeability, increment attempt
    mergeable="$(gh pr view "${PROMOTE_PR}" --json mergeable --jq .mergeable)"
    if [ "${mergeable}" = "CONFLICTING" ]; then
      conflict_upsert "Repair promote PR #${PROMOTE_PR}; push repaired commits to existing branch; wait for reevaluate."
      report "conflict_blocked" "promote PR #${PROMOTE_PR} conflicting"
      exit 0
    fi
    report "waiting" "staging-gate not green on PR #${PROMOTE_PR} head ${PROMOTE_HEAD}"
    exit 0
  fi

  head_now="$(gh pr view "${PROMOTE_PR}" --json headRefOid --jq .headRefOid)"
  if [ "${head_now}" != "${PROMOTE_HEAD}" ]; then
    report "blocked" "promote head changed during gate wait (${head_now} != ${PROMOTE_HEAD})"
    exit 0
  fi

  if gh pr merge "${PROMOTE_PR}" --merge; then
    tid="$(python3 -c 'import hashlib; print(hashlib.sha256(f"'"${REPO}"'|staging|'"${DEV_SHA}"'|'"${STG_SHA}"'".encode()).hexdigest()[:16])')"
    python3 "${SCRIPT_DIR}/conflict_task.py" resolve --repo "${REPO}" --id "${tid}" >/dev/null 2>&1 || true
    report "promoted" "merged promote PR #${PROMOTE_PR} at ${PROMOTE_HEAD}"
    exit 0
  fi
  conflict_upsert "Merge failed for PR #${PROMOTE_PR} after green gate; inspect permissions/rules."
  report "blocked" "merge failed for PR #${PROMOTE_PR}"
  exit 0
}

if [ "${MODE}" = "reevaluate" ] || [ "${MODE}" = "repair-resume" ]; then
  reevaluate_existing
fi

if [ "${MODE}" != "build" ]; then
  report "failed" "unknown MODE=${MODE}"
  exit 1
fi

if git merge-base --is-ancestor origin/development origin/staging; then
  report "skipped" "development already contained in staging"
  exit 0
fi

# If promote PR already exists for this short sha, do not rebuild — reevaluate instead
existing="$(gh pr list --base staging --head "${PROMOTE_BRANCH}" --state open --json number --jq '.[0].number // empty' || true)"
if [ -n "${existing}" ]; then
  echo "Promote PR #${existing} already exists — switching to reevaluate (no rebuild)"
  MODE=reevaluate
  reevaluate_existing
fi

if [ "${DRY_RUN}" = "1" ]; then
  report "dry_run" "would create ${PROMOTE_BRANCH}"
  exit 0
fi

# Build once in a temporary worktree — do not disturb caller checkout
START_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
START_SHA="$(git rev-parse HEAD)"
WT="$(mktemp -d "${TMPDIR:-/tmp}/stg-promote.XXXXXX")"
cleanup() { git worktree remove --force "${WT}" >/dev/null 2>&1 || rm -rf "${WT}"; }
trap cleanup EXIT

git worktree add --detach "${WT}" origin/staging >/dev/null
git -C "${WT}" checkout -B "${PROMOTE_BRANCH}" >/dev/null

if ! git -C "${WT}" merge --no-ff origin/development -m "chore(promote): merge development ${SHORT} into staging candidate"; then
  git -C "${WT}" merge --abort 2>/dev/null || true
  conflict_upsert "Repair merge of development into staging on ${PROMOTE_BRANCH}; push; wait for reevaluate."
  report "conflict_blocked" "merge conflict building staging candidate — protected branches unchanged"
  exit 0
fi

PROMOTE_HEAD="$(git -C "${WT}" rev-parse HEAD)"
git -C "${WT}" push -u origin "HEAD:refs/heads/${PROMOTE_BRANCH}"

BODY="$(cat <<EOF
## Staging promote candidate

Temporary promotion branch (never a direct push to staging).

- Schedule: Tue/Fri 10:00 ${TIMEZONE_LABEL}
- development SHA: \`${DEV_SHA}\`
- previous staging SHA: \`${STG_SHA}\`
- candidate SHA: \`${PROMOTE_HEAD}\`
- staging-gate must pass on **this PR head** (combined result).

Prefer-incoming is forbidden.
EOF
)"

PR_URL="$(gh pr create --base staging --head "${PROMOTE_BRANCH}" \
  --title "chore(promote): development → staging (${SHORT})" \
  --body "${BODY}")"
PROMOTE_PR="$(gh pr view "${PR_URL}" --json number --jq .number)"
report "packaged" "opened promote PR #${PROMOTE_PR} head ${PROMOTE_HEAD} (build does not wait/merge)"
# Caller checkout unchanged
[ "$(git rev-parse --abbrev-ref HEAD)" = "${START_BRANCH}" ] || exit 1
[ "$(git rev-parse HEAD)" = "${START_SHA}" ] || exit 1
exit 0
