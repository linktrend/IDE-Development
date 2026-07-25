#!/usr/bin/env bash
# Apply a repository ruleset so PRs into development require Bugbot + listed CI checks.
# Integrator then merges only when those gates are green.
#
# Usage:
#   ./scripts/apply-development-merge-ruleset.sh
#   ./scripts/apply-development-merge-ruleset.sh --repo linktrend/LiNKskills
#   ./scripts/apply-development-merge-ruleset.sh --repo linktrend/LiNKskills \
#     -- "Cursor Bugbot" "test" "Enforce allowed PR source branches"
#
# Defaults:
#   repo   = linktrend/IDE-Development (or GH_REPO)
#   checks = Cursor Bugbot + Verify IDE Development + Enforce allowed PR source branches

set -euo pipefail

REPO="${GH_REPO:-linktrend/IDE-Development}"
CHECKS=(
  "Cursor Bugbot"
  "Verify IDE Development"
  "Enforce allowed PR source branches"
)
CHECKS_SET=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --repo)
      [ "$#" -ge 2 ] || { echo "FAIL: --repo needs owner/name" >&2; exit 1; }
      REPO="$2"
      shift 2
      ;;
    --)
      shift
      CHECKS=("$@")
      CHECKS_SET=1
      break
      ;;
    -h|--help)
      sed -n '2,14p' "$0"
      exit 0
      ;;
    */*)
      if [[ "$1" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]]; then
        REPO="$1"
        shift
      else
        CHECKS=("$@")
        CHECKS_SET=1
        break
      fi
      ;;
    *)
      # Check names (may contain spaces) — replace defaults entirely only via explicit list.
      CHECKS=("$@")
      CHECKS_SET=1
      break
      ;;
  esac
done

# If caller passed check names without --repo, keep Cursor Bugbot unless they included it.
if [ "${CHECKS_SET}" -eq 1 ]; then
  has_bugbot=0
  for c in "${CHECKS[@]}"; do
    if [ "$c" = "Cursor Bugbot" ]; then
      has_bugbot=1
      break
    fi
  done
  if [ "${has_bugbot}" -eq 0 ]; then
    CHECKS=("Cursor Bugbot" "${CHECKS[@]}")
  fi
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
  existing_bypass="$(
    gh api "repos/${REPO}/rulesets/${existing_id}" --jq '.bypass_actors // []'
  )"
  body="$(echo "${body}" | jq --argjson bypass "${existing_bypass}" '.bypass_actors=$bypass')"
  echo "Updating ruleset id=${existing_id} (preserving bypass_actors)"
  echo "${body}" | gh api --method PUT "repos/${REPO}/rulesets/${existing_id}" --input -
else
  echo "Creating ruleset"
  echo "${body}" | gh api --method POST "repos/${REPO}/rulesets" --input -
fi

gh api --method PATCH "repos/${REPO}" -f allow_auto_merge=true >/dev/null
echo "allow_auto_merge: true"
echo "SUCCESS: development merge ruleset applied on ${REPO}"
