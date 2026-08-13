#!/usr/bin/env python3
"""Remove only the scoped coordinator installation and its exact plist."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from host.coordinator.service import uninstall  # noqa: E402


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Uninstall only the IDE coordinator service files")
    parser.add_argument("--install-root", default="~/.linktrend/ide-coordinator")
    parser.add_argument("--plist", default="~/Library/LaunchAgents/ai.linktrend.ide-coordinator.plist")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(uninstall(args.install_root, args.plist, dry_run=args.dry_run), indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({"error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
