#!/usr/bin/env bash
# Verify platform adoption via a temp consumer repo (no real 8-consumer wiring).
# Runs the real wire-repo.sh installer with a non-default CI workflow name.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
fail() { echo "FAIL: $1" >&2; exit 1; }
pass() { echo "PASS: $1"; }

required=(
  ".cursor/rules/02-autonomous-ship-pull.mdc"
  "core/commands/agentsetup.md"
  "core/commands/agentcomply.md"
  "codex/AGENTS.md"
  "chatgpt/AGENTS.md"
  "docs/contracts/AGENT-COMPLETION.md"
  "docs/contracts/REPAIR-DISPATCHER.md"
  "docs/contracts/ACTIONS-COST-CONTROLS.md"
  "docs/contracts/LISA-LOCAL-CLEANUP-HANDOFF.md"
  "scripts/gitops/create_issue_branch.py"
  "scripts/gitops/completion_gate.py"
  "scripts/gitops/repair_task.py"
  "scripts/gitops/repair_observer.py"
  "scripts/wire-repo.sh"
  "core/github/managed-workflows/linktrend-cleanup-merged.yml"
  "core/github/managed-workflows/linktrend-repair-observer.yml"
  "core/github/managed-runtime/MANIFEST.json"
  "scripts/sync-managed-runtime.sh"
  "scripts/sync-agents-managed-section.sh"
  ".github/linktrend-gitops-consumer.json"
)

for f in "${required[@]}"; do
  [ -e "$f" ] || fail "missing $f"
done
pass "Required entrypoints and contracts present"

for f in chatgpt/AGENTS.md codex/AGENTS.md .cursor/rules/02-autonomous-ship-pull.mdc core/commands/agentcomply.md; do
  grep -q 'Review Ready\|review-ready\|review_ready' "$f" || fail "$f missing Review Ready language"
  if grep -qiE 'Open or update (a )?PR|open a PR targeting development' "$f"; then
    fail "$f still instructs implementer to open PR"
  fi
done
pass "Platform docs: Review Ready present; no implementer Open-PR instruction"

grep -q 'Lisa ACP Repair Dispatcher\|repair task' .cursor/rules/02-autonomous-ship-pull.mdc \
  || fail "ship-pull rule missing Lisa ACP Repair Dispatcher language"
if grep -nE 'prefer-incoming' .cursor/rules/02-autonomous-ship-pull.mdc docs/AUTONOMOUS-GIT-OPERATIONS.md \
  | grep -viE 'No prefer-incoming|no prefer-incoming|Never.*prefer-incoming|Must not|do not'; then
  fail "active prefer-incoming instruction"
fi
pass "Repair dispatcher language; no prefer-incoming instruction"

# ---- Temp consumer: real wire-repo.sh with non-default CI name ----
TMP="$(mktemp -d "${TMPDIR:-/tmp}/verify-platform-adoption.XXXXXX")"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

CONSUMER="${TMP}/consumer"
mkdir -p "${CONSUMER}"
(
  cd "$CONSUMER"
  git init -q -b development
  git config user.email t@example.com
  git config user.name t
  echo base >README.md
  git add README.md
  git commit -q -m "chore: base"
)
CUSTOM_MARK="CONSUMER_CUSTOM_TEXT_DO_NOT_WIPE_$$"
cat >"${CONSUMER}/AGENTS.md" <<EOF
# Consumer AGENTS

${CUSTOM_MARK}

Consumer-specific policies live here.
EOF
mkdir -p "${CONSUMER}/.github/workflows" "${CONSUMER}/.cursor/rules"
# Pre-existing consumer-owned cursor surfaces must be preserved
echo "# consumer owned rule" >"${CONSUMER}/.cursor/rules/99-consumer-owned.mdc"
mkdir -p "${CONSUMER}/.cursor/commands" "${CONSUMER}/.cursor/skills/custom-owned"
echo "# consumer owned command" >"${CONSUMER}/.cursor/commands/99-consumer-owned.md"
echo "# consumer owned skill" >"${CONSUMER}/.cursor/skills/custom-owned/SKILL.md"
cat >"${CONSUMER}/.github/workflows/ci.yml" <<'EOF'
name: Consumer CI
on: [push]
jobs:
  verify:
    name: Verify Consumer
    runs-on: ubuntu-latest
    steps:
      - run: echo ok
EOF

# Real installer (not a simplified imitation)
chmod +x "$ROOT/scripts/wire-repo.sh"
bash "$ROOT/scripts/wire-repo.sh" "$CONSUMER" \
  --ci-workflow-name "Consumer CI" \
  --branch-policy-workflow-name "Branch Source Policy" \
  --bugbot-check-name "Cursor Bugbot"

# Config committed path
[ -f "${CONSUMER}/.github/linktrend-gitops-consumer.json" ] || fail "missing consumer gitops config"
grep -q '"ciWorkflowName": "Consumer CI"' "${CONSUMER}/.github/linktrend-gitops-consumer.json" \
  || fail "consumer config missing Consumer CI"

