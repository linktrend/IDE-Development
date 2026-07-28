#!/usr/bin/env python3
"""Race-safe Bugbot request against a shared comment backend (file lock for tests).

Production relies on GitHub Actions concurrency to serialize Packager evaluate jobs.
This helper proves that when two evaluators race on the same SHA with a shared store,
exactly one posts the marker.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from packager_logic import (  # noqa: E402
    DEFAULT_BUGBOT_COMMAND,
    build_bugbot_comment,
    marker_for,
    should_request_bugbot,
)


def _lock_path(store: Path) -> Path:
    return store.with_suffix(store.suffix + ".lock")


def _read_comments(store: Path) -> list[dict]:
    if not store.is_file():
        return []
    return json.loads(store.read_text(encoding="utf-8") or "[]")


def _write_comments(store: Path, comments: list[dict]) -> None:
    store.parent.mkdir(parents=True, exist_ok=True)
    store.write_text(json.dumps(comments, indent=2) + "\n", encoding="utf-8")


def request_once(
    *,
    store: Path,
    head_sha: str,
    fast_gate_ok: bool,
    command: str = DEFAULT_BUGBOT_COMMAND,
    hold_lock_seconds: float = 0.0,
    pretouch_delay: float = 0.0,
) -> dict:
    """Atomically decide and append a Bugbot request for head_sha under flock."""
    import fcntl

    if pretouch_delay > 0:
        time.sleep(pretouch_delay)

    lock_f = open(_lock_path(store), "a+", encoding="utf-8")
    try:
        fcntl.flock(lock_f.fileno(), fcntl.LOCK_EX)
        if hold_lock_seconds > 0:
            time.sleep(hold_lock_seconds)
        comments = _read_comments(store)
        ok, reason = should_request_bugbot(
            comments=comments, head_sha=head_sha, fast_gate_ok=fast_gate_ok
        )
        if not ok:
            return {"status": "skipped", "detail": reason, "headSha": head_sha}
        body = build_bugbot_comment(command, head_sha)
        comments.append({"body": body})
        _write_comments(store, comments)
        return {
            "status": "bugbot_requested",
            "detail": f"requested_for_{head_sha.lower()}",
            "headSha": head_sha,
            "marker": marker_for(head_sha),
        }
    finally:
        fcntl.flock(lock_f.fileno(), fcntl.LOCK_UN)
        lock_f.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--store", required=True)
    ap.add_argument("--sha", required=True)
    ap.add_argument("--fast-gate-ok", action="store_true")
    ap.add_argument("--command", default=DEFAULT_BUGBOT_COMMAND)
    ap.add_argument("--hold-lock-seconds", type=float, default=0.0)
    ap.add_argument("--pretouch-delay", type=float, default=0.0)
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    result = request_once(
        store=Path(args.store),
        head_sha=args.sha,
        fast_gate_ok=bool(args.fast_gate_ok),
        command=args.command,
        hold_lock_seconds=args.hold_lock_seconds,
        pretouch_delay=args.pretouch_delay,
    )
    text = json.dumps(result, indent=2) + "\n"
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
    sys.stdout.write(text)
    return 0 if result["status"] in {"bugbot_requested", "skipped"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
