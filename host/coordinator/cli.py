"""Command line interface for the local coordinator."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .daemon import CoordinatorDaemon
from .queue import QueueRequest, priority_for


def _json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, default=str)


def _daemon(args: argparse.Namespace) -> CoordinatorDaemon:
    return CoordinatorDaemon(args.db)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ide-coordinator", description="Bounded LiNKtrend local delivery coordinator")
    parser.add_argument("--db", default="~/.linktrend/ide-coordinator/coordinator.sqlite3", help="scoped SQLite database path")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="show persisted queue and registry state")
    sub.add_parser("pause", help="pause new job execution")
    sub.add_parser("resume", help="resume new job execution")
    doctor = sub.add_parser("doctor", help="run local fail-closed diagnostics")
    doctor.add_argument("--register", nargs=3, metavar=("REPOSITORY", "ROOT", "DEFAULT_BRANCH"), help="register one allowlisted repository")
    enqueue = sub.add_parser("enqueue", help="enqueue an exact candidate gate")
    enqueue.add_argument("repository")
    enqueue.add_argument("gate")
    enqueue.add_argument("identity", help="candidate identity JSON file")
    enqueue.add_argument("--priority", type=int)
    enqueue.add_argument("--pr-number", type=int)
    enqueue.add_argument("--phase-id")
    enqueue.add_argument("--candidate-command", dest="candidate_command", nargs="+", default=["true"])
    cancel = sub.add_parser("cancel", help="cancel queued or running obsolete work")
    cancel.add_argument("repository")
    cancel.add_argument("--pr-number", type=int)
    cancel.add_argument("--identity", help="live candidate identity JSON file")
    approve = sub.add_parser("approve-main", help="record exact-bound principal approval")
    approve.add_argument("approval", help="approval JSON file")
    approve.add_argument("--staging-source-sha", required=True)
    approve.add_argument("--main-base-sha", required=True)
    approve.add_argument("--pr-head-sha", required=True)
    approve.add_argument("--receipt-identity", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    daemon = _daemon(args)
    try:
        if args.command == "status":
            print(_json(daemon.status()))
        elif args.command == "pause":
            daemon.pause()
            print(_json({"paused": True}))
        elif args.command == "resume":
            daemon.resume()
            print(_json({"paused": False}))
        elif args.command == "doctor":
            if args.register:
                daemon.register(*args.register)
            result = daemon.doctor()
            print(_json(result))
            return 0 if result.get("ok") else 1
        elif args.command == "enqueue":
            identity = json.loads(Path(args.identity).read_text(encoding="utf-8"))
            priority = args.priority if args.priority is not None else priority_for(args.gate)
            result = daemon.enqueue_request(QueueRequest(args.repository, args.gate, identity, priority=priority, pr_number=args.pr_number, phase_id=args.phase_id, payload={"command": args.candidate_command}))
            print(_json(result.__dict__))
        elif args.command == "cancel":
            identity = json.loads(Path(args.identity).read_text(encoding="utf-8")) if args.identity else None
            print(_json({"cancelled": daemon.cancel_obsolete(args.repository, args.pr_number, identity)}))
        elif args.command == "approve-main":
            approval = json.loads(Path(args.approval).read_text(encoding="utf-8"))
            print(_json(daemon.approve_main(approval, current_staging_sha=args.staging_source_sha, current_main_base_sha=args.main_base_sha, current_pr_head_sha=args.pr_head_sha, current_receipt_identity=args.receipt_identity)))
        return 0
    except Exception as exc:
        print(_json({"error": str(exc)}), file=sys.stderr)
        return 1
    finally:
        daemon.close()


__all__ = ["build_parser", "main"]
