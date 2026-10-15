#!/usr/bin/env bash
# Promote development → main via temporary promote/main/* branch + PR.
# MODE=package|reevaluate; Main merge authority belongs to delivery_controller.py complete-main.
set -euo pipefail
MODE="${MODE:-package}"
case "${MODE}" in
  package|reevaluate) ;;
  approve-merge)
    echo "FAIL: shell approve-merge is disabled; use delivery_controller.py complete-main with exact Principal approval JSON" >&2
    exit 1
    ;;
  *) echo "FAIL: unsupported main promotion MODE=${MODE}" >&2; exit 1 ;;
esac
# This is an operational lead lease, not a separate credential or identity.
case "${LINKTREND_CONTROLLER_ROLE:-}" in
  program-lead|founder) ;;
  *) echo "FAIL: designated Program lead role required for main promotion" >&2; exit 1 ;;
esac
# Note: gh 403/429 → simple retry 2x with sleep (gh_retry).

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || {
  echo "FAIL: not a git repository" >&2
  exit 1
}
cd "$ROOT"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=work-branch-allowlist.sh
source "${SCRIPT_DIR}/work-branch-allowlist.sh"

MAIN_PROMOTION_MODE="${MAIN_PROMOTION_MODE:-principal-approval}"
PROMOTE_PR_NUMBER="${PROMOTE_PR_NUMBER:-}"
REPO="${GH_REPO:-${GITHUB_REPOSITORY:-}}"
TOKEN="${AUTOMATION_TOKEN:-}"
export GH_TOKEN="${TOKEN}"
export GITHUB_TOKEN="${TOKEN}"
OUTCOME="${OUTCOME_FILE:-gitops-outcome.json}"
RECEIPT_GATE="${SCRIPT_DIR}/promotion_receipt_gate.py"
RECEIPT_PATH="${RECEIPT_PATH:-${LINKTREND_RECEIPT_PATH:-}}"
RECEIPT_DEPENDENCY_FILES="${RECEIPT_DEPENDENCY_FILES:-}"
TRANSITION_RECEIPT_PATH="${LINKTREND_TRANSITION_RECEIPT_PATH:-}"
RECEIPT_IDENTITY_ARGS=()
RECEIPT_PROFILE_ARGS=()
COORDINATOR_RECEIPT_ROOT="${LINKTREND_COORDINATOR_RECEIPT_ROOT:-${HOME}/.linktrend/ide-coordinator/receipts}"

case "${MAIN_PROMOTION_MODE}" in
  principal-approval) ;;
  automatic)
    echo "FAIL: automatic main promotion is disabled; explicit Principal approval is required" >&2
    exit 1
    ;;
  *) echo "FAIL: unsupported main promotion mode ${MAIN_PROMOTION_MODE}" >&2; exit 1 ;;
esac


repair_task_upsert() {
  local ec
  set +e
  python3 "${SCRIPT_DIR}/repair_task.py" upsert "$@" >/dev/null
  ec=$?
  set -e
  if [ "$ec" -ne 0 ]; then
    _gh_present="${GH_TOKEN-}"
    if [ -z "$_gh_present" ]; then
      _gh_present="${GITHUB_TOKEN-}"
    fi
    if [ -n "$_gh_present" ]; then
      echo "FAIL: repair_task.py upsert failed with GitHub token present" >&2
      unset _gh_present
      return "$ec"
    fi
    unset _gh_present
    echo "WARN: repair_task.py upsert failed without GitHub token; continuing without repair task" >&2
  fi
  return 0
}


record_usage_limit_repair_task() {
  repair_task_upsert \
    --repo "${REPO}" \
    --failure-type usage_limit \
    --severity immediate \
    --workflow "main-promote" \
    --next-action "Wait for GitHub API quota; do not ACP-repair usage limits."
}


