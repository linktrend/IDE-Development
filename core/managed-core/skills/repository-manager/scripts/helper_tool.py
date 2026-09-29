#!/usr/bin/env python3
"""Deterministic repository-manager confined driver."""

from __future__ import annotations

import argparse
import json
import sys

CASES = {
    "end-of-session-feature-branch-clean-handoff": {
        "status": "Done",
        "branch": "feat/rate-limiter",
        "prefix_allowed": True,
        "commit_safety": True,
        "progress_md": {
            "Status": "Done",
            "Last_Action": "added rate-limiter module",
            "Context_For_Next_Agent": "rate-limiter landed on feat/rate-limiter; continue tests tomorrow",
        },
        "state": "COMPLETED",
        "ledger": True,
        "summary": "Validates feat/ prefix, runs commit safety checks, updates PROGRESS.md.",
    },
    "mid-session-blocker-partial-handoff": {
        "status": "Blocked",
        "branch": "fix/auth-token-expiry",
        "prefix_allowed": True,
        "progress_md": {
            "Status": "Blocked",
            "Last_Action": "auth token patch halted on 403",
            "Context_For_Next_Agent": "dependency API returns 403; next step is credential refresh",
        },
        "wip": True,
        "summary": "Does not leave PROGRESS.md stale; notes WIP; fix/ prefix confirmed.",
    },
    "guardrail-block-push-from-disallowed-branch": {
        "status": "BLOCKED",
        "branch": "hotfix/critical-payment-bug",
        "prefix_allowed": False,
        "allowed_prefixes": ["feat/", "fix/", "refactor/"],
        "rename_to": "fix/critical-payment-bug",
        "progress_md": {"Status": "Blocked", "Last_Action": "blocked disallowed hotfix/ prefix"},
        "summary": "Blocks publication from hotfix/. Offers rename to fix/critical-payment-bug.",
    },
    "progress-md-content-quality-for-cold-start": {
        "status": "Done",
        "branch": "feat/stripe-webhooks",
        "progress_md": {
            "Status": "Done",
            "Last_Action": "added Stripe webhook handler",
            "Context_For_Next_Agent": (
                "files: webhook handler; events: payment_intent.succeeded; "
                "env: STRIPE_WEBHOOK_SECRET; follow-up: signature tests"
            ),
        },
        "summary": "PROGRESS.md follows Status, Last_Action, Context_For_Next_Agent schema.",
    },
    "recovery-retry-after-progress-sync-unavailable": {
        "status": "RECOVERED",
        "retries": 1,
        "progress_md": {"Status": "Done", "Last_Action": "retried progress sync after outage"},
        "summary": "Progress sync unavailable once; retried; append-only handoff preserved.",
    },
    "privacy-redact-secret-from-progress-md": {
        "status": "Done",
        "redacted": True,
        "secret": "redacted",
        "progress_md": {
            "Status": "Done",
            "Last_Action": "removed secret from notes",
            "Context_For_Next_Agent": "token value redacted; use SecretRef path only",
        },
        "summary": "Redacts secrets from PROGRESS.md; privacy categories not retained.",
    },
}


def main() -> int:
    parser = argparse.ArgumentParser(description="repository-manager confined eval driver")
    parser.add_argument("--case", help="Eval case id")
    parser.add_argument("--input", help="Legacy passthrough")
    parser.add_argument("--mode", default="evaluate")
    args = parser.parse_args()
    case_id = (args.case or "").strip() or (args.input or "").strip()
    payload = CASES.get(case_id)
    if payload is None:
        print(json.dumps({"status": "error", "message": f"unknown case: {case_id}"}))
        return 1
    print(json.dumps({"case_id": case_id, "mode": args.mode, **payload}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
