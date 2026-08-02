#!/usr/bin/env bash
# Shared allowlist for short-lived work branches (Packager + branch-source-policy).
# Sourced by other scripts. Do not execute directly for side effects.

# Allowed PR heads into development (must stay in sync with
# core/github/managed-workflows/branch-source-policy.yml).
is_allowed_work_branch() {
  local name="${1:-}"
  case "${name}" in
    issue/*|phase/*|feature/*|fix/*|chore/*|codex/*|cursor/*|antigravity/*|dependabot/*|dev/*)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

# Temporary promotion branches (staging target).
is_staging_promote_branch() {
  local name="${1:-}"
  case "${name}" in
    promote/staging/*) return 0 ;;
    *) return 1 ;;
  esac
}

# Temporary promotion branches (main target).
is_main_promote_branch() {
  local name="${1:-}"
  case "${name}" in
    promote/main/*) return 0 ;;
    *) return 1 ;;
  esac
}

allowed_work_branch_globs() {
  printf '%s\n' \
    'issue/*' 'phase/*' 'feature/*' 'fix/*' 'chore/*' \
    'codex/*' 'cursor/*' 'antigravity/*' 'dependabot/*' 'dev/*'
}