# Rate-limit backoff: on gh 403/429, retry up to 2 times with sleep (see ACTIONS-COST-CONTROLS.md).
gh_retry() {
  local attempt=1
  local max=3
  local delay=5
  local out ec
  while true; do
    set +e
    out="$("$@" 2>&1)"
    ec=$?
    set -e
    if [ "$ec" -eq 0 ]; then
      printf '%s
' "$out"
      return 0
    fi
    if printf '%s' "$out" | grep -Eq 'HTTP 403|HTTP 429|rate limit|secondary rate'; then
      if [ "$attempt" -ge "$max" ]; then
        record_usage_limit_repair_task
        printf '%s
' "$out" >&2
        return "$ec"
      fi
      echo "WARN: gh rate-limit/403/429 — retry ${attempt}/${max} after ${delay}s" >&2
      sleep "$delay"
      delay=$((delay * 2))
      attempt=$((attempt + 1))
      continue
    fi
    printf '%s
' "$out" >&2
    return "$ec"
  done
}


write_out() {
  python3 "${SCRIPT_DIR}/write_outcome.py" --file "${OUTCOME}" --status "$1" --detail "$2"
}

receipt_identity_args() {
  local raw dep
  RECEIPT_IDENTITY_ARGS=()
  raw="$(printf '%s' "${RECEIPT_DEPENDENCY_FILES}" | tr ',' '\n')"
  while IFS= read -r dep; do
    [ -n "${dep}" ] && RECEIPT_IDENTITY_ARGS+=(--dependency "${dep}")
  done <<< "${raw}"
  return 0
}

receipt_profile_args() {
  local candidate_repo="$1"
  RECEIPT_PROFILE_ARGS=()
  if [ -f "${candidate_repo}/.github/linktrend-delivery-mode.json" ]; then
    RECEIPT_PROFILE_ARGS=(--profile-file ".github/linktrend-delivery-mode.json")
  elif [ -f "${candidate_repo}/.ide-development/config/delivery.json" ]; then
    RECEIPT_PROFILE_ARGS=(--profile-file ".ide-development/config/delivery.json")
  else
    echo "FAIL: delivery profile configuration is unavailable in promotion candidate" >&2
    return 1
  fi
  return 0
}

verify_receipt_before_mutation() {
  local candidate_repo="$1"
  local profile="${2:-full}"
  if [ -z "${RECEIPT_PATH}" ] || [ ! -f "${RECEIPT_PATH}" ]; then
    write_out "blocked" "promotion receipt missing; protected main was not mutated"
    return 1
  fi
  receipt_identity_args
  receipt_profile_args "${candidate_repo}"
  local transition_args=()
  [ -z "${TRANSITION_RECEIPT_PATH}" ] || transition_args=(--transition-receipt "${TRANSITION_RECEIPT_PATH}")
  local identity_file
  identity_file="$(mktemp "${TMPDIR:-/tmp}/main-source-identity.XXXXXX.json")"
  python3 "${SCRIPT_DIR}/gate_receipt.py" identity --repo "${candidate_repo}" --profile "${profile}" --source-branch development \
    ${RECEIPT_PROFILE_ARGS[@]+"${RECEIPT_PROFILE_ARGS[@]}"} \
    ${RECEIPT_IDENTITY_ARGS[@]+"${RECEIPT_IDENTITY_ARGS[@]}"} >"${identity_file}"
  local verify_result=0
  python3 "${RECEIPT_GATE}" verify \
    --receipt "${RECEIPT_PATH}" \
    --identity "${identity_file}" \
    --profile "${profile}" \
    --gate full-gate \
    ${RECEIPT_PROFILE_ARGS[@]+"${RECEIPT_PROFILE_ARGS[@]}"} \
    ${RECEIPT_IDENTITY_ARGS[@]+"${RECEIPT_IDENTITY_ARGS[@]}"} \
    ${transition_args[@]+"${transition_args[@]}"} || verify_result=$?
  rm -f "${identity_file}"
  return "${verify_result}"
}

