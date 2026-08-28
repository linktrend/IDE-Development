"""Focused ENV-01/ENV-02 runtime preflight and disposable rollback tests."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from scripts.gitops import runtime_preflight as preflight


ROOT = Path(__file__).resolve().parents[2]


def manifest(*, architecture: str = "arm64", service: bool = False, minimum_memory: int = 0) -> dict:
    return {
        "schemaVersion": 1,
        "kind": "toolchain-manifest",
        "manifestVersion": "toolchain-manifest/test-v1",
        "checks": [
            {
                "id": "test-check",
                "profiles": ["focused"],
                "supported": {"os": ["macos"], "architectures": [architecture]},
                "runnerClass": "disposable",
                "python": {"required": True, "executable": "python3", "version": ">=3.9"},
                "node": {"required": False, "executable": "node", "version": None},
                "packageManager": {"required": False, "executable": "npm", "version": None},
                "systemTools": [],
                "services": ([{"id": "postgresql", "required": True, "probe": ["pg_isready"]}] if service else []),
                "requiredConfig": [],
                "networkPolicy": "offline",
                "resources": {
                    "minimumMemoryMb": minimum_memory,
                    "minimumCpuCount": 1,
                    "maximumMemoryMb": 4096,
                    "maximumProcesses": 8,
                },
            }
        ],
    }


def write_manifest(root: Path, payload: dict) -> Path:
    path = root / "toolchain.json"
    path.write_text(json.dumps(payload) + "\n", encoding="utf-8")
    return path


class RuntimePreflightTests(unittest.TestCase):
    def test_checked_in_manifest_is_schema_valid_and_versioned(self) -> None:
        schema = json.loads((ROOT / "core/managed-core/schemas/toolchain-manifest.schema.json").read_text(encoding="utf-8"))
        payload = json.loads((ROOT / "core/managed-core/content/config/toolchain-manifest.json").read_text(encoding="utf-8"))
        errors = list(Draft202012Validator(schema).iter_errors(payload))
        self.assertEqual(errors, [])
        self.assertTrue(payload["manifestVersion"].startswith("toolchain-manifest/"))

    def test_missing_tool_is_environment_blocked_not_source_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = write_manifest(root, manifest())
            result = preflight.run_preflight(
                root,
                profile="focused",
                manifest_path=path,
                executable_finder=lambda name: None if name == "python3" else "/bin/true",
                system="Darwin",
                machine="arm64",
                physical_memory_bytes=1024 * 1024 * 1024,
            )
            row = next(row for row in result["checks"] if row["id"] == "test-check:python")
            self.assertEqual(row["status"], preflight.ENVIRONMENT_BLOCKED)
            self.assertEqual(row["code"], "missing_tool")
            self.assertEqual(row["classification"], "environment")
            self.assertFalse(result["ok"])

    def test_service_architecture_and_resource_conditions_are_typed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            architecture_result = preflight.run_preflight(
                root,
                manifest_path=write_manifest(root, manifest(architecture="x86_64")),
                system="Darwin",
                machine="arm64",
            )
            self.assertEqual(architecture_result["checks"][0]["code"], "unsupported_architecture")

            service_result = preflight.run_preflight(
                root,
                manifest_path=write_manifest(root, manifest(service=True)),
                system="Darwin",
                machine="arm64",
                executable_finder=lambda name: None,
                physical_memory_bytes=1024 * 1024 * 1024,
            )
            service_row = next(row for row in service_result["checks"] if ":service:" in row["id"])
            self.assertEqual(service_row["code"], "missing_service")

            resource_result = preflight.run_preflight(
                root,
                manifest_path=write_manifest(root, manifest(minimum_memory=8192)),
                system="Darwin",
                machine="arm64",
                physical_memory_bytes=1024 * 1024,
            )
            self.assertEqual(resource_result["checks"][0]["code"], "resource_limit")

    def test_ci_evidence_adapter_matches_existing_strict_schema(self) -> None:
        schema = json.loads((ROOT / "core/managed-core/schemas/ci-evidence.schema.json").read_text(encoding="utf-8"))
        result = {
            "ok": False,
            "status": preflight.ENVIRONMENT_BLOCKED,
            "environmentBlocked": ["test-check:python"],
            "sourceFailures": [],
            "checks": [
                {
                    "id": "test-check:python",
                    "status": preflight.ENVIRONMENT_BLOCKED,
                    "code": "missing_tool",
                    "resolvedPath": "",
                }
            ],
        }
        evidence = preflight.as_ci_preflight_evidence(result)
        errors = list(Draft202012Validator(schema).iter_errors(evidence))
        self.assertEqual(errors, [])
        self.assertFalse(evidence["ok"])
        self.assertEqual(evidence["classification"], "infrastructure")

    def test_disposable_rollback_restores_exact_bytes_and_does_not_touch_host(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "state.txt"
            target.write_bytes(b"before\x00bytes\n")
            before = target.read_bytes()

            def mutate(disposable: Path) -> None:
                (disposable / "state.txt").write_bytes(b"changed\n")

            def rollback(disposable: Path) -> None:
                (disposable / "state.txt").write_bytes(before)

            result = preflight.run_disposable_rollback(root, ["state.txt"], mutate, rollback)
            self.assertTrue(result["ok"])
            self.assertTrue(result["exactRestore"])
            self.assertFalse(result["hostMutated"])
            self.assertEqual(target.read_bytes(), before)

    def test_preflight_source_never_reads_environment_or_provider_state(self) -> None:
        source = (ROOT / "scripts/gitops/runtime_preflight.py").read_text(encoding="utf-8")
        self.assertNotIn("os.environ", source)
        self.assertNotIn("GH_TOKEN", source)
        self.assertNotIn("GITHUB_TOKEN", source)


if __name__ == "__main__":
    unittest.main()
