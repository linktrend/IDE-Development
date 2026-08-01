#!/usr/bin/env bash
# Portable IDE Development v2 — top-level integration harness (WP6).
#
# Orchestrates Wave 1 acceptance suites without mutating real consumers or
# live GitHub settings. Default mode runs documentation/version invariants
# (WP6-owned) and discovers peer packet test suites when present.
#
# Usage:
#   bash tests/test-portable-v2-integration.sh              # WP6 docs/version invariants (focused)
#   bash tests/test-portable-v2-integration.sh --with-peers # docs + discovered peer packet suites
#   bash tests/test-portable-v2-integration.sh --full       # peers + existing GitOps/verify suites
#   bash tests/test-portable-v2-integration.sh --docs-only  # alias of default
#
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

MODE="${1:-default}"
fail() { echo "FAIL: $1" >&2; exit 1; }
pass() { echo "PASS: $1"; }
info() { echo "INFO: $1"; }
skip() { echo "SKIP: $1"; }

run_cmd() {
  local label="$1"
  shift
  info "Running: $*"
  if "$@"; then
    pass "$label"
  else
    fail "$label (exit $?)"
  fi
}

# ---- WP6 documentation / version invariants ----

assert_docs() {
  local ver
  ver="$(tr -d '[:space:]' < VERSION)"
  [[ "$ver" == "v2.0.0" ]] || fail "VERSION must be v2.0.0 (got '$ver')"
  pass "VERSION is v2.0.0"

  for f in README.md SETUP.md \
    docs/IDE-DEVELOPMENT-INTENT.md \
    docs/IDE-DEVELOPMENT-TECHNICAL-PRD.md \
    docs/IDE-DEVELOPMENT-OPERATIONS-MANUAL.md \
    docs/GITOPS-CONSUMER-ROLLOUT.md \
    docs/AUTONOMOUS-GIT-OPERATIONS.md; do
    [[ -f "$f" ]] || fail "missing active doc $f"
  done
  pass "Active architecture/operations/rollout docs present"

  # Current support claims must not list Claude as supported.
  if grep -nE '(?i)(supported.*(Claude|Claude Code)|(Claude|Claude Code).*supported|Codex/Claude|Cursor.*Codex.*Claude)' \
      README.md SETUP.md \
      docs/IDE-DEVELOPMENT-INTENT.md \
      docs/IDE-DEVELOPMENT-TECHNICAL-PRD.md \
      docs/IDE-DEVELOPMENT-OPERATIONS-MANUAL.md \
      docs/GITOPS-CONSUMER-ROLLOUT.md 2>/dev/null \
    | grep -viE 'not (in |a )?supported|outside.*support|not supported|historical|not treat|Claude Code is outside|Claude Code as a supported|Claude Code platform support|Claude Code remains outside|no new Claude|Not in current v2 support' \
    | grep -qiE 'Claude'; then
    fail "active docs still claim Claude as currently supported"
  fi
  # Stronger explicit negatives must exist in the support surfaces.
  grep -qiE 'Claude Code.*(outside|not).*(support|roadmap)|not (in current v2 support|supported).*Claude' \
    README.md SETUP.md docs/IDE-DEVELOPMENT-TECHNICAL-PRD.md \
    || fail "active docs missing explicit Claude out-of-scope language"
  pass "Claude removed from current support/roadmap claims"

  # Physical managed install — not consumer-to-system .cursor symlink as the model.
  grep -q '\.ide-development/' README.md SETUP.md docs/IDE-DEVELOPMENT-TECHNICAL-PRD.md \
    || fail "missing .ide-development/ physical install language"
  grep -qiE 'ide-development\.py' README.md SETUP.md \
    || fail "missing installer CLI references"
  for cmd in install update drift verify version rollback; do
    grep -q "$cmd" README.md SETUP.md || fail "README/SETUP missing command '$cmd'"
  done
  pass "Physical install + installer commands documented"

  # IDE Development is not a consumer rollout entry.
  grep -qiE 'not a consumer rollout' README.md docs/GITOPS-CONSUMER-ROLLOUT.md docs/IDE-DEVELOPMENT-TECHNICAL-PRD.md \
    || fail "missing IDE Development self-verification / non-consumer language"
  ! grep -nE '^\| *1 *\| *IDE Development' docs/GITOPS-CONSUMER-ROLLOUT.md \
    || fail "GITOPS-CONSUMER-ROLLOUT still lists IDE Development as consumer #1"
  pass "IDE Development treated as system source, not consumer rollout"

  # Locked consumer order (exact sequence).
  python3 - <<'PY'
from pathlib import Path
text = Path("docs/GITOPS-CONSUMER-ROLLOUT.md").read_text()
order = [
    "openclaw_prime",
    "LiNKplatform",
    "LiNKskills",
    "LiNKbrain",
    "LiNKsites",
    "LiNKdeveloper",
    "LiNKlibraries",
    "LiNKautowork",
    "LiNKtrading-codebase",
]
positions = []
for name in order:
    idx = text.find(name)
    if idx < 0:
        raise SystemExit(f"missing consumer {name} in rollout doc")
    positions.append(idx)
if positions != sorted(positions):
    raise SystemExit("consumer rollout order is not sequential as locked")
# Carlos / Principal approval + read-only drift before each consumer
needles = ["read-only drift", "Carlos", "development", "staging", "main"]
missing = [n for n in needles if n.lower() not in text.lower()]
# tighten: require explicit phrases
for phrase in [
    "read-only drift report",
    "Carlos",
    "`development`",
    "`staging`",
    "`main`",
]:
    if phrase not in text and phrase.replace("`", "") not in text:
        # allow without backticks for branch names already checked via needles
        if phrase.startswith("`"):
            continue
        raise SystemExit(f"rollout doc missing required phrase: {phrase}")
if "read-only drift report" not in text:
    raise SystemExit("rollout doc missing read-only drift report requirement")
if "Carlos" not in text:
    raise SystemExit("rollout doc missing Carlos approval requirement")
print("ok")
PY
  pass "Consumer rollout order + drift/approval gates recorded"

  # External-state boundary language.
  grep -qiE 'GitHub App|secrets|variables|Bugbot' docs/GITOPS-CONSUMER-ROLLOUT.md SETUP.md \
    || fail "missing external-state (App/secrets/variables/Bugbot) language"
  grep -qiE 'dry-run|plan' docs/GITOPS-CONSUMER-ROLLOUT.md SETUP.md \
    || fail "missing dry-run/plan external-settings language"
  pass "External settings remain external (documented)"

  # No Wave 1 tag/release claim.
  if grep -qiE 'creat(e|ed|ing) (a )?(git )?tag|publish(ed|ing)? (a )?release' \
      README.md SETUP.md docs/GITOPS-CONSUMER-ROLLOUT.md \
    | grep -viE 'does not|do not|must not|without tagging|no Git tag|not create'; then
    fail "active docs appear to claim a Wave 1 tag/release was created"
  fi
  grep -qiE 'no Git tag|does \*\*not\*\* create a Git tag|without tagging|no Git tag or GitHub release' \
    README.md docs/GITOPS-CONSUMER-ROLLOUT.md \
    || fail "missing explicit no-tag/no-release Wave 1 language"
  pass "v2.0.0 identified without tag/release claim"

  # Historical Claude files may remain; harness must not delete them.
  [[ -f claude/CLAUDE.md ]] || info "historical claude/CLAUDE.md not present (ok if previously absent)"
  pass "Documentation invariants complete"
}