# Rendered observer must contain Consumer CI literally; no placeholders
OBS="${CONSUMER}/.github/workflows/linktrend-repair-observer.yml"
[ -f "$OBS" ] || fail "missing installed repair observer"
grep -q 'Consumer CI' "$OBS" || fail "installed observer missing Consumer CI"
! grep -q '__LINKTREND_' "$OBS" || fail "installed observer still has placeholders"
python3 - "$OBS" <<'PY'
from pathlib import Path
import sys
text = Path(sys.argv[1]).read_text()
assert "Consumer CI" in text
assert "- Consumer CI" in text
print("ok")
PY
pass "Non-default Consumer CI rendered into installed workflows"

# Unsafe workflow names must be rejected (quotes, expressions, newlines, placeholders)
BAD="${TMP}/bad-consumer"
mkdir -p "${BAD}/.github"
cp "${CONSUMER}/.github/linktrend-gitops-consumer.json" "${BAD}/.github/"
python3 - "$ROOT" "$BAD" <<'PY'
import json, subprocess, sys
from pathlib import Path
root, bad = Path(sys.argv[1]), Path(sys.argv[2])
cfg_path = bad / ".github/linktrend-gitops-consumer.json"
base = json.loads(cfg_path.read_text())
cases = [
    ("quote", 'Bad"CI'),
    ("expression", "CI${{ github.token }}"),
    ("newline", "CI\nEvil"),
    ("placeholder", "__LINKTREND_CI_WORKFLOW_NAME__"),
]
for label, value in cases:
    cfg = dict(base)
    cfg["ciWorkflowName"] = value
    cfg_path.write_text(json.dumps(cfg, indent=2) + "\n")
    r = subprocess.run(
        ["bash", str(root / "scripts/sync-managed-workflows.sh"), str(bad)],
        capture_output=True,
        text=True,
    )
    if r.returncode == 0:
        raise SystemExit(f"unsafe name should be rejected: {label}")
    blob = (r.stdout or "") + (r.stderr or "")
    if not any(k in blob.lower() for k in ("unsafe", "placeholder", "too long")):
        raise SystemExit(f"rejection message missing for {label}: {blob}")
print("ok")
PY
pass "Unsafe consumer workflow names rejected"

# Confirm every scripts/ path referenced by installed linktrend-*.yml exists
missing=0
while IFS= read -r yml; do
  while IFS= read -r spath; do
    [ -n "$spath" ] || continue
    spath="${spath%/}"
    if [ ! -e "${CONSUMER}/${spath}" ]; then
      echo "MISSING in consumer: $spath (from $(basename "$yml"))" >&2
      missing=$((missing + 1))
    fi
  done < <(
    grep -vE '^[[:space:]]*#' "$yml" \
      | grep -oE 'scripts/[A-Za-z0-9_./-]+' \
      | sort -u
  )
done < <(find "${CONSUMER}/.github/workflows" -name 'linktrend-*.yml' -print)
[ "$missing" -eq 0 ] || fail "managed workflows reference missing scripts ($missing)"
pass "All scripts/ paths from linktrend-*.yml exist in consumer"

# Physical Cursor entrypoints — agentsetup/agentcomply resolvable without IDE Development
[ ! -L "${CONSUMER}/.cursor" ] || fail "consumer .cursor must not be a symlink"
for rel in \
  ".cursor/rules/cursor-gitops-bootstrap.mdc" \
  ".cursor/rules/linktrend-git-branching.mdc" \
  ".cursor/commands/agentsetup.md" \
  ".cursor/commands/agentcomply.md" \
  ".cursor/skills/agentsetup/SKILL.md" \
  ".cursor/skills/agentcomply/SKILL.md" \
  "scripts/gitops/create_issue_branch.py" \
  "scripts/gitops/completion_gate.py"; do
  [ -f "${CONSUMER}/${rel}" ] || fail "missing managed entrypoint: $rel"
  [ ! -L "${CONSUMER}/${rel}" ] || fail "entrypoint must be regular file: $rel"
done
# Commands point at installed skills; skills point at installed scripts
grep -q '\.cursor/skills/agentsetup/SKILL.md' "${CONSUMER}/.cursor/commands/agentsetup.md" \
  || fail "agentsetup command missing skill pointer"
grep -q '\.cursor/skills/agentcomply/SKILL.md' "${CONSUMER}/.cursor/commands/agentcomply.md" \
  || fail "agentcomply command missing skill pointer"
grep -q 'scripts/gitops/create_issue_branch.py' "${CONSUMER}/.cursor/skills/agentsetup/SKILL.md" \
  || fail "agentsetup skill missing create_issue_branch"
grep -q 'scripts/gitops/create_issue_branch.py' "${CONSUMER}/.cursor/skills/agentcomply/SKILL.md" \
  || fail "agentcomply skill missing create_issue_branch"
# No installed instruction may refer to a missing consumer-relative path that it claims is local
python3 - "$CONSUMER" <<'PY'
from pathlib import Path
import re, sys
root = Path(sys.argv[1])
texts = []
for p in [
    root/".cursor/commands/agentsetup.md",
    root/".cursor/commands/agentcomply.md",
    root/".cursor/skills/agentsetup/SKILL.md",
    root/".cursor/skills/agentcomply/SKILL.md",
    root/"AGENTS.md",
]:
    texts.append((p, p.read_text(encoding="utf-8")))
