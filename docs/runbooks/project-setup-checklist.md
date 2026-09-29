# Project setup checklist (v3 Wave 0.8)

**Audience:** the orchestrator of a new Cursor Project (one per repo), and Carlos for the one-time actions.
**Status:** proven on the IDE-Development pilot (Wave 0, 2026-09-29). Every step below was run on that Project; the notes record what actually happened, not what was expected.
**Related:** [`watchdog-and-runlog.md`](./watchdog-and-runlog.md) · [`phase-issue-convention.md`](./phase-issue-convention.md) · [`../../core/ledger/README.md`](../../core/ledger/README.md) · [`../../scripts/codex/README.md`](../../scripts/codex/README.md)

Replace `IDE` with the repo's Ledger prefix and `IDE-Development` with the repo name throughout.

---

## Part A — What Carlos does (one-time, plain language)

Most of this happens once for the whole studio; items 3–5 happen once per new Project. The orchestrator tells you when each one is due and gives you the exact screen to open.

1. **Turn on device-code sign-in for ChatGPT (once).** In ChatGPT's security settings, allow "device code" sign-in. Without it, Codex cannot be connected to an orchestrator.
2. **Rename the cursor-002 API key (optional, once).** It is currently labelled "Cursor-001" in the cursor-002 dashboard. The key itself stays the same.
3. **Create the Cursor Project and its orchestrator** on the chosen frontier model, when the rollout order says so.
4. **Register the repo's environment on the cursor-002 account.** In the cursor-002 Cursor dashboard, open Cloud Agents → Environments, create an environment for the repo, and let it finish its first build. The pilot showed this cannot be done by API, and without it cursor-002 workers start on a bare machine with none of the repo's tools. (The same is true on cursor-001 for a repo that has never had an environment.)
5. **Approve the Codex sign-in for the new orchestrator.** The orchestrator shows you a short code and a web address. Open the address, sign in to ChatGPT, and type the code. It takes about a minute. Do this once per orchestrator; the sign-in is never copied to another one. If Codex ever says the sign-in expired, the orchestrator stops and asks you to do this again.
6. **Add secrets in the Cursor Dashboard** (Cloud Agents → Secrets) when asked:
   - `CODEX_AUTH_STORE_KEY`, a long random passphrase used only by this orchestrator. It is required before the Codex sign-in, because the sign-in is only ever saved encrypted.
   - `CURSOR_002_API_KEY`, already there for IDE-Development.
   - Later: the Ledger login, the orchestrator's Tailscale pass and the hub key.
7. **Report Cursor spend by hand** when the orchestrator asks. The Cursor API only reports tokens, not money.

You do **not** approve merges or releases.

---

## Part B — Orchestrator checklist

Work through these in order and tick them in the setup Phase Issue. Each section maps to a pilot Phase.

### B1. Environment recipe (pilot 0.1)

