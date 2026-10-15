#!/usr/bin/env bash
# Sync managed GitHub workflow templates from IDE Development into a target repo.
# Does not overwrite consumer-specific ci.yml or unrelated workflows.
# Stdlib/bash only. Exit 0 on success; non-zero on failure.

set -euo pipefail

SYSTEM_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMPLATE_DIR="${SYSTEM_ROOT}/core/github/managed-workflows"

MANAGED_FILES=(
  "branch-source-policy.yml"
  "linktrend-review-packager.yml"
  "linktrend-review-ready-publisher.yml"
  "linktrend-development-to-staging.yml"
  "linktrend-staging-to-main.yml"
  "linktrend-integrator-merge.yml"
  "linktrend-cleanup-merged.yml"
  "linktrend-repair-observer.yml"
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

For one guarded workflow only:
  $(basename "$0") <repo-path> --only-workflow linktrend-integrator-merge.yml \\
    --expected-source-sha256 SHA256 --expected-target-sha256 SHA256 [--dry-run]

For the fixed LiNKpublish overlay only:
  $(basename "$0") <repo-path> --only-workflow linktrend-integrator-merge.yml \\
    --source-variant linktrend-publish --expected-source-sha256 SHA256 \\
    --expected-target-sha256 SHA256 [--dry-run]

For the fixed OpenClaw overlays only:
  $(basename "$0") <repo-path> --only-workflow <supported-workflow> \
    --source-variant linktrend-openclaw --expected-source-sha256 SHA256 \
    --expected-target-sha256 SHA256 [--dry-run]
  Supported: linktrend-integrator-merge.yml, linktrend-repair-observer.yml,
  linktrend-review-gate.yml (fixed retirement marker removes only this file).
  Each operation is separate and hash guarded; use retained Git preimages
  for a separately verified scoped restore. No automatic multi-file rollback.

Copy managed GitHub workflow templates into <repo-path>/.github/workflows/.
Never overwrites ci.yml. Idempotent when files already match.

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
ONLY_WORKFLOW=""
EXPECTED_SOURCE_SHA256=""
EXPECTED_TARGET_SHA256=""
SOURCE_VARIANT=""

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
    --only-workflow)
      [ $# -ge 2 ] || fail "--only-workflow requires a filename"
      ONLY_WORKFLOW="$2"
      shift 2
      ;;
    --expected-source-sha256)
      [ $# -ge 2 ] || fail "--expected-source-sha256 requires a SHA-256 digest"
      EXPECTED_SOURCE_SHA256="$2"
      shift 2
      ;;
    --expected-target-sha256)
      [ $# -ge 2 ] || fail "--expected-target-sha256 requires a SHA-256 digest"
      EXPECTED_TARGET_SHA256="$2"
      shift 2
      ;;
    --source-variant)
      [ $# -ge 2 ] || fail "--source-variant requires a fixed variant name"
      SOURCE_VARIANT="$2"
      shift 2
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

# A narrowly authorized materialization path for workflows that are not
# represented by the consumer's installed MANIFEST. Keep it independent from
# the broad renderer: no config reads/normalization, profile inference, mkdir,
# or writes outside the one guarded destination file.
if [ -n "$ONLY_WORKFLOW" ] || [ -n "$EXPECTED_SOURCE_SHA256" ] || [ -n "$EXPECTED_TARGET_SHA256" ] || [ -n "$SOURCE_VARIANT" ]; then
  case "$ONLY_WORKFLOW" in
    linktrend-integrator-merge.yml|linktrend-repair-observer.yml|linktrend-review-gate.yml) ;;
    *) fail "unsupported --only-workflow" ;;
  esac
  [ -z "$CONFIG_INPUT" ] || fail "--config is not supported with --only-workflow"
  [ -z "$ORCHESTRATION_MODE" ] || fail "--orchestration-mode is not supported with --only-workflow"
  case "$SOURCE_VARIANT" in
    ""|linktrend-publish|linktrend-openclaw) ;;
    *) fail "unsupported --source-variant: $SOURCE_VARIANT" ;;
  esac
  python3 - "$SYSTEM_ROOT" "$TARGET_REPO" "$ONLY_WORKFLOW" "$SOURCE_VARIANT" "$EXPECTED_SOURCE_SHA256" "$EXPECTED_TARGET_SHA256" "$DRY_RUN" <<'PY'
import hashlib
import os
import re
import stat
import sys
import tempfile
from pathlib import Path

system_root = Path(sys.argv[1])
target_root = Path(sys.argv[2])
name, variant, expected_source, expected_target, dry_run = sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7] == "1"
remove_operation = False
if variant != "linktrend-openclaw" and name != "linktrend-integrator-merge.yml":
    raise SystemExit("FAIL: unsupported scoped workflow")
if variant == "":
    source = system_root / "core" / "github" / "managed-workflows" / name
