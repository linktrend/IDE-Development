#!/usr/bin/env bash
# Wire a consumer repository to IDE Development via .cursor symlink.
# Stdlib/bash only. Exit 0 on success or already-wired; non-zero on failure.

set -euo pipefail

SYSTEM_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CURSOR_SOURCE="${SYSTEM_ROOT}/.cursor"

fail() {
  echo "FAIL: $1" >&2
  exit 1
}

info() {
  echo "$1"
}

# Resolve a path to an absolute, symlink-expanded location.
canonicalize() {
  local target="$1"
  local dir

  if [ -d "$target" ]; then
    (cd "$target" && pwd -P)
  elif [ -e "$target" ]; then
    dir="$(cd "$(dirname "$target")" && pwd -P)"
    echo "${dir}/$(basename "$target")"
  else
    echo "$target"
  fi
}

# Follow symlinks until a non-link path is reached.
resolve_symlink() {
  local path="$1"
  local link dir

  while [ -L "$path" ]; do
    link="$(readlink "$path")"
    if [[ "$link" != /* ]]; then
      dir="$(cd "$(dirname "$path")" && pwd -P)"
      path="${dir}/${link}"
    else
      path="$link"
    fi
    path="$(canonicalize "$path")"
  done
  echo "$path"
}

# Compute a relative path from $1 (directory) to $2 (file or directory).
relpath() {
  local from to from_parts to_parts i common_len rel up

  from="$(canonicalize "$1")"
  to="$(canonicalize "$2")"

  IFS='/' read -r -a from_parts <<< "${from#/}"
  IFS='/' read -r -a to_parts <<< "${to#/}"

  common_len=0
  for ((i = 0; i < ${#from_parts[@]} && i < ${#to_parts[@]}; i++)); do
    if [ "${from_parts[$i]}" = "${to_parts[$i]}" ]; then
      common_len=$((i + 1))
    else
      break
    fi
  done

  rel=""
  for ((i = common_len; i < ${#from_parts[@]}; i++)); do
    rel="${rel}../"
  done

  for ((i = common_len; i < ${#to_parts[@]}; i++)); do
    rel="${rel}${to_parts[$i]}"
    if [ "$i" -lt $(( ${#to_parts[@]} - 1 )) ]; then
      rel="${rel}/"
    fi
  done

  if [ -z "$rel" ]; then
    rel="."
  fi

  echo "$rel"
}

usage() {
  cat <<EOF
Usage: $(basename "$0") <consumer-repo-path>

Wire a consumer repository to IDE Development by creating:
  <consumer-repo>/.cursor -> <relative path to IDE Development>/.cursor

The script backs up an existing .cursor directory or mismatched symlink before wiring.
It verifies required runtime paths after wiring and is idempotent when already correct.

Examples:
  $(basename "$0") /Users/you/Projects/SomeProductRepo
  $(basename "$0") ../AnotherRepo
EOF
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

if [ $# -ne 1 ]; then
  usage >&2
  exit 1
fi

TARGET_INPUT="$1"

if [ ! -d "$TARGET_INPUT" ]; then
  fail "Target path is not a directory: $TARGET_INPUT"
fi

TARGET_REPO="$(cd "$TARGET_INPUT" && pwd -P)"
TARGET_CURSOR="${TARGET_REPO}/.cursor"
EXPECTED_CURSOR="$(canonicalize "$CURSOR_SOURCE")"

info "System repository: $SYSTEM_ROOT"
info "Consumer repository: $TARGET_REPO"

if [ "$TARGET_REPO" = "$(canonicalize "$SYSTEM_ROOT")" ]; then
  fail "Refusing to wire the system repository to itself"
fi

[ -d "$CURSOR_SOURCE" ] || fail "System .cursor surface missing: $CURSOR_SOURCE"
[ -f "${CURSOR_SOURCE}/README.md" ] || fail "System .cursor/README.md missing"

already_wired=0
if [ -L "$TARGET_CURSOR" ]; then
  resolved="$(resolve_symlink "$TARGET_CURSOR")"
  if [ "$resolved" = "$EXPECTED_CURSOR" ]; then
    already_wired=1
    info "PASS: Already wired — $TARGET_CURSOR resolves to $EXPECTED_CURSOR"
  fi
elif [ -e "$TARGET_CURSOR" ]; then
  timestamp="$(date +%Y%m%d-%H%M%S)"
  backup_path="${TARGET_REPO}/.cursor-backup-${timestamp}"
  info "Backing up existing .cursor to $backup_path"
  mv "$TARGET_CURSOR" "$backup_path"
  info "PASS: Backup created at $backup_path"
fi

if [ "$already_wired" -eq 0 ]; then
  rel_link="$(relpath "$TARGET_REPO" "$CURSOR_SOURCE")"
  info "Creating symlink: $TARGET_CURSOR -> $rel_link"
  ln -sfn "$rel_link" "$TARGET_CURSOR"

  resolved="$(resolve_symlink "$TARGET_CURSOR")"
  if [ "$resolved" != "$EXPECTED_CURSOR" ]; then
    fail "Symlink created but resolves incorrectly: $resolved (expected $EXPECTED_CURSOR)"
  fi
  info "PASS: Symlink created and resolves correctly"
fi

required_paths=(
  ".cursor/README.md"
  ".cursor/execution/INDEX.yaml"
  ".cursor/templates/INDEX.yaml"
  ".cursor/commands/INDEX.yaml"
)

(
  cd "$TARGET_REPO"
  for rel in "${required_paths[@]}"; do
    [ -e "$rel" ] || fail "Verification failed — not reachable from consumer repo: $rel"
    info "PASS: $rel reachable"
  done
)

info ""
info "Wire summary: SUCCESS"
info "Consumer: $TARGET_REPO"
info "Link: $TARGET_CURSOR -> $(readlink "$TARGET_CURSOR")"
exit 0
