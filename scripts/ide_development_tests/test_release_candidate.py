"""Unit tests for release-candidate packaging gates and archive safety."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from ide_development import release_candidate as rc
from ide_development.constants import (
    EXIT_INVALID_PACKAGE,
    PACKAGE_VERSION_TARGET,
    RC_REQUIRED_SCHEMA_RELS,
)
from ide_development.errors import InstallerError
from ide_development.hashing import sha256_file


def runtime_baseline_environment(
    *,
    baseline_ref: str,
    repo_root: Path = rc.REPO_ROOT,
) -> dict[str, str]:
    sha = subprocess.check_output(
        ["git", "rev-parse", f"{baseline_ref}^{{commit}}"],
        cwd=repo_root,
        text=True,
    ).strip()
    return {
        "LINKTREND_TARGET_BASELINE_SHA": sha,
        "LINKTREND_TARGET_BASELINE_REF": baseline_ref,
    }


class ReleaseCandidateGateTests(unittest.TestCase):
    def test_validate_versions_ok(self) -> None:
        version = rc.validate_versions()
        self.assertEqual(version, PACKAGE_VERSION_TARGET)

    def test_validate_schemas_ok(self) -> None:
        ids = rc.validate_schemas()
        for rel in RC_REQUIRED_SCHEMA_RELS:
            self.assertIn(rel, ids)

    def test_dirty_worktree_refusal(self) -> None:
        # Concurrent WP1 lanes leave the worktree dirty; production create must refuse.
        if not rc.worktree_is_dirty():
            self.skipTest("worktree currently clean; dirty refusal covered when dirty")
        # Baseline discovery is independently tested below; hosted issue checkouts
        # are allowed to omit unrelated remote branches.
        with mock.patch.object(rc, "finalize_candidate"):
            with self.assertRaises(InstallerError) as ctx:
                rc.create_release_candidate(
                    allow_dirty=False,
                    skip_install_verify=True,
                    skip_evidence=True,
                )
        self.assertEqual(ctx.exception.exit_code, EXIT_INVALID_PACKAGE)
        self.assertIn("dirty", ctx.exception.message.lower())

    def test_missing_evidence_refusal(self) -> None:
        # This unit test exercises the evidence gate, not Git baseline discovery.
        # Hosted issue-branch checkouts intentionally may not fetch development.
        with mock.patch.object(rc, "finalize_candidate"), mock.patch.object(
            rc,
            "validate_tests_and_evidence",
            side_effect=rc.ReleaseCandidateError(
                "Required tests/evidence missing",
                details={"missing": ["tests/packaging/LANE_D_RESULT.md"]},
            ),
        ):
            with self.assertRaises(InstallerError) as ctx:
                rc.create_release_candidate(
                    allow_dirty=True,
                    skip_install_verify=True,
                    skip_evidence=False,
                )
            self.assertIn("evidence", ctx.exception.message.lower())

    def test_fixture_environment_accepts_named_remote_without_origin_target(self) -> None:
        with tempfile.TemporaryDirectory(prefix="release-candidate-baseline-") as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q", "-b", "development"], cwd=root, check=True)
            subprocess.run(
                ["git", "config", "user.email", "release-candidate@example.invalid"],
                cwd=root,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Release Candidate Tests"],
                cwd=root,
                check=True,
            )
            (root / "README.md").write_text("baseline\n", encoding="utf-8")
            subprocess.run(["git", "add", "README.md"], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "fixture baseline"], cwd=root, check=True)
            baseline = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=root,
                text=True,
            ).strip()
            subprocess.run(["git", "remote", "add", "fixture", str(root / "fixture.git")], cwd=root, check=True)
            subprocess.run(
                ["git", "update-ref", "refs/remotes/fixture/development", baseline],
                cwd=root,
                check=True,
            )
            subprocess.run(["git", "commit", "--allow-empty", "-qm", "fixture candidate"], cwd=root, check=True)

            environment = runtime_baseline_environment(
                repo_root=root,
                baseline_ref="fixture/development",
            )

            self.assertEqual(environment["LINKTREND_TARGET_BASELINE_SHA"], baseline)
            self.assertEqual(environment["LINKTREND_TARGET_BASELINE_REF"], "fixture/development")

    def test_version_inconsistency_refusal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "VERSION").write_text("v9.9.9\n", encoding="utf-8")
            managed = root / "core" / "managed-core"
            managed.mkdir(parents=True)
            (managed / "VERSION").write_text("9.9.9\n", encoding="utf-8")
            with self.assertRaises(InstallerError) as ctx:
                rc.validate_versions(root)
            self.assertIn("2.4.0", ctx.exception.message.lower() + str(ctx.exception.details))


class ReleaseCandidateArchiveTests(unittest.TestCase):
    def test_host_path_scan_ignores_documentation_path_component(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rc._scan_bytes_for_host_paths(
                "skill.md",
                b"See linktrend/LiNKtrend-System/docs/workspace/MVO-UI-POLICY.md.\n",
                repo_root=Path("/workspace"),
            )

    def test_tar_and_zip_reproducible(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            staging = Path(tmp) / "stage"
            staging.mkdir()
            (staging / "VERSION").write_text("2.0.0\n", encoding="utf-8")
            nested = staging / "core" / "managed-core"
            nested.mkdir(parents=True)
            (nested / "VERSION").write_text("2.0.0\n", encoding="utf-8")
            identities = ["VERSION", "core/managed-core/VERSION"]
            out = Path(tmp) / "out"
            out.mkdir()
            a1 = out / "a.tar.gz"
            a2 = out / "b.tar.gz"
            rc.build_tar_gz(staging, a1, identities)
            rc.build_tar_gz(staging, a2, identities)
            self.assertEqual(a1.read_bytes(), a2.read_bytes())
            z1 = out / "a.zip"
            z2 = out / "b.zip"
            rc.build_zip(staging, z1, identities)
            rc.build_zip(staging, z2, identities)
            self.assertEqual(z1.read_bytes(), z2.read_bytes())
            self.assertTrue(sha256_file(a1).startswith("sha256:"))

    def test_refuse_symlink_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            staging = root / "stage"
            staging.mkdir()
            target = root / "real.txt"
            target.write_text("x\n", encoding="utf-8")
            link = root / "link.txt"
            try:
                os.symlink(target, link)
            except OSError:
                self.skipTest("symlinks unavailable")
            with self.assertRaises(InstallerError):
                rc.stage_package_tree(
                    repo_root=root,
                    staging_root=staging,
                    paths=["link.txt"],
                )

    def test_refuse_secret_like_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            staging = root / "stage"
            staging.mkdir()
            bad = root / "leak.txt"
            bad.write_text("api_key=" + "SUPERSECRETVALUE123456" + "\n", encoding="utf-8")
            with self.assertRaises(InstallerError) as ctx:
                rc.stage_package_tree(
                    repo_root=root,
                    staging_root=staging,
                    paths=["leak.txt"],
                )
            self.assertIn("credential", ctx.exception.message.lower())

    def test_refuse_host_absolute_path_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            staging = root / "stage"
            staging.mkdir()
            bad = root / "pathy.txt"
            bad.write_text(f"checkout={root}/something\n", encoding="utf-8")
            with self.assertRaises(InstallerError) as ctx:
                rc.stage_package_tree(
                    repo_root=root,
                    staging_root=staging,
                    paths=["pathy.txt"],
                )
            self.assertIn("host", ctx.exception.message.lower())

    def test_metadata_schema_shape(self) -> None:
        schema = json.loads(
            (rc.REPO_ROOT / "core/managed-core/schemas/release-candidate.schema.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(schema["properties"]["kind"]["const"], "ide-development-release-candidate")
        required = set(schema["required"])
        for key in (
            "packageVersion",
            "sourceCommit",
            "manifestHash",
            "archives",
            "provenance",
            "installInstructions",
            "rollbackInstructions",
        ):
            self.assertIn(key, required)


class ReleaseCandidateCliSmokeTests(unittest.TestCase):
    def test_module_help(self) -> None:
        parser = rc.build_parser()
        help_text = parser.format_help()
        self.assertIn("create", help_text)
        self.assertIn("verify", help_text)


if __name__ == "__main__":
    unittest.main()
