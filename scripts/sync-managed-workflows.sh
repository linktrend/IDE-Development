#!/usr/bin/env bash
# Sync managed GitHub workflow templates from IDE Development into a target repo.
# Does not overwrite consumer-specific ci.yml or unrelated workflows.
# Stdlib/bash only. Exit 0 on success; non-zero on failure.

set -euo pipefail

SYSTEM_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE_DIR="${SYSTEM_ROOT}/core/github/managed-workflows"

MANAGED_FILES=(
  "branch-source-policy.yml"
  "linktrend-cleanup-merged.yml"
  "linktrend-promote-main.yml"
)

# Synced only when the target declares a deploy target; a caller for a
# reusable workflow without a target would fail every push to main.
DEPLOY_FILE="linktrend-deploy.yml"
DEPLOY_TARGET_REL="deploy/target.json"

# v2 workflows retired in v3. Removed only when the file still equals a
# published v2 rendering for this consumer (scripts/ide_development/retired_workflows.py);
# a locally edited copy is reported as a conflict and kept.
RETIRED_FILES=(
  "linktrend-development-to-staging.yml"
  "linktrend-integrator-merge.yml"
  "linktrend-repair-observer.yml"
  "linktrend-review-gate.yml"
  "linktrend-review-packager.yml"
  "linktrend-review-ready-publisher.yml"
  "linktrend-staging-to-main.yml"
)

fail() {
  echo "FAIL: $1" >&2
  exit 1
}

info() {
  echo "$1"
}

usage() {
  cat <<EOF
Usage: $(basename "$0") <repo-path> [--config PATH] [--orchestration-mode MODE] [--dry-run]

Copy managed GitHub workflow templates into <repo-path>/.github/workflows/.
Never overwrites ci.yml. Idempotent when files already match.

linktrend-deploy.yml is synced only when <repo-path>/deploy/target.json exists.
Retired v2 workflows are removed only when they still match a published v2
rendering; a locally modified copy is kept and reported (exit 11).

Workflow templates may contain __LINKTREND_* placeholders. They are rendered
from <repo-path>/.github/linktrend-gitops-consumer.json unless --config is set.
MODE is local-coordinator or github-actions. When omitted, the v2 delivery
configuration is consulted, then the consumer config, then github-actions.

Examples:
  $(basename "$0") /Users/you/Projects/SomeProductRepo
  $(basename "$0") . --config .github/linktrend-gitops-consumer.json --dry-run
EOF
}

DRY_RUN=0
TARGET_INPUT=""
CONFIG_INPUT=""
ORCHESTRATION_MODE=""

while [ $# -gt 0 ]; do
  case "$1" in
    -h|--help)
      usage
      exit 0
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --config)
      [ $# -ge 2 ] || fail "--config requires a path"
      CONFIG_INPUT="$2"
      shift 2
      ;;
    --config=*)
      CONFIG_INPUT="${1#--config=}"
      shift
      ;;
    --orchestration-mode)
      [ $# -ge 2 ] || fail "--orchestration-mode requires a value"
      ORCHESTRATION_MODE="$2"
      shift 2
      ;;
    --orchestration-mode=*)
      ORCHESTRATION_MODE="${1#--orchestration-mode=}"
      shift
      ;;
    *)
      if [ -z "$TARGET_INPUT" ]; then
        TARGET_INPUT="$1"
        shift
      else
        fail "Unexpected argument: $1"
      fi
      ;;
  esac
done

if [ -z "$TARGET_INPUT" ]; then
  usage >&2
  exit 1
fi

[ -d "$TARGET_INPUT" ] || fail "Target path is not a directory: $TARGET_INPUT"
[ -d "$TEMPLATE_DIR" ] || fail "Template directory missing: $TEMPLATE_DIR"

TARGET_REPO="$(cd "$TARGET_INPUT" && pwd -P)"
DEST_DIR="${TARGET_REPO}/.github/workflows"
if [ -n "$CONFIG_INPUT" ]; then
  [ -f "$CONFIG_INPUT" ] || fail "Consumer config missing: $CONFIG_INPUT"
  CONFIG_PATH="$(cd "$(dirname "$CONFIG_INPUT")" && pwd -P)/$(basename "$CONFIG_INPUT")"
