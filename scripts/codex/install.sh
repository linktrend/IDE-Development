#!/usr/bin/env bash
# Install the Codex CLI for the orchestrator VM and force file-based credential storage.
# Idempotent. Never touches credentials; use codex_orchestrator.py for sign-in and auth sync.
set -euo pipefail

CODEX_CLI_VERSION="${CODEX_CLI_VERSION:-0.158.0}"
PREFIX="${CODEX_NPM_PREFIX:-$HOME/.local}"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"

if ! command -v npm >/dev/null 2>&1; then
  echo "install.sh: npm is required (install Node.js first)" >&2
  exit 2
fi

current=""
if [ -x "$PREFIX/bin/codex" ]; then
  current="$("$PREFIX/bin/codex" --version 2>/dev/null | awk '{print $2}')"
fi
if [ "$current" != "$CODEX_CLI_VERSION" ]; then
  # The system npm prefix is root-owned on Cursor cloud VMs, so install per user.
  npm install -g --silent --prefix "$PREFIX" "@openai/codex@$CODEX_CLI_VERSION"
fi

case ":$PATH:" in
  *":$PREFIX/bin:"*) ;;
  *) echo "install.sh: add $PREFIX/bin to PATH" >&2 ;;
esac

if ! command -v bwrap >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
  (sudo -n apt-get update -qq && sudo -n apt-get install -y -qq bubblewrap) >/dev/null 2>&1 \
    || echo "install.sh: bubblewrap install failed; Codex falls back to its bundled copy" >&2
fi

mkdir -p "$CODEX_HOME"
chmod 700 "$CODEX_HOME"
config="$CODEX_HOME/config.toml"
python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/set_codex_config.py" "$config"

"$PREFIX/bin/codex" --version
echo "config: $config (cli_auth_credentials_store = \"file\")"
