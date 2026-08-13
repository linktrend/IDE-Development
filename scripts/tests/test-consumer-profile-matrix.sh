#!/usr/bin/env bash
# Authoritative disposable portability matrix for every managed-core consumer.
# It installs the candidate package and runs the same profile/CI-discovery
# commands used by the hosted Fast and Full workflow steps.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TMP="$(mktemp -d "${TMPDIR:-/tmp}/consumer-profile-matrix.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

consumers=(LiNKplatform LiNKbrain LiNKsites LiNKdeveloper LiNKskills openclaw_prime LiNKlibraries LiNKautowork LiNKtrading-codebase)
head="0123456789012345678901234567890123456789"
for name in "${consumers[@]}"; do
  repo="$TMP/$name"
  mkdir -p "$repo/.github"
  git -C "$repo" init -q -b development
  cat >"$repo/.github/linktrend-gitops-consumer.json" <<JSON
{"schemaVersion":1,"ciWorkflowName":"${name} CI","branchPolicyWorkflowName":"Branch Source Policy","bugbotCheckName":"Cursor Bugbot","runnerType":"github-hosted"}
JSON

  # Exercise the candidate package as an installed consumer, rather than
  # copying source scripts into a hand-made directory.
  python3 "$ROOT/scripts/ide-development.py" install --package "$ROOT" --target "$repo" --json >/dev/null
  python3 "$ROOT/scripts/ide-development.py" verify --package "$ROOT" --target "$repo" --json >/dev/null

  python3 - "$repo" "${name} CI" <<'PY'
import json, sys
from pathlib import Path
root, ci = Path(sys.argv[1]), sys.argv[2]
config = json.loads((root / ".github/linktrend-gitops-consumer.json").read_text())
assert config["ciWorkflowName"] == ci and config["runnerType"] == "github-hosted"
assert not (root / "scripts/tests/test_candidate_lifecycle.py").exists()
PY

  # Exact hosted Fast command after checkout: profile is argv-only and never
  # imports IDE-source-only modules from a system path.
  (cd "$repo" && git diff --check && python3 scripts/gitops/run_delivery_profile.py fast)

  # Exact hosted Full command after checkout: the declared repository-owned
  # CI must have succeeded for this exact head. The fixture injects only the
  # GitHub API response, so the same managed discovery code is exercised.
  runs="{\"workflow_runs\":[{\"name\":\"${name} CI\",\"head_sha\":\"${head}\",\"conclusion\":\"success\"}]}"
  (cd "$repo" && git diff --check && python3 scripts/gitops/run_delivery_profile.py full && \
    LINKTREND_ACTIONS_RUNS_JSON="$runs" python3 scripts/gitops/require_exact_ci_success.py \
      --repository "linktrend/${name}" --head "$head")
done

# Missing delivery mode, malformed consumer CI configuration, and a stale CI
# run each fail closed before a promotion can use the profile.
bad="$TMP/missing-config"; mkdir -p "$bad/scripts/gitops"
cp "$ROOT/scripts/gitops/run_delivery_profile.py" "$bad/scripts/gitops/"
if (cd "$bad" && python3 scripts/gitops/run_delivery_profile.py fast) >/dev/null 2>&1; then
  echo "FAIL: missing consumer profile configuration was accepted" >&2; exit 1
fi
mkdir -p "$bad/.github"
cp "$ROOT/scripts/gitops/require_exact_ci_success.py" "$bad/scripts/gitops/"
printf '%s\n' '{"ciWorkflowName":"Bad CI"}' >"$bad/.github/linktrend-gitops-consumer.json"
if (cd "$bad" && LINKTREND_ACTIONS_RUNS_JSON='{"workflow_runs":[]}' \
  python3 scripts/gitops/require_exact_ci_success.py --repository linktrend/bad --head "$head") >/dev/null 2>&1; then
  echo "FAIL: missing exact-head consumer CI was accepted" >&2; exit 1
fi
echo "PASS: installed nine-consumer Fast/Full profile and exact CI matrix"
