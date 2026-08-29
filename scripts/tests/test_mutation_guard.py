from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.gitops.mutation_guard import (
    DECLARATION_KIND,
    MutationGuard,
    MutationGuardError,
    capture_identity,
    read_only_declaration,
    validate_argv,
    validate_worker_evidence,
)
from scripts.gitops.secret_scan import scan_repository


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "core/managed-core/schemas/mutation-declaration.schema.json"


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)
    if result.returncode:
        raise AssertionError(result.stderr or result.stdout)
    return result.stdout.strip()


def init_repo() -> tuple[tempfile.TemporaryDirectory[str], Path]:
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name) / "repo"
    root.mkdir()
    git(root, "init", "-q", "-b", "development")
    git(root, "config", "user.email", "guard@example.invalid")
    git(root, "config", "user.name", "mutation guard")
    git(root, "remote", "add", "origin", "https://github.com/acme/security.git")
    (root / "README.md").write_text("clean\n", encoding="utf-8")
    git(root, "add", "README.md")
    git(root, "commit", "-qm", "base")
    return tmp, root


class MutationGuardTests(unittest.TestCase):
    def test_schema_and_read_only_declaration_are_typed(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        tmp, root = init_repo()
        self.addCleanup(tmp.cleanup)
        declaration = read_only_declaration(root, tool="focused-check")
        payload = declaration.to_dict()
        self.assertEqual(payload["kind"], DECLARATION_KIND)
        self.assertFalse(list(Draft202012Validator(schema).iter_errors(payload)))
        guard = MutationGuard(root, payload)
        guard.verify_after()

    def test_read_only_and_broad_mutations_fail_closed(self) -> None:
        tmp, root = init_repo()
        self.addCleanup(tmp.cleanup)
        readonly = read_only_declaration(root, tool="read-check")
        guard = MutationGuard(root, readonly)
        with self.assertRaisesRegex(MutationGuardError, "credential_discovery_forbidden"):
            guard.run(lambda: None, argv=["cat", "/tmp/.env"])
        (root / "README.md").write_text("changed\n", encoding="utf-8")
        with self.assertRaisesRegex(MutationGuardError, "unexpected_mutation") as raised:
            guard.verify_after()
        self.assertEqual(raised.exception.last_known_good, guard.before.identity)

        # Restore the disposable fixture, then allow only one exact path.
        (root / "README.md").write_text("clean\n", encoding="utf-8")
        identity = capture_identity(root)
        payload = {
            "schemaVersion": 1,
            "kind": DECLARATION_KIND,
            "mode": "mutating",
            "tool": "bounded-edit",
            "identity": identity.to_dict(),
            "authorizedPaths": ["README.md"],
            "maxChangedFiles": 1,
            "maxChangedBytes": 100,
            "credentialDiscovery": False,
        }
        guard = MutationGuard(root, payload)
        (root / "README.md").write_text("bounded\n", encoding="utf-8")
        guard.verify_after()

        (root / "other.txt").write_text("unexpected\n", encoding="utf-8")
        with self.assertRaisesRegex(MutationGuardError, "unexpected_broad_mutation"):
            guard.verify_after()

    def test_untrusted_identity_and_credential_discovery_are_rejected(self) -> None:
        tmp, root = init_repo()
        self.addCleanup(tmp.cleanup)
        declaration = read_only_declaration(root, tool="read-check").to_dict()
        declaration["identity"]["source"] = "mock"
        with self.assertRaisesRegex(MutationGuardError, "identity_untrusted"):
            MutationGuard(root, declaration)
        with self.assertRaisesRegex(MutationGuardError, "credential_discovery_forbidden"):
            validate_argv(["cat", "/tmp/.env"])

        evidence = {
            "repository": capture_identity(root).repository,
            "startingRef": "development",
            "startingCommit": capture_identity(root).commit,
            "startingTree": capture_identity(root).tree,
            "resultingCheckpoint": {"commit": capture_identity(root).commit, "tree": capture_identity(root).tree},
            "provider": "cursor-cloud",
            "model": "bounded-worker",
            "effort": "high",
            "fastMode": True,
            "authoritativeRun": {"id": "run-123", "status": "finished"},
            "scope": {"authorizedPaths": [], "maxChangedFiles": 0, "maxChangedBytes": 0},
            "tests": ["focused mutation tests"],
            "verdict": "PASS",
            "receiptDigest": "sha256:" + "a" * 64,
        }
        validate_worker_evidence(evidence)
        evidence["authoritativeRun"]["id"] = "mock-run"
        with self.assertRaisesRegex(MutationGuardError, "identity_untrusted"):
            validate_worker_evidence(evidence)

    def test_secret_scan_child_discovery_is_blocking_and_sanitized(self) -> None:
        tmp, root = init_repo()
        self.addCleanup(tmp.cleanup)
        scanner = root / "scanner.sh"
        scanner.write_text("#!/bin/sh\ncat /tmp/credentials\n", encoding="utf-8")
        scanner.chmod(0o755)
        config = root / ".github/linktrend-repository-secret-scanners.json"
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text(
            json.dumps({"schemaVersion": 1, "scanners": [{"id": "owned", "command": ["cat", "/tmp/credentials"]}]}) + "\n",
            encoding="utf-8",
        )
        git(root, "add", "--", ".github/linktrend-repository-secret-scanners.json", "scanner.sh")
        git(root, "commit", "-qm", "scanner declaration")
        result = scan_repository(root)
        self.assertFalse(result["ok"])
        finding = next(row for row in result["findings"] if row.get("scannerId") == "owned")
        self.assertEqual(finding["rule"], "repository_scanner.credential_discovery")
        self.assertNotIn("credentials", json.dumps(result))


if __name__ == "__main__":
    unittest.main()
