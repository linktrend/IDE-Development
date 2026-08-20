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
{"schemaVersion":1,"fastWorkflowName":"Linktrend Fast Checks","ciWorkflowName":"${name} CI","branchPolicyWorkflowName":"Branch Source Policy","bugbotCheckName":"Linktrend Review Gate","reviewGateCheckName":"Linktrend Review Gate","bugbotProviderCheckName":"Cursor Bugbot","runnerType":"github-hosted"}
JSON

  # Exercise the candidate package as an installed consumer, rather than
  # copying source scripts into a hand-made directory.
  python3 "$ROOT/scripts/ide-development.py" install --package "$ROOT" --target "$repo" --json >/dev/null
  python3 "$ROOT/scripts/ide-development.py" verify --package "$ROOT" --target "$repo" --json >/dev/null
  # Packaged hosted tests contain approved synthetic values.  Carry only the
  # declarations for the materialized test destinations into this disposable
  # consumer; never turn undeclared or realistic values into fixtures.
  python3 - "$ROOT" "$repo" <<'PY'
import json
import sys
from pathlib import Path

source_root, consumer_root = (Path(value) for value in sys.argv[1:3])
source_declaration = json.loads(
    (source_root / ".github/linktrend-secret-scan-fixtures.json").read_text(encoding="utf-8")
)
manifest = json.loads(
    (source_root / "core/managed-core/MANIFEST.json").read_text(encoding="utf-8")
)
destinations = {
    row["source"]: row["destination"]
    for row in manifest["files"]
    if isinstance(row.get("source"), str)
    and isinstance(row.get("destination"), str)
    and row["destination"].startswith(".ide-development/tests/")
}
fixtures = []
for fixture in source_declaration["fixtures"]:
    destination = destinations.get(fixture["path"])
    if destination is None:
        continue
    copied = dict(fixture)
    copied["path"] = destination
    fixtures.append(copied)
consumer_declaration = {
    "schemaVersion": source_declaration["schemaVersion"],
    "kind": source_declaration["kind"],
    "scannerPolicyVersion": source_declaration["scannerPolicyVersion"],
    "candidateTree": "0" * 40,
    "fixtures": fixtures,
}
declaration = consumer_root / ".github/linktrend-secret-scan-fixtures.json"
declaration.write_text(
    json.dumps(consumer_declaration, indent=2) + "\n",
    encoding="utf-8",
)
PY
  git -C "$repo" add -A
  python3 "$repo/scripts/gitops/generated_output_closure.py" --generate-fixtures
  git -C "$repo" add .github/linktrend-secret-scan-fixtures.json
  git -C "$repo" config user.email "consumer-matrix@example.invalid"
  git -C "$repo" config user.name "Consumer matrix"
  git -C "$repo" remote add origin "$repo/origin.git"
  git -C "$repo" add -A
  git -C "$repo" commit -qm "authoritative consumer baseline"
  python3 "$repo/scripts/gitops/generated_output_closure.py" --generate-fixtures
  git -C "$repo" add .github/linktrend-secret-scan-fixtures.json
  git -C "$repo" commit -qm "bind packaged fixture declaration"
  baseline_sha="$(git -C "$repo" rev-parse HEAD)"
  git -C "$repo" remote add fixture "$repo/fixture.git"
  git -C "$repo" update-ref refs/remotes/fixture/development "$baseline_sha"
  git -C "$repo" commit --allow-empty -qm "consumer candidate tip"
  baseline_ref="fixture/development"

  if git -C "$repo" rev-parse --verify origin/development^{commit} >/dev/null 2>&1; then
    echo "FAIL: shallow consumer fixture unexpectedly provided origin/development" >&2
    exit 1
  fi

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
  (cd "$repo" && LINKTREND_TARGET_BASELINE_SHA="$baseline_sha" LINKTREND_TARGET_BASELINE_REF="$baseline_ref" \
    python3 -c 'import os; from pathlib import Path; from scripts.gitops.generated_output_closure import candidate_diff_check; candidate_diff_check(Path.cwd(), environ=os.environ)' && \
    python3 scripts/gitops/run_delivery_profile.py fast)

  # Exact hosted Full command after checkout: the declared repository-owned
  # CI must have succeeded for this exact head. The fixture injects only the
  # GitHub API response, so the same managed discovery code is exercised.
  runs="{\"workflow_runs\":[{\"name\":\"Linktrend Fast Checks\",\"head_sha\":\"${head}\",\"conclusion\":\"success\"},{\"name\":\"${name} CI\",\"head_sha\":\"${head}\",\"conclusion\":\"success\"}]}"
  (cd "$repo" && LINKTREND_TARGET_BASELINE_SHA="$baseline_sha" LINKTREND_TARGET_BASELINE_REF="$baseline_ref" \
    python3 -c 'import os; from pathlib import Path; from scripts.gitops.generated_output_closure import candidate_diff_check; candidate_diff_check(Path.cwd(), environ=os.environ)' && \
    python3 scripts/gitops/run_delivery_profile.py full && \
    LINKTREND_ACTIONS_RUNS_JSON="$runs" python3 scripts/gitops/require_exact_ci_success.py \
      --repository "linktrend/${name}" --head "$head" --config-key fastWorkflowName && \
    LINKTREND_ACTIONS_RUNS_JSON="$runs" python3 scripts/gitops/require_exact_ci_success.py \
      --repository "linktrend/${name}" --head "$head")
