#!/usr/bin/env bash
# Integrator evaluate/merge for PRs into development.
# Emits integrator-result.json with status: merged|waiting|blocked|failed
# Posts check run "Linktrend Integrator Result" with honest conclusion.
# The Actions job should treat evaluate as report-only; this script's exit code:
#   0 = merged or waiting (non-error)
#   1 = blocked or failed
set -euo pipefail

PR_NUMBER="${PR_NUMBER:-}"
HEAD_SHA="${HEAD_SHA:-}"
REQUIRED_CHECKS="${REQUIRED_CHECKS:-Verify IDE Development}"
BUGBOT_SUCCESS_CHECK_NAME="${BUGBOT_SUCCESS_CHECK_NAME:-Cursor Bugbot}"
GATE_WAIT_SECONDS="${GATE_WAIT_SECONDS:-900}"
GATE_POLL_SECONDS="${GATE_POLL_SECONDS:-20}"
GH_REPO="${GH_REPO:-${GITHUB_REPOSITORY:-}}"

write_result() {
  local status="$1"
  local detail="$2"
  local pr="${3:-}"
  python3 - "$status" "$detail" "$pr" <<'PY'
import json, sys
status, detail, pr = sys.argv[1:4]
payload = {"status": status, "detail": detail, "pr": pr or None}
open("integrator-result.json", "w", encoding="utf-8").write(json.dumps(payload, indent=2) + "\n")
print(f"INTEGRATOR_STATUS={status}")
print(f"INTEGRATOR_DETAIL={detail}")
PY
}

post_check() {
  local status="$1"
  local detail="$2"
  local sha="$3"
  local conclusion="neutral"
  case "$status" in
    merged) conclusion="success" ;;
    waiting) conclusion="neutral" ;;
    blocked) conclusion="neutral" ;;
    failed) conclusion="failure" ;;
  esac
  if [ -z "$sha" ] || [ -z "${GH_REPO}" ]; then
    return 0
  fi
  # Create check run with honest conclusion (does not claim merge unless merged).
  gh api --method POST "repos/${GH_REPO}/check-runs" \
    -f name='Linktrend Integrator Result' \
    -f head_sha="$sha" \
    -f status='completed' \
    -f conclusion="$conclusion" \
    -f output[title]="Integrator: ${status}" \
    -f output[summary]="${detail}" >/dev/null || true
}

