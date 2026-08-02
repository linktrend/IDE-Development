#!/usr/bin/env python3
"""Read-only external-state verify entrypoint (WP1 Lane C).

Delegates to ``external_state_audit.main`` with mode ``verify``.
Never mutates GitHub settings; never prints secret values.
Exit 0 only when every required check is ok/matched.
"""

from __future__ import annotations

import sys

from external_state_audit import main


if __name__ == "__main__":
    argv = list(sys.argv[1:])
    if not argv or argv[0] not in {"plan", "report", "verify", "apply"}:
        argv = ["verify", *argv]
    raise SystemExit(main(argv))
