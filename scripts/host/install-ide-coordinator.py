#!/usr/bin/env python3
"""Prepare a versioned coordinator installation; activation is operator-owned."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from host.coordinator.service import install_version, rollback  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Install a versioned, scoped IDE coordinator package")
    parser.add_argument("--source-root", default=str(REPO_ROOT))
    parser.add_argument("--install-root", default="~/.linktrend/ide-coordinator")
    parser.add_argument("--version")
    parser.add_argument("--plist", default="~/Library/LaunchAgents/ai.linktrend.ide-coordinator.plist")
    parser.add_argument("--database", default="~/.linktrend/ide-coordinator/coordinator.sqlite3")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--rollback", action="store_true", help="swap current and retained previous version")
    args = parser.parse_args(argv)
    try:
        if args.rollback:
            print(json.dumps(rollback(args.install_root, dry_run=args.dry_run), indent=2, sort_keys=True))
        else:
            if not args.version:
                parser.error("--version is required unless --rollback is used")
            plan = install_version(args.source_root, args.install_root, args.version, args.plist, database=args.database, dry_run=args.dry_run)
            print(json.dumps(plan.__dict__, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
