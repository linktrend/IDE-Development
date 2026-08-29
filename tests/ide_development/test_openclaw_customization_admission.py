"""Focused tests for OpenClaw-only customization-scoped v2.5.2 admission."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from ide_development.hashing import sha256_bytes  # noqa: E402
from ide_development.openclaw_customization_admission import (  # noqa: E402
    KIND,
    SCHEMA_REL,
    admit_openclaw_customization,
)

SCHEMA_SOURCE = "core/managed-core/schemas/openclaw-customization-admission.schema.json"
SCHEMA_DEST = ".ide-development/schemas/openclaw-customization-admission.schema.json"
# Forbidden whole trees from OpenClaw Prime checkpoint
# ab288dbe8d5fc64978db8eee9e6507b6372c1880; admission must never check them.
FORBIDDEN_UPSTREAM_TREES = (
    "src",
    "extensions",
    "ui",
    "apps",
    "packages",
    "test",
    "qa",
    "skills",
    "security",
    "examples",
    "config",
    "deploy",
)


CONSUMER_COMMIT = "a" * 40
CONSUMER_TREE = "b" * 40
UPSTREAM_COMMIT = "c" * 40
UPSTREAM_TREE = "d" * 40
CUSTOM_PATH = "linkbots/lisa/ops/contract.md"
MANAGED_DEST = ".ide-development/schemas/manifest.schema.json"
UPSTREAM_PATH = "src/gateway/server.ts"


def _git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=True,
    )
    return (result.stdout or "").strip()


def _init_repo(root: Path) -> tuple[str, str]:
    root.mkdir(parents=True, exist_ok=True)
    _git(root, "init")
    _git(root, "config", "user.email", "admission-test@example.com")
    _git(root, "config", "user.name", "Admission Test")
    (root / CUSTOM_PATH).parent.mkdir(parents=True, exist_ok=True)
    (root / CUSTOM_PATH).write_text("customization\n", encoding="utf-8")
    (root / UPSTREAM_PATH).parent.mkdir(parents=True, exist_ok=True)
    (root / UPSTREAM_PATH).write_text("untouched upstream\n", encoding="utf-8")
    _git(root, "add", CUSTOM_PATH, UPSTREAM_PATH)
    _git(root, "commit", "-m", "init")
    return _git(root, "rev-parse", "HEAD"), _git(root, "rev-parse", "HEAD^{tree}")


def _canonical(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _write_manifest(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    body = dict(payload)
    body.pop("contentDigest", None)
    digest = sha256_bytes(_canonical(body))
    body["contentDigest"] = digest
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(body, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return body


def _package_root(tmp: Path) -> Path:
    package = tmp / "package"
    manifest = package / "core" / "managed-core" / "MANIFEST.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps(
            {
                "schemaVersion": 1,
                "packageVersion": "2.5.2",
                "files": [
                    {
                        "source": "core/managed-core/schemas/manifest.schema.json",
                        "destination": MANAGED_DEST,
                    }
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return package


def _base_manifest(*, commit: str, tree: str) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "kind": "openclaw-prime-customization-manifest",
        "repository": "linktrend/openclaw_prime",
        "installerVersion": "2.5.2",
        "consumer": {"commit": commit, "tree": tree},
        "upstream": {"commit": UPSTREAM_COMMIT, "tree": UPSTREAM_TREE},
        "customizationPaths": [CUSTOM_PATH],
        "acceptedFindings": [],
    }


def _pass_scanner(paths: list[str]) -> dict[str, Any]:
    return {"ok": True, "findings": [], "errorType": None}


class OpenClawCustomizationAdmissionTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.consumer = self.tmp / "consumer"
        commit, tree = _init_repo(self.consumer)
        self.commit = commit
        self.tree = tree
        self.package = _package_root(self.tmp)
        self.manifest_path = self.tmp / "consumer-manifest.json"
        self.scanned: list[list[str]] = []

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _admit(self, **kwargs: Any) -> dict[str, Any]:
        scanner = kwargs.pop("scanner", self._recording_scanner(_pass_scanner))
        kwargs.setdefault(
            "observed_upstream",
            {"commit": UPSTREAM_COMMIT, "tree": UPSTREAM_TREE},
        )
        return admit_openclaw_customization(
            consumer_root=self.consumer,
            package_root=self.package,
            manifest_path=self.manifest_path,
            scanner=scanner,
            **kwargs,
        )

    def _recording_scanner(self, inner):
        def wrapped(paths: list[str]) -> dict[str, Any]:
            self.scanned.append(list(paths))
            return inner(paths)

        return wrapped

    def test_schema_file_is_the_owned_managed_contract(self) -> None:
        schema_path = ROOT / SCHEMA_REL
        self.assertTrue(schema_path.is_file())
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["kind"]["const"], KIND)
        self.assertEqual(schema["properties"]["installerVersion"]["const"], "2.5.2")
        self.assertIn("checkedPaths", schema["properties"])
        self.assertNotIn("wholeRepositoryBaseline", schema["properties"])

    def test_schema_is_closed_in_generated_manifest(self) -> None:
        payload = json.loads((ROOT / "core/managed-core/MANIFEST.json").read_text(encoding="utf-8"))
        sources = {row["source"] for row in payload["files"]}
        destinations = {row["destination"] for row in payload["files"]}
        self.assertIn(SCHEMA_SOURCE, sources)
        self.assertIn(SCHEMA_DEST, destinations)

    def test_openclaw_boundary_kind_fails_closed_without_scanning(self) -> None:
        _write_manifest(
            self.manifest_path,
            {
                "schemaVersion": 1,
                "kind": "openclaw-prime-customization-boundary",
                "repository": "linktrend/openclaw_prime",
                "installerVersion": "2.5.2",
                "consumer": {"commit": self.commit, "tree": self.tree},
                "upstream": {"commit": UPSTREAM_COMMIT, "tree": UPSTREAM_TREE},
                "customizationPaths": [CUSTOM_PATH],
                "acceptedFindings": [],
            },
        )
        with self.assertRaisesRegex(Exception, "stale-manifest"):
            self._admit()
        self.assertEqual(self.scanned, [])

    def test_forbidden_upstream_trees_are_absent_from_checked_paths(self) -> None:
        _write_manifest(self.manifest_path, _base_manifest(commit=self.commit, tree=self.tree))
        result = self._admit()
        for path in result["checkedPaths"] + self.scanned[0]:
            first = path.split("/", 1)[0]
            self.assertNotIn(first, FORBIDDEN_UPSTREAM_TREES)
            self.assertNotEqual(path, UPSTREAM_PATH)

    def test_admits_customization_and_managed_paths_without_scanning_upstream(self) -> None:
        _write_manifest(self.manifest_path, _base_manifest(commit=self.commit, tree=self.tree))
        result = self._admit()
        self.assertEqual(result["verdict"], "admitted")
        self.assertEqual(result["kind"], KIND)
        checked = set(result["checkedPaths"])
        self.assertIn(CUSTOM_PATH, checked)
        self.assertIn(MANAGED_DEST, checked)
        self.assertNotIn(UPSTREAM_PATH, checked)
        self.assertEqual(len(self.scanned), 1)
        self.assertEqual(set(self.scanned[0]), checked)
        self.assertNotIn(UPSTREAM_PATH, self.scanned[0])

    def test_missing_manifest_fails_closed(self) -> None:
        with self.assertRaisesRegex(Exception, "missing-manifest"):
            self._admit()

    def test_stale_manifest_digest_fails_closed(self) -> None:
        payload = _write_manifest(
            self.manifest_path, _base_manifest(commit=self.commit, tree=self.tree)
        )
        payload["contentDigest"] = "sha256:" + ("0" * 64)
        self.manifest_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        with self.assertRaisesRegex(Exception, "stale-manifest"):
            self._admit()

    def test_stale_consumer_identity_fails_closed(self) -> None:
        _write_manifest(
            self.manifest_path,
            _base_manifest(commit=CONSUMER_COMMIT, tree=CONSUMER_TREE),
        )
        with self.assertRaisesRegex(Exception, "stale-manifest"):
            self._admit()

    def test_upstream_identity_drift_fails_closed(self) -> None:
        _write_manifest(self.manifest_path, _base_manifest(commit=self.commit, tree=self.tree))
        with self.assertRaisesRegex(Exception, "upstream-identity-drift"):
            self._admit(
                observed_upstream={"commit": "e" * 40, "tree": "f" * 40},
            )

    def test_new_finding_in_checked_path_fails_closed(self) -> None:
        _write_manifest(self.manifest_path, _base_manifest(commit=self.commit, tree=self.tree))

        def scanner(paths: list[str]) -> dict[str, Any]:
            return {
                "ok": False,
                "findings": [
                    {
                        "kind": "credential_finding",
                        "path": CUSTOM_PATH,
                        "rule": "assignment.secret",
                    }
                ],
            }

        with self.assertRaisesRegex(Exception, "new-or-changed-finding"):
            self._admit(scanner=self._recording_scanner(scanner))

    def test_changed_finding_in_checked_path_fails_closed(self) -> None:
        manifest = _base_manifest(commit=self.commit, tree=self.tree)
        manifest["acceptedFindings"] = [
            {
                "kind": "credential_finding",
                "path": CUSTOM_PATH,
                "rule": "assignment.secret",
                "digest": "sha256:" + ("1" * 64),
            }
        ]
        _write_manifest(self.manifest_path, manifest)

        def scanner(paths: list[str]) -> dict[str, Any]:
            return {
                "ok": False,
                "findings": [
                    {
                        "kind": "credential_finding",
                        "path": CUSTOM_PATH,
                        "rule": "assignment.secret",
                        "digest": "sha256:" + ("2" * 64),
                    }
                ],
            }

        with self.assertRaisesRegex(Exception, "new-or-changed-finding"):
            self._admit(scanner=self._recording_scanner(scanner))

    def test_accepted_finding_on_checked_path_is_admitted(self) -> None:
        finding = {
            "kind": "credential_finding",
            "path": CUSTOM_PATH,
            "rule": "assignment.secret",
            "digest": "sha256:" + ("1" * 64),
        }
        manifest = _base_manifest(commit=self.commit, tree=self.tree)
        manifest["acceptedFindings"] = [finding]
        _write_manifest(self.manifest_path, manifest)

        def scanner(paths: list[str]) -> dict[str, Any]:
            return {"ok": False, "findings": [finding]}

        result = self._admit(scanner=self._recording_scanner(scanner))
        self.assertEqual(result["verdict"], "admitted")

    def test_upstream_finding_outside_checked_paths_is_ignored(self) -> None:
        _write_manifest(self.manifest_path, _base_manifest(commit=self.commit, tree=self.tree))

        def scanner(paths: list[str]) -> dict[str, Any]:
            return {
                "ok": False,
                "findings": [
                    {
                        "kind": "credential_finding",
                        "path": UPSTREAM_PATH,
                        "rule": "assignment.secret",
                    }
                ],
            }

        result = self._admit(scanner=self._recording_scanner(scanner))
        self.assertEqual(result["verdict"], "admitted")
        self.assertNotIn(UPSTREAM_PATH, result["checkedPaths"])

    def test_scanner_error_fails_closed(self) -> None:
        _write_manifest(self.manifest_path, _base_manifest(commit=self.commit, tree=self.tree))

        def scanner(paths: list[str]) -> dict[str, Any]:
            return {"ok": False, "errorType": "scanner-error", "findings": []}

        with self.assertRaisesRegex(Exception, "scanner-error"):
            self._admit(scanner=self._recording_scanner(scanner))

    def test_scanner_timeout_fails_closed(self) -> None:
        _write_manifest(self.manifest_path, _base_manifest(commit=self.commit, tree=self.tree))

        def scanner(paths: list[str]) -> dict[str, Any]:
            raise TimeoutError("scan exceeded bound")

        with self.assertRaisesRegex(Exception, "scanner-timeout"):
            self._admit(scanner=self._recording_scanner(scanner), timeout_seconds=1)

    def test_new_skipped_input_fails_closed(self) -> None:
        _write_manifest(self.manifest_path, _base_manifest(commit=self.commit, tree=self.tree))

        def scanner(paths: list[str]) -> dict[str, Any]:
            return {
                "ok": True,
                "findings": [
                    {
                        "kind": "skipped_input",
                        "path": CUSTOM_PATH,
                        "rule": "input.undecodable",
                    }
                ],
            }

        with self.assertRaisesRegex(Exception, "new-skipped-input"):
            self._admit(scanner=self._recording_scanner(scanner))


if __name__ == "__main__":
    unittest.main()
