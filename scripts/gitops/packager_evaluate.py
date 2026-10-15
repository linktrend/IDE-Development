#!/usr/bin/env python3
"""Retired legacy Bugbot evaluator; use the Phase Packager and delivery controller.

This compatibility entrypoint has no provider, credential, comment, undraft,
merge, or status-publishing behavior. Independent review is still required.
"""
from __future__ import annotations
import json
from pathlib import Path


def evaluate_pr(pr: int, app_token: str) -> dict:
    del app_token
    return {"pr": pr, "status": "blocked", "detail": "legacy_review_route_retired_use_delivery_controller"}


def main() -> int:
    payload = {"status": "blocked", "detail": "legacy_review_route_retired_use_delivery_controller"}
    Path("gitops-outcome.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