elif variant == "linktrend-publish":
    source = system_root / "core" / "github" / "managed-workflows" / "repository-overlays" / "linktrend-LiNKpublish" / "Full.yml"
    if expected_source != "7bb95f1c82f5777572590150f936791002d13fb70bb64252e30fadcc3a4d8d23":
        raise SystemExit("FAIL: linktrend-publish source SHA-256 must match the reviewed fixed overlay")
    if expected_target != "5eb82e65c68ae825015beedaeeb1ee7e49ec34677514e55c58ed97ca3b1cb525":
        raise SystemExit("FAIL: linktrend-publish target SHA-256 must match the reviewed Publish Full preimage")
elif variant == "linktrend-openclaw":
    overlays = {
        "linktrend-integrator-merge.yml": ("Full.yml", "47b8a9b911da549e55c7edea80d45755bc34b757972627155c65fb9568e3e8c7", "f8fe760a115424d27984c042112390c52993971dcb675b8d2b307115093c7a37", False),
        "linktrend-repair-observer.yml": ("RepairObserver.yml", "76d604485c21f16c2e96d387c53ea7f1f01e35b82bf363369eff553bdcbaee35", "c82a719f88f913cdb4184199d53c82c2849b8d926e110497447a965ad0ae06fa", False),
        "linktrend-review-gate.yml": ("ReviewGate.removed", "5afc95e4c8ea08acfed9374968a9d8832f00c4db7b4ccd9e91f4e37f14eb1f4b", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855", True),
    }
    if name not in overlays:
        raise SystemExit("FAIL: unsupported OpenClaw workflow")
    source_name, fixed_target, fixed_source, remove_operation = overlays[name]
    source = system_root / "core" / "github" / "managed-workflows" / "repository-overlays" / "linktrend-openclaw_prime" / source_name
    if expected_source != fixed_source or expected_target != fixed_target:
        raise SystemExit("FAIL: linktrend-openclaw digests must match the reviewed fixed overlay and preimage")
else:
    raise SystemExit("FAIL: unsupported source variant")
for label, value in (("source", expected_source), ("target", expected_target)):
    if not re.fullmatch(r"[0-9a-f]{64}", value):
        raise SystemExit(f"FAIL: expected {label} SHA-256 must be 64 lowercase hex characters")

github_dir = target_root / ".github"
dest_dir = github_dir / "workflows"
dest = dest_dir / name
source_is_within_root = False
for parent in source.parents:
    if parent == system_root:
        source_is_within_root = True
        break
    if parent.is_symlink():
        raise SystemExit("FAIL: source parents must not be symlinks")
if not source_is_within_root:
    raise SystemExit("FAIL: scoped source escaped the system source root")
if source.is_symlink() or not source.is_file():
    raise SystemExit("FAIL: source must be an existing regular non-symlink file")
if github_dir.is_symlink() or dest_dir.is_symlink() or not github_dir.is_dir() or not dest_dir.is_dir():
    raise SystemExit("FAIL: destination parents must be existing regular directories, not symlinks")
if dest.is_symlink() or not dest.is_file():
    raise SystemExit("FAIL: destination must be an existing regular non-symlink file")
source_bytes = source.read_bytes()
target_bytes = dest.read_bytes()
source_digest = hashlib.sha256(source_bytes).hexdigest()
target_digest = hashlib.sha256(target_bytes).hexdigest()
if source_digest != expected_source:
    raise SystemExit(f"FAIL: source SHA-256 mismatch (actual {source_digest})")
if target_digest != expected_target:
    raise SystemExit(f"FAIL: target SHA-256 mismatch (actual {target_digest})")
if variant == "" and target_digest == "5eb82e65c68ae825015beedaeeb1ee7e49ec34677514e55c58ed97ca3b1cb525":
    raise SystemExit("FAIL: this Publish root preimage requires --source-variant linktrend-publish")
if variant == "" and target_digest == "47b8a9b911da549e55c7edea80d45755bc34b757972627155c65fb9568e3e8c7":
    raise SystemExit("FAIL: this OpenClaw root preimage requires --source-variant linktrend-openclaw")
if b"__LINKTREND_" in source_bytes:
    raise SystemExit("FAIL: scoped source contains unresolved consumer placeholders")
if remove_operation:
    if source_bytes:
        raise SystemExit("FAIL: retired workflow source marker must be empty")
    if dry_run:
        print(f"DRY-RUN: would remove only {dest} from {variant} ({target_digest})")
        raise SystemExit(0)
    dest.unlink()
    directory_fd = os.open(dest_dir, os.O_RDONLY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
    print(f"PASS: removed only {dest} from {variant}; preimage SHA-256 {target_digest}")
    raise SystemExit(0)
if source_bytes == target_bytes:
    print(f"PASS: unchanged {name} ({variant or 'generic'}); source and destination SHA-256 {source_digest}")
    raise SystemExit(0)
if dry_run:
    print(f"DRY-RUN: would update only {dest} from {variant or 'generic'} ({target_digest} -> {source_digest})")
    raise SystemExit(0)

mode = stat.S_IMODE(dest.lstat().st_mode)
fd, temporary_name = tempfile.mkstemp(prefix=f".{name}.", suffix=".tmp", dir=dest_dir)
try:
    with os.fdopen(fd, "wb") as handle:
        handle.write(source_bytes)
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(temporary_name, mode, follow_symlinks=False)
    os.replace(temporary_name, dest)
    directory_fd = os.open(dest_dir, os.O_RDONLY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
except BaseException:
    try:
        os.unlink(temporary_name)
    except FileNotFoundError:
        pass
    raise
print(f"PASS: updated only {dest} from {variant or 'generic'}; SHA-256 {target_digest} -> {source_digest}; mode {mode:04o} preserved")
PY
  exit $?
fi

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
profile = sys.argv[4]

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
provider_name = str(cfg.get("bugbotProviderCheckName") or "Cursor Bugbot").strip()
review_gate_name = str(cfg.get("reviewGateCheckName") or cfg.get("bugbotCheckName") or "Linktrend Review Gate").strip()
if review_gate_name == "Cursor Bugbot":
    raise SystemExit("consumer config bugbotCheckName/reviewGateCheckName must not remain Cursor Bugbot")
rendered = rendered.replace("__LINKTREND_BUGBOT_PROVIDER_CHECK_NAME__", provider_name)
rendered = rendered.replace("__LINKTREND_REVIEW_GATE_CHECK_NAME__", review_gate_name)
rendered = rendered.replace("__LINKTREND_BUGBOT_CHECK_NAME__", review_gate_name)  # legacy alias -> managed gate
rendered = rendered.replace(
    "__LINKTREND_UNTRUSTED_RUNS_ON__", runner_types[runner_type]["untrusted"]
)
rendered = rendered.replace("__LINKTREND_RUNS_ON__", runner_types[runner_type]["privileged"])
if "__LINKTREND_" in rendered:
    raise SystemExit(f"unrendered __LINKTREND_ placeholder remains in {src}")


def remove_event_blocks(value: str, prohibited: set[str]) -> str:
    """Remove event mappings without YAML parsing ``on`` as a boolean."""
    lines = value.splitlines(keepends=True)
    output: list[str] = []
    index = 0
    while index < len(lines):
        if lines[index].rstrip("\r\n") != "on:":
            output.append(lines[index])
            index += 1
            continue
        output.append(lines[index])
        index += 1
        while index < len(lines):
            line = lines[index]
            if line.strip() and not line.startswith(" "):
                break
            match = re.match(r"^  ([A-Za-z0-9_-]+):", line)
            if not match:
                output.append(line)
                index += 1
                continue
            event = match.group(1)
            block: list[str] = [line]
            index += 1
            while index < len(lines):
                candidate = lines[index]
                if candidate.strip() and not candidate.startswith(" "):
                    break
                if re.match(r"^  [A-Za-z0-9_-]+:", candidate):
                    break
                block.append(candidate)
                index += 1
            if event not in prohibited:
                output.extend(block)
    return "".join(output)


if profile == "local-coordinator" and src.name in {
    "linktrend-review-packager.yml",
    "linktrend-integrator-merge.yml",
    "linktrend-repair-observer.yml",
    "linktrend-development-to-staging.yml",
    "linktrend-staging-to-main.yml",
}:
    rendered = remove_event_blocks(
        rendered, {"schedule", "check_run", "workflow_run", "pull_request_target"}
    )
    if src.name == "linktrend-repair-observer.yml" and "\n  workflow_dispatch:" not in rendered:
        rendered = rendered.replace("on:\n", "on:\n  workflow_dispatch:\n", 1)
        rendered = rendered.replace(
            "    if: >\n      (\n",
            "    if: >\n      github.event_name == 'workflow_dispatch' ||\n      (\n",
            1,
        )
    rendered = (
        "# Orchestration profile: local-coordinator\n"
        "# Automatic schedule/check-run/workflow-run/pull-request-target wakes are disabled.\n"
        "# Manual recovery remains available; the local coordinator publishes these frozen contexts:\n"
        "# Linktrend Fast Gate | Linktrend Full Suite | Linktrend Phase Ready\n"
        "# Linktrend Staging Gate | Linktrend Release Gate | Linktrend Coordinator\n"
        "# Cursor Bugbot remains the provider observation name; required context is Linktrend Review Gate.\n"
        + rendered
    )
out.write_text(rendered, encoding="utf-8")
PY
}

copied=0
unchanged=0

for file in "${MANAGED_FILES[@]}"; do
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

  cp "$rendered" "$dest"
  info "PASS: synced $file"
  copied=$((copied + 1))
done

info ""
info "Managed workflow sync: SUCCESS"
info "Target: $TARGET_REPO"
info "Synced/updated: $copied"
info "Already matched: $unchanged"
info "Next: complete core/checklists/BUGBOT-INHERITANCE.md for this repo"
info "Next: ensure Cursor Automations exist (docs/CURSOR-AUTOMATIONS-SETUP.md)"
exit 0