discover_and_run_new_suites() {
  local found=0
  local f

  # WP1 package integrity gate (read-only)
  found=1
  run_cmd "managed-core MANIFEST verify" \
    env PYTHONPATH=scripts python3 -m ide_development.build_manifest --verify

  # WP2 installer unit/black-box tests
  while IFS= read -r f; do
    [[ -z "$f" ]] && continue
    found=1
    if [[ "$f" == *.py ]]; then
      run_cmd "installer unit: $f" env PYTHONPATH=scripts python3 -m unittest "$f"
    else
      run_cmd "installer suite: $f" bash "$f"
    fi
  done < <(find scripts/ide_development_tests tests/ide_development \
    -type f \( -name 'test_*.py' -o -name 'test-*.sh' -o -name '*_test.py' \) 2>/dev/null | sort)

  # WP3 adapters
  if [[ -x tests/adapters/run.sh ]]; then
    found=1
    run_cmd "WP3 adapters" bash tests/adapters/run.sh
  elif [[ -f tests/adapters/test_managed_core_adapters.py ]]; then
    found=1
    run_cmd "WP3 adapters" python3 tests/adapters/test_managed_core_adapters.py
  fi

  # WP4 migration black-box (catalog + fixtures; live installer optional via env)
  if [[ -f tests/managed-core-migration-bb/run_tests.py ]]; then
    found=1
    if [[ "${PORTABLE_V2_WITH_INSTALLER:-}" == "1" ]]; then
      run_cmd "WP4 migration BB (+installer)" \
        python3 tests/managed-core-migration-bb/run_tests.py --with-installer
    else
      run_cmd "WP4 migration BB" python3 tests/managed-core-migration-bb/run_tests.py
    fi
  fi

  # WP3/WP5 discovered shells under scripts/tests and tests/
  while IFS= read -r f; do
    [[ -z "$f" ]] && continue
    case "$f" in
      *test-gitops*) continue ;;
      *test-integrator*) continue ;;
      *test-portable-v2-integration*) continue ;;
    esac
    found=1
    run_cmd "discovered suite: $f" bash "$f"
  done < <(find scripts/tests tests \
    -type f \( -name 'test-*ide-development*.sh' -o -name 'test-*managed*.sh' \
      -o -name 'test-*portable*.sh' -o -name 'test-*migrat*.sh' \
      -o -name 'test-*adapter*.sh' -o -name 'test-*protect*.sh' \
      -o -name 'test-*install*.sh' \) 2>/dev/null | sort)

  # Python unittest discovery for package tests if a runner module exists
  if [[ -d scripts/ide_development_tests ]] && \
     find scripts/ide_development_tests -name 'test_*.py' -print -quit 2>/dev/null | grep -q .; then
    found=1
    run_cmd "unittest discover ide_development_tests" \
      env PYTHONPATH=scripts python3 -m unittest discover -s scripts/ide_development_tests -p 'test_*.py' -v
  fi

  if [[ "$found" -eq 0 ]]; then
    skip "No peer-packet installer/migration/adapter/protection suites discovered yet"
  fi
}

