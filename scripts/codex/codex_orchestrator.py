#!/usr/bin/env python3
"""Codex CLI dispatch for the IDE Development orchestrator VM (v3 Wave 0.4).

Subcommands:
  auth-status     show local/store sign-in state (never prints token contents)
  auth-restore    sync ~/.codex/auth.json with the private store (newest copy wins)
  auth-save       same sync; run after every Codex invocation
  login           interactive device-code sign-in, then save to the private store
  liveness        `codex cloud list --json --limit 1`
  allowance       app-server `account/rateLimits/read`, two-window rule
  models          resolve Luna / Sol model IDs via app-server `model/list`
  gate            restore -> liveness -> allowance -> save; prints the routing decision
  run             per-Issue git worktree `codex exec` runner
  parallel-test   concurrent trivial runs at 1/2/4 worktrees (needs a live sign-in)

Exit codes: 0 = dispatch to Codex, 10 = overflow to cursor-002,
20 = stop and ask Carlos to sign in again, 1 = Codex attempt failed, 2 = usage/tooling error.

The private store is a FUSE mount that ignores chmod, so the store copy is readable by every
agent sharing that store. Set CODEX_AUTH_STORE_KEY (a Cursor secret) to keep it encrypted at rest.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import contextlib
import datetime as dt
import fcntl
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Iterator

EXIT_CODEX = 0
EXIT_ATTEMPT_FAILED = 1
EXIT_ERROR = 2
EXIT_OVERFLOW = 10
EXIT_ASK_CARLOS = 20

DEFAULT_THRESHOLD = 75
DEFAULT_STORE = "/cursor/stores/self/private/codex"
STORE_KEY_ENV = "CODEX_AUTH_STORE_KEY"
TIERS = {"luna": ("luna", "high"), "sol": ("sol", "medium")}
FIVE_HOUR_MAX_MINS = 24 * 60
LOGIN_COMMAND = "python3 scripts/codex/codex_orchestrator.py login"
ASK_CARLOS = (
    "Codex sign-in is missing or expired. Stop Codex dispatch and ask Carlos to approve a new "
    f"device-code sign-in (orchestrator runs: {LOGIN_COMMAND})."
)
LOGGED_OUT_RE = re.compile(
    r"not signed in|not logged in|log ?in again|sign ?in again|run 'codex login'|unauthori[sz]ed|\b401\b"
    r"|refresh[_ ]token|token (?:is |has )?(?:expired|revoked|invalid)|authentication required",
    re.IGNORECASE,
)
ISSUE_RE = re.compile(r"^[A-Z][A-Z0-9]*-\d+$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,48}$")
SELF_REPORT_RE = re.compile(r"^MODEL_SELF_REPORT:\s*(.+)$", re.MULTILINE)


class ToolError(RuntimeError):
    pass


class LoggedOut(RuntimeError):
    pass


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex")


def store_dir() -> Path:
    return Path(os.environ.get("CODEX_AUTH_STORE") or DEFAULT_STORE).resolve()


def state_dir() -> Path:
    return Path(os.environ.get("IDE_CODEX_STATE") or Path.home() / ".local/state/ide-codex")


def codex_bin() -> str:
    found = os.environ.get("CODEX_BIN") or shutil.which("codex")
    if not found:
        candidate = Path.home() / ".local/bin/codex"
        if candidate.exists():
            return str(candidate)
        raise ToolError("codex CLI not found; run scripts/codex/install.sh")
    return found


# --- auth.json sync -----------------------------------------------------------------------


def parse_auth(raw: bytes | None) -> dict[str, Any] | None:
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def auth_usable(data: dict[str, Any] | None) -> bool:
    if not data:
        return False
    tokens = data.get("tokens") or {}
    return data.get("auth_mode") in (None, "chatgpt") and bool(tokens.get("refresh_token"))


def auth_freshness(data: dict[str, Any] | None) -> dt.datetime:
    floor = dt.datetime.min.replace(tzinfo=dt.timezone.utc)
    value = (data or {}).get("last_refresh")
    if not isinstance(value, str):
        return floor
    try:
        # Codex writes nanosecond fractions; older Pythons only parse up to microseconds.
        normalized = re.sub(r"(\.\d{6})\d+", r"\1", value.replace("Z", "+00:00"))
        parsed = dt.datetime.fromisoformat(normalized)
    except ValueError:
        return floor
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=dt.timezone.utc)


def auth_summary(data: dict[str, Any] | None, present: bool) -> dict[str, Any]:
    return {
        "present": present,
        "usable": auth_usable(data),
        "authMode": (data or {}).get("auth_mode"),
        "lastRefresh": (data or {}).get("last_refresh"),
    }


def local_auth_path() -> Path:
    return codex_home() / "auth.json"


def store_auth_path() -> Path:
    name = "auth.json.enc" if os.environ.get(STORE_KEY_ENV) else "auth.json"
    return store_dir() / name


def _openssl(data: bytes, decrypt: bool) -> bytes:
    cmd = ["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-iter", "200000", "-salt", "-pass", f"env:{STORE_KEY_ENV}"]
    if decrypt:
        cmd.append("-d")
    proc = subprocess.run(cmd, input=data, capture_output=True, check=False)
    if proc.returncode != 0:
        raise ToolError("openssl failed on the auth store copy (wrong CODEX_AUTH_STORE_KEY?)")
    return proc.stdout


def read_local() -> bytes | None:
    path = local_auth_path()
    return path.read_bytes() if path.exists() else None


def read_store() -> bytes | None:
    path = store_auth_path()
    if not path.exists():
        return None
    raw = path.read_bytes()
    return _openssl(raw, decrypt=True) if os.environ.get(STORE_KEY_ENV) else raw


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(tmp, path)
    with contextlib.suppress(OSError):
        os.chmod(path, 0o600)


def write_local(data: bytes) -> None:
    home = codex_home()
    home.mkdir(parents=True, exist_ok=True)
    os.chmod(home, 0o700)
    _atomic_write(local_auth_path(), data)


def write_store(data: bytes) -> None:
    payload = _openssl(data, decrypt=False) if os.environ.get(STORE_KEY_ENV) else data
    _atomic_write(store_auth_path(), payload)


@contextlib.contextmanager
def auth_lock() -> Iterator[None]:
    home = codex_home()
    home.mkdir(parents=True, exist_ok=True)
    with open(home / ".ide-auth-sync.lock", "w") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def sync_auth() -> dict[str, Any]:
    """Make local and store copies identical, keeping the most recently refreshed one.

    Never re-seeds a newer local file from an older store copy, so concurrent runs on this VM
    cannot roll back a token that Codex has just rotated.
    """
    with auth_lock():
        local_raw, store_raw = read_local(), read_store()
        local, store = parse_auth(local_raw), parse_auth(store_raw)
        action = "none"
        if auth_usable(store) and (not auth_usable(local) or auth_freshness(store) > auth_freshness(local)):
            write_local(store_raw or b"")
            action = "restored"
        elif auth_usable(local) and local_raw != store_raw:
            write_store(local_raw or b"")
            action = "saved"
        elif auth_usable(local):
            action = "in_sync"
        if local_auth_path().exists():
            os.chmod(local_auth_path(), 0o600)
        final = parse_auth(read_local())
        return {
            "action": action,
            "usable": auth_usable(final),
            "lastRefresh": (final or {}).get("last_refresh"),
            "store": str(store_auth_path()),
            "encryptedAtRest": bool(os.environ.get(STORE_KEY_ENV)),
        }


def auth_status() -> dict[str, Any]:
    local_raw = read_local()
    try:
        store_raw = read_store()
        store_error = None
    except ToolError as exc:
        store_raw, store_error = None, str(exc)
    status = {
        "local": auth_summary(parse_auth(local_raw), local_raw is not None),
        "store": auth_summary(parse_auth(store_raw), store_raw is not None),
        "storePath": str(store_auth_path()),
        "encryptedAtRest": bool(os.environ.get(STORE_KEY_ENV)),
    }
    if store_error:
        status["storeError"] = store_error
    return status


# --- app-server JSON-RPC ------------------------------------------------------------------


class AppServerError(RuntimeError):
    pass


class AppServer:
    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout
        self.proc = subprocess.Popen(
            [codex_bin(), "app-server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )
        self.lines: queue.Queue[str | None] = queue.Queue()
        threading.Thread(target=self._pump, daemon=True).start()
        self.next_id = 1
        self.request("initialize", {"clientInfo": {"name": "ide-orchestrator", "version": "1"}})
        self._send({"method": "initialized"})

    def _pump(self) -> None:
        assert self.proc.stdout is not None
        for line in self.proc.stdout:
            self.lines.put(line)
        self.lines.put(None)

    def _send(self, message: dict[str, Any]) -> None:
        assert self.proc.stdin is not None
        self.proc.stdin.write(json.dumps(message) + "\n")
        self.proc.stdin.flush()

    def request(self, method: str, params: dict[str, Any] | None = None) -> Any:
        request_id = self.next_id
        self.next_id += 1
        message: dict[str, Any] = {"id": request_id, "method": method}
        if params is not None:
            message["params"] = params
        self._send(message)
        deadline = time.monotonic() + self.timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise AppServerError(f"{method}: timed out")
            try:
                line = self.lines.get(timeout=remaining)
            except queue.Empty as exc:
                raise AppServerError(f"{method}: timed out") from exc
            if line is None:
                raise AppServerError(f"{method}: app-server exited")
            try:
                reply = json.loads(line)
            except ValueError:
                continue
            if reply.get("id") != request_id:
                continue
            if "error" in reply:
                raise AppServerError(str((reply["error"] or {}).get("message") or reply["error"]))
            return reply.get("result")

    def close(self) -> None:
        with contextlib.suppress(Exception):
            assert self.proc.stdin is not None
            self.proc.stdin.close()
        with contextlib.suppress(Exception):
            self.proc.terminate()
            self.proc.wait(timeout=5)
        with contextlib.suppress(Exception):
            assert self.proc.stdout is not None
            self.proc.stdout.close()

    def __enter__(self) -> "AppServer":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()


def read_rate_limits() -> dict[str, Any]:
    with AppServer() as server:
        try:
            return server.request("account/rateLimits/read") or {}
        except AppServerError as exc:
            if LOGGED_OUT_RE.search(str(exc)):
                raise LoggedOut(str(exc)) from exc
            raise


def list_models() -> list[dict[str, Any]]:
    models: list[dict[str, Any]] = []
    with AppServer() as server:
        cursor = None
        while True:
            params: dict[str, Any] = {"includeHidden": False}
            if cursor:
                params["cursor"] = cursor
            result = server.request("model/list", params) or {}
            models.extend(result.get("data") or [])
            cursor = result.get("nextCursor")
            if not cursor:
                return models


# --- decisions (pure) ---------------------------------------------------------------------


def evaluate_allowance(result: dict[str, Any], threshold: int = DEFAULT_THRESHOLD) -> dict[str, Any]:
    """Codex is allowed only when both the 5-hour and weekly windows are below `threshold`%."""
    snapshot = (result.get("rateLimitsByLimitId") or {}).get("codex") or result.get("rateLimits") or {}
    windows: dict[str, dict[str, Any]] = {}
    for position, default_kind in (("primary", "fiveHour"), ("secondary", "weekly")):
        window = snapshot.get(position)
        if not window:
            continue
        minutes = window.get("windowDurationMins")
        kind = default_kind
        if isinstance(minutes, int) and minutes > 0:
            kind = "fiveHour" if minutes <= FIVE_HOUR_MAX_MINS else "weekly"
        if kind in windows:
            kind = default_kind
        windows[kind] = {
            "position": position,
            "usedPercent": window.get("usedPercent"),
            "windowDurationMins": minutes,
            "resetsAt": window.get("resetsAt"),
        }
    reasons = []
    for kind in ("fiveHour", "weekly"):
        window = windows.get(kind)
        used = (window or {}).get("usedPercent")
        if window is None or not isinstance(used, (int, float)):
            reasons.append(f"{kind}_window_unknown")
        elif used >= threshold:
            reasons.append(f"{kind}_used_{used}pct")
    if snapshot.get("rateLimitReachedType"):
        reasons.append(f"limit_reached:{snapshot['rateLimitReachedType']}")
    if result.get("ordinaryUsageAllowed") is False:
        reasons.append("ordinary_usage_not_allowed")
    return {
        "allowed": not reasons,
        "threshold": threshold,
        "windows": windows,
        "reasons": reasons,
        "planType": snapshot.get("planType"),
    }


def _version_key(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in text.split("."))


def resolve_model(models: list[dict[str, Any]], tier: str, effort: str | None = None) -> dict[str, Any]:
    family, default_effort = TIERS[tier]
    effort = effort or default_effort
    override = os.environ.get(f"CODEX_MODEL_{tier.upper()}")
    pattern = re.compile(rf"^gpt-(\d+(?:\.\d+)*)-{family}$")
    chosen: dict[str, Any] | None = None
    if override:
        chosen = next((m for m in models if m.get("id") == override), {"id": override, "supportedReasoningEfforts": []})
    else:
        candidates = [
            (_version_key(match.group(1)), model)
            for model in models
            if not model.get("hidden") and (match := pattern.match(str(model.get("id", ""))))
        ]
        if candidates:
            chosen = max(candidates, key=lambda item: item[0])[1]
    if not chosen:
        raise ToolError(f"no Codex model found for tier {tier!r} (family {family})")
    efforts = [e.get("reasoningEffort") for e in chosen.get("supportedReasoningEfforts") or []]
    if efforts and effort not in efforts:
        raise ToolError(f"model {chosen['id']} does not support reasoning effort {effort!r}")
    return {"tier": tier, "model": chosen["id"], "effort": effort, "override": bool(override)}


def classify_liveness(returncode: int, output: str) -> str:
    if returncode == 0:
        return "live"
    return "logged_out" if LOGGED_OUT_RE.search(output) else "error"


# --- checks ------------------------------------------------------------------------------


def liveness() -> dict[str, Any]:
    if not auth_usable(parse_auth(read_local())):
        return {"state": "logged_out", "detail": "no usable ~/.codex/auth.json"}
    try:
        proc = subprocess.run(
            [codex_bin(), "cloud", "list", "--json", "--limit", "1"],
            capture_output=True,
            text=True,
            timeout=90,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"state": "error", "detail": "codex cloud list timed out"}
    output = f"{proc.stderr}\n{proc.stdout if proc.returncode else ''}"
    state = classify_liveness(proc.returncode, output)
    detail = "" if state == "live" else (proc.stderr.strip().splitlines() or [""])[-1][:300]
    return {"state": state, "detail": detail}


def gate(threshold: int = DEFAULT_THRESHOLD) -> tuple[int, dict[str, Any]]:
    decision: dict[str, Any] = {"checkedAt": now_iso(), "threshold": threshold}
    try:
        decision["auth"] = sync_auth()
        if not decision["auth"]["usable"]:
            return _stop(decision, "no_usable_sign_in")
        decision["liveness"] = liveness()
        if decision["liveness"]["state"] == "logged_out":
            return _stop(decision, "liveness_logged_out")
        if decision["liveness"]["state"] != "live":
            return _overflow(decision, ["liveness_error"])
        try:
            allowance = evaluate_allowance(read_rate_limits(), threshold)
        except LoggedOut:
            return _stop(decision, "rate_limits_logged_out")
        except (AppServerError, OSError) as exc:
            decision["allowance"] = {"error": str(exc)[:300]}
            return _overflow(decision, ["allowance_unreadable"])
        decision["allowance"] = allowance
        if not allowance["allowed"]:
            return _overflow(decision, allowance["reasons"])
        decision.update(route="codex", askCarlos=False, reasons=[])
        return EXIT_CODEX, decision
    finally:
        with contextlib.suppress(Exception):
            decision["authAfter"] = sync_auth()


def _stop(decision: dict[str, Any], reason: str) -> tuple[int, dict[str, Any]]:
    decision.update(route="stop", askCarlos=True, reasons=[reason], message=ASK_CARLOS)
    return EXIT_ASK_CARLOS, decision


def _overflow(decision: dict[str, Any], reasons: list[str]) -> tuple[int, dict[str, Any]]:
    decision.update(route="cursor-002", askCarlos=False, reasons=reasons)
    return EXIT_OVERFLOW, decision


# --- worktree runner ---------------------------------------------------------------------


def git(*args: str, cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)
    if check and proc.returncode != 0:
        raise ToolError(f"git {' '.join(args)} failed: {proc.stderr.strip()[:500]}")
    return proc


def remote_has_branch(repo: Path, branch: str) -> bool:
    return git("ls-remote", "--exit-code", "--heads", "origin", branch, cwd=repo, check=False).returncode == 0


def default_base(repo: Path) -> str:
    return "development" if remote_has_branch(repo, "development") else "main"


def prepare_worktree(repo: Path, branch: str, base: str, path: Path) -> dict[str, Any]:
    git("fetch", "--quiet", "origin", base, cwd=repo)
    if path.exists():
        current = git("rev-parse", "--abbrev-ref", "HEAD", cwd=path).stdout.strip()
        if current != branch:
            raise ToolError(f"{path} exists on branch {current}, expected {branch}")
        return {"path": str(path), "created": False, "start": "existing"}
    path.parent.mkdir(parents=True, exist_ok=True)
    if git("rev-parse", "--verify", "--quiet", f"refs/heads/{branch}", cwd=repo, check=False).returncode == 0:
        git("worktree", "add", str(path), branch, cwd=repo)
        start = f"local {branch}"
    elif remote_has_branch(repo, branch):
        git("fetch", "--quiet", "origin", branch, cwd=repo)
        git("worktree", "add", "--no-track", "-b", branch, str(path), f"origin/{branch}", cwd=repo)
        start = f"origin/{branch}"
    else:
        git("worktree", "add", "--no-track", "-b", branch, str(path), f"origin/{base}", cwd=repo)
        start = f"origin/{base}"
    return {"path": str(path), "created": True, "start": start}


def build_prompt(issue_prompt: str, issue: str, branch: str, worktree: Path) -> str:
    return (
        f"{issue_prompt.rstrip()}\n\n"
        "--- IDE Development runner rules ---\n"
        f"- Ledger ID: {issue}. Branch: {branch}. Work only inside this worktree: {worktree}.\n"
        f'- Commit early and often on this branch with messages starting "{issue}: ". '
        "Do not push, open PRs, or switch branches; the runner pushes for you.\n"
        "- Run the repo's fast checks relevant to your change before your final commit.\n"
        "- Never read, copy, or print credentials (for example ~/.codex/auth.json or /cursor/stores/*/private).\n"
        '- End your final message with a short "Lessons:" note (at most 5 bullets), then a last line exactly:\n'
        "  MODEL_SELF_REPORT: <your model name and reasoning effort>\n"
    )


def extract_usage(events_path: Path) -> dict[str, Any] | None:
    usage = None
    if not events_path.exists():
        return None
    for line in events_path.read_text(errors="replace").splitlines():
        with contextlib.suppress(ValueError):
            event = json.loads(line)
            if isinstance(event, dict) and isinstance(event.get("usage"), dict):
                usage = event["usage"]
    return usage


def push_branch(worktree: Path, branch: str) -> bool:
    for delay in (0, 4, 8, 16, 32):
        time.sleep(delay)
        if git("push", "--quiet", "-u", "origin", branch, cwd=worktree, check=False).returncode == 0:
            return True
    return False


def append_run_log(record: dict[str, Any], path: Path | None = None) -> Path:
    target = path or Path(os.environ.get("IDE_CODEX_RUN_LOG") or state_dir() / "runs.jsonl")
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "a") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
    return target


def run_issue(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    if not ISSUE_RE.match(args.issue) or not SLUG_RE.match(args.slug):
        raise ToolError("--issue must look like IDE-42 and --slug like fix-login")
    repo = Path(git("rev-parse", "--show-toplevel", cwd=Path(args.repo)).stdout.strip())
    if not args.skip_gate:
        code, decision = gate(args.threshold)
        if code != EXIT_CODEX:
            return code, {"issue": args.issue, "dispatched": False, "gate": decision}
    resolved = resolve_model(list_models(), args.tier, args.effort)
    branch = f"issue/{args.issue}-{args.slug}"
    base = args.base or default_base(repo)
    root = Path(args.worktree_root or Path.home() / "codex-worktrees" / repo.name)
    worktree = Path(prepare_worktree(repo, branch, base, root / f"{args.issue}-{args.slug}")["path"])
    head_before = git("rev-parse", "HEAD", cwd=worktree).stdout.strip()
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = state_dir() / "runs" / f"{args.issue}-{args.slug}-{stamp}-{os.getpid()}"
    run_dir.mkdir(parents=True, exist_ok=True)
    prompt = build_prompt(Path(args.prompt_file).read_text(), args.issue, branch, worktree)
    (run_dir / "prompt.md").write_text(prompt)
    common_dir = Path(git("rev-parse", "--path-format=absolute", "--git-common-dir", cwd=worktree).stdout.strip())
    cmd = [
        codex_bin(), "exec",
        "-C", str(worktree),
        "-m", resolved["model"],
        "-c", f'model_reasoning_effort="{resolved["effort"]}"',
        "-c", 'approval_policy="never"',
        "-s", "workspace-write",
        "--add-dir", str(common_dir),
        "--json",
        "-o", str(run_dir / "last-message.md"),
    ]
    if args.network:
        cmd += ["-c", "sandbox_workspace_write.network_access=true"]
    cmd.append("-")
    started = time.monotonic()
    record: dict[str, Any] = {
        "issue": args.issue,
        "branch": branch,
        "base": base,
        "executor": "codex-cli",
        "tier": args.tier,
        "requestedModel": resolved["model"],
        "requestedEffort": resolved["effort"],
        "startedAt": now_iso(),
        "worktree": str(worktree),
        "runDir": str(run_dir),
    }
    try:
        with open(run_dir / "events.jsonl", "w") as out, open(run_dir / "stderr.log", "w") as err:
            try:
                proc = subprocess.run(cmd, input=prompt, stdout=out, stderr=err, text=True, timeout=args.timeout, check=False)
                record["codexExit"] = proc.returncode
            except subprocess.TimeoutExpired:
                record["codexExit"] = 124
    finally:
        with contextlib.suppress(Exception):
            record["authSync"] = sync_auth()["action"]
    record["durationSec"] = round(time.monotonic() - started, 1)
    if git("status", "--porcelain", cwd=worktree).stdout.strip():
        git("add", "-A", cwd=worktree)
        autosave = git("commit", "--quiet", "-m", f"{args.issue}: WIP autosave by codex runner", cwd=worktree, check=False)
        record["autosaveCommit"] = autosave.returncode == 0
    head_after = git("rev-parse", "HEAD", cwd=worktree).stdout.strip()
    record["head"] = head_after
    record["newCommits"] = int(git("rev-list", "--count", f"{head_before}..{head_after}", cwd=worktree).stdout.strip() or 0)
    record["pushed"] = False
    if not args.no_push and head_after != head_before:
        record["pushed"] = push_branch(worktree, branch)
    last = run_dir / "last-message.md"
    match = SELF_REPORT_RE.search(last.read_text(errors="replace")) if last.exists() else None
    record["selfReport"] = match.group(1).strip() if match else None
    record["usage"] = extract_usage(run_dir / "events.jsonl")
    record["endedAt"] = now_iso()
    ok = record["codexExit"] == 0 and (args.no_push or head_after == head_before or record["pushed"])
    record["result"] = "success" if ok else "failed"
    record["runLog"] = str(append_run_log(record))
    return (EXIT_CODEX if ok else EXIT_ATTEMPT_FAILED), record


# --- parallel test ------------------------------------------------------------------------


PTEST_PROMPT = (
    "Create a file named PTEST.md at the repository root containing exactly one line: "
    "'parallel test {label}'. Commit it with the message '{issue}: ptest {label}'. Do nothing else."
)


def parallel_test(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    code, decision = gate(args.threshold)
    if code != EXIT_CODEX:
        return code, {"ran": False, "gate": decision}
    repo = Path(git("rev-parse", "--show-toplevel", cwd=Path(args.repo)).stdout.strip())
    root = Path(args.worktree_root or Path.home() / "codex-worktrees" / f"{repo.name}-ptest")
    prompts = state_dir() / "ptest"
    prompts.mkdir(parents=True, exist_ok=True)
    script = str(Path(__file__).resolve())
    results: dict[str, Any] = {"startedAt": now_iso(), "tier": args.tier, "levels": []}

    def one(n: int, i: int, issue: str) -> dict[str, Any]:
        label = f"n{n}-{i}"
        prompt_file = prompts / f"{label}.md"
        prompt_file.write_text(PTEST_PROMPT.format(label=label, issue=issue))
        cmd = [
            sys.executable, script, "run", "--skip-gate", "--no-push",
            "--repo", str(repo), "--issue", issue, "--slug", f"ptest-{label}",
            "--tier", args.tier, "--prompt-file", str(prompt_file), "--worktree-root", str(root),
        ]
        start = time.monotonic()
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        entry: dict[str, Any] = {"issue": issue, "label": label, "exit": proc.returncode, "wallSec": round(time.monotonic() - start, 1)}
        with contextlib.suppress(ValueError):
            record = json.loads(proc.stdout)
            entry.update({k: record.get(k) for k in ("codexExit", "newCommits", "durationSec", "runDir", "usage")})
            stderr_log = Path(record.get("runDir", "")) / "stderr.log"
            if stderr_log.exists():
                text = stderr_log.read_text(errors="replace")
                entry["rateLimited"] = bool(re.search(r"rate.?limit|429|too many requests|concurren", text, re.I))
        return entry

    overall = EXIT_CODEX
    next_issue = args.first_issue
    for n in args.counts:
        issues = [f"{args.prefix}-{next_issue + k}" for k in range(n)]
        next_issue += n
        before = evaluate_allowance(read_rate_limits(), args.threshold)
        start = time.monotonic()
        with concurrent.futures.ThreadPoolExecutor(max_workers=n) as pool:
            runs = list(pool.map(lambda i: one(n, i, issues[i - 1]), range(1, n + 1)))
        after = evaluate_allowance(read_rate_limits(), args.threshold)
        level = {
            "concurrency": n,
            "wallSec": round(time.monotonic() - start, 1),
            "succeeded": sum(1 for r in runs if r["exit"] == 0 and (r.get("newCommits") or 0) > 0),
            "runs": runs,
            "allowanceBefore": before["windows"],
            "allowanceAfter": after["windows"],
        }
        results["levels"].append(level)
        if not args.keep:
            for i, issue in enumerate(issues, start=1):
                label = f"n{n}-{i}"
                git("worktree", "remove", "--force", str(root / f"{issue}-ptest-{label}"), cwd=repo, check=False)
                git("branch", "-D", f"issue/{issue}-ptest-{label}", cwd=repo, check=False)
        if level["succeeded"] < n or not after["allowed"]:
            overall = EXIT_ATTEMPT_FAILED
            results["stoppedAt"] = n
            break
    results["maxCleanConcurrency"] = max(
        [lvl["concurrency"] for lvl in results["levels"] if lvl["succeeded"] == lvl["concurrency"]], default=0
    )
    results["endedAt"] = now_iso()
    out = state_dir() / f"ptest-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(results, indent=2))
    results["resultFile"] = str(out)
    return overall, results


# --- CLI ----------------------------------------------------------------------------------


def login() -> tuple[int, dict[str, Any]]:
    proc = subprocess.run([codex_bin(), "login", "--device-auth"], check=False)
    if proc.returncode != 0:
        return EXIT_ASK_CARLOS, {"login": "failed", "exit": proc.returncode}
    with auth_lock():
        fresh = read_local()
        if not auth_usable(parse_auth(fresh)):
            return EXIT_ASK_CARLOS, {"login": "no usable auth.json written"}
        write_store(fresh or b"")
    synced = sync_auth()
    live = liveness()
    return (EXIT_CODEX if live["state"] == "live" else EXIT_ASK_CARLOS), {"login": "ok", "auth": synced, "liveness": live}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("auth-status", "auth-restore", "auth-save", "login", "liveness"):
        sub.add_parser(name)
    for name in ("allowance", "gate"):
        sub.add_parser(name).add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD)
    models = sub.add_parser("models")
    models.add_argument("--tier", choices=sorted(TIERS), action="append")
    run = sub.add_parser("run")
    run.add_argument("--issue", required=True, help="Ledger ID, e.g. IDE-42")
    run.add_argument("--slug", required=True)
    run.add_argument("--prompt-file", required=True)
    run.add_argument("--tier", choices=sorted(TIERS), default="luna", help="luna = default, sol = hard Issues")
    run.add_argument("--effort", help="override the tier's reasoning effort")
    run.add_argument("--repo", default=".")
    run.add_argument("--base", help="base branch (default: development if it exists, else main)")
    run.add_argument("--worktree-root")
    run.add_argument("--timeout", type=int, default=3600)
    run.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD)
    run.add_argument("--network", action="store_true", help="allow network inside the Codex sandbox")
    run.add_argument("--no-push", action="store_true")
    run.add_argument("--skip-gate", action="store_true", help="skip liveness/allowance (caller already gated)")
    ptest = sub.add_parser("parallel-test")
    ptest.add_argument("--counts", type=lambda s: [int(x) for x in s.split(",")], default=[1, 2, 4])
    ptest.add_argument("--tier", choices=sorted(TIERS), default="luna")
    ptest.add_argument("--repo", default=".")
    ptest.add_argument("--worktree-root")
    ptest.add_argument("--threshold", type=int, default=DEFAULT_THRESHOLD)
    ptest.add_argument("--prefix", default="IDE", help="Ledger ID prefix for throwaway test Issues")
    ptest.add_argument("--first-issue", type=int, default=10, help="first throwaway Issue number")
    ptest.add_argument("--keep", action="store_true", help="keep test worktrees and local branches")
    return parser


def dispatch(args: argparse.Namespace) -> tuple[int, Any]:
    command = args.command
    if command == "auth-status":
        return EXIT_CODEX, auth_status()
    if command in ("auth-restore", "auth-save"):
        result = sync_auth()
        return (EXIT_CODEX if result["usable"] else EXIT_ASK_CARLOS), result
    if command == "login":
        return login()
    if command == "liveness":
        result = liveness()
        code = {"live": EXIT_CODEX, "logged_out": EXIT_ASK_CARLOS}.get(result["state"], EXIT_OVERFLOW)
        return code, result
    if command == "allowance":
        try:
            result = evaluate_allowance(read_rate_limits(), args.threshold)
        except LoggedOut:
            return EXIT_ASK_CARLOS, {"allowed": False, "askCarlos": True, "message": ASK_CARLOS}
        return (EXIT_CODEX if result["allowed"] else EXIT_OVERFLOW), result
    if command == "models":
        catalog = list_models()
        return EXIT_CODEX, [resolve_model(catalog, tier) for tier in (args.tier or sorted(TIERS))]
    if command == "gate":
        return gate(args.threshold)
    if command == "run":
        return run_issue(args)
    if command == "parallel-test":
        return parallel_test(args)
    raise ToolError(f"unknown command {command}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        code, payload = dispatch(args)
    except (ToolError, AppServerError, OSError) as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return EXIT_ERROR
    print(json.dumps(payload, indent=2, sort_keys=True))
    return code


if __name__ == "__main__":
    sys.exit(main())
