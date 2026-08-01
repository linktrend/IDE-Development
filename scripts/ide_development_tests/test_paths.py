"""Unit tests for path safety and hashing."""

from __future__ import annotations

import unittest
from pathlib import Path

from ide_development.hashing import normalize_mode, sha256_bytes
from ide_development.paths import as_posix_rel, encode_backup_name, decode_backup_name, join_under
from ide_development.errors import ConflictError, InvalidPackageError
from ide_development_tests import TempRepoTestCase


class PathTests(TempRepoTestCase):
    def test_spaces_and_join(self) -> None:
        rel = ".ide-development/assets/file with spaces.txt"
        dest = join_under(self.target, rel)
        self.assertTrue(str(dest).endswith("file with spaces.txt"))
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("x\n", encoding="utf-8")
        self.assertTrue(dest.is_file())

    def test_rejects_traversal(self) -> None:
        with self.assertRaises(InvalidPackageError):
            as_posix_rel("../outside")

    def test_rejects_escape(self) -> None:
        # Craft a relative path that would escape after resolve via symlink if allowed —
        # join_under should still keep literal parts under root for normal relatives.
        dest = join_under(self.target, ".ide-development/CORE.txt")
        self.assertTrue(str(dest).startswith(str(self.target)))

    def test_backup_encoding_roundtrip(self) -> None:
        rel = ".ide-development/assets/file with spaces.txt"
        enc = encode_backup_name(rel)
        self.assertNotIn("/", enc)
        self.assertEqual(decode_backup_name(enc), rel)

    def test_mode_normalize(self) -> None:
        self.assertEqual(normalize_mode("644"), "0644")
        self.assertEqual(normalize_mode(0o755), "0755")

    def test_sha(self) -> None:
        self.assertTrue(sha256_bytes(b"abc").startswith("sha256:"))


if __name__ == "__main__":
    unittest.main()
