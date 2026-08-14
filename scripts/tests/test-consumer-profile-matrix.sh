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
{"schemaVersion":1,"fastWorkflowName":"Linktrend Fast Checks","ciWorkflowName":"${name} CI","branchPolicyWorkflowName":"Branch Source Policy","bugbotCheckName":"Cursor Bugbot","runnerType":"github-hosted"}
JSON

  # Exercise the candidate package as an installed consumer, rather than
  # copying source scripts into a hand-made directory.
  python3 "$ROOT/scripts/ide-development.py" install --package "$ROOT" --target "$repo" --json >/dev/null
  python3 "$ROOT/scripts/ide-development.py" verify --package "$ROOT" --target "$repo" --json >/dev/null

  # Every installed consumer contract must retain both declared workflow
  # names.  This prevents a Full-only rollout discovery after publication.

  python3 - "$repo" "${name} CI" <<'PY'
import json, sys
from pathlib import Path
root, ci = Path(sys.argv[1]), sys.argv[2]
config = json.loads((root / ".github/linktrend-gitops-consumer.json").read_text())
assert config["fastWorkflowName"] == "Linktrend Fast Checks"
assert config["ciWorkflowName"] == ci and config["runnerType"] == "github-hosted"
assert not (root / "scripts/tests/test_candidate_lifecycle.py").exists()
PY

  # Exact hosted Fast command after checkout: profile is argv-only and never
  # imports IDE-source-only modules from a system path.
  (cd "$repo" && git diff --check && python3 scripts/gitops/run_delivery_profile.py fast)

  # Exact hosted Full command after checkout: the declared repository-owned
  # CI must have succeeded for this exact head. The fixture injects only the
  # GitHub API response, so the same managed discovery code is exercised.
  runs="{\"workflow_runs\":[{\"name\":\"Linktrend Fast Checks\",\"head_sha\":\"${head}\",\"conclusion\":\"success\"},{\"name\":\"${name} CI\",\"head_sha\":\"${head}\",\"conclusion\":\"success\"}]}"
  (cd "$repo" && git diff --check && python3 scripts/gitops/run_delivery_profile.py full && \
    LINKTREND_ACTIONS_RUNS_JSON="$runs" python3 scripts/gitops/require_exact_ci_success.py \
      --repository "linktrend/${name}" --head "$head" --config-key fastWorkflowName && \
    LINKTREND_ACTIONS_RUNS_JSON="$runs" python3 scripts/gitops/require_exact_ci_success.py \
      --repository "linktrend/${name}" --head "$head")
done

# The installer/sync upgrade path fills the sole historic omission only; blank
# or wrong explicit names remain fail-closed when exact workflow discovery runs.
legacy="$TMP/legacy-fast-omitted"; mkdir -p "$legacy/.github"
git -C "$legacy" init -q -b development
printf '%s\n' '{"schemaVersion":1,"ciWorkflowName":"Legacy CI","branchPolicyWorkflowName":"Branch Source Policy","bugbotCheckName":"Cursor Bugbot","runnerType":"github-hosted"}' >"$legacy/.github/linktrend-gitops-consumer.json"
python3 "$ROOT/scripts/ide-development.py" install --package "$ROOT" --target "$legacy" --json >/dev/null
python3 - "$legacy/.github/linktrend-gitops-consumer.json" <<'PY'
import json, sys
cfg = json.load(open(sys.argv[1], encoding="utf-8"))
assert cfg["fastWorkflowName"] == "Linktrend Fast Checks"
assert cfg["ciWorkflowName"] == "Legacy CI"
PY

# The one historic private runner declaration is a managed delivery migration,
# not a consumer choice. The installer must upgrade it with the missing Fast
# key, while arbitrary runner values remain rejected below.
private_legacy="$TMP/legacy-private-runner"; mkdir -p "$private_legacy/.github"
git -C "$private_legacy" init -q -b development
printf '%s\n' '{"schemaVersion":1,"ciWorkflowName":"Legacy CI","branchPolicyWorkflowName":"Branch Source Policy","bugbotCheckName":"Cursor Bugbot","runnerType":"linktrend-private-macos-arm64"}' >"$private_legacy/.github/linktrend-gitops-consumer.json"
python3 "$ROOT/scripts/ide-development.py" install --package "$ROOT" --target "$private_legacy" --json >/dev/null
python3 - "$private_legacy/.github/linktrend-gitops-consumer.json" <<'PY'
import json, sys
cfg = json.load(open(sys.argv[1], encoding="utf-8"))
assert cfg["fastWorkflowName"] == "Linktrend Fast Checks"
assert cfg["runnerType"] == "github-hosted"
assert cfg["ciWorkflowName"] == "Legacy CI"
PY

