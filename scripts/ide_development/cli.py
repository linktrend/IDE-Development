"""CLI for the IDE Development installer."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from .constants import (
    EXIT_CONFLICT,
    EXIT_DRIFT,
    EXIT_ERROR,
    EXIT_INVALID_PACKAGE,
    EXIT_OK,
    EXIT_ROLLBACK_FAILURE,
)
from .engine import (
    run_drift,
    run_install_or_update,
    run_plan,
    run_rollback,
    run_verify,
    run_version,
)
from .errors import InstallerError


def _emit(payload: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=False))
        return
    # Human-readable compact summary plus JSON block for agents
    command = payload.get("command")
    summary = payload.get("summary") or payload.get("verify") or {}
    print(f"command={command}")
    if "packageVersion" in payload:
        print(f"packageVersion={payload.get('packageVersion')}")
    if "installerVersion" in payload:
        print(f"installerVersion={payload.get('installerVersion')}")
    if summary:
        print(f"summary={json.dumps(summary, sort_keys=True)}")
    if payload.get("conflicts"):
        print(f"conflicts={len(payload['conflicts'])}")
    if payload.get("drift") and command in {"drift", "verify", "plan", "install", "update"}:
        print(f"drift={len(payload['drift'])}")
    print("--- json ---")
    print(json.dumps(payload, indent=2, sort_keys=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ide-development",
        description=(
            "Transactional cross-platform installer for IDE Development managed core v2. "
            "Stdlib only. Physical files. Fail-closed conflicts."
        ),
    )

    # Common options are attached to each subparser so `cmd --package ...` works
    # on Python 3.9 (parent optionals after the subcommand are otherwise rejected).
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON only",
    )
    common.add_argument(
        "--package",
        type=Path,
        default=None,
        help="Package/system repository root (default: detect from this script)",
    )
    common.add_argument(
        "--target",
        "--repo",
        dest="target",
        type=Path,
        default=None,
        help="Target consumer git repository (default: cwd for most commands). --repo is an alias.",
    )
    common.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan only; guarantee no repository or git-metadata writes",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser(
        "plan",
        parents=[common],
        help="Build a deterministic install/update plan (always dry-run)",
    )
    sub.add_parser(
        "install",
        parents=[common],
        help="Install managed core into a consumer repository",
    )
    sub.add_parser(
        "update",
        parents=[common],
        help="Update an existing managed-core installation",
    )
    sub.add_parser(
        "drift",
        parents=[common],
        help="Report precise managed-file drift categories",
    )
    sub.add_parser(
        "verify",
        parents=[common],
        help="Verify installation matches package + installed-state",
    )
    sub.add_parser(
        "version",
        parents=[common],
        help="Show installer and package versions",
    )
    sub.add_parser(
        "rollback",
        parents=[common],
        help="Restore exact pre-change bytes from last transaction",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    as_json = bool(args.json)
    dry_run = bool(getattr(args, "dry_run", False))
    target = Path(args.target) if args.target is not None else Path.cwd()
    package = Path(args.package) if args.package is not None else None

    try:
        if args.command == "plan":
            result = run_plan(target=target, package=package, command="plan", dry_run=True)
        elif args.command == "install":
            result = run_install_or_update(
                target=target,
                package=package,
                command="install",
                dry_run=dry_run,
            )
        elif args.command == "update":
            result = run_install_or_update(
                target=target,
                package=package,
                command="update",
                dry_run=dry_run,
            )
        elif args.command == "drift":
            result = run_drift(target=target, package=package)
        elif args.command == "verify":
            result = run_verify(target=target, package=package)
        elif args.command == "version":
            result = run_version(target=target if args.target else None, package=package)
        elif args.command == "rollback":
            result = run_rollback(target=target)
        else:  # pragma: no cover
            parser.error(f"Unknown command: {args.command}")
            return EXIT_ERROR
    except InstallerError as exc:
        payload = {
            "schemaVersion": 1,
            "ok": False,
            "command": args.command,
            "error": exc.message,
            "details": exc.details,
            "exitCode": exc.exit_code,
        }
        _emit(payload, as_json=as_json)
        return int(exc.exit_code)
    except BrokenPipeError:  # pragma: no cover
        return EXIT_OK
    except Exception as exc:  # pragma: no cover
        payload = {
            "schemaVersion": 1,
            "ok": False,
            "command": args.command,
            "error": str(exc),
            "exitCode": EXIT_ERROR,
        }
        _emit(payload, as_json=as_json)
        return EXIT_ERROR

    _emit(result.payload, as_json=as_json)
    return int(result.exit_code)


# Re-export exit codes for wrappers/tests
__all__ = [
    "main",
    "build_parser",
    "EXIT_OK",
    "EXIT_ERROR",
    "EXIT_DRIFT",
    "EXIT_CONFLICT",
    "EXIT_INVALID_PACKAGE",
    "EXIT_ROLLBACK_FAILURE",
]


if __name__ == "__main__":
    sys.exit(main())