missing = []
for p, text in texts:
    for m in re.finditer(r'`((?:\.cursor|scripts)/[^`]+)`', text):
        rel = m.group(1)
        if not (root / rel).exists():
            missing.append(f"{p.name}:{rel}")
if missing:
    raise SystemExit("missing referenced paths: " + ", ".join(missing))
print("ok")
PY
# Codex/ChatGPT via root AGENTS
grep -q 'agentsetup' "${CONSUMER}/AGENTS.md" || fail "AGENTS missing agentsetup"
grep -q 'agentcomply' "${CONSUMER}/AGENTS.md" || fail "AGENTS missing agentcomply"
grep -q 'create_issue_branch.py' "${CONSUMER}/AGENTS.md" || fail "AGENTS missing create_issue_branch"
grep -q 'linktrend-gitops-consumer.json' "${CONSUMER}/AGENTS.md" \
  || fail "AGENTS still omits consumer JSON config for workflow names"
! grep -q 'LINKTREND_CI_WORKFLOW_NAME.*(default' "${CONSUMER}/AGENTS.md" \
  || fail "AGENTS still claims workflow wake names are Actions variables defaults"
[ -f "${CONSUMER}/.cursor/rules/99-consumer-owned.mdc" ] || fail "consumer-owned cursor rule wiped"
[ -f "${CONSUMER}/.cursor/commands/99-consumer-owned.md" ] || fail "consumer-owned command wiped"
[ -f "${CONSUMER}/.cursor/skills/custom-owned/SKILL.md" ] || fail "consumer-owned skill wiped"
pass "agentsetup/agentcomply installed; AGENTS equivalent; consumer-owned preserved"

# Prove usable without IDE Development source directory dependency
python3 - "$CONSUMER" "$ROOT" <<'PY'
from pathlib import Path
import sys
consumer = Path(sys.argv[1]).resolve()
root = Path(sys.argv[2]).resolve()
for rel in [
    ".cursor/commands/agentsetup.md",
    ".cursor/skills/agentsetup/SKILL.md",
    ".cursor/commands/agentcomply.md",
    ".cursor/skills/agentcomply/SKILL.md",
]:
    p = (consumer / rel).resolve()
    assert p.is_file() and not p.is_symlink()
    assert root not in p.parents
print("ok")
PY
pass "Installed entrypoints independent of IDE Development path"

# AGENTS markers + consumer text preserved
grep -q 'BEGIN LINKTREND-IDE-MANAGED' "${CONSUMER}/AGENTS.md" || fail "AGENTS missing BEGIN marker"
grep -q 'END LINKTREND-IDE-MANAGED' "${CONSUMER}/AGENTS.md" || fail "AGENTS missing END marker"
grep -q "$CUSTOM_MARK" "${CONSUMER}/AGENTS.md" || fail "AGENTS lost consumer custom text"
pass "AGENTS.md has IDE markers and preserves consumer text"

# actionlint installed / rendered workflows (ignore SC2129)
if command -v actionlint >/dev/null 2>&1; then
  set +e
  actionlint_out="$(actionlint "${CONSUMER}/.github/workflows/"*.yml 2>&1)"
  al_ec=$?
  set -e
  filtered="$(printf '%s\n' "$actionlint_out" | grep -E '\.yml:[0-9]+:[0-9]+:' | grep -v 'SC2129' || true)"
  if [ -n "$(printf '%s' "$filtered" | tr -d '[:space:]')" ]; then
    echo "$filtered" >&2
    fail "actionlint reported errors"
  fi
  pass "actionlint on installed workflows (SC2129 ignored)"
else
  pass "actionlint not installed; skipped (workflows present)"
fi

# Idempotent second real wire (config exists — no CLI flags)
RULE="${CONSUMER}/.cursor/rules/cursor-gitops-bootstrap.mdc"
before="$(cksum "$RULE" | awk '{print $1" "$2}')"
bash "$ROOT/scripts/wire-repo.sh" "$CONSUMER" >/dev/null
after="$(cksum "$RULE" | awk '{print $1" "$2}')"
[ "$before" = "$after" ] || fail "second wire-repo changed bootstrap checksum unexpectedly"
grep -q "$CUSTOM_MARK" "${CONSUMER}/AGENTS.md" || fail "second wire wiped consumer AGENTS text"
[ -f "${CONSUMER}/.cursor/rules/99-consumer-owned.mdc" ] || fail "second wire wiped consumer-owned rule"
[ -f "${CONSUMER}/.cursor/commands/99-consumer-owned.md" ] || fail "second wire wiped consumer-owned command"
[ ! -L "${CONSUMER}/.cursor" ] || fail "second wire reintroduced .cursor symlink"
pass "Second wire-repo.sh idempotent; consumer-owned files preserved"

echo "verify-platform-adoption: OK"