done

# A real credential remains blocking even when the matrix's packaged-fixture
# declaration is present for another consumer.
actual="$TMP/actual-credential"; mkdir -p "$actual"
git -C "$actual" init -q -b development
git -C "$actual" config user.email "consumer-matrix@example.invalid"
git -C "$actual" config user.name "Consumer matrix"
printf 'token = "ghp_%s"\n' "$(printf '%*s' 36 '' | tr ' ' A)" >"$actual/credential.py"
git -C "$actual" add credential.py
git -C "$actual" commit -qm "actual credential regression vector"
if python3 "$ROOT/scripts/gitops/secret_scan.py" --repo "$actual" >/dev/null; then
  echo "FAIL: actual credential was not rejected by secret scan" >&2
  exit 1
fi

# The installer/sync upgrade path fills the sole historic omission only; blank
# or wrong explicit names remain fail-closed when exact workflow discovery runs.
legacy="$TMP/legacy-fast-omitted"; mkdir -p "$legacy/.github"
git -C "$legacy" init -q -b development
printf '%s\n' '{"schemaVersion":1,"ciWorkflowName":"Legacy CI","branchPolicyWorkflowName":"Branch Source Policy","bugbotCheckName":"Linktrend Review Gate","reviewGateCheckName":"Linktrend Review Gate","bugbotProviderCheckName":"Cursor Bugbot","runnerType":"github-hosted"}' >"$legacy/.github/linktrend-gitops-consumer.json"
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
printf '%s\n' '{"schemaVersion":1,"ciWorkflowName":"Legacy CI","branchPolicyWorkflowName":"Branch Source Policy","bugbotCheckName":"Linktrend Review Gate","reviewGateCheckName":"Linktrend Review Gate","bugbotProviderCheckName":"Cursor Bugbot","runnerType":"linktrend-private-macos-arm64"}' >"$private_legacy/.github/linktrend-gitops-consumer.json"
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
  printf '%s\n' '{"schemaVersion":1,"ciWorkflowName":"Upgrade CI","branchPolicyWorkflowName":"Branch Source Policy","bugbotCheckName":"Linktrend Review Gate","reviewGateCheckName":"Linktrend Review Gate","bugbotProviderCheckName":"Cursor Bugbot","runnerType":"github-hosted"}' >"$upgrade_repo/.github/linktrend-gitops-consumer.json"
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
  '{"schemaVersion":1,"fastWorkflowName":"","ciWorkflowName":"CI","branchPolicyWorkflowName":"Branch Source Policy","bugbotCheckName":"Linktrend Review Gate","reviewGateCheckName":"Linktrend Review Gate","bugbotProviderCheckName":"Cursor Bugbot","runnerType":"github-hosted"}' \
  '{"schemaVersion":1,"fastWorkflowName":"Other Fast","ciWorkflowName":"CI","branchPolicyWorkflowName":"Branch Source Policy","bugbotCheckName":"Linktrend Review Gate","reviewGateCheckName":"Linktrend Review Gate","bugbotProviderCheckName":"Cursor Bugbot","runnerType":"github-hosted"}' \
  '{"schemaVersion":1,"fastWorkflowName":"Linktrend Fast Checks","ciWorkflowName":"","branchPolicyWorkflowName":"Branch Source Policy","bugbotCheckName":"Linktrend Review Gate","reviewGateCheckName":"Linktrend Review Gate","bugbotProviderCheckName":"Cursor Bugbot","runnerType":"github-hosted"}'; do
  invalid_repo="$TMP/invalid-${RANDOM}"; mkdir -p "$invalid_repo/.github"
  git -C "$invalid_repo" init -q -b development
  printf '%s\n' "$invalid" >"$invalid_repo/.github/linktrend-gitops-consumer.json"
  if python3 "$ROOT/scripts/ide-development.py" install --package "$ROOT" --target "$invalid_repo" --json >/dev/null 2>&1; then
    echo "FAIL: installer accepted invalid workflow contract" >&2; exit 1
  fi
done
echo "PASS: installed nine-consumer Fast/Full profile and exact CI matrix"
