#!/usr/bin/env bash
# Apply a repository ruleset so PRs into development require Bugbot + listed CI checks.
# Integrator then merges only when those gates are green.
#
# Usage:
#   ./scripts/apply-development-merge-ruleset.sh [owner/repo] [check context...]
#
# Defaults:
#   repo   = linktrend/IDE-Development (or GH_REPO)
#   checks = Cursor Bugbot + Verify IDE Development + Enforce allowed PR source branches
#
# Example for a consumer whose CI job has a different name:
#   ./scripts/apply-development-merge-ruleset.sh linktrend/LiNKskills \
#     "Cursor Bugbot" "test" "Enforce allowed PR source branches"

set -euo pipefail

REPO_INPUT="${1:-}"
if [ -n "${REPO_INPUT}" ] && [[ "${REPO_INPUT}" == */* ]]; then
  REPO="${REPO_INPUT}"
  shift || true
else
  REPO="${GH_REPO:-linktrend/IDE-Development}"
fi

if [ "$#" -gt 0 ]; then
  CHECKS=("$@")
else
  CHECKS=(
    "Cursor Bugbot"
    "Verify IDE Development"
    "Enforce allowed PR source branches"
  )
fi

RULESET_NAME="development-autonomous-merge"

required_checks_json="$(
  printf '%s\n' "${CHECKS[@]}" | jq -R . | jq -s 'map({context: .})'
)"

body="$(jq -n \
  --arg name "${RULESET_NAME}" \
  --argjson checks "${required_checks_json}" \
  '{
    name: $name,
    target: "branch",
    enforcement: "active",
    conditions: {
      ref_name: {
        include: ["refs/heads/development"],
        exclude: []
      }
    },
    rules: [
      {
        type: "required_status_checks",
        parameters: {
          strict_required_status_checks_policy: true,
          do_not_enforce_on_create: false,
          required_status_checks: $checks
        }
      }
    ],
    bypass_actors: []
  }')"

echo "Repo: ${REPO}"
echo "Ruleset: ${RULESET_NAME}"
echo "Required checks:"
printf '  - %s\n' "${CHECKS[@]}"

existing_id="$(
  gh api "repos/${REPO}/rulesets" --jq \
    ".[] | select(.name==\"${RULESET_NAME}\") | .id" 2>/dev/null | head -1 || true
)"

if [ -n "${existing_id}" ]; then
  echo "Updating ruleset id=${existing_id}"
  echo "${body}" | gh api --method PUT "repos/${REPO}/rulesets/${existing_id}" --input -
else
  echo "Creating ruleset"
  echo "${body}" | gh api --method POST "repos/${REPO}/rulesets" --input -
fi

gh api --method PATCH "repos/${REPO}" -f allow_auto_merge=true >/dev/null
echo "allow_auto_merge: true"
echo "SUCCESS: development merge ruleset applied on ${REPO}"