- [ ] Add `scripts/setup.sh`: idempotent, non-interactive, never touches credentials. For IDE-Development it installs apt basics (`git`, `jq`, `ripgrep`, Python ≥ 3.11), `jsonschema==4.26.0` (as CI), Node 22 via nvm, and the pinned Codex CLI (`@openai/codex@0.158.0`, override `IDE_SETUP_CODEX_VERSION`) with `cli_auth_credentials_store = "file"`. It writes `~/.cache/ide-development/setup-done.json` when done. Warm re-run: about 16 s.
  - `IDE_SETUP_SKIP_CODEX=1` skips Codex (use it inside Codex's own setup box).
  - `IDE_SETUP_POSTGRES=1` also installs Postgres server and client, needed only for the Ledger SQL test (`scripts/ledger/test-ide-ledger-sql.sh`).
- [ ] Add `.cursor/environment.json`: `{"name": "<Repo>", "install": "bash scripts/setup.sh"}`. Validate it against `https://cursor.com/schemas/environment.schema.json`.
- [ ] Run a real draft build on cursor-001 and check the log shows the tool versions. Pilot: build `bld-20260929-1108672c-…` succeeded.
- [ ] Know how the file is picked up (pilot finding):
  - The committed file is used only through **builds of an environment that is already registered** for the repo on that account.
  - New agents boot from the latest **promoted** build, and only default-branch (`main`) builds are promotable. So a recipe change takes effect after it reaches `main` and the next build runs.
  - cursor-002 has no environment endpoints in its API. Until Carlos registers the environment (Part A, item 4), the cursor-002 dispatch prompt runs `scripts/setup.sh` itself when the marker file is missing.
- [ ] `node` on Cursor VMs resolves to Cursor's bundled Node 22 ahead of nvm's; `npm` and `codex` come from nvm. Harmless.

### B2. Frontier orchestrator and cheap-helper rule (pilot 0.2)

- [ ] Copy `.cursor/rules/07-orchestrator-helper-routing.mdc` (repo-local until Wave 1.5 moves it to managed core).
- [ ] Smoke test: two read-only helper subagents (`grok-4.7` medium, then `composer-2.5`) each do one lookup and one 3-bullet summary; check both answers against the source.

### B3. cursor-002 dispatch (pilot 0.3)

- [ ] `CURSOR_002_API_KEY` is present as a Cursor secret (never printed, never committed).
- [ ] `python3 scripts/dispatch/cursor002.py resolve --route grok-medium` and `--route opus-medium` succeed. Every dispatch re-checks the model ID and variant against `GET /v1/models` and fails closed if a model was renamed; aliases are refused.
- [ ] Dispatch one small real Issue with `create --branch issue/IDE-<n>-<slug> --ref <base> --issue-id IDE-<n> --wait --run-log <file>`. The client pre-creates the branch and the worker pushes to it. Check the diff yourself, then `archive` the agent. Pilot: IDE-9, Grok 4.7, 66 s, one-line commit.
- [ ] Record the model's self-report (`MODEL-SELF-REPORT:` line); the API reports neither the model nor cost, and `usage` is cumulative per agent.

### B4. Codex on the orchestrator VM (pilot 0.4)

- [ ] `bash scripts/codex/install.sh` (or rely on `scripts/setup.sh`).
- [ ] `CODEX_AUTH_STORE_KEY` is set (Part A, item 6). It is mandatory: without it every auth command, `login` and `gate` stop with exit 20. There is no plaintext mode.
- [ ] If the store still holds a plaintext `auth.json` from before this rule, run `python3 scripts/codex/codex_orchestrator.py migrate`. Then run `login` again to rotate the refresh token, because the plaintext copy was readable by other agents.
- [ ] **Sign-in**, in a tmux session so the prompt survives:
  1. `python3 scripts/codex/codex_orchestrator.py login`
  2. Send Carlos the address and code it prints (Part A, item 5) and wait.
  3. On success it saves the sign-in to the private store, encrypted as `auth.json.enc` (`$CODEX_AUTH_STORE`, default `/cursor/stores/self/private/codex`, recorded as the resolved Project-store path), and runs the liveness check. Exit 20 means sign-in failed; ask Carlos again.
- [ ] `python3 scripts/codex/codex_orchestrator.py gate` returns exit 0 (route `codex`, liveness `live`).
- [ ] **Restart check:** delete `~/.codex/auth.json`, run `gate` again, and confirm `auth.action: restored`.
- [ ] **Allowance rule (pilot decision, recorded as a plan amendment by the orchestrator):** Codex is used only while **every window the backend reports** is below 75% used. A window the backend does not report does not block (it is listed in `notReported`); if no window is reported at all, work overflows to cursor-002. The pilot account reported only the weekly window. `--strict-windows` or `CODEX_STRICT_WINDOWS=1` restores "both windows must be reported". The free "Full reset" credit is never used by the scripts.
- [ ] Run one real Issue: `python3 scripts/codex/codex_orchestrator.py run --issue IDE-<n> --slug <slug> --prompt-file <file> [--tier sol]`. Codex cannot commit inside its sandbox; the runner commits as `IDE-<n>: <message>` and pushes. Trust `cliModel` / `cliEffort` from the readback, not the model's self-report (Luna High reports itself as "medium"). Pilot: IDE-18, 128 s.
- [ ] Parallel test only when needed: `parallel-test` at 1/2/4 worktrees. Pilot: 4 concurrent runs all succeeded; no limit found, Codex cloud overflow not needed.
- [ ] Never use the same `auth.json` from two machines at once, and never print or commit it. The Project store ignores `chmod` and is shared by every agent in the Project, which is why the store copy is always encrypted.
- [ ] Codex and Git run with an allowlisted environment and hooks disabled. Codex has no write access to the Git common directory; the runner commits for it. Never add orchestrator secrets to the Codex environment.

### B5. Ledger (pilot 0.5)

- [ ] Pick the repo's Ledger prefix (for example `IDE`). IDs are `<prefix>-<n>`, branches `issue/<prefix>-<n>-<slug>`.
- [ ] The Ledger schema lives in IDE-Development (`core/ledger/sql/ide_ledger.sql`) and is applied once, by LiNKplatform (Wave 3.1). Other repos only need the prefix registered.
- [ ] Until the Ledger is live, keep the run log in the Project store (B6) and import it later with `runlog.py export-sql`.

### B6. Watchdog and run log (pilot 0.6)

- [ ] Run log root: `--root`, else `$IDE_RUNLOG_DIR`, else the pilot Project store `internal/runlog/`. Other Projects set `IDE_RUNLOG_DIR` to their own resolved store path (not the `/cursor/stores/self` alias, which points at a different store on each worker VM). Set `IDE_CODEX_RUN_LOG` for Codex runs and pass `--run-log` to `cursor002.py` so the raw logs sit next to it.
- [ ] Subscribe the watchdog timer (`subscribe_timer`, name `ide-watchdog`, 1800 s) running `python3 scripts/orchestrator/watchdog.py --repo /workspace --fetch --exit-zero`. Details: [`watchdog-and-runlog.md`](./watchdog-and-runlog.md).
- [ ] Prove it once: start a run, do not heartbeat it, run the watchdog with a short `--stall-minutes`, and see the stalled finding.

### B7. Phase Issue convention (pilot 0.7)

- [ ] Copy `.github/ISSUE_TEMPLATE/phase-summary.yml` and create the `phase` label in the repo.
- [ ] One GitHub Issue per Phase; per-Issue detail stays in the Ledger. See [`phase-issue-convention.md`](./phase-issue-convention.md).

---

## Part C — Known pitfalls (from the pilot)

1. **Secret-scan fixture pin (until Wave 1 retires it).** `.github/linktrend-secret-scan-fixtures.json` pins a hash of the whole tree (`candidateTree`), so any added or changed file fails `secret_scan.py` until it is refreshed. Workers refresh it on their branch; when several branches are packaged together, refresh it **once more on the combined head** and commit the result:

   ```bash
   python3 scripts/gitops/generated_output_closure.py --generate-fixtures
   ```

   Branch-level refresh commits all conflict on that one line; resolve by regenerating, not by picking a side.
2. **Commit signing makes local checks slow.** Cursor VMs sign every commit, including throwaway commits in test fixtures. Full verification takes about 14–19 min that way and about 3 min with signing off for the check only:

   ```bash
   GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=commit.gpgsign GIT_CONFIG_VALUE_0=false \
     CI=true bash scripts/verify-ide-development.sh
   ```

   Real commits that get pushed stay signed.
3. **Run verifications one at a time on a VM.** `scripts/tests/test-gitops-lifecycle.sh` writes to fixed `/tmp` paths, so two suites running together clobber each other and fail randomly.
4. **Codex sandbox has no git write and no network by default.** The runner commits for it through the Git directory it recorded before the run, and fails the attempt if Codex rewrote the worktree's `.git` link. Add `--network` only when the Issue needs it.
5. **Worker branches, not PRs.** Workers push `issue/<prefix>-<n>-<slug>` and never open PRs; the orchestrator packages branches into PRs to `development`.