else
  CONFIG_PATH="${TARGET_REPO}/.github/linktrend-gitops-consumer.json"
fi

if [ -z "${ORCHESTRATION_MODE}" ]; then
  ORCHESTRATION_MODE="$({
    python3 - "${TARGET_REPO}" "${CONFIG_PATH}" <<'PY'
import json
import sys
from pathlib import Path

target = Path(sys.argv[1])
consumer = Path(sys.argv[2])
for path in (target / ".github" / "linktrend-delivery-mode.json", consumer):
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        continue
    if isinstance(value, dict) and value.get("orchestrationMode"):
        print(str(value["orchestrationMode"]).strip())
        break
else:
    print("github-actions")
PY
  })"
fi
case "${ORCHESTRATION_MODE}" in
  local-coordinator|github-actions) ;;
  *) fail "unsupported orchestration mode: ${ORCHESTRATION_MODE} (expected local-coordinator or github-actions)" ;;
esac

info "System repository: $SYSTEM_ROOT"
info "Target repository: $TARGET_REPO"
info "Template source: $TEMPLATE_DIR"
info "Consumer config: $CONFIG_PATH"
info "Orchestration profile: $ORCHESTRATION_MODE"

[ -f "$CONFIG_PATH" ] || fail "Consumer config missing: $CONFIG_PATH (create .github/linktrend-gitops-consumer.json or pass --config)"

removal_conflict() {
  echo "CONFLICT: $1; no managed workflows were removed" >&2
}