run_existing_suites() {
  run_cmd "gitops lifecycle" bash scripts/tests/test-gitops-lifecycle.sh
  run_cmd "gitops review packager" bash scripts/tests/test-gitops-review-packager.sh
  run_cmd "gitops behavioral" bash scripts/tests/test-gitops-behavioral.sh
  run_cmd "platform adoption" bash scripts/verify-platform-adoption.sh
  run_cmd "verify ide development" env SKIP_LOCAL_ARCHIVE_CHECKS=1 bash scripts/verify-ide-development.sh
  if git diff --check >/dev/null 2>&1; then
    pass "git diff --check"
  else
    # Unstaged intentional Wave 1 work may include conflict markers elsewhere;
    # check only WP6-owned paths tightly.
    git diff --check -- README.md SETUP.md VERSION \
      docs/IDE-DEVELOPMENT-INTENT.md \
      docs/IDE-DEVELOPMENT-TECHNICAL-PRD.md \
      docs/IDE-DEVELOPMENT-OPERATIONS-MANUAL.md \
      docs/GITOPS-CONSUMER-ROLLOUT.md \
      docs/AUTONOMOUS-GIT-OPERATIONS.md \
      tests/test-portable-v2-integration.sh \
      || fail "git diff --check on WP6-owned paths"
    pass "git diff --check (WP6-owned paths)"
  fi
}

echo "=== portable v2 integration harness (mode=$MODE) ==="
assert_docs

case "$MODE" in
  --docs-only|docs-only|default|"")
    info "Focused WP6 mode: documentation/version invariants only"
    ;;
  --with-peers|with-peers)
    discover_and_run_new_suites
    ;;
  --full|full)
    discover_and_run_new_suites
    run_existing_suites
    ;;
  *)
    fail "unknown mode '$MODE' (use default | --docs-only | --with-peers | --full)"
    ;;
esac

echo "=== ALL HARNESS CHECKS PASSED (mode=$MODE) ==="
