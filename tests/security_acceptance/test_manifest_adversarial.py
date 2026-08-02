"""Malformed manifests, hashes, modes, types, partial packages."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from harness import (
    DisposableRepoTestCase,
    load_manifest,
    run_cli,
    write_manifest,
)

from ide_development.constants import EXIT_CONFLICT, EXIT_ERROR, EXIT_INVALID_PACKAGE, EXIT_OK
from ide_development.engine import run_install_or_update, run_plan
from ide_development.errors import InvalidPackageError
from ide_development.hashing import normalize_mode
from ide_development.manifest import load_manifest as parse_package_manifest


class ManifestAdversarialTests(DisposableRepoTestCase):
    def test_malformed_json(self) -> None:
        path = self.package / "core/managed-core/MANIFEST.json"
        path.write_text("{not-json", encoding="utf-8")
        payload = self.assert_cli_refusal(
            "plan",
            "--package",
            str(self.package),
            "--target",
            str(self.target),
            expected_exit=EXIT_INVALID_PACKAGE,
        )
        self.assertIn("JSON", payload["error"])

    def test_duplicate_destination(self) -> None:
        data = load_manifest(self.package)
        clone = dict(data["files"][0])
        clone["id"] = "dup-dest"
        clone["destination"] = data["files"][1]["destination"]
        data["files"].append(clone)
        write_manifest(self.package, data)
        with self.assertRaises(InvalidPackageError) as ctx:
            parse_package_manifest(self.package)
        self.assertIn("Duplicate destination", str(ctx.exception))

    def test_duplicate_id(self) -> None:
        data = load_manifest(self.package)
        clone = dict(data["files"][1])
        clone["destination"] = ".ide-development/other.txt"
        # need a real source file
        src = self.package / "core/managed-core/files/CORE.txt"
        other = self.package / "core/managed-core/files/other.txt"
        other.write_bytes(src.read_bytes())
        clone["source"] = "core/managed-core/files/other.txt"
        clone["id"] = data["files"][0]["id"]
        from ide_development.hashing import sha256_file

        clone["sourceHash"] = sha256_file(other)
        data["files"].append(clone)
        write_manifest(self.package, data)
        with self.assertRaises(InvalidPackageError) as ctx:
            parse_package_manifest(self.package)
        self.assertIn("Duplicate manifest id", str(ctx.exception))

    def test_wrong_hash(self) -> None:
        data = load_manifest(self.package)
        data["files"][0]["sourceHash"] = "sha256:" + ("a" * 64)
        write_manifest(self.package, data)
        payload = self.assert_cli_refusal(
            "plan",
            "--package",
            str(self.package),
            "--target",
            str(self.target),
            expected_exit=EXIT_INVALID_PACKAGE,
        )
        self.assertIn("sourceHash", payload["error"])

    def test_invalid_hash_format(self) -> None:
        data = load_manifest(self.package)
        data["files"][0]["sourceHash"] = "md5:deadbeef"
        write_manifest(self.package, data)
        with self.assertRaises(InvalidPackageError):
            parse_package_manifest(self.package)

    def test_claude_surface_refused(self) -> None:
        data = load_manifest(self.package)
        data["files"][0]["destination"] = "CLAUDE.md"
        write_manifest(self.package, data)
        with self.assertRaises(InvalidPackageError) as ctx:
            parse_package_manifest(self.package)
        self.assertIn("Claude", str(ctx.exception))

    def test_missing_source_partial_package(self) -> None:
        core = self.package / "core/managed-core/files/CORE.txt"
        core.unlink()
        payload = self.assert_cli_refusal(
            "plan",
            "--package",
            str(self.package),
            "--target",
            str(self.target),
            expected_exit=EXIT_INVALID_PACKAGE,
        )
        self.assertIn("Missing source", payload["error"])

    def test_empty_files_array(self) -> None:
        data = load_manifest(self.package)
        data["files"] = []
        write_manifest(self.package, data)
        with self.assertRaises(InvalidPackageError):
            parse_package_manifest(self.package)

    def test_destination_is_directory_not_a_file(self) -> None:
        dest = self.target / ".ide-development" / "CORE.txt"
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "nested.txt").write_text("nope\n", encoding="utf-8")
        result = run_install_or_update(
            target=self.target,
            package=self.package,
            command="install",
            dry_run=False,
        )
        self.assertEqual(result.exit_code, EXIT_CONFLICT, result.payload)
        kinds = {c["kind"] for c in result.payload.get("conflicts") or []}
        self.assertIn("not_a_file", kinds)

    def test_invalid_mode_rwxr_exits_invalid_package(self) -> None:
        """Non-octal mode strings refuse as EXIT_INVALID_PACKAGE (12)."""
        data = load_manifest(self.package)
        data["files"][0]["mode"] = "rwxr"
        write_manifest(self.package, data)
        proc = run_cli(
            "plan",
            "--package",
            str(self.package),
            "--target",
            str(self.target),
            "--json",
        )
        self.assertEqual(proc.returncode, EXIT_INVALID_PACKAGE, proc.stdout + proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertFalse(payload.get("ok", True))
        self.assertEqual(payload.get("exitCode"), EXIT_INVALID_PACKAGE)

    def test_mode_999_refused_as_invalid_package(self) -> None:
        """Invalid octal digit strings refuse closed (no decimal mask)."""
        with self.assertRaises(InvalidPackageError):
            normalize_mode("999")
        data = load_manifest(self.package)
        data["files"][0]["mode"] = "999"
        write_manifest(self.package, data)
        with self.assertRaises(InvalidPackageError):
            parse_package_manifest(self.package)


class ExternalStateManifestTests(DisposableRepoTestCase):
    def test_external_state_requires_github_platform(self) -> None:
        data = load_manifest(self.package)
        data["files"].append(
            {
                "id": "ext-bad",
                "ownershipClass": "external-state",
                "source": "core/managed-core/files/CORE.txt",
                "destination": ".github/external-plan-only.json",
                "mode": "0644",
                "platform": "all",
                "os": "all",
                "mergeStrategy": "external-plan-only",
                "sourceHash": data["files"][0]["sourceHash"],
            }
        )
        write_manifest(self.package, data)
        with self.assertRaises(InvalidPackageError) as ctx:
            parse_package_manifest(self.package)
        self.assertIn("platform=github", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
