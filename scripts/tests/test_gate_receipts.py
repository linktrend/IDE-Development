"""W1-P2 exact-content receipt tests and negative probes."""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.gitops.coordinator import receipts


SHA = "a" * 40
DIGEST = "sha256:" + ("b" * 64)


def run_git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo, check=True, capture_output=True, text=True
    )
    return result.stdout.strip()


class GateReceiptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name) / "receipt-repo"
        self.repo.mkdir()
        run_git(self.repo, "init", "-q")
        run_git(self.repo, "config", "user.email", "receipt-test@example.com")
        run_git(self.repo, "config", "user.name", "Receipt Test")
        run_git(self.repo, "remote", "add", "origin", "https://github.com/acme/receipt-repo.git")
        (self.repo / "src").mkdir()
        (self.repo / "src" / "app.txt").write_text("version one\n", encoding="utf-8")
        (self.repo / "deps.lock").write_text("dependency one\n", encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-qm", "initial")
        self.identity = receipts.compute_candidate_identity(self.repo, ["deps.lock"], "full")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _result(self, **changes: object) -> dict[str, object]:
        value: dict[str, object] = {
            "schemaVersion": 1,
            "status": "passed",
            "repository": self.identity.repository,
            "gate": "full-gate",
            "sourceSha": self.identity.source_sha,
            "testedCheckoutSha": self.identity.source_sha,
            "gitTreeSha": self.identity.git_tree_sha,
            "dependencyDigests": self.identity.dependency_digests,
            "testProfile": "full",
            "attempt": 1,
            "coordinatorVersion": "1.0.0",
            "startedAt": "2026-08-13T01:00:00Z",
            "completedAt": "2026-08-13T01:01:00Z",
            "evidenceDigests": {"evidence/full.log": DIGEST},
            "github": {"pullRequest": None, "runUrl": None},
        }
        value.update(changes)
        return value

    def _write(self, path: Path | None = None) -> Path:
        output = path or Path(self.tmp.name) / "receipt.json"
        receipts.write_receipt(self._result(), output)
        return output

    def test_exact_identity_and_different_commit_same_tree_pass(self) -> None:
        receipt = self._write()
        self.assertTrue(
            receipts.verify_receipt(
                receipts.load_json(receipt), self.identity, "full-gate"
            )
        )
        old_source = self.identity.source_sha
        run_git(self.repo, "commit", "--allow-empty", "-qm", "metadata-only")
        newer = receipts.compute_candidate_identity(self.repo, ["deps.lock"], "full")
        self.assertNotEqual(old_source, newer.source_sha)
        self.assertEqual(self.identity.git_tree_sha, newer.git_tree_sha)
        verdict = receipts.verify_receipt(receipts.load_json(receipt), newer, "full-gate")
        self.assertEqual(verdict.code, "accepted")

    def test_one_byte_source_changes_tree(self) -> None:
        receipt = self._write()
        (self.repo / "src" / "app.txt").write_text("version two\n", encoding="utf-8")
        run_git(self.repo, "add", ".")
        run_git(self.repo, "commit", "-qm", "source change")
        changed = receipts.compute_candidate_identity(self.repo, ["deps.lock"], "full")
        verdict = receipts.verify_receipt(receipts.load_json(receipt), changed, "full-gate")
        self.assertEqual(verdict.code, "tree_mismatch")

    def test_one_byte_dependency_changes_digest(self) -> None:
        receipt = self._write()
        (self.repo / "deps.lock").write_text("dependency two\n", encoding="utf-8")
        changed = receipts.compute_candidate_identity(self.repo, ["deps.lock"], "full")
        verdict = receipts.verify_receipt(receipts.load_json(receipt), changed, "full-gate")
        self.assertEqual(verdict.code, "dependency_mismatch")

    def test_repository_gate_and_profile_mismatch(self) -> None:
        receipt = self._write()
        original = receipts.load_json(receipt)
        cases = (
            ({"repository": "other/repository"}, "repository_mismatch"),
            ({"gate": "release-gate"}, "gate_mismatch"),
            ({"testProfile": "fast"}, "profile_mismatch"),
        )
        for changes, expected in cases:
            candidate = dict(original)
            candidate.update(changes)
            self.assertEqual(
                receipts.verify_receipt(candidate, self.identity, "full-gate").code,
                expected,
            )

    def test_failed_status_and_evidence_mismatch_fail(self) -> None:
        receipt = self._write()
        failed = self._result(status="failed")
        self.assertEqual(
            receipts.verify_receipt(failed, self.identity, "full-gate").code,
            "receipt_not_passed",
        )
        evidence = self._result(evidenceDigests={"evidence/full.log": "bad"})
        self.assertEqual(
            receipts.verify_receipt(evidence, self.identity, "full-gate").code,
            "evidence_mismatch",
        )
        self.assertTrue(receipt.exists())

    def test_malformed_sha_path_escape_and_corrupt_json_fail(self) -> None:
        malformed = self._result(sourceSha="not-a-sha")
        self.assertEqual(
            receipts.verify_receipt(malformed, self.identity, "full-gate").code,
            "invalid_sha",
        )
        with self.assertRaises(receipts.ReceiptError) as context:
            receipts.compute_candidate_identity(self.repo, ["../outside.txt"], "full")
        self.assertEqual(context.exception.code, "invalid_path")
        corrupt = Path(self.tmp.name) / "corrupt.json"
        corrupt.write_text("{not json", encoding="utf-8")
        with self.assertRaises(receipts.ReceiptError) as context:
            receipts.load_json(corrupt)
        self.assertEqual(context.exception.code, "invalid_receipt")

    def test_symlink_escape_is_rejected(self) -> None:
        outside = Path(self.tmp.name) / "outside.txt"
        outside.write_text("secret\n", encoding="utf-8")
        (self.repo / "escape.lock").symlink_to(outside)
        with self.assertRaises(receipts.ReceiptError) as context:
            receipts.compute_candidate_identity(self.repo, ["escape.lock"], "full")
        self.assertEqual(context.exception.code, "invalid_path")

    def test_canonical_output_is_byte_stable(self) -> None:
        first = Path(self.tmp.name) / "one.json"
        second = Path(self.tmp.name) / "two.json"
        result = self._result(
            dependencyDigests={"deps.lock": self.identity.dependency_digests["deps.lock"]},
            evidenceDigests={"evidence/full.log": DIGEST},
        )
        receipts.write_receipt(result, first)
        receipts.write_receipt(json.loads(first.read_text(encoding="utf-8")), second)
        self.assertEqual(first.read_bytes(), second.read_bytes())
        self.assertEqual(first.read_bytes(), first.read_bytes())

    def test_interrupted_atomic_write_preserves_previous_receipt(self) -> None:
        output = self._write()
        previous = output.read_bytes()
        with mock.patch.object(receipts.os, "replace", side_effect=RuntimeError("interrupted")):
            with self.assertRaises(RuntimeError):
                receipts.write_receipt(self._result(completedAt="2026-08-13T01:02:00Z"), output)
        self.assertEqual(output.read_bytes(), previous)
        self.assertFalse(any(output.parent.glob(f".{output.name}.*.tmp")))


if __name__ == "__main__":
    unittest.main()
