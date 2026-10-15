#!/usr/bin/env bash
# Compatibility protection wrapper for genuine CI checks; Bugbot is retired.
# Integrator then merges only when those gates are green.
#
# Compatibility wrapper around scripts/gitops/repository_protection.py
# (development branch only). Invoking this script still applies (historical behavior).
# Prefer scripts/manage-repository-protections.sh for plan/verify across all three branches.
#
# Usage:
#   ./scripts/apply-development-merge-ruleset.sh
#   ./scripts/apply-development-merge-ruleset.sh --repo linktrend/LiNKskills
#   ./scripts/apply-development-merge-ruleset.sh --repo linktrend/LiNKskills \
#     -- "Linktrend Review Gate" "test" "Linktrend Branch Source Policy"
#
# Defaults:
#   repo   = linktrend/IDE-Development (or GH_REPO)
#   checks = Linktrend Review Gate + Verify IDE Development + Linktrend Branch Source Policy

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO="${GH_REPO:-linktrend/IDE-Development}"
CHECKS=(
  "Verify IDE Development"
  "Linktrend Branch Source Policy"
)
CHECKS_SET=0
FIXTURE_DIR=""
DRY_RUN=0

while [ "$#" -gt 0 ]; do
  case "$1" in
    --repo)
      [ "$#" -ge 2 ] || { echo "FAIL: --repo needs owner/name" >&2; exit 1; }
      REPO="$2"
      shift 2
      ;;
    --fixture-dir)
      [ "$#" -ge 2 ] || { echo "FAIL: --fixture-dir needs a path" >&2; exit 1; }
      FIXTURE_DIR="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --)
      shift
      CHECKS=("$@")
      CHECKS_SET=1
      break
      ;;
    -h|--help)
      sed -n '2,18p' "$0"
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

# Retired review contexts cannot become required through legacy overrides.
for check in "${CHECKS[@]}"; do
  case "$check" in
    "Cursor Bugbot"|"Linktrend Review Gate")
      echo "FAIL: retired review context must be removed through approved protection migration" >&2
      exit 2 ;;
  esac
done

echo "Repo: ${REPO}"
echo "Ruleset: development-autonomous-merge"
echo "Required checks:"
printf '  - %s\n' "${CHECKS[@]}"

COMMON=(
  --repo "${REPO}"
  --branches development
  --development-checks "${CHECKS[@]}"
)
if [ -n "${FIXTURE_DIR}" ]; then
  COMMON+=(--fixture-dir "${FIXTURE_DIR}")
fi

if [ "${DRY_RUN}" -eq 1 ]; then
  echo "Dry-run: planning only (no mutation)"
  # Mode first so --development-checks nargs=* cannot swallow it.
  python3 "${ROOT}/scripts/gitops/repository_protection.py" plan "${COMMON[@]}"
  exit 0
fi

# Historical behavior: this wrapper applies when invoked.
python3 "${ROOT}/scripts/gitops/repository_protection.py" apply --apply "${COMMON[@]}"
echo "SUCCESS: development merge ruleset applied on ${REPO}"
