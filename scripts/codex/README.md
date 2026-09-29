# Codex orchestrator

Dispatch Codex CLI work on the IDE Development orchestrator VM with `scripts/codex/codex_orchestrator.py`.

## Install

Install the pinned CLI and configure file-based credential storage once:

```sh
bash scripts/codex/install.sh
```

The idempotent installer places Codex under `~/.local` by default, creates `~/.codex`, and sets `cli_auth_credentials_store = "file"`. It does not sign in or access credentials. Ensure `~/.local/bin` is on `PATH`.

## Sign-in and auth sync

Run device-code sign-in with `python3 scripts/codex/codex_orchestrator.py login`. Carlos must approve the device code. The command saves the usable sign-in to the private store and checks Codex liveness. By default, the gate syncs `auth.json` with the store before dispatch; the runner syncs it after every Codex attempt. The newest refreshed copy wins. Never print or commit `auth.json` or its store copy. `CODEX_AUTH_STORE_KEY` encrypts the store copy at rest.

## Routing gate

Run `python3 scripts/codex/codex_orchestrator.py gate` before dispatch. The gate restores auth, checks liveness and rate limits, then saves auth. It allows Codex only when every reported rate-limit window is below 75% used. An omitted window is ignored by default; no reported windows means overflow. Use `--strict-windows` to make an omitted window block dispatch, or set `CODEX_STRICT_WINDOWS=1` for strict handling by default. `--threshold N` changes the default 75% threshold.

| Exit code | Meaning |
| --- | --- |
| `0` | Dispatch to Codex |
| `10` | Overflow to `cursor-002` |
| `20` | Stop and ask Carlos to sign in again |
| `1` | Codex attempt failed |
| `2` | Usage or tooling error |

## Models and runs

`python3 scripts/codex/codex_orchestrator.py models` resolves model IDs from the live catalog. Luna uses high reasoning effort by default; use Sol with medium effort for hard Issues. `run` resolves the model at dispatch time. `CODEX_MODEL_LUNA` and `CODEX_MODEL_SOL` override their tier's model ID.

Example Issue run (uses Luna and passes the gate by default):

```sh
python3 scripts/codex/codex_orchestrator.py run \
  --issue IDE-42 --slug update-readme --prompt-file /tmp/ide-42-prompt.md
```

The runner creates a per-Issue Git worktree, commits changed files, and pushes the branch by default. Use `--tier sol` for Sol or `--no-push` to skip pushing.

## Parallel test

`python3 scripts/codex/codex_orchestrator.py parallel-test` runs trivial tasks in concurrent throwaway worktrees at 1, 2, and 4 workers by default. It requires a live sign-in and passing gate, records a result JSON in the state directory, and cleans up worktrees and local branches unless `--keep` is set.

## Environment

| Variable | Purpose |
| --- | --- |
| `CODEX_AUTH_STORE` | Auth store directory (default `/cursor/stores/self/private/codex`) |
| `CODEX_AUTH_STORE_KEY` | Encrypt/decrypt the stored auth copy |
| `IDE_CODEX_RUN_LOG` | Run log path (default `runs.jsonl` in the state directory) |
| `IDE_CODEX_STATE` | State directory (default `~/.local/state/ide-codex`) |
| `CODEX_BIN` | Codex executable path override |
| `CODEX_STRICT_WINDOWS` | Set to `1` to block when a rate-limit window is omitted |
| `CODEX_MODEL_LUNA`, `CODEX_MODEL_SOL` | Model ID overrides for each tier |
| `CODEX_HOME` | Codex home directory (default `~/.codex`) |