# Exercise real upgrades from both published legacy package layouts.  They
# intentionally omit the later receipt-bound Fast declaration; current install
# must add it while retaining each repository-owned CI declaration.
for legacy_ref in cea9660bb507dec665d020dcf105ac1df67d8edc 2c81d37c0a7ab948dc9d9bf08b0ba917d3949d38; do
  legacy_source="$TMP/source-${legacy_ref:0:7}"
  mkdir -p "$legacy_source"
  git -C "$ROOT" archive "$legacy_ref" | tar -x -C "$legacy_source"
  upgrade_repo="$TMP/upgrade-${legacy_ref:0:7}"
  mkdir -p "$upgrade_repo/.github"
  git -C "$upgrade_repo" init -q -b development
  printf '%s\n' '{"schemaVersion":1,"ciWorkflowName":"Upgrade CI","branchPolicyWorkflowName":"Branch Source Policy","bugbotCheckName":"Cursor Bugbot","runnerType":"github-hosted"}' >"$upgrade_repo/.github/linktrend-gitops-consumer.json"
  python3 "$legacy_source/scripts/ide-development.py" install --package "$legacy_source" --target "$upgrade_repo" --json >/dev/null
  python3 "$ROOT/scripts/ide-development.py" update --package "$ROOT" --target "$upgrade_repo" --json >/dev/null
  python3 - "$upgrade_repo/.github/linktrend-gitops-consumer.json" <<'PY'
import json, sys
cfg = json.load(open(sys.argv[1], encoding="utf-8"))
assert cfg["fastWorkflowName"] == "Linktrend Fast Checks"
assert cfg["ciWorkflowName"] == "Upgrade CI"
PY
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
printf '%s\n' '{"fastWorkflowName":"Bad Fast","ciWorkflowName":"Bad CI"}' >"$bad/.github/linktrend-gitops-consumer.json"
if (cd "$bad" && LINKTREND_ACTIONS_RUNS_JSON='{"workflow_runs":[]}' \
  python3 scripts/gitops/require_exact_ci_success.py --repository linktrend/bad --head "$head") >/dev/null 2>&1; then
  echo "FAIL: missing exact-head consumer CI was accepted" >&2; exit 1
fi

# The installer must reject explicit bad workflow declarations rather than
# overwrite them during an upgrade.
for invalid in \
  '{"schemaVersion":1,"fastWorkflowName":"","ciWorkflowName":"CI","branchPolicyWorkflowName":"Branch Source Policy","bugbotCheckName":"Cursor Bugbot","runnerType":"github-hosted"}' \
  '{"schemaVersion":1,"fastWorkflowName":"Other Fast","ciWorkflowName":"CI","branchPolicyWorkflowName":"Branch Source Policy","bugbotCheckName":"Cursor Bugbot","runnerType":"github-hosted"}' \
  '{"schemaVersion":1,"fastWorkflowName":"Linktrend Fast Checks","ciWorkflowName":"","branchPolicyWorkflowName":"Branch Source Policy","bugbotCheckName":"Cursor Bugbot","runnerType":"github-hosted"}'; do
  invalid_repo="$TMP/invalid-${RANDOM}"; mkdir -p "$invalid_repo/.github"
  git -C "$invalid_repo" init -q -b development
  printf '%s\n' "$invalid" >"$invalid_repo/.github/linktrend-gitops-consumer.json"
  if python3 "$ROOT/scripts/ide-development.py" install --package "$ROOT" --target "$invalid_repo" --json >/dev/null 2>&1; then
    echo "FAIL: installer accepted invalid workflow contract" >&2; exit 1
  fi
done
echo "PASS: installed nine-consumer Fast/Full profile and exact CI matrix"
