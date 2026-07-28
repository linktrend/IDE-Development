#!/usr/bin/env bash
# Promote development → staging via a temporary promotion branch + PR.
# Never pushes directly to staging. Never prefer-incoming.
#
# Usage (from a full clone with origin):
#   promote_staging.sh
#
# Env:
#   GH_TOKEN / GH_REPO (optional; defaults via gh)
#   STAGING_GATE_CHECKS  comma-separated check names (default: Verify IDE Development)
#   TIMEZONE_LABEL       default Asia/Taipei
#   DRY_RUN=1            plan only
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "FAIL: not a git repository" >&2
  exit 1
}
cd "$ROOT"
# shellcheck source=work-branch-allowlist.sh
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/work-branch-allowlist.sh"

STAGING_GATE_CHECKS="${STAGING_GATE_CHECKS:-Verify IDE Development}"
TIMEZONE_LABEL="${TIMEZONE_LABEL:-Asia/Taipei}"
DRY_RUN="${DRY_RUN:-0}"
REPO="${GH_REPO:-$(gh repo view --json nameWithOwner --jq .nameWithOwner)}"

report() {
  local status="$1"
  local why="$2"
  mkdir -p /tmp
  {
    echo "## Staging promote report"
    echo ""
    echo "- Timezone: ${TIMEZONE_LABEL}"
    echo "- Status: **${status}**"
    echo "- Reason: ${why}"
    echo "- development: \`${DEV_SHA:-unknown}\`"
    echo "- staging: \`${STG_SHA:-unknown}\`"
    echo "- promote_branch: \`${PROMOTE_BRANCH:-none}\`"
  } | tee staging-promote-report.md
  echo "STAGING_PROMOTE_STATUS=${status}"
  echo "STAGING_PROMOTE_REASON=${why}"
}

ensure_conflict_task() {
  python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/conflict_task.py" upsert \
    --repo "${REPO}" \
    --stage staging \
    --source-branch development \
    --target-branch staging \
    --source-sha "${DEV_SHA}" \
    --target-sha "${STG_SHA}" \
    --status conflict_blocked \
    --next-action "Repair merge of development into staging on a promote/staging/* branch; push; wait for automatic reevaluation (max 3 attempts)."
}

git fetch origin development staging

DEV_SHA="$(git rev-parse origin/development)"
STG_SHA="$(git rev-parse origin/staging)"
SHORT="$(echo "${DEV_SHA}" | cut -c1-12)"
PROMOTE_BRANCH="promote/staging/${SHORT}"

if git merge-base --is-ancestor origin/development origin/staging; then
  report "skipped" "development is already fully contained in staging — nothing to promote"
  exit 0
fi

if ! is_staging_promote_branch "${PROMOTE_BRANCH}"; then
  report "failed" "internal: promote branch name not allowed"
  exit 1
fi

# Build temporary promotion branch from staging tip
if [ "${DRY_RUN}" = "1" ]; then
  report "dry_run" "would create ${PROMOTE_BRANCH} from staging and merge ${DEV_SHA}"
  exit 0
fi

git branch -f "${PROMOTE_BRANCH}" origin/staging
git checkout "${PROMOTE_BRANCH}"

if ! git merge --no-ff origin/development -m "chore(promote): merge development ${SHORT} into staging candidate"; then
  git merge --abort 2>/dev/null || true
  ensure_conflict_task || true
  report "conflict_blocked" "merge conflict building staging promotion candidate — protected branches unchanged"
  git checkout --detach origin/staging >/dev/null 2>&1 || true
  exit 0
fi

CANDIDATE_SHA="$(git rev-parse HEAD)"
git push -u origin "${PROMOTE_BRANCH}" --force-with-lease

BODY="$(cat <<EOF
## Staging promote candidate

Temporary promotion branch (never a direct push to staging).

- Schedule: Tue/Fri 10:00 ${TIMEZONE_LABEL}
- development SHA: \`${DEV_SHA}\`
- previous staging SHA: \`${STG_SHA}\`
- candidate SHA: \`${CANDIDATE_SHA}\`
- staging-gate must pass on **this PR head** (combined result), not on development alone.

Prefer-incoming is forbidden. On conflict: conflict_blocked repair task.
EOF
)"

EXISTING="$(gh pr list --base staging --head "${PROMOTE_BRANCH}" --state open --json number --jq '.[0].number // empty' || true)"
if [ -n "${EXISTING}" ]; then
  PR="${EXISTING}"
  gh pr edit "${PR}" --body "${BODY}" --title "chore(promote): development → staging (${SHORT})"
else
  PR_URL="$(gh pr create --base staging --head "${PROMOTE_BRANCH}" \
    --title "chore(promote): development → staging (${SHORT})" \
    --body "${BODY}")"
  PR="$(gh pr view "${PR_URL}" --json number --jq .number)"
fi

echo "Opened/refreshed staging promote PR #${PR} head=${CANDIDATE_SHA}"

# Wait briefly for checks to register; merge only when staging-gate green on PR head.
python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/wait_named_gate.py" \
  --pr "${PR}" \
  --required "${STAGING_GATE_CHECKS}" \
  --timeout-seconds "${GATE_WAIT_SECONDS:-900}" \
  --poll-seconds "${GATE_POLL_SECONDS:-20}" \
  --report-file staging-gate-wait.json \
  || {
    report "waiting" "staging-gate not green yet on promote PR #${PR} head ${CANDIDATE_SHA}; left open"
    exit 0
  }

HEAD_NOW="$(gh pr view "${PR}" --json headRefOid --jq .headRefOid)"
if [ "${HEAD_NOW}" != "${CANDIDATE_SHA}" ]; then
  report "blocked" "promote PR head drifted (${HEAD_NOW} != ${CANDIDATE_SHA})"
  exit 0
fi

if gh pr merge "${PR}" --merge; then
  report "promoted" "merged promote PR #${PR} at combined candidate ${CANDIDATE_SHA}"
  exit 0
fi

report "blocked" "staging-gate green but merge failed for PR #${PR} — not force-merging; no direct push"
exit 0
