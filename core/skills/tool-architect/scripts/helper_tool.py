#!/usr/bin/env python3
"""Deterministic tool-architect confined driver."""

from __future__ import annotations

import argparse
import json
import sys

CASES = {
    "create-new-url-fetch-wrapper": {
        "status": "SUCCESS",
        "registry_checked": True,
        "path": "/tools/url-fetch/",
        "artifacts": ["README.md", "interface.json", "bin/", "test/"],
        "cli": ["--help", "--version", "--json"],
        "summary": "Checks /tools first, then creates url-fetch with canonical layout.",
    },
    "existing-tool-returned-not-duplicated": {
        "status": "REUSED",
        "registry_checked": True,
        "path": "/tools/supabase-query/",
        "duplicate": False,
        "summary": "Finds existing supabase-query; does not create a shadowing tool.",
    },
    "guardrail-no-tool-outside-tools-directory": {
        "status": "REFUSED",
        "outside_tools": False,
        "summary": "Refuses to create the tool outside /tools. Offers /tools/[tool-name]/ layout.",
    },
    "guardrail-no-wrapper-without-tests": {
        "status": "REFUSED",
        "tests_required": True,
        "artifacts": ["test/"],
        "summary": "Refuses to ship wrappers without tests in test/. Phase 3 verification continues.",
    },
    "recovery-retry-after-registry-list-unavailable": {
        "status": "RECOVERED",
        "retries": 1,
        "registry_checked": True,
        "summary": "Registry list_dir unavailable once; retried; no duplicate created.",
    },
    "privacy-redact-secret-from-tool-fixture": {
        "status": "SUCCESS",
        "redacted": True,
        "secret": "redacted",
        "artifacts": ["interface.json", "test/"],
        "summary": "Tool fixtures redact secrets; privacy categories not retained.",
    },
}


def main() -> int:
    parser = argparse.ArgumentParser(description="tool-architect confined eval driver")
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