bugbot_state_from_checks() {
  echo "$1" | jq -r --arg n "${BUGBOT_SUCCESS_CHECK_NAME}" '
    [.[] | select(.name==$n)] as $b
    | if ($b|length)==0 then "missing"
      else
        ($b | sort_by(.completedAt // .startedAt // "") | last | .state) as $s
        | if ($s=="PENDING" or $s=="QUEUED" or $s=="IN_PROGRESS") then "pending"
          elif ($s=="SUCCESS") then "success"
          else "not_success"
          end
      end'
}

resolve_reviewed_sha() {
  local pr="$1"
  local body comments
  body="$(gh pr view "${pr}" --json body --jq .body 2>/dev/null || true)"
  comments="$(gh api "repos/${GH_REPO}/issues/${pr}/comments" --paginate --jq '.[].body' 2>/dev/null || true)"
  printf '%s\n%s\n' "${body}" "${comments}" \
    | grep -oE '<!-- linktrend-bugbot-requested:[[:space:]]*[0-9a-fA-F]+[[:space:]]*-->' \
    | tail -n1 \
    | sed -E 's/.*linktrend-bugbot-requested:[[:space:]]*([0-9a-fA-F]+).*/\1/' \
    | tr 'A-F' 'a-f' || true
}

collect_pr() {
  if [ -n "${PR_NUMBER}" ]; then
    echo "${PR_NUMBER}"
  elif [ -n "${HEAD_SHA}" ]; then
    gh pr list --base development --state open \
      --json number,isDraft,headRefOid \
      --jq "[.[] | select(.isDraft==false and .headRefOid==\"${HEAD_SHA}\") | .number] | .[0] // empty"
  fi
}

pr="$(collect_pr || true)"
if [ -z "${pr}" ]; then
  write_result "waiting" "No candidate development PR to evaluate" ""
  post_check "waiting" "No candidate PR" "${HEAD_SHA}"
  exit 0
fi

meta="$(gh pr view "${pr}" --json baseRefName,isDraft,state,headRefOid,mergeable)"
echo "${meta}" | jq -e '.baseRefName=="development" and .isDraft==false and .state=="OPEN"' >/dev/null \
  || {
    write_result "blocked" "PR #${pr} is not an open non-draft development PR" "${pr}"
    post_check "blocked" "invalid PR state" "$(echo "${meta}" | jq -r .headRefOid)"
    exit 1
  }

head_sha="$(echo "${meta}" | jq -r .headRefOid)"
reviewed="$(resolve_reviewed_sha "${pr}")"
if [ -z "${reviewed}" ]; then
  write_result "waiting" "PR #${pr}: no Bugbot-requested marker yet for a reviewed SHA" "${pr}"
  post_check "waiting" "awaiting Bugbot request marker" "${head_sha}"
  exit 0
fi
if [ "${head_sha}" != "${reviewed}" ]; then
  write_result "blocked" "PR #${pr}: head ${head_sha} != reviewed ${reviewed}" "${pr}"
  post_check "blocked" "head drifted from reviewed SHA" "${head_sha}"
  exit 1
fi

mergeable="$(echo "${meta}" | jq -r .mergeable)"
if [ "${mergeable}" = "CONFLICTING" ]; then
  write_result "blocked" "PR #${pr}: conflict_blocked" "${pr}"
  post_check "blocked" "merge conflict" "${head_sha}"
  exit 1
fi

deadline=$((SECONDS + GATE_WAIT_SECONDS))
while true; do
  if ! checks_raw="$(gh pr checks "${pr}" --json name,state,completedAt,startedAt 2>/tmp/gh-pr-checks.err)"; then
    if [ "${SECONDS}" -ge "${deadline}" ]; then
      write_result "waiting" "PR #${pr}: could not read checks before timeout" "${pr}"
      post_check "waiting" "checks unreadable" "${head_sha}"
      exit 0
    fi
    sleep "${GATE_POLL_SECONDS}"
    continue
  fi

  bugbot="$(bugbot_state_from_checks "${checks_raw}")"
  gate_json="$(printf '%s' "${checks_raw}" | python3 -c '
import json,sys
sys.path.insert(0,"scripts/gitops")
from packager_logic import fast_gate_status, parse_required_checks
checks=json.load(sys.stdin)
import os
status,detail=fast_gate_status(checks, parse_required_checks(os.environ["REQUIRED_CHECKS"]))
print(json.dumps({"status":status,"detail":detail}))
')"
  gate_status="$(echo "${gate_json}" | jq -r .status)"
  gate_detail="$(echo "${gate_json}" | jq -r .detail)"

  if [ "${bugbot}" = "success" ] && [ "${gate_status}" = "success" ]; then
    if gh pr merge "${pr}" --squash --auto || gh pr merge "${pr}" --squash; then
      write_result "merged" "PR #${pr} merged at ${head_sha}" "${pr}"
      post_check "merged" "merged ${head_sha}" "${head_sha}"
      exit 0
    fi
    write_result "blocked" "PR #${pr}: gates green but merge failed (policy/conflict)" "${pr}"
    post_check "blocked" "merge failed" "${head_sha}"
    exit 1
  fi

  if [ "${bugbot}" = "not_success" ]; then
    write_result "blocked" "PR #${pr}: ${BUGBOT_SUCCESS_CHECK_NAME} not success" "${pr}"
    post_check "blocked" "Bugbot not success" "${head_sha}"
    exit 1
  fi
  if [ "${gate_status}" = "failed" ]; then
    write_result "blocked" "PR #${pr}: fast-gate failed (${gate_detail})" "${pr}"
    post_check "blocked" "fast-gate failed: ${gate_detail}" "${head_sha}"
    exit 1
  fi

  if [ "${SECONDS}" -ge "${deadline}" ]; then
    write_result "waiting" "PR #${pr}: still waiting (bugbot=${bugbot} gate=${gate_status}:${gate_detail})" "${pr}"
    post_check "waiting" "timeout waiting for gates" "${head_sha}"
    exit 0
  fi
  sleep "${GATE_POLL_SECONDS}"
done