workflow_directory_is_safe() {
  local github_dir="${TARGET_REPO}/.github"
  local workflows_dir="${github_dir}/workflows"
  local physical_dir=""

  if [ -L "$github_dir" ] || [ -L "$workflows_dir" ]; then
    removal_conflict ".github or .github/workflows is a symlink"
    return 1
  fi

  if [ -d "$workflows_dir" ]; then
    physical_dir="$(cd -P -- "$workflows_dir" && pwd -P)" || {
      removal_conflict "unable to resolve the physical .github/workflows path"
      return 1
    }
  else
    physical_dir="$(cd -P -- "$github_dir" && pwd -P)" || {
      removal_conflict "unable to resolve the physical .github path"
      return 1
    }
  fi

  case "$physical_dir" in
    "$TARGET_REPO"|"$TARGET_REPO"/*) return 0 ;;
    *)
      removal_conflict "physical workflow path is outside target repository"
      return 1
      ;;
  esac
}

if ! workflow_directory_is_safe; then
  info ""
  info "Managed workflow sync: CONFLICT (unsafe workflow destination; no removals attempted)"
  info "Target: $TARGET_REPO"
  exit 11
fi

removal_file_is_safe() {
  local dest="$1"
  local file="$2"
  local physical_parent=""

  if [ -L "$dest" ]; then
    echo "CONFLICT: ${file} is a symlink; not removed" >&2
    return 1
  fi
  physical_parent="$(cd -P -- "$(dirname -- "$dest")" && pwd -P)" || {
    echo "CONFLICT: ${file} physical parent cannot be resolved; not removed" >&2
    return 1
  }
  case "$physical_parent" in
    "$TARGET_REPO"|"$TARGET_REPO"/*) return 0 ;;
    *)
      echo "CONFLICT: ${file} physical path is outside target repository; not removed" >&2
      return 1
      ;;
  esac
}

# ``fastWorkflowName`` became a receipt-bound contract after early consumers
# had already received the config file.  Normalize only a missing key to the
# fixed managed Fast workflow name; never infer or overwrite a repository's
# declared CI name.  An explicit blank/unsafe/wrong value is rejected below.
if [ "$DRY_RUN" -eq 0 ]; then
  python3 - "$CONFIG_PATH" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
try:
    value = json.loads(path.read_text(encoding="utf-8"))
except Exception as exc:
    raise SystemExit(f"invalid consumer config {path}: {exc}") from exc
if not isinstance(value, dict):
    raise SystemExit(f"invalid consumer config {path}: expected object")
if "fastWorkflowName" not in value:
    value["fastWorkflowName"] = "Linktrend Fast Checks"
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: normalized required fastWorkflowName in {path}")
PY
fi

if [ "$DRY_RUN" -eq 0 ]; then
  mkdir -p "$DEST_DIR"
fi

TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/linktrend-workflows.XXXXXX")"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

render_template() {
  local src="$1"
  local out="$2"
  python3 - "$CONFIG_PATH" "$src" "$out" "$ORCHESTRATION_MODE" <<'PY'
import json
import re
import sys
from pathlib import Path

config_path = Path(sys.argv[1])
src = Path(sys.argv[2])
out = Path(sys.argv[3])

try:
    cfg = json.loads(config_path.read_text(encoding="utf-8"))
except Exception as exc:
    raise SystemExit(f"invalid consumer config {config_path}: {exc}")

required = {
    "schemaVersion": int,
    "fastWorkflowName": str,
    "ciWorkflowName": str,
    "branchPolicyWorkflowName": str,
    "bugbotCheckName": str,
}
for key, typ in required.items():
    if key not in cfg:
        raise SystemExit(f"consumer config missing required field: {key}")
    if typ is int:
        try:
            value = int(cfg[key])
        except (TypeError, ValueError):
            raise SystemExit(f"consumer config field must be integer: {key}")
        if value != 1:
            raise SystemExit(f"unsupported consumer config schemaVersion: {value}")
        continue
    value = str(cfg[key]).strip()
    if not value:
        raise SystemExit(f"consumer config field must be non-empty: {key}")
    if "__LINKTREND_" in value:
        raise SystemExit(f"consumer config field still contains placeholder: {key}")
    # Fail closed on names that would corrupt YAML or GitHub Expressions
    forbidden = {
        "'", '"', "`", "$", "{", "}", "\\", "\n", "\r", "\t",
        "<", ">", "|", "&", ";", "(", ")", "[", "]", "*", "!", "?", "#",
    }
    if any(ch in forbidden for ch in value) or value != value.strip():
        raise SystemExit(
            f"consumer config field contains unsafe characters for workflow YAML/expressions: {key}"
        )
    if len(value) > 100:
        raise SystemExit(f"consumer config field too long: {key}")
if cfg["fastWorkflowName"] != "Linktrend Fast Checks":
    raise SystemExit("consumer config fastWorkflowName must equal Linktrend Fast Checks")

runner_type = str(cfg.get("runnerType", "github-hosted")).strip()
runner_types = {
    "github-hosted": {
        "privileged": "ubuntu-24.04-arm",
        "untrusted": "ubuntu-24.04-arm",
    },
}
if runner_type not in runner_types:
    raise SystemExit(
        "unsupported consumer config runnerType: "
        f"{runner_type} (expected one of: {', '.join(sorted(runner_types))})"
    )

text = src.read_text(encoding="utf-8")
rendered = text
rendered = rendered.replace("__LINKTREND_CI_WORKFLOW_NAME__", str(cfg["ciWorkflowName"]).strip())
rendered = rendered.replace(
    "__LINKTREND_BRANCH_POLICY_WORKFLOW_NAME__",
    str(cfg["branchPolicyWorkflowName"]).strip(),
)
review_gate_name = str(cfg.get("reviewGateCheckName") or cfg.get("bugbotCheckName") or "").strip()
if review_gate_name == "Cursor Bugbot":
    raise SystemExit("consumer config bugbotCheckName/reviewGateCheckName must not remain Cursor Bugbot")
rendered = rendered.replace(
    "__LINKTREND_UNTRUSTED_RUNS_ON__", runner_types[runner_type]["untrusted"]
)
rendered = rendered.replace("__LINKTREND_RUNS_ON__", runner_types[runner_type]["privileged"])
if "__LINKTREND_" in rendered:
    raise SystemExit(f"unrendered __LINKTREND_ placeholder remains in {src}")

out.write_text(rendered, encoding="utf-8")
PY
}

copied=0
unchanged=0

SYNC_FILES=("${MANAGED_FILES[@]}")
if [ -f "${TARGET_REPO}/${DEPLOY_TARGET_REL}" ]; then
  info "Deploy target: ${DEPLOY_TARGET_REL} present; syncing ${DEPLOY_FILE}"
  SYNC_FILES+=("${DEPLOY_FILE}")
else
  info "Deploy target: ${DEPLOY_TARGET_REL} absent; ${DEPLOY_FILE} not synced"
fi

for file in "${SYNC_FILES[@]}"; do
  src="${TEMPLATE_DIR}/${file}"
  dest="${DEST_DIR}/${file}"
  rendered="${TMP_DIR}/${file}"
  [ -f "$src" ] || fail "Missing template: $src"
  render_template "$src" "$rendered"

  if grep -q '__LINKTREND_' "$rendered"; then
    fail "Rendered workflow still contains placeholder: $file"
  fi

  if [ -f "$dest" ] && cmp -s "$rendered" "$dest"; then
    info "PASS: unchanged $file"
    unchanged=$((unchanged + 1))
    continue
  fi

  if [ "$DRY_RUN" -eq 1 ]; then
    if [ -f "$dest" ]; then
      info "DRY-RUN: would update $file"
    else
      info "DRY-RUN: would create $file"
    fi
    copied=$((copied + 1))
    continue
  fi

  restore_mode=""
  if [ -f "$dest" ] && [ ! -w "$dest" ]; then
    restore_mode="$(stat -c '%a' "$dest" 2>/dev/null || stat -f '%OLp' "$dest")"
    chmod u+w "$dest" || fail "Unable to grant write for read-only managed workflow: $file"
  fi
  cp "$rendered" "$dest"
  if [ -n "$restore_mode" ]; then
    chmod "$restore_mode" "$dest" || fail "Unable to restore read-only mode for $file"
  fi
  info "PASS: synced $file"
  copied=$((copied + 1))
done

deploy_conflict=0
deploy_dest="${DEST_DIR}/${DEPLOY_FILE}"
if [ ! -f "${TARGET_REPO}/${DEPLOY_TARGET_REL}" ] && [ -f "$deploy_dest" ]; then
  if ! removal_file_is_safe "$deploy_dest" "$DEPLOY_FILE"; then
    deploy_conflict=1
  elif cmp -s "${TEMPLATE_DIR}/${DEPLOY_FILE}" "$deploy_dest"; then
    if [ "$DRY_RUN" -eq 1 ]; then
      info "DRY-RUN: would remove ${DEPLOY_FILE} (no ${DEPLOY_TARGET_REL})"
    else
      rm -f "$deploy_dest"
      info "PASS: removed ${DEPLOY_FILE} (no ${DEPLOY_TARGET_REL})"
    fi
  else
    echo "CONFLICT: ${DEPLOY_FILE} is locally modified but ${DEPLOY_TARGET_REL} is absent; not removed" >&2
    deploy_conflict=1
  fi
fi

retired_args=(--target "$TARGET_REPO" --package "$SYSTEM_ROOT")
if [ "$DRY_RUN" -eq 1 ]; then
  retired_args+=(--dry-run)
fi
retired_status=0
python3 "${SYSTEM_ROOT}/scripts/ide_development/retired_workflows.py" "${retired_args[@]}" || retired_status=$?
case "$retired_status" in
  0) ;;
  11) ;;
  *) fail "retired workflow check failed (exit ${retired_status})" ;;
esac

if [ "$retired_status" -eq 11 ] || [ "$deploy_conflict" -eq 1 ]; then
  info ""
  info "Managed workflow sync: CONFLICT (managed files synced; modified retired files kept)"
  info "Target: $TARGET_REPO"
  exit 11
fi

info ""
info "Managed workflow sync: SUCCESS"
info "Target: $TARGET_REPO"
info "Synced/updated: $copied"
info "Already matched: $unchanged"
info "Next: complete core/checklists/BUGBOT-INHERITANCE.md for this repo"
info "Next: ensure the repo has a v3 cloud orchestrator (docs/AUTONOMOUS-GIT-OPERATIONS.md)"
exit 0
