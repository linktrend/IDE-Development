"""Absence of credentials / usernames / absolute checkout paths in packages + evidence."""

from __future__ import annotations

import unittest
from pathlib import Path

from harness import (
    FIXTURE_PACKAGE,
    REPO_ROOT,
    SECURITY_FIXTURES,
    scan_text,
    scan_tree,
)


class NoSecretsPackagingTests(unittest.TestCase):
    def test_fixture_package_v2_has_no_secrets_or_host_paths(self) -> None:
        findings = scan_tree(FIXTURE_PACKAGE)
        self.assertEqual(findings, [], msg="\n".join(findings))

    def test_managed_core_source_tree_clean(self) -> None:
        root = REPO_ROOT / "core" / "managed-core"
        if not root.is_dir():
            self.skipTest("core/managed-core not present in this worktree")
        findings = scan_tree(root)
        self.assertEqual(findings, [], msg="\n".join(findings[:30]))

    def test_tainted_fixture_is_detected(self) -> None:
        """Positive control: scanner must flag intentionally tainted fixture bytes."""
        tainted = SECURITY_FIXTURES / "tainted" / "leaky-snippet.txt"
        self.assertTrue(tainted.is_file())
        findings = scan_text(tainted.read_text(encoding="utf-8"), rel="tainted/leaky-snippet.txt")
        self.assertTrue(findings, "expected scanner to flag tainted fixture")

    def test_evidence_fixture_without_secrets(self) -> None:
        clean = SECURITY_FIXTURES / "evidence" / "clean-completion-evidence.json"
        self.assertTrue(clean.is_file())
        findings = scan_text(clean.read_text(encoding="utf-8"), rel=clean.name)
        self.assertEqual(findings, [])

    def test_evidence_fixture_with_host_path_detected(self) -> None:
        dirty = SECURITY_FIXTURES / "evidence" / "host-path-evidence.json"
        self.assertTrue(dirty.is_file())
        findings = scan_text(dirty.read_text(encoding="utf-8"), rel=dirty.name)
        self.assertTrue(any("absolute" in f or "username" in f for f in findings), findings)

    def test_security_fixtures_tainted_dir_only_contains_intentional_secrets(self) -> None:
        """Only the tainted/ subtree may contain secret-like patterns under security fixtures."""
        for path in sorted(SECURITY_FIXTURES.rglob("*")):
            if not path.is_file() or path.is_symlink():
                continue
            rel = path.relative_to(SECURITY_FIXTURES).as_posix()
            if rel.startswith("tainted/"):
                continue
            if "host-path" in path.name or "wrong-repo" in path.name:
                # wrong-repo / host-path fixtures are intentional adversarial samples
                continue
            findings = scan_text(path.read_text(encoding="utf-8"), rel=rel)
            self.assertEqual(findings, [], msg=f"{rel}: {findings}")


if __name__ == "__main__":
    unittest.main()
