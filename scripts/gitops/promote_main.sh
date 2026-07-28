#!/usr/bin/env bash
# Promote staging → main via a temporary promotion branch + PR.
# Never pushes directly to main. Binds approval to staging SHA + promote PR head.
#
# Env:
#   EXPECTED_STAGING_SHA  optional exact staging tip required for approve
#   EXPECTED_PROMOTE_HEAD optional exact promote PR head required for approve
#   RELEASE_GATE_CHECKS   default Verify IDE Development
#   MODE=package|approve-merge
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "FAIL: not a git repository" >&2
  exit 1
}
cd "$ROOT"
# shellcheck source=work-branch-allowlist.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/work-branch-allowlist.sh"

MODE="${MODE:-package}"
RELEASE_GATE_CHECKS="${RELEASE_GATE_CHECKS:-Verify IDE Development}"
TIMEZONE_LABEL="${TIMEZONE_LABEL:-Asia/Taipei}"
EXPECTED_STAGING_SHA="${EXPECTED_STAGING_SHA:-}"
EXPECTED_PROMOTE_HEAD="${EXPECTED_PROMOTE_HEAD:-}"
REPO="${GH_REPO:-$(gh repo view --json nameWithOwner --jq .nameWithOwner)}"

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
  } | tee main-promote-report.md
  echo "MAIN_PROMOTE_STATUS=${status}"
}

ensure_conflict_task() {
  python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/conflict_task.py" upsert \
    --repo "${REPO}" \
    --stage main \
    --source-branch staging \
    --target-branch main \
    --source-sha "${STG_SHA}" \
    --target-sha "${MAIN_SHA}" \
    --status conflict_blocked \
    --next-action "Repair merge of staging into main on a promote/main/* branch; push; wait for automatic reevaluation (max 3 attempts)."
}

git fetch origin main staging
STG_SHA="$(git rev-parse origin/staging)"
MAIN_SHA="$(git rev-parse origin/main)"
SHORT="$(echo "${STG_SHA}" | cut -c1-12)"
PROMOTE_BRANCH="promote/main/${SHORT}"

if git merge-base --is-ancestor origin/staging origin/main; then
  report "skipped" "staging already fully contained in main"
  exit 0
fi

if [ "${MODE}" = "package" ]; then
  if ! is_main_promote_branch "${PROMOTE_BRANCH}"; then
    report "failed" "internal: promote branch name not allowed"
    exit 1
  fi
  git branch -f "${PROMOTE_BRANCH}" origin/main
  git checkout "${PROMOTE_BRANCH}"
  if ! git merge --no-ff origin/staging -m "chore(promote): merge staging ${SHORT} into main candidate"; then
    git merge --abort 2>/dev/null || true
    ensure_conflict_task || true
    report "conflict_blocked" "merge conflict building main promotion candidate — protected branches unchanged"
    exit 0
  fi
  CANDIDATE_SHA="$(git rev-parse HEAD)"
  git push -u origin "${PROMOTE_BRANCH}" --force-with-lease

  BODY="$(cat <<EOF
## Main promote package (awaiting Principal Approve)

Temporary promotion branch (never a direct push to main).

- Package time: Mon 08:00 ${TIMEZONE_LABEL}
- staging SHA (source): \`${STG_SHA}\`
- previous main SHA: \`${MAIN_SHA}\`
- promote candidate SHA: \`${CANDIDATE_SHA}\`
- **Do not merge** until Principal Approves via Lisa (~08:30).
- Approve must bind **both** staging SHA \`${STG_SHA}\` and this PR head \`${CANDIDATE_SHA}\`.
- release-gate must pass on **this PR head** (combined result).

Dispatch: \`action=approve-merge\` with \`expected_sha=${STG_SHA}\` and \`expected_promote_head=${CANDIDATE_SHA}\`.
EOF
)"
  EXISTING="$(gh pr list --base main --head "${PROMOTE_BRANCH}" --state open --json number --jq '.[0].number // empty' || true)"
  if [ -n "${EXISTING}" ]; then
    gh pr edit "${EXISTING}" --title "chore(promote): staging → main (awaiting Approve ${SHORT})" --body "${BODY}"
    report "packaged" "refreshed main promote PR #${EXISTING} candidate ${CANDIDATE_SHA}"
  else
    URL="$(gh pr create --base main --head "${PROMOTE_BRANCH}" \
      --title "chore(promote): staging → main (awaiting Approve ${SHORT})" \
      --body "${BODY}")"
    NUM="$(gh pr view "${URL}" --json number --jq .number)"
    report "packaged" "opened main promote PR #${NUM} candidate ${CANDIDATE_SHA}"
  fi
  exit 0
fi

if [ "${MODE}" != "approve-merge" ]; then
  report "failed" "unknown MODE=${MODE}"
  exit 1
fi

if [ -n "${EXPECTED_STAGING_SHA}" ] && [ "${EXPECTED_STAGING_SHA}" != "${STG_SHA}" ]; then
  report "failed" "expected_sha ${EXPECTED_STAGING_SHA} != staging tip ${STG_SHA}"
  exit 1
fi

PR_NUM="$(gh pr list --base main --head "${PROMOTE_BRANCH}" --state open --json number --jq '.[0].number // empty' || true)"
HEAD=""
if [ -n "${PR_NUM}" ]; then
  HEAD="$(gh pr view "${PR_NUM}" --json headRefOid --jq .headRefOid)"
else
  # Accept any open promote/main/* PR whose body mentions this staging SHA
  PR_JSON="$(gh pr list --base main --state open --json number,headRefName,headRefOid,body)"
  PR_NUM="$(echo "${PR_JSON}" | python3 -c '
import json,sys
sha=sys.argv[1]
rows=json.load(sys.stdin)
for r in rows:
    if str(r.get("headRefName","")).startswith("promote/main/") and sha in (r.get("body") or ""):
        print(r["number"]); break
' "${STG_SHA}")"
  if [ -z "${PR_NUM}" ]; then
    report "failed" "no open main promote PR for staging ${STG_SHA}"
    exit 1
  fi
  HEAD="$(gh pr view "${PR_NUM}" --json headRefOid --jq .headRefOid)"
fi

if [ -n "${EXPECTED_PROMOTE_HEAD}" ] && [ "${EXPECTED_PROMOTE_HEAD}" != "${HEAD}" ]; then
  report "failed" "expected_promote_head ${EXPECTED_PROMOTE_HEAD} != PR head ${HEAD}"
  exit 1
fi

python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/wait_named_gate.py" \
  --pr "${PR_NUM}" \
  --required "${RELEASE_GATE_CHECKS}" \
  --timeout-seconds "${GATE_WAIT_SECONDS:-300}" \
  --poll-seconds 15 \
  --report-file release-gate-wait.json \
  || {
    report "blocked" "release-gate not green on promote PR #${PR_NUM} head ${HEAD}"
    exit 1
  }

HEAD_NOW="$(gh pr view "${PR_NUM}" --json headRefOid --jq .headRefOid)"
if [ "${HEAD_NOW}" != "${HEAD}" ]; then
  report "failed" "promote PR head drifted during gate wait"
  exit 1
fi

if gh pr merge "${PR_NUM}" --merge; then
  report "promoted" "merged main promote PR #${PR_NUM} (staging=${STG_SHA} head=${HEAD})"
  exit 0
fi

report "failed" "merge failed for PR #${PR_NUM} — no direct push to main"
exit 1
