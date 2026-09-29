#!/usr/bin/env python3
"""cursor-002 dispatch client (IDE Development v3, Wave 0.3).

Create, poll, read and archive Cursor Cloud Agents on the cursor-002 account via
``https://api.cursor.com/v1``. Standard library only.

Key: ``CURSOR_002_API_KEY`` (never printed). Output is JSON on stdout.

Pinned routes (plan, "Ground rules for every Wave"):
  grok-medium  -> grok-4.7        context=500k reasoning_effort=medium fast=false
  opus-medium  -> claude-opus-5-5 context=1m   effort=medium           fast=false
The model ID and parameter variant are re-validated against ``GET /v1/models`` at
every dispatch; aliases such as ``opus`` / ``opus-latest`` are refused.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

API_BASE = os.environ.get("CURSOR_API_BASE", "https://api.cursor.com")
KEY_ENV = "CURSOR_002_API_KEY"
CREATE_TIMEOUT_S = 180
DEFAULT_TIMEOUT_S = 60
TERMINAL_RUN_STATES = {"FINISHED", "ERROR", "CANCELLED", "EXPIRED"}
SELF_REPORT_TAG = "MODEL-SELF-REPORT:"
SETUP_MARKER = "~/.cache/ide-development/setup-done.json"
BRANCH_RE = re.compile(r"^issue/[A-Z][A-Z0-9]*-\d+-[a-z0-9][a-z0-9-]*$")

ROUTES: dict[str, dict[str, Any]] = {
    "grok-medium": {
        "family": "grok-4.7",
        "params": {"context": "500k", "reasoning_effort": "medium", "fast": "false"},
    },
    "opus-medium": {
        "family": "claude-opus-5-5",
        "params": {"context": "1m", "effort": "medium", "fast": "false"},
    },
}
FORBIDDEN_MODEL_IDS = {"opus", "opus-latest", "gpt", "gpt-latest", "sonnet", "sonnet-latest"}


class DispatchError(RuntimeError):
    def __init__(self, code: str, message: str, **detail: Any) -> None:
        super().__init__(message)
        self.code = code
        self.detail = detail

    def as_dict(self) -> dict[str, Any]:
        return {"ok": False, "error": self.code, "message": str(self), **self.detail}


# --------------------------------------------------------------------------- HTTP


class Client:
    def __init__(self, api_key: str, base: str = API_BASE) -> None:
        if not api_key:
            raise DispatchError("missing_api_key", f"{KEY_ENV} is not set")
        self._key = api_key
        self.base = base.rstrip("/")

    def request(
        self,
        method: str,
        path: str,
        body: Mapping[str, Any] | None = None,
        *,
        timeout: float = DEFAULT_TIMEOUT_S,
    ) -> tuple[int, Any]:
        headers = {"Authorization": f"Bearer {self._key}", "Accept": "application/json"}
        data = None
        # Archive and other bodiless POSTs must not carry a JSON Content-Type (API returns 400).
        if body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(self.base + path, data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
                status = resp.status
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            status = exc.code
        try:
            payload = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            payload = {"raw": raw[:500].decode(errors="replace")}
        return status, payload

    def get(self, path: str) -> Any:
        status, payload = self.request("GET", path)
        if status != 200:
            raise DispatchError("http_error", f"GET {path} returned {status}", status=status, body=payload)
        return payload


# ------------------------------------------------------------------ model routing


def resolve_model(models_payload: Any, route: str) -> dict[str, Any]:
    """Validate the pinned route against the live ``/v1/models`` list."""
    if route not in ROUTES:
        raise DispatchError("unknown_route", f"route must be one of {sorted(ROUTES)}", route=route)
    pinned = ROUTES[route]
    model_id = pinned["family"]
    if model_id in FORBIDDEN_MODEL_IDS:
        raise DispatchError("alias_forbidden", f"{model_id} is an alias; pin an exact ID")
    items = _model_items(models_payload)
    match = next((m for m in items if m.get("id") == model_id), None)
    if match is None:
        raise DispatchError(
            "model_unavailable",
            f"{model_id} is not listed by GET /v1/models; the provider may have renamed it",
            available=sorted(str(m.get("id")) for m in items),
        )
    wanted = dict(pinned["params"])
    variants = [_variant_params(v) for v in match.get("variants") or []]
    if variants and wanted not in variants:
        raise DispatchError(
            "variant_unavailable",
            f"{model_id} has no variant {wanted}",
            variants=variants,
        )
    return {
        "route": route,
        "id": model_id,
        "params": [{"id": k, "value": v} for k, v in wanted.items()],
    }


def _model_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [m for m in payload if isinstance(m, dict)]
    if isinstance(payload, dict):
        for key in ("items", "models", "data"):
            if isinstance(payload.get(key), list):
                return [m for m in payload[key] if isinstance(m, dict)]
    return []


def _variant_params(variant: Any) -> dict[str, str]:
    params = variant.get("params") if isinstance(variant, dict) else variant
    if isinstance(params, dict):
        return {str(k): str(v).lower() for k, v in params.items()}
    if isinstance(params, list):
        return {str(p.get("id")): str(p.get("value")).lower() for p in params if isinstance(p, dict)}
    return {}


# ----------------------------------------------------------------------- prompts


def build_prompt(issue_text: str, *, issue_id: str | None, branch: str | None) -> str:
    rules = [
        "You are a worker for IDE Development. Follow these rules exactly:",
        # cursor-002 has no registered environment build yet, so the repo install never ran.
        f"- First, if `{SETUP_MARKER}` does not exist and `scripts/setup.sh` exists, run `bash scripts/setup.sh`.",
        "- Do not open pull requests.",
        "- Commit small, clear commits and push often.",
    ]
    if branch:
        rules.append(f"- Work only on branch `{branch}` (already checked out); push to it. Do not create other branches.")
    if issue_id:
        rules.append(f"- Prefix commit messages with `{issue_id}: `.")
    rules += [
        "- Run the fast checks named in the Issue before your final push.",
        "- End your final reply with a short lessons note, then one last line exactly:",
        f"  `{SELF_REPORT_TAG} <the exact model name and version you are>`",
    ]
    return "\n".join(rules) + "\n\n--- ISSUE ---\n" + issue_text.strip() + "\n"


def extract_self_report(text: str | None) -> str | None:
    if not text:
        return None
    for line in reversed(text.strip().splitlines()):
        idx = line.find(SELF_REPORT_TAG)
        if idx >= 0:
            return line[idx + len(SELF_REPORT_TAG):].strip().strip("`").strip() or None
    return None


# ------------------------------------------------------------------------ git


def ensure_remote_branch(repo_url: str, branch: str, base_ref: str, *, git_dir: str | None) -> str:
    """Create ``branch`` on the remote from ``base_ref`` if missing. Returns the tip SHA."""
    if not BRANCH_RE.match(branch):
        raise DispatchError("bad_branch", "branch must look like issue/IDE-<n>-<slug>", branch=branch)
    remote = repo_url if repo_url.endswith(".git") else repo_url + ".git"
    ls = _git(["ls-remote", "--heads", remote, branch], git_dir)
    if ls.strip():
        return ls.split()[0]
    _git(["fetch", "--quiet", remote, base_ref], git_dir)
    sha = _git(["rev-parse", "FETCH_HEAD"], git_dir).strip()
    _git(["push", "--quiet", remote, f"{sha}:refs/heads/{branch}"], git_dir)
    return sha


def _git(args: Sequence[str], git_dir: str | None) -> str:
    cmd = ["git"] + (["-C", git_dir] if git_dir else []) + list(args)
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise DispatchError("git_failed", f"git {' '.join(args[:2])} failed", stderr=proc.stderr[-500:])
    return proc.stdout


# ------------------------------------------------------------------- operations


def create_agent(
    client: Client,
    *,
    route: str,
    prompt: str,
    repo_url: str | None,
    ref: str | None,
    work_on_current_branch: bool,
    name: str | None,
) -> dict[str, Any]:
    model = resolve_model(client.get("/v1/models"), route)
    agent_id = f"bc-{uuid.uuid4()}"
    body: dict[str, Any] = {
        "agentId": agent_id,
        "prompt": {"text": prompt},
        "model": {"id": model["id"], "params": model["params"]},
        "autoCreatePR": False,
    }
    if name:
        body["name"] = name[:100]
    if repo_url:
        repo: dict[str, Any] = {"url": repo_url}
        if ref:
            repo["startingRef"] = ref
        body["repos"] = [repo]
        body["workOnCurrentBranch"] = work_on_current_branch
    status, payload = _create_with_retry(client, body, agent_id)
    agent = payload.get("agent", payload) if isinstance(payload, dict) else {}
    run = payload.get("run", {}) if isinstance(payload, dict) else {}
    return {
        "ok": True,
        "createStatus": status,
        "agentId": agent.get("id", agent_id),
        "runId": run.get("id") or agent.get("latestRunId"),
        "url": agent.get("url", f"https://cursor.com/agents/{agent_id}"),
        "requestedModel": {"id": model["id"], "params": {p["id"]: p["value"] for p in model["params"]}},
        "route": route,
        "repo": repo_url,
        "startingRef": ref,
        "workOnCurrentBranch": work_on_current_branch if repo_url else None,
    }


def _create_with_retry(client: Client, body: Mapping[str, Any], agent_id: str) -> tuple[int, Any]:
    """POST with a client-supplied agentId so a timed-out create can be retried safely."""
    for attempt in range(2):
        try:
            status, payload = client.request("POST", "/v1/agents", body, timeout=CREATE_TIMEOUT_S)
        except (TimeoutError, urllib.error.URLError, OSError):
            if attempt == 0:
                continue
            status, payload = 0, None
        if status in (200, 201):
            return status, payload
        if status == 409 or (status == 0 and attempt == 1):
            agent = client.get(f"/v1/agents/{agent_id}")
            return 200, {"agent": agent}
        raise DispatchError("create_rejected", f"POST /v1/agents returned {status}", status=status, body=payload)
    raise DispatchError("create_failed", "create did not complete")  # pragma: no cover


def read_result(client: Client, agent_id: str, run_id: str | None = None) -> dict[str, Any]:
    agent = client.get(f"/v1/agents/{agent_id}")
    run_id = run_id or agent.get("latestRunId")
    run = client.get(f"/v1/agents/{agent_id}/runs/{run_id}") if run_id else {}
    usage = None
    try:
        usage = client.get(f"/v1/agents/{agent_id}/usage").get("totalUsage")
    except DispatchError:
        pass
    text = run.get("result")
    return {
        "ok": True,
        "agentId": agent_id,
        "agentStatus": agent.get("status"),
        "runId": run_id,
        "runStatus": run.get("status"),
        "terminal": run.get("status") in TERMINAL_RUN_STATES,
        "durationMs": run.get("durationMs"),
        "branches": (run.get("git") or {}).get("branches", []),
        "selfReportedModel": extract_self_report(text),
        "usage": usage,
        "result": text,
        "url": agent.get("url"),
    }


def poll(
    client: Client, agent_id: str, *, interval: float, timeout: float, run_id: str | None = None
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while True:
        res = read_result(client, agent_id, run_id)
        if res["terminal"]:
            return res
        if time.monotonic() >= deadline:
            res["ok"] = False
            res["error"] = "poll_timeout"
            return res
        time.sleep(interval)


def followup(client: Client, agent_id: str, prompt: str) -> dict[str, Any]:
    status, payload = client.request(
        "POST", f"/v1/agents/{agent_id}/runs", {"prompt": {"text": prompt}}, timeout=CREATE_TIMEOUT_S
    )
    if status not in (200, 201):
        raise DispatchError("followup_rejected", f"create run returned {status}", status=status, body=payload)
    run = payload.get("run", {}) if isinstance(payload, dict) else {}
    return {"ok": True, "agentId": agent_id, "runId": run.get("id")}


def archive(client: Client, agent_id: str) -> dict[str, Any]:
    status, payload = client.request("POST", f"/v1/agents/{agent_id}/archive")
    if status != 200:
        raise DispatchError("archive_failed", f"archive returned {status}", status=status, body=payload)
    return {"ok": True, "agentId": agent_id, "archived": True}


def append_run_log(path: str, record: Mapping[str, Any]) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    entry = {"loggedAt": datetime.now(timezone.utc).isoformat(timespec="seconds"), **record}
    entry.pop("result", None)
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, sort_keys=True) + "\n")


# ------------------------------------------------------------------------- CLI


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("resolve", help="validate a route against GET /v1/models")
    m.add_argument("--route", choices=sorted(ROUTES), default="grok-medium")

    c = sub.add_parser("create", help="create an agent and enqueue its first run")
    c.add_argument("--route", choices=sorted(ROUTES), default="grok-medium")
    src = c.add_mutually_exclusive_group(required=True)
    src.add_argument("--prompt-file")
    src.add_argument("--prompt")
    c.add_argument("--raw-prompt", action="store_true", help="send the prompt without the worker wrapper")
    c.add_argument("--repo", help="e.g. https://github.com/linktrend/IDE-Development")
    c.add_argument("--ref", help="starting branch or SHA (base for --branch)")
    c.add_argument("--branch", help="issue/IDE-<n>-<slug>: created from --ref if missing; agent pushes to it")
    c.add_argument("--issue-id", help="Ledger ID, e.g. IDE-9")
    c.add_argument("--name")
    c.add_argument("--git-dir", help="local clone used to create --branch (default: cwd)")
    c.add_argument("--wait", action="store_true", help="poll until the run is terminal")
    c.add_argument("--interval", type=float, default=30)
    c.add_argument("--timeout", type=float, default=3600)
    c.add_argument("--run-log", help="append a JSONL run-log record")

    for name, help_ in (("status", "read agent/run state and result"), ("poll", "wait for a terminal run")):
        s = sub.add_parser(name, help=help_)
        s.add_argument("agent_id")
        s.add_argument("--run-id")
        s.add_argument("--interval", type=float, default=30)
        s.add_argument("--timeout", type=float, default=3600)
        s.add_argument("--run-log")

    f = sub.add_parser("followup", help="send a follow-up run to an idle agent (e.g. a repair attempt)")
    f.add_argument("agent_id")
    fsrc = f.add_mutually_exclusive_group(required=True)
    fsrc.add_argument("--prompt-file")
    fsrc.add_argument("--prompt")
    f.add_argument("--wait", action="store_true")
    f.add_argument("--interval", type=float, default=30)
    f.add_argument("--timeout", type=float, default=3600)
    f.add_argument("--run-log")

    a = sub.add_parser("archive", help="archive an agent")
    a.add_argument("agent_id")
    return p


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        client = Client(os.environ.get(KEY_ENV, ""))
        if args.cmd == "resolve":
            out: dict[str, Any] = {"ok": True, **resolve_model(client.get("/v1/models"), args.route)}
        elif args.cmd == "create":
            text = args.prompt if args.prompt is not None else open(args.prompt_file, encoding="utf-8").read()
            if not args.raw_prompt:
                text = build_prompt(text, issue_id=args.issue_id, branch=args.branch)
            ref = args.ref
            if args.branch:
                if not (args.repo and args.ref):
                    raise DispatchError("missing_args", "--branch needs --repo and --ref")
                ensure_remote_branch(args.repo, args.branch, args.ref, git_dir=args.git_dir)
                ref = args.branch
            out = create_agent(
                client,
                route=args.route,
                prompt=text,
                repo_url=args.repo,
                ref=ref,
                work_on_current_branch=bool(args.branch),
                name=args.name or (f"{args.issue_id} {args.route}" if args.issue_id else None),
            )
            out["issueId"] = args.issue_id
            if args.wait:
                out.update(poll(client, out["agentId"], interval=args.interval, timeout=args.timeout))
            if args.run_log:
                append_run_log(args.run_log, out)
        elif args.cmd in ("status", "poll"):
            if args.cmd == "poll":
                out = poll(client, args.agent_id, interval=args.interval, timeout=args.timeout,
                           run_id=args.run_id)
            else:
                out = read_result(client, args.agent_id, args.run_id)
            if args.run_log:
                append_run_log(args.run_log, out)
        elif args.cmd == "followup":
            text = args.prompt if args.prompt is not None else open(args.prompt_file, encoding="utf-8").read()
            out = followup(client, args.agent_id, text)
            if args.wait:
                out.update(poll(client, args.agent_id, interval=args.interval, timeout=args.timeout,
                                run_id=out["runId"]))
            if args.run_log:
                append_run_log(args.run_log, out)
        else:
            out = archive(client, args.agent_id)
    except DispatchError as exc:
        print(json.dumps(exc.as_dict(), indent=2))
        return 2
    print(json.dumps(out, indent=2))
    return 0 if out.get("ok", True) else 1


if __name__ == "__main__":
    sys.exit(main())
