"""Regression tests for extracted-package script materialization."""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
import os
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness.installer import materialize_isolated_rc_extract, materialize_package_copy
from harness.paths import PACKAGE_FIXTURE


REPO_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_SOURCES = (
    "scripts/gitops/repository_ci_contract.py",
    "scripts/gitops/promotion_receipt_gate.py",
    "core/execution/__init__.py",
    "core/execution/protocol.py",
    "core/execution/lifecycle.py",
    "core/execution/scheduler.py",
    "core/execution/verification_liveness.py",
    "core/execution/manifest_persistence.py",
    "core/managed-core/content/config/manifest-persistence.json",
    "core/managed-core/schemas/manifest-persistence.schema.json",
)


class PackageMaterializationTests(unittest.TestCase):
    def test_package_copy_materializes_canonical_runtime_sources(self) -> None:
        with tempfile.TemporaryDirectory(prefix="package-copy-") as tmp:
            package = Path(tmp) / "package"
            materialize_package_copy(package, source=PACKAGE_FIXTURE)

            for rel in RUNTIME_SOURCES:
                self.assertTrue(
                    (package / rel).is_file(),
                    f"constructed package lost runtime source {rel}",
                )

    def test_extracted_package_preserves_runtime_contract_dependencies(self) -> None:
        with tempfile.TemporaryDirectory(prefix="package-materialization-") as tmp:
            source = Path(tmp) / "source"
            extract = Path(tmp) / "extract"
            for rel in RUNTIME_SOURCES:
                source_path = REPO_ROOT / rel
                destination = source / rel
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, destination)

            materialize_isolated_rc_extract(extract, source=source)

            for rel in RUNTIME_SOURCES:
                self.assertTrue(
                    (extract / rel).is_file(),
                    f"extracted package lost runtime source {rel}",
                )

    def test_extracted_package_imports_scheduler_liveness_and_manifest_runtime(self) -> None:
        with tempfile.TemporaryDirectory(prefix="package-execution-runtime-") as tmp:
            package = Path(tmp) / "package"
            materialize_package_copy(package, source=PACKAGE_FIXTURE)
            env = os.environ.copy()
            env.pop("PYTHONPATH", None)
            proc = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    "from core.execution import manifest_persistence, scheduler, verification_liveness; "
                    "print(manifest_persistence.MAX_PERSISTENCE_ATTEMPTS, "
                    "scheduler.__name__, verification_liveness.__name__)",
                ],
                cwd=package,
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("3", proc.stdout)


if __name__ == "__main__":
    unittest.main()
