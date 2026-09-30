#!/usr/bin/env bash
set -euo pipefail

staged_files="$(git diff --cached --name-only)"
if [[ -z "${staged_files}" ]]; then
  exit 0
fi

blocked="$(printf '%s\n' "${staged_files}" | rg -n '\.(json|bin)$' || true)"
if [[ -n "${blocked}" ]]; then
  echo "[git-pre-commit] Commit blocked: staged .json/.bin files detected."
  echo "${blocked}"
  exit 1
fi

exit 0
