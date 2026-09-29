"""End-to-end v2.5.2 -> v3.0.0 upgrade on a synthetic consumer (no network).

The fixture is a real v2.5.2 state: the published v2.5.2 package (release
commit 5a64f7f, read from local git objects) installs itself into a temporary
consumer, and the v2.5.2 ``sync-managed-workflows.sh`` renders its root
workflows. The v3 installer from this checkout then plans, updates, verifies
and rolls back that consumer.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from ide_development import v3_retirements
from ide_development.engine import _migration_catalog
from ide_development.errors import ConflictError
from ide_development.manifest import load_manifest
from ide_development.plan import build_plan
from ide_development.retired_workflows import RETIRED_ROOT_WORKFLOWS
from ide_development.state import load_installed_state
from ide_development.transaction import apply_plan, current_tx_dir

REPO = Path(__file__).resolve().parents[2]
V3_CLI = REPO / "scripts" / "ide-development.py"
V3_SYNC = REPO / "scripts" / "sync-managed-workflows.sh"
V252_REF = v3_retirements.V252_REF
CONSUMER_CONFIG = {
    "schemaVersion": 1,
    "ciWorkflowName": "CI",
    "branchPolicyWorkflowName": "Branch Source Policy",
    "bugbotCheckName": "Linktrend Review Gate",
}
CONSUMER_CI = "name: CI\non: [push]\njobs: {}\n"


def _git(*args: str, cwd: Path, **kwargs) -> subprocess.CompletedProcess:
    env = {
        **os.environ,
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "commit.gpgsign",
        "GIT_CONFIG_VALUE_0": "false",
    }
    return subprocess.run(["git", *args], cwd=cwd, env=env, check=True, capture_output=True, **kwargs)


def _have_v252_objects() -> bool:
    probe = subprocess.run(
        ["git", "-C", str(REPO), "cat-file", "-e", f"{V252_REF}^{{commit}}"],
        capture_output=True,
    )
    return probe.returncode == 0


def _rmtree(path: Path) -> None:
    def _unlock(func, target, _exc):
        os.chmod(target, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
        func(target)

    shutil.rmtree(path, onerror=_unlock)


def _snapshot(root: Path) -> dict[str, tuple]:
    out: dict[str, tuple] = {}
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        if rel == ".git" or rel.startswith(".git/"):
            continue
        if path.is_symlink():
            out[rel] = ("link", os.readlink(path))
        elif path.is_file():
            out[rel] = ("file", path.read_bytes(), stat.S_IMODE(path.stat().st_mode))
        else:
            out[rel] = ("dir",)
    return out


def _cli(command: str, target: Path, *extra: str) -> tuple[int, dict]:
    proc = subprocess.run(
        [sys.executable, str(V3_CLI), command, "--json", "--target", str(target), *extra],
        capture_output=True,
        text=True,
    )
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        payload = {"stdout": proc.stdout, "stderr": proc.stderr}
    return proc.returncode, payload


@unittest.skipUnless(shutil.which("git") and shutil.which("bash"), "git and bash required")
@unittest.skipUnless(os.name == "posix", "v2.5.2 fixture uses POSIX modes and bash")
class V3UpgradeTests(unittest.TestCase):
    tmp: Path
    fixture: Path

    @classmethod
    def setUpClass(cls) -> None:
        if not _have_v252_objects():
            raise unittest.SkipTest(
                f"v2.5.2 release commit {V252_REF[:7]} not in local git objects (shallow clone)"
            )
        cls.tmp = Path(tempfile.mkdtemp(prefix="ide-v3-upgrade-"))
        cls.package252 = cls.tmp / "package-v2.5.2"
        cls.package252.mkdir()
        archive = subprocess.run(
            ["git", "-C", str(REPO), "archive", "--format=tar", V252_REF],
            capture_output=True,
            check=True,
        ).stdout
        subprocess.run(["tar", "-x", "-C", str(cls.package252)], input=archive, check=True)
        cls.fixture = cls._build_consumer(cls.tmp / "fixture-github-actions", profile="github-actions")

    @classmethod
    def tearDownClass(cls) -> None:
        if getattr(cls, "tmp", None) is not None and cls.tmp.exists():
            _rmtree(cls.tmp)

    @classmethod
    def _build_consumer(cls, root: Path, *, profile: str) -> Path:
        root.mkdir(parents=True)
        _git("init", "-q", "-b", "development", cwd=root)
        _git("config", "user.email", "fixture@example.invalid", cwd=root)
        _git("config", "user.name", "fixture", cwd=root)
        workflows = root / ".github" / "workflows"
        workflows.mkdir(parents=True)
        (root / ".github" / "linktrend-gitops-consumer.json").write_text(
            json.dumps(CONSUMER_CONFIG, indent=2) + "\n", encoding="utf-8"
        )
        (workflows / "ci.yml").write_text(CONSUMER_CI, encoding="utf-8")
        (root / "README.md").write_text("consumer\n", encoding="utf-8")
        _git("add", "-A", cwd=root)
        _git("commit", "-qm", "consumer", cwd=root)
        install = subprocess.run(
            [sys.executable, str(cls.package252 / "scripts/ide-development.py"), "install",
             "--json", "--target", str(root)],
            capture_output=True,
            text=True,
        )
        if install.returncode != 0:
            raise AssertionError(f"v2.5.2 install failed: {install.stdout[-2000:]} {install.stderr[-2000:]}")
        subprocess.run(
            ["bash", str(cls.package252 / "scripts/sync-managed-workflows.sh"), str(root),
             "--orchestration-mode", profile],
            capture_output=True,
            text=True,
            check=True,
        )
        _git("add", "-A", cwd=root)
        _git("commit", "-qm", "v2.5.2", cwd=root)
        return root

    def _consumer(self) -> Path:
        dest = Path(tempfile.mkdtemp(prefix="consumer-", dir=self.tmp)) / "repo"
        shutil.copytree(self.fixture, dest, symlinks=True)
        return dest

    def _retired_catalog_paths(self) -> set[str]:
        catalog = json.loads((REPO / v3_retirements.CATALOG_REL).read_text(encoding="utf-8"))
        return {
            entry["path"]
            for entry in catalog["entries"]
            if entry.get("sincePackageVersion") == v3_retirements.SINCE_VERSION
        }

    def _move_directory_outside_and_link(self, consumer: Path, rel: str) -> Path:
        source = consumer / rel
        outside = Path(tempfile.mkdtemp(prefix="outside-", dir=self.tmp)) / "payload"
        shutil.copytree(source, outside, symlinks=True)
        _rmtree(source)
        source.symlink_to(outside, target_is_directory=True)
        return outside

    def test_fixture_is_a_clean_v252_install(self) -> None:
        state = json.loads((self.fixture / ".ide-development/installed-state.json").read_text())
        self.assertEqual(state["packageVersion"], "2.5.2")
        verify = subprocess.run(
            [sys.executable, str(self.package252 / "scripts/ide-development.py"), "verify",
             "--json", "--target", str(self.fixture)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(verify.returncode, 0, verify.stdout[-2000:])
        for name in RETIRED_ROOT_WORKFLOWS:
            if name == "linktrend-review-gate.yml":
                continue  # never in the v2.5.2 sync list
            self.assertTrue((self.fixture / ".github/workflows" / name).is_file(), name)

    def test_catalog_is_generated_from_v252_manifest(self) -> None:
        rows = v3_retirements.retired_manifest_rows()
        self.assertEqual({row["destination"] for row in rows}, self._retired_catalog_paths())
        try:
            errors = v3_retirements.check()
        except RuntimeError as exc:
            self.skipTest(f"published release tags unavailable: {exc}")
        self.assertEqual(errors, [])

    def test_upgrade_removes_every_retired_file_and_rollback_restores_exactly(self) -> None:
        consumer = self._consumer()
        before = _snapshot(consumer)
        state = json.loads((consumer / ".ide-development/installed-state.json").read_text())
        retired_present = sorted(p for p in self._retired_catalog_paths() if p in state["files"])
        self.assertTrue(retired_present)
        workflows_present = sorted(
            f".github/workflows/{name}"
            for name in RETIRED_ROOT_WORKFLOWS
            if (consumer / ".github/workflows" / name).is_file()
        )

        code, plan = _cli("plan", consumer)
        self.assertEqual(code, 0, plan.get("conflicts"))
        self.assertEqual(plan["conflicts"], [])
        removed = sorted(a["path"] for a in plan["actions"] if a["op"] == "remove")
        self.assertEqual(removed, sorted(retired_present + workflows_present))
        self.assertEqual(_snapshot(consumer), before, "plan must not mutate")

        code, update = _cli("update", consumer)
        self.assertEqual(code, 0, update.get("conflicts") or update)
        self.assertTrue(update["applied"])
        after_state = json.loads((consumer / ".ide-development/installed-state.json").read_text())
        self.assertEqual(after_state["packageVersion"], "3.0.0")
        for rel in removed:
            self.assertFalse((consumer / rel).exists(), rel)
            self.assertNotIn(rel, after_state["files"])
        live = sorted(os.listdir(consumer / ".github/workflows"))
        self.assertEqual(
            live, ["branch-source-policy.yml", "ci.yml", "linktrend-cleanup-merged.yml"]
        )
        self.assertEqual((consumer / ".github/workflows/ci.yml").read_text(), CONSUMER_CI)

        code, verify = _cli("verify", consumer)
        self.assertEqual(code, 0, verify.get("drift"))
        self.assertTrue(verify["verify"]["ok"])
        code, drift = _cli("drift", consumer)
        self.assertEqual(code, 0, drift.get("drift"))
        self.assertFalse([d for d in drift["all"] if d["kind"] == "orphan_managed"])

        rollback = subprocess.run(
            [sys.executable, str(V3_CLI), "rollback", "--json", "--target", str(consumer)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(rollback.returncode, 0, rollback.stdout[-2000:])
        self.assertEqual(_snapshot(consumer), before)
        status = _git("status", "--porcelain", cwd=consumer, text=True).stdout
        self.assertEqual(status, "")

    def test_modified_retired_managed_file_is_a_conflict_not_a_deletion(self) -> None:
        consumer = self._consumer()
        target = consumer / "scripts/gitops/delivery_controller.py"
        target.chmod(0o644)
        target.write_text(target.read_text() + "# local change\n")
        before = _snapshot(consumer)
        code, update = _cli("update", consumer)
        self.assertEqual(code, 11)
        paths = {(c["kind"], c["path"]) for c in update["conflicts"]}
        self.assertEqual(paths, {("unknown_content", "scripts/gitops/delivery_controller.py")})
        detail = update["conflicts"][0]["detail"]
        self.assertIn("modified locally", detail)
        self.assertIn("refusing removal", detail)
        self.assertEqual(_snapshot(consumer), before)

    def test_older_published_bytes_of_a_retired_file_are_removed(self) -> None:
        catalog = json.loads((REPO / v3_retirements.CATALOG_REL).read_text(encoding="utf-8"))
        older = next(
            e for e in catalog["entries"]
            if e.get("sincePackageVersion") == v3_retirements.SINCE_VERSION and "@v" in e["identity"]
        )
        release = older["identity"].rsplit("@", 1)[1]
        data = subprocess.run(
            ["git", "-C", str(REPO), "show", f"{release}:{v3_retirements.MANIFEST_REL}"],
            capture_output=True,
            check=True,
        ).stdout
        source = next(
            row["source"] for row in json.loads(data)["files"] if row["destination"] == older["path"]
        )
        old_bytes = subprocess.run(
            ["git", "-C", str(REPO), "show", f"{release}:{source}"], capture_output=True, check=True
        ).stdout
        consumer = self._consumer()
        target = consumer / older["path"]
        target.chmod(0o644)
        target.write_bytes(old_bytes)
        code, plan = _cli("plan", consumer)
        self.assertEqual(code, 0, plan.get("conflicts"))
        action = next(a for a in plan["actions"] if a["path"] == older["path"])
        self.assertEqual((action["op"], action["entryId"]), ("remove", older["identity"]))

    def test_modified_retired_root_workflow_is_a_conflict_not_a_deletion(self) -> None:
        consumer = self._consumer()
        target = consumer / ".github/workflows/linktrend-review-packager.yml"
        target.write_text(target.read_text() + "# local change\n")
        before = _snapshot(consumer)
        code, update = _cli("update", consumer)
        self.assertEqual(code, 11)
        self.assertEqual(
            [(c["kind"], c["path"]) for c in update["conflicts"]],
            [("unknown_content", ".github/workflows/linktrend-review-packager.yml")],
        )
        self.assertEqual(_snapshot(consumer), before)

    def test_symlinked_github_directory_never_deletes_outside_workflow(self) -> None:
        consumer = self._consumer()
        outside = self._move_directory_outside_and_link(consumer, ".github")
        victim = outside / "workflows/linktrend-review-packager.yml"
        expected = victim.read_bytes()

        code, update = _cli("update", consumer)

        self.assertEqual(code, 11, update)
        self.assertIn("symlink", json.dumps(update).lower())
        self.assertEqual(victim.read_bytes(), expected)

    def test_symlinked_workflows_directory_never_deletes_outside_workflow(self) -> None:
        consumer = self._consumer()
        outside = self._move_directory_outside_and_link(consumer, ".github/workflows")
        victim = outside / "linktrend-review-packager.yml"
        expected = victim.read_bytes()

        code, update = _cli("update", consumer)

        self.assertEqual(code, 11, update)
        self.assertIn("symlink", json.dumps(update).lower())
        self.assertEqual(victim.read_bytes(), expected)

    def test_symlinked_workflow_file_is_a_conflict_not_a_deletion(self) -> None:
        consumer = self._consumer()
        target = consumer / ".github/workflows/linktrend-review-packager.yml"
        outside = Path(tempfile.mkdtemp(prefix="outside-", dir=self.tmp)) / target.name
        outside.write_bytes(target.read_bytes())
        target.unlink()
        target.symlink_to(outside)
        expected = outside.read_bytes()

        code, update = _cli("update", consumer)

        self.assertEqual(code, 11, update)
        self.assertIn("symlink", json.dumps(update).lower())
        self.assertEqual(outside.read_bytes(), expected)
        self.assertTrue(target.is_symlink())

    def test_retired_file_under_symlinked_directory_conflicts_in_plan_verify_and_drift(
        self,
    ) -> None:
        consumer = self._consumer()
        rel = ".ide-development-upgrade-notes/obsolete-sparse-gitops-note-v1.md"
        outside = self._move_directory_outside_and_link(
            consumer, ".ide-development-upgrade-notes"
        )
        victim = outside / "obsolete-sparse-gitops-note-v1.md"
        expected = victim.read_bytes()

        code, plan = _cli("plan", consumer)

        self.assertEqual(code, 11, plan)
        self.assertIn(("symlink", rel), {(c["kind"], c["path"]) for c in plan["conflicts"]})
        self.assertNotIn(
            rel,
            {a["path"] for a in plan["actions"] if a["op"] == "remove"},
        )

        verify_code, verify = _cli("verify", consumer)
        self.assertEqual(verify_code, 11, verify)
        self.assertIn(("symlink", rel), {(c["kind"], c["path"]) for c in verify["conflicts"]})
        self.assertIn(
            ("unexpected_symlink", rel),
            {(d["kind"], d["path"]) for d in verify["drift"]},
        )

        drift_code, drift = _cli("drift", consumer)
        self.assertNotEqual(drift_code, 0, drift)
        self.assertIn(
            ("unexpected_symlink", rel),
            {(d["kind"], d["path"]) for d in drift["drift"]},
        )
        self.assertEqual(victim.read_bytes(), expected)

    def test_remove_revalidates_hash_and_rolls_back_when_file_changes_after_plan(self) -> None:
        consumer = self._consumer()
        manifest = load_manifest(REPO)
        prior = load_installed_state(consumer)
        plan = build_plan(
            command="update",
            package_root=REPO,
            target_root=consumer,
            manifest=manifest,
            migration=_migration_catalog(REPO, consumer),
            prior=prior,
            dry_run=False,
        )
        self.assertFalse(plan.has_conflicts)
        rel = ".github/workflows/linktrend-review-packager.yml"
        target = consumer / rel
        target.write_text(target.read_text(encoding="utf-8") + "# changed after plan\n")
        changed = _snapshot(consumer)

        with self.assertRaises(ConflictError) as caught:
            apply_plan(
                target_root=consumer,
                package_root=REPO,
                manifest=manifest,
                plan=plan,
                prior=prior,
            )

        self.assertIn(rel, caught.exception.message)
        self.assertEqual(_snapshot(consumer), changed)
        self.assertFalse(current_tx_dir(consumer).exists())

    def test_local_coordinator_renderings_are_recognised(self) -> None:
        consumer = self._build_consumer(self.tmp / "fixture-local-coordinator", profile="local-coordinator")
        header = (consumer / ".github/workflows/linktrend-review-packager.yml").read_text()
        self.assertTrue(header.startswith("# Orchestration profile: local-coordinator"))
        code, plan = _cli("plan", consumer)
        self.assertEqual(code, 0, plan.get("conflicts"))
        removed = {a["path"] for a in plan["actions"] if a["op"] == "remove"}
        for name in RETIRED_ROOT_WORKFLOWS:
            if (consumer / ".github/workflows" / name).is_file():
                self.assertIn(f".github/workflows/{name}", removed)

    def _sync(self, consumer: Path, *extra: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["bash", str(V3_SYNC), str(consumer), *extra], capture_output=True, text=True
        )

    def test_v3_sync_removes_retired_workflows_and_gates_deploy_caller(self) -> None:
        consumer = self._consumer()
        workflows = consumer / ".github/workflows"
        dry = self._sync(consumer, "--dry-run")
        self.assertEqual(dry.returncode, 0, dry.stderr)
        self.assertIn("DRY-RUN: would remove retired .github/workflows/linktrend-review-packager.yml", dry.stdout)
        self.assertTrue((workflows / "linktrend-review-packager.yml").is_file())

        synced = self._sync(consumer)
        self.assertEqual(synced.returncode, 0, synced.stderr)
        self.assertEqual(
            sorted(os.listdir(workflows)),
            ["branch-source-policy.yml", "ci.yml", "linktrend-cleanup-merged.yml", "linktrend-promote-main.yml"],
        )
        self.assertIn("deploy/target.json absent; linktrend-deploy.yml not synced", synced.stdout)

        (consumer / "deploy").mkdir()
        (consumer / "deploy/target.json").write_text("{}\n", encoding="utf-8")
        with_target = self._sync(consumer)
        self.assertEqual(with_target.returncode, 0, with_target.stderr)
        caller = workflows / "linktrend-deploy.yml"
        self.assertEqual(
            caller.read_bytes(),
            (REPO / "core/github/managed-workflows/linktrend-deploy.yml").read_bytes(),
        )

        (consumer / "deploy/target.json").unlink()
        without = self._sync(consumer)
        self.assertEqual(without.returncode, 0, without.stderr)
        self.assertFalse(caller.exists())

    def test_v3_sync_refuses_symlinked_workflow_directory_without_touching_outside(self) -> None:
        consumer = self._consumer()
        caller = consumer / ".github/workflows/linktrend-deploy.yml"
        caller.write_bytes(
            (REPO / "core/github/managed-workflows/linktrend-deploy.yml").read_bytes()
        )
        outside = self._move_directory_outside_and_link(consumer, ".github/workflows")
        before = _snapshot(outside)

        result = self._sync(consumer)

        self.assertEqual(result.returncode, 11, result)
        self.assertIn(".github or .github/workflows is a symlink", result.stderr)
        self.assertEqual(_snapshot(outside), before)

    def test_v3_sync_refuses_symlinked_deploy_file_without_touching_outside(self) -> None:
        consumer = self._consumer()
        caller = consumer / ".github/workflows/linktrend-deploy.yml"
        outside = Path(tempfile.mkdtemp(prefix="outside-", dir=self.tmp)) / caller.name
        outside.write_bytes(
            (REPO / "core/github/managed-workflows/linktrend-deploy.yml").read_bytes()
        )
        caller.symlink_to(outside)
        expected = outside.read_bytes()

        result = self._sync(consumer)

        self.assertEqual(result.returncode, 11, result)
        self.assertIn("linktrend-deploy.yml is a symlink; not removed", result.stderr)
        self.assertEqual(outside.read_bytes(), expected)
        self.assertTrue(caller.is_symlink())

    def test_v3_sync_keeps_modified_retired_workflow(self) -> None:
        consumer = self._consumer()
        target = consumer / ".github/workflows/linktrend-staging-to-main.yml"
        target.write_text(target.read_text() + "# local change\n")
        result = self._sync(consumer)
        self.assertEqual(result.returncode, 11)
        self.assertIn("CONFLICT: retired .github/workflows/linktrend-staging-to-main.yml", result.stderr)
        self.assertTrue(target.is_file())
        self.assertFalse((consumer / ".github/workflows/linktrend-review-packager.yml").exists())

    def test_sync_script_lists_the_same_retired_workflows(self) -> None:
        text = V3_SYNC.read_text(encoding="utf-8")
        block = text.split("RETIRED_FILES=(", 1)[1].split(")", 1)[0]
        listed = tuple(line.strip().strip('"') for line in block.splitlines() if line.strip())
        self.assertEqual(listed, RETIRED_ROOT_WORKFLOWS)


if __name__ == "__main__":
    unittest.main()
