#!/usr/bin/env python3
"""Pilot run log: one JSON record per Issue attempt, file-backed.

Until ide_ledger is live (v3 Wave 3.1) the orchestrator writes each attempt to
``<root>/<ISSUE>/attempt-<NNN>.json``. The record fields mirror
``ide_ledger.run`` so ``export-sql`` can replay them through the Ledger RPCs
(``start_run`` / ``finish_run``) once the schema is applied.

Root: ``--root``, else ``$IDE_RUNLOG_DIR``, else
``/cursor/stores/self/internal/runlog`` (the orchestrator's Project store).

Only the orchestrator writes here; workers never get Ledger or store access.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SCHEMA = "ide-runlog/v1"
DEFAULT_ROOT = "/cursor/stores/self/internal/runlog"
EXECUTORS = ("codex-cli", "cursor-002", "cursor-001-subagent", "orchestrator", "other")
RESULTS = ("running", "success", "failure", "stalled", "cancelled")
TERMINAL_RESULTS = tuple(r for r in RESULTS if r != "running")
ISSUE_RE = re.compile(r"^[A-Z][A-Z0-9]{1,9}-[1-9][0-9]*$")
SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")
ATTEMPT_RE = re.compile(r"^attempt-([0-9]{3,})\.json$")
MAX_ATTEMPTS = 999

FIELDS = (
    "schema",
    "run_key",
    "issue",
    "attempt",
    "executor",
    "requested_model",
    "reasoning_effort",
    "self_reported_model",
    "repair_rung",
    "branch",
    "external_ref",
    "result",
    "head_sha",
    "failure_summary",
    "cost_usd",
    "started_at",
    "updated_at",
    "ended_at",
)


class RunLogError(ValueError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def resolve_root(root: str | None) -> Path:
    return Path(root or os.environ.get("IDE_RUNLOG_DIR") or DEFAULT_ROOT)


def validate(record: dict[str, Any]) -> dict[str, Any]:
    missing = [f for f in FIELDS if f not in record]
    extra = [f for f in record if f not in FIELDS]
    if missing or extra:
        raise RunLogError(f"record fields mismatch: missing={missing} extra={extra}")
    if record["schema"] != SCHEMA:
        raise RunLogError(f"unsupported schema {record['schema']!r}")
    if not ISSUE_RE.match(str(record["issue"])):
        raise RunLogError(f"issue must look like IDE-<n>, got {record['issue']!r}")
    if not isinstance(record["attempt"], int) or not 1 <= record["attempt"] <= MAX_ATTEMPTS:
        raise RunLogError("attempt must be an integer between 1 and 999")
    if record["executor"] not in EXECUTORS:
        raise RunLogError(f"executor must be one of {EXECUTORS}")
    if not record["requested_model"]:
        raise RunLogError("requested_model is required")
    if record["repair_rung"] not in (0, 1, 2, 3):
        raise RunLogError("repair_rung must be 0..3")
    if record["result"] not in RESULTS:
        raise RunLogError(f"result must be one of {RESULTS}")
    if record["head_sha"] is not None and not SHA_RE.match(record["head_sha"]):
        raise RunLogError("head_sha must be a lowercase hex git SHA")
    if record["cost_usd"] is not None and (
        not isinstance(record["cost_usd"], (int, float)) or record["cost_usd"] < 0
    ):
        raise RunLogError("cost_usd must be a non-negative number")
    if (record["result"] == "running") != (record["ended_at"] is None):
        raise RunLogError("ended_at is set exactly when the result is terminal")
    for key in ("started_at", "updated_at", "ended_at"):
        if record[key] is not None:
            parse_ts(record[key])
    if not 8 <= len(record["run_key"]) <= 80:
        raise RunLogError("run_key must be 8..80 characters")
    return record


def _atomic_write(path: Path, record: dict[str, Any]) -> None:
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".tmp-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(record, handle, indent=2, sort_keys=False)
            handle.write("\n")
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def _attempt_path(root: Path, issue: str, attempt: int) -> Path:
    return root / issue / f"attempt-{attempt:03d}.json"


def iter_records(root: Path, issue: str | None = None) -> Iterable[tuple[Path, dict[str, Any]]]:
    if not root.is_dir():
        return
    issue_dirs = [root / issue] if issue else sorted(p for p in root.iterdir() if p.is_dir())
    for issue_dir in issue_dirs:
        if not issue_dir.is_dir():
            continue
        for path in sorted(issue_dir.iterdir()):
            if not ATTEMPT_RE.match(path.name):
                continue
            text = path.read_text(encoding="utf-8")
            if text.strip():  # empty while start_run is between claim and write
                yield path, json.loads(text)


def find_run(root: Path, issue: str, run_key: str) -> tuple[Path, dict[str, Any]]:
    for path, record in iter_records(root, issue):
        if record.get("run_key") == run_key:
            return path, record
    raise RunLogError(f"no run {run_key!r} for {issue}")


def start_run(
    root: Path,
    *,
    issue: str,
    executor: str,
    requested_model: str,
    reasoning_effort: str | None = None,
    repair_rung: int = 0,
    branch: str | None = None,
    external_ref: str | None = None,
    run_key: str | None = None,
    started_at: str | None = None,
) -> dict[str, Any]:
    now = started_at or utc_now()
    record = {
        "schema": SCHEMA,
        "run_key": run_key or f"run-{uuid.uuid4().hex}",
        "issue": issue,
        "attempt": 1,
        "executor": executor,
        "requested_model": requested_model,
        "reasoning_effort": reasoning_effort,
        "self_reported_model": None,
        "repair_rung": repair_rung,
        "branch": branch or None,
        "external_ref": external_ref,
        "result": "running",
        "head_sha": None,
        "failure_summary": None,
        "cost_usd": None,
        "started_at": now,
        "updated_at": now,
        "ended_at": None,
    }
    validate(record)
    issue_dir = root / issue
    issue_dir.mkdir(parents=True, exist_ok=True)
    for _, existing in iter_records(root, issue):
        if existing.get("run_key") == record["run_key"]:
            return existing
    taken = [int(m.group(1)) for p in issue_dir.iterdir() if (m := ATTEMPT_RE.match(p.name))]
    attempt = max(taken, default=0) + 1
    while attempt <= MAX_ATTEMPTS:
        record["attempt"] = attempt
        path = _attempt_path(root, issue, attempt)
        try:
            # O_EXCL claims the attempt number atomically across concurrent writers.
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        except FileExistsError:
            attempt += 1
            continue
        os.close(fd)
        _atomic_write(path, record)
        return record
    raise RunLogError(f"{issue} exceeded {MAX_ATTEMPTS} attempts")


def heartbeat(root: Path, *, issue: str, run_key: str, head_sha: str | None = None) -> dict[str, Any]:
    path, record = find_run(root, issue, run_key)
    if record["result"] != "running":
        raise RunLogError(f"run {run_key} is already {record['result']}")
    record["updated_at"] = utc_now()
    if head_sha:
        record["head_sha"] = head_sha
    _atomic_write(path, validate(record))
    return record


def finish_run(
    root: Path,
    *,
    issue: str,
    run_key: str,
    result: str,
    self_reported_model: str | None = None,
    head_sha: str | None = None,
    failure_summary: str | None = None,
    cost_usd: float | None = None,
    ended_at: str | None = None,
) -> dict[str, Any]:
    if result not in TERMINAL_RESULTS:
        raise RunLogError(f"finish needs a terminal result {TERMINAL_RESULTS}")
    path, record = find_run(root, issue, run_key)
    if record["result"] != "running":
        if record["result"] == result:
            return record
        raise RunLogError(f"run {run_key} already finished as {record['result']}")
    now = ended_at or utc_now()
    record.update(
        result=result,
        self_reported_model=self_reported_model or record["self_reported_model"],
        head_sha=head_sha or record["head_sha"],
        failure_summary=failure_summary,
        cost_usd=cost_usd,
        updated_at=now,
        ended_at=now,
    )
    _atomic_write(path, validate(record))
    return record


def _sql(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    return "'" + str(value).replace("'", "''") + "'"


def export_sql(root: Path) -> str:
    """Replays the file log through the Ledger RPCs. Idempotent on run_key."""
    lines = ["begin;"]
    for _, rec in iter_records(root):
        validate(rec)
        lines.append(
            "select ide_ledger.start_run("
            + ", ".join(
                _sql(v)
                for v in (
                    rec["run_key"],
                    rec["issue"],
                    rec["executor"],
                    rec["requested_model"],
                    rec["reasoning_effort"],
                    rec["repair_rung"],
                    rec["branch"],
                    rec["external_ref"],
                )
            )
            + f", {_sql(rec['started_at'])}::timestamptz);"
        )
        if rec["result"] != "running":
            lines.append(
                "select ide_ledger.finish_run("
                + ", ".join(
                    _sql(v)
                    for v in (
                        rec["run_key"],
                        rec["result"],
                        rec["self_reported_model"],
                        rec["head_sha"],
                        rec["failure_summary"],
                    )
                )
                + f", {_sql(rec['cost_usd'])}::numeric, {_sql(rec['ended_at'])}::timestamptz);"
            )
    lines.append("commit;")
    return "\n".join(lines) + "\n"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", help="run-log directory (default $IDE_RUNLOG_DIR or the Project store)")
    sub = parser.add_subparsers(dest="command", required=True)

    start = sub.add_parser("start", help="open a new attempt")
    start.add_argument("--issue", required=True)
    start.add_argument("--executor", required=True, choices=EXECUTORS)
    start.add_argument("--requested-model", required=True)
    start.add_argument("--reasoning-effort")
    start.add_argument("--repair-rung", type=int, default=0)
    start.add_argument("--branch")
    start.add_argument("--external-ref", help="agent id, codex session id, ...")
    start.add_argument("--run-key")

    beat = sub.add_parser("heartbeat", help="mark a running attempt as alive")
    beat.add_argument("--issue", required=True)
    beat.add_argument("--run-key", required=True)
    beat.add_argument("--head-sha")

    finish = sub.add_parser("finish", help="close an attempt")
    finish.add_argument("--issue", required=True)
    finish.add_argument("--run-key", required=True)
    finish.add_argument("--result", required=True, choices=TERMINAL_RESULTS)
    finish.add_argument("--self-reported-model")
    finish.add_argument("--head-sha")
    finish.add_argument("--failure-summary")
    finish.add_argument("--cost-usd", type=float)

    lst = sub.add_parser("list", help="print records as JSON lines")
    lst.add_argument("--issue")

    sub.add_parser("export-sql", help="print Ledger RPC calls replaying the log")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = resolve_root(args.root)
    try:
        if args.command == "start":
            out = start_run(
                root,
                issue=args.issue,
                executor=args.executor,
                requested_model=args.requested_model,
                reasoning_effort=args.reasoning_effort,
                repair_rung=args.repair_rung,
                branch=args.branch,
                external_ref=args.external_ref,
                run_key=args.run_key,
            )
        elif args.command == "heartbeat":
            out = heartbeat(root, issue=args.issue, run_key=args.run_key, head_sha=args.head_sha)
        elif args.command == "finish":
            out = finish_run(
                root,
                issue=args.issue,
                run_key=args.run_key,
                result=args.result,
                self_reported_model=args.self_reported_model,
                head_sha=args.head_sha,
                failure_summary=args.failure_summary,
                cost_usd=args.cost_usd,
            )
        elif args.command == "list":
            for _, record in iter_records(root, args.issue):
                print(json.dumps(record, sort_keys=True))
            return 0
        else:
            sys.stdout.write(export_sql(root))
            return 0
    except RunLogError as exc:
        print(f"runlog: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(out, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
