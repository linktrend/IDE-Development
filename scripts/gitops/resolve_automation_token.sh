#!/usr/bin/env bash
# Resolve automation token: prefer GitHub App installation token; fail closed.
# Never prints secret material. Sets AUTOMATION_TOKEN and AUTOMATION_TOKEN_SOURCE.
#
# Required for autonomous PR create/update/merge that must trigger further workflows:
#   vars.LINKTREND_GITOPS_APP_ID
#   secrets.LINKTREND_GITOPS_APP_PRIVATE_KEY
#
# See docs/contracts/GITHUB-APP-GITOPS-CREDENTIALS.md
set -euo pipefail

AUTOMATION_TOKEN=""
AUTOMATION_TOKEN_SOURCE="none"
AUTOMATION_CREDENTIALS_STATUS="missing"

APP_ID="${LINKTREND_GITOPS_APP_ID:-${LINKTREND_GITOPS_APP_ID_VAR:-}}"
# Private key must come from env already injected by Actions secrets — never from repo files.
APP_KEY="${LINKTREND_GITOPS_APP_PRIVATE_KEY:-}"

if [ -n "${APP_ID}" ] && [ -n "${APP_KEY}" ]; then
  # Prefer official action output when caller already created a token file/env.
  if [ -n "${LINKTREND_APP_TOKEN:-}" ]; then
    AUTOMATION_TOKEN="${LINKTREND_APP_TOKEN}"
    AUTOMATION_TOKEN_SOURCE="github_app"
    AUTOMATION_CREDENTIALS_STATUS="configured"
  else
    echo "AUTOMATION_CREDENTIALS_STATUS=missing_runtime_token" >&2
    echo "App ID present but LINKTREND_APP_TOKEN not injected by workflow step." >&2
    AUTOMATION_CREDENTIALS_STATUS="missing_runtime_token"
  fi
else
  AUTOMATION_CREDENTIALS_STATUS="missing"
fi

# Optional diagnostic-only fallback explicitly disallowed for autonomous PR mutation.
ALLOW_GITHUB_TOKEN_FALLBACK="${LINKTREND_ALLOW_GITHUB_TOKEN_FALLBACK:-0}"
if [ "${AUTOMATION_TOKEN_SOURCE}" = "none" ] && [ "${ALLOW_GITHUB_TOKEN_FALLBACK}" = "1" ]; then
  if [ -n "${GITHUB_TOKEN:-}" ] || [ -n "${GH_TOKEN:-}" ]; then
    AUTOMATION_TOKEN="${LINKTREND_APP_TOKEN:-${GH_TOKEN:-${GITHUB_TOKEN:-}}}"
    AUTOMATION_TOKEN_SOURCE="github_token_fallback_non_autonomous"
    AUTOMATION_CREDENTIALS_STATUS="fallback_non_autonomous"
  fi
fi

export AUTOMATION_TOKEN
export AUTOMATION_TOKEN_SOURCE
export AUTOMATION_CREDENTIALS_STATUS

echo "AUTOMATION_TOKEN_SOURCE=${AUTOMATION_TOKEN_SOURCE}"
echo "AUTOMATION_CREDENTIALS_STATUS=${AUTOMATION_CREDENTIALS_STATUS}"

if [ "${REQUIRE_APP_TOKEN:-1}" = "1" ]; then
  if [ "${AUTOMATION_TOKEN_SOURCE}" != "github_app" ] || [ -z "${AUTOMATION_TOKEN}" ]; then
    echo "automation_credentials_blocked" >&2
    exit 78  # EX_CONFIG — fail closed for autonomous path
  fi
fi