if [ -z "${TOKEN}" ] || [ "${AUTOMATION_TOKEN_SOURCE:-}" != "github_token" ]; then
  # automation token unavailable: local outcome only — no repair/check mutation via workflow token.
  write_out "automation_credentials_blocked" "main promote requires normal GitHub automation token"
  exit 0
fi

git fetch origin main development

DEV_SHA="$(git rev-parse origin/development)"
MAIN_SHA="$(git rev-parse origin/main)"

marker_json() {
  python3 -c 'import json,sys
value = {
    "schemaVersion": 1,
    "stage": "main",
    "sourceBranch": "development",
    "targetBranch": "main",
    "sourceSha": sys.argv[1],
    "targetSha": sys.argv[2],
    "candidateHead": sys.argv[3],
    "promoteBranch": sys.argv[4],
    "fullRunId": int(sys.argv[5]),
  }
if sys.argv[6]:
    with open(sys.argv[6], encoding="utf-8") as handle:
        value["transitionReceipt"] = json.load(handle)
    value["transitionReceiptDigest"] = value["transitionReceipt"]["receiptDigest"]
with open(sys.argv[7], encoding="utf-8") as handle:
    value["candidateIdentity"] = json.load(handle)
print(json.dumps(value, separators=(",", ":")))' "$1" "$2" "$3" "$4" "$5" "${TRANSITION_RECEIPT_PATH}" "${RECEIPT_IDENTITY_FILE}"
}

if [ "${MODE}" = "reevaluate" ]; then
  if [ -z "${PROMOTE_PR_NUMBER}" ]; then
    write_out "failed" "reevaluate requires PROMOTE_PR_NUMBER"
    exit 1
  fi
  write_out "waiting" "main reevaluate observes PR #${PROMOTE_PR_NUMBER}; merge requires delivery_controller.py complete-main with exact Principal approval JSON"
  exit 0
fi

if [ "${MODE}" = "package" ]; then
  if git merge-base --is-ancestor origin/development origin/main; then
    write_out "skipped" "development already in main"
    exit 0
  fi
  SHORT="$(echo "${DEV_SHA}" | cut -c1-12)"
  PROMOTE_BRANCH="promote/main/${SHORT}"

  existing_json="$(gh_retry gh pr list --base main --state open \
    --json number,body,headRefName,headRefOid,baseRefName,state,isCrossRepository,headRepository)"
  reuse_json="$(printf '%s\n' "${existing_json}" | python3 "${SCRIPT_DIR}/main_approve_package_reuse.py" \
    --expected-source "${DEV_SHA}" \
    --expected-target "${MAIN_SHA}" \
    --expected-branch "${PROMOTE_BRANCH}" \
    --repository "${REPO}")"
  reuse_action="$(printf '%s\n' "${reuse_json}" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("action",""))')"
  reuse_pr="$(printf '%s\n' "${reuse_json}" | python3 -c 'import json,sys; v=json.load(sys.stdin).get("pr"); print(v if v is not None else "")')"
  reuse_reason="$(printf '%s\n' "${reuse_json}" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("reason",""))')"
  if [ "${reuse_action}" = "reuse" ] && [ -n "${reuse_pr}" ]; then
    write_out "packaged" "main promote PR #${reuse_pr} already open and valid for reuse (open/same-repo/base/branch/marker/head)"
    exit 0
  fi
  if [ "${reuse_action}" = "repackage" ]; then
    python3 "${SCRIPT_DIR}/repair_task.py" upsert \
      --repo "${REPO}" --failure-type promotion_conflict \
      --stage main \
      --source-branch development --target-branch main \
      --branch "development->main" \
      --head-sha "${DEV_SHA}" --base-sha "${MAIN_SHA}" \
      --pr "${reuse_pr:-0}" --status conflict_blocked \
      --next-action "Existing main promote package invalid (${reuse_reason}); close/repair and repackage; do not silently reuse or overwrite." \
      >/dev/null || true
    write_out "blocked" "existing main promote package invalid (${reuse_reason}); requires repackage"
    exit 0
  fi

  START_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
  START_SHA="$(git rev-parse HEAD)"
  WT="$(mktemp -d "${TMPDIR:-/tmp}/main-promote.XXXXXX")"
  RECEIPT_IDENTITY_FILE="$(mktemp "${TMPDIR:-/tmp}/main-identity.XXXXXX.json")"
  cleanup() {
    git worktree remove --force "${WT}" >/dev/null 2>&1 || rm -rf "${WT}"
    rm -f "${RECEIPT_IDENTITY_FILE}"
  }
  trap cleanup EXIT
  # Preserve the exact accepted Development head; a synthetic merge head
  # would invalidate headCommit receipt identity even for an equal tree.
  if ! git merge-base --is-ancestor origin/main origin/development; then
    write_out "blocked" "main is not an ancestor of accepted Development; integrate normally and obtain exact evidence first"
    exit 0
  fi
  git worktree add --detach "${WT}" "${DEV_SHA}" >/dev/null
  CANDIDATE="$(git -C "${WT}" rev-parse HEAD)"
  CANDIDATE_TREE="$(git -C "${WT}" rev-parse HEAD^{tree})"
  if [ -z "${RECEIPT_PATH}" ]; then
    RECEIPT_PATH="${COORDINATOR_RECEIPT_ROOT}/${CANDIDATE_TREE}-full-gate.json"
  fi
