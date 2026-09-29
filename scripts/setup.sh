#!/usr/bin/env bash
# Environment recipe for IDE Development cloud agents (Cursor `install`, Codex setup box).
# Idempotent and non-interactive. Installs what the CI "Verify IDE Development" job needs
# (.github/workflows/ci.yml) plus the Codex CLI. Never reads or writes credentials.
set -euo pipefail

NODE_MAJOR="${IDE_SETUP_NODE_MAJOR:-22}"
PYTHON_MIN_MINOR="${IDE_SETUP_PYTHON_MIN_MINOR:-11}"
JSONSCHEMA_VERSION="${IDE_SETUP_JSONSCHEMA_VERSION:-4.26.0}"
CODEX_VERSION="${IDE_SETUP_CODEX_VERSION:-0.158.0}"
NVM_VERSION="${IDE_SETUP_NVM_VERSION:-v0.40.3}"
SKIP_CODEX="${IDE_SETUP_SKIP_CODEX:-0}"
# Postgres server + client, only for scripts/ledger/test-ide-ledger-sql.sh (off by default).
WITH_POSTGRES="${IDE_SETUP_POSTGRES:-0}"

log() { printf '[setup] %s\n' "$*"; }
die() { printf '[setup] ERROR: %s\n' "$*" >&2; exit 1; }

SUDO=""
if [ "$(id -u)" -ne 0 ]; then
  if command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
    SUDO="sudo -n"
  fi
fi

apt_install() {
  local missing=()
  local pkg
  for pkg in "$@"; do
    dpkg -s "$pkg" >/dev/null 2>&1 || missing+=("$pkg")
  done
  [ "${#missing[@]}" -eq 0 ] && return 0
  command -v apt-get >/dev/null 2>&1 || die "apt-get unavailable; install manually: ${missing[*]}"
  if [ -z "$SUDO" ] && [ "$(id -u)" -ne 0 ]; then
    die "need root or passwordless sudo to install: ${missing[*]}"
  fi
  log "apt-get install ${missing[*]}"
  $SUDO env DEBIAN_FRONTEND=noninteractive apt-get update -qq
  $SUDO env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends "${missing[@]}"
}

link_bin() {
  # Expose a tool on the default PATH for non-login shells (CI scripts, codex exec).
  local src="$1" name="$2"
  if [ -n "$SUDO" ] || [ "$(id -u)" -eq 0 ]; then
    $SUDO ln -sf "$src" "/usr/local/bin/$name"
  else
    mkdir -p "$HOME/.local/bin"
    ln -sf "$src" "$HOME/.local/bin/$name"
  fi
}

log "system packages"
apt_install ca-certificates curl git jq ripgrep python3 python3-pip python3-venv

if [ "$WITH_POSTGRES" = "1" ]; then
  log "postgres server + client"
  apt_install postgresql postgresql-client
fi

log "python >= 3.${PYTHON_MIN_MINOR}"
python3 - "$PYTHON_MIN_MINOR" <<'PY' || die "python3 is older than 3.${PYTHON_MIN_MINOR} (CI uses 3.11)"
import sys
raise SystemExit(0 if sys.version_info >= (3, int(sys.argv[1])) else 1)
PY

log "python deps: jsonschema==${JSONSCHEMA_VERSION}"
if ! python3 -c "import importlib.metadata as m,sys; sys.exit(m.version('jsonschema')!='${JSONSCHEMA_VERSION}')" 2>/dev/null; then
  pip_args=(--disable-pip-version-check --no-input --user "jsonschema==${JSONSCHEMA_VERSION}")
  if ls /usr/lib/python3*/EXTERNALLY-MANAGED >/dev/null 2>&1; then
    pip_args=(--break-system-packages "${pip_args[@]}")
  fi
  python3 -m pip install "${pip_args[@]}"
fi

log "node ${NODE_MAJOR} via nvm"
export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
if [ ! -s "$NVM_DIR/nvm.sh" ]; then
  curl -fsSL "https://raw.githubusercontent.com/nvm-sh/nvm/${NVM_VERSION}/install.sh" | PROFILE=/dev/null bash
fi
# nvm.sh is not written for `set -u`.
set +u
# shellcheck source=/dev/null
. "$NVM_DIR/nvm.sh"
nvm install "$NODE_MAJOR" >/dev/null
nvm alias default "$NODE_MAJOR" >/dev/null
nvm use default >/dev/null
set -u
NODE_BIN_DIR="$(dirname "$(nvm which default)")"
export PATH="$NODE_BIN_DIR:$PATH"
if ! grep -qs 'NVM_DIR/nvm.sh' "$HOME/.bashrc"; then
  printf '\nexport NVM_DIR="$HOME/.nvm"\n[ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"\n' >> "$HOME/.bashrc"
fi

if [ "$SKIP_CODEX" != "1" ]; then
  log "codex cli @openai/codex@${CODEX_VERSION}"
  installed="$("$NODE_BIN_DIR/npm" ls -g --depth=0 --json 2>/dev/null \
    | python3 -c "import json,sys; print(json.load(sys.stdin).get('dependencies',{}).get('@openai/codex',{}).get('version',''))" 2>/dev/null || true)"
  if [ "$installed" != "$CODEX_VERSION" ]; then
    "$NODE_BIN_DIR/npm" install -g --no-fund --no-audit "@openai/codex@${CODEX_VERSION}"
  fi
  link_bin "$NODE_BIN_DIR/codex" codex
  # File-backed credentials so the orchestrator can save/restore ~/.codex/auth.json via its store.
  mkdir -p "$HOME/.codex"
  if ! grep -qs '^cli_auth_credentials_store' "$HOME/.codex/config.toml"; then
    printf 'cli_auth_credentials_store = "file"\n' >> "$HOME/.codex/config.toml"
  fi
fi

log "versions"
printf '  node    %s\n' "$("$NODE_BIN_DIR/node" --version)"
printf '  npm     %s\n' "$("$NODE_BIN_DIR/npm" --version)"
printf '  python  %s\n' "$(python3 -c 'import platform; print(platform.python_version())')"
printf '  jsonschema %s\n' "$(python3 -c 'import importlib.metadata as m; print(m.version("jsonschema"))')"
printf '  jq      %s\n' "$(jq --version)"
printf '  rg      %s\n' "$(rg --version | head -1)"
printf '  git     %s\n' "$(git --version)"
if [ "$WITH_POSTGRES" = "1" ]; then
  printf '  psql    %s\n' "$(psql --version)"
fi
if [ "$SKIP_CODEX" != "1" ]; then
  printf '  codex   %s\n' "$(codex --version 2>&1 | head -1)"
fi
marker_dir="$HOME/.cache/ide-development"
mkdir -p "$marker_dir"
printf '{"completedAt":"%s","commit":"%s","codex":"%s"}\n' \
  "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  "$(git -C "$(dirname "$0")/.." rev-parse HEAD 2>/dev/null || echo unknown)" \
  "$([ "$SKIP_CODEX" = "1" ] && echo skipped || echo "$CODEX_VERSION")" > "$marker_dir/setup-done.json"
log "done (marker: $marker_dir/setup-done.json)"