receipt_identity_args
receipt_profile_args "${WT}"
python3 "${SCRIPT_DIR}/gate_receipt.py" identity \
  --repo "${WT}" --profile full --source-branch development \
  ${RECEIPT_PROFILE_ARGS[@]+"${RECEIPT_PROFILE_ARGS[@]}"} \
  ${RECEIPT_IDENTITY_ARGS[@]+"${RECEIPT_IDENTITY_ARGS[@]}"} >"${RECEIPT_IDENTITY_FILE}"
  verify_receipt_before_mutation "${WT}" full || exit 0
  git -C "${WT}" push -u origin "HEAD:refs/heads/${PROMOTE_BRANCH}"
  FULL_RUN_ID="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["workflowRunId"])' "${RECEIPT_PATH}")"
  MARKER="$(marker_json "${DEV_SHA}" "${MAIN_SHA}" "${CANDIDATE}" "${PROMOTE_BRANCH}" "${FULL_RUN_ID}")"
  RECEIPT_DIGEST="$(python3 - "${RECEIPT_PATH}" "${SCRIPT_DIR}" <<'PY'
import sys
sys.path.insert(0, sys.argv[2])
from coordinator.receipts import compute_receipt_digest, load_json
print(compute_receipt_digest(load_json(sys.argv[1])))
PY
)"
  MARKER="$(echo "${MARKER}" | jq --arg digest "${RECEIPT_DIGEST}" --arg mode "${MAIN_PROMOTION_MODE}" '. + {receiptDigest:$digest,approvalMode:$mode}')"
  BODY="$(cat <<EOF
## Main promote package (awaiting Principal Approve)

Approve must bind:
- expected_sha (development source) = \`${DEV_SHA}\`
- expected_main_sha (prior main target) = \`${MAIN_SHA}\`
- expected_promote_head = \`${CANDIDATE}\`

<!-- linktrend-promote: ${MARKER} -->
EOF
)"
  URL="$(gh_retry gh pr create --base main --head "${PROMOTE_BRANCH}" \
    --title "chore(promote): development → main (awaiting Approve ${SHORT})" \
    --body "${BODY}")"
  PR="$(gh_retry gh pr view "${URL}" --json number --jq .number)"
  write_out "packaged" "opened main promote PR #${PR} head ${CANDIDATE}"
  [ "$(git rev-parse --abbrev-ref HEAD)" = "${START_BRANCH}" ]
  [ "$(git rev-parse HEAD)" = "${START_SHA}" ]
  exit 0
fi
