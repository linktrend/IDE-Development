"""Offline tests for scripts/sync-linkskills.py using a local fake upstream."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "sync-linkskills.py"


def _load_sync():
    spec = importlib.util.spec_from_file_location("sync_linkskills", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load sync-linkskills")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _git(path, "init", "-q")
    _git(path, "config", "user.email", "sync-test@example.com")
    _git(path, "config", "user.name", "sync-test")
    _git(path, "config", "commit.gpgsign", "false")


def _commit_all(path: Path, message: str) -> str:
    _git(path, "add", "-A")
    _git(path, "commit", "-q", "-m", message)
    return _git(path, "rev-parse", "HEAD")


def _lock(skill_id: str = "alpha") -> dict:
    return {
        "provider": {
            "repository": "linktrend/LiNKskills",
            "commit": "a" * 40,
            "tree": "b" * 40,
        },
        "skills": [
            {
                "skillId": skill_id,
                "version": "0.0.1",
                "decision": "qualified",
                "authority": "linkskills",
                "entrypointDigest": "sha256:" + ("c" * 64),
                "fragments": [
                    {
                        "fragmentId": "skill-md",
                        "fragmentLevel": 2,
                        "path": "SKILL.md",
                        "digest": "sha256:" + ("d" * 64),
                    }
                ],
            },
            {
                "skillId": "agentsetup",
                "version": "1.3.0",
                "decision": "qualified",
                "authority": "required_local_adapter",
                "entrypointDigest": "sha256:" + ("e" * 64),
            },
            {
                "skillId": "retired-local",
                "version": "0.0.0",
                "decision": "retired",
                "authority": "none",
                "entrypointDigest": "sha256:" + ("f" * 64),
            },
        ],
        "copies": [
            {
                "path": f"core/skills/{skill_id}/SKILL.md",
                "skillId": skill_id,
                "digest": "sha256:" + ("1" * 64),
            },
            {
                "path": "core/skills/retired-local/SKILL.md",
                "skillId": "retired-local",
                "digest": "sha256:" + ("2" * 64),
            },
        ],
    }


class SyncLinkskillsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.upstream = base / "upstream"
        self.ide = base / "ide"
        _init_repo(self.upstream)
        skill = self.upstream / "skills" / "alpha"
        skill.mkdir(parents=True)
        (skill / "SKILL.md").write_text(
            "---\nname: alpha\nversion: 1.4.0\n---\n\n# Alpha\n",
            encoding="utf-8",
        )
        (skill / "notes").mkdir()
        (skill / "notes" / "readme.md").write_text("note\n", encoding="utf-8")
        self.sha = _commit_all(self.upstream, "pin alpha")
        self.tree = _git(self.upstream, "rev-parse", f"{self.sha}^{{tree}}")
        lock_dir = self.ide / "core" / "link-integrations"
        lock_dir.mkdir(parents=True)
        (lock_dir / "skills-lock.json").write_text(
            json.dumps(_lock(), indent=2) + "\n",
            encoding="utf-8",
        )
        (self.ide / "core" / "skills").mkdir(parents=True)
        (self.ide / "core" / "managed-core" / "skills").mkdir(parents=True)
        mirror = self.ide / "core" / "managed-core" / "platforms" / "cursor"
        mirror.mkdir(parents=True)
        shutil.copyfile(lock_dir / "skills-lock.json", mirror / "skills-lock.json")

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(SCRIPT), *args],
            cwd=self.ide,
            capture_output=True,
            text=True,
        )

    def _write(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return self._run(
            "--commit",
            self.sha,
            "--repo",
            str(self.upstream),
            "--allow-local-repo",
            "--write",
            *extra,
        )

    def test_write_then_check(self) -> None:
        written = self._write()
        self.assertEqual(written.returncode, 0, written.stderr)
        for root in (
            self.ide / "core" / "skills" / "alpha",
            self.ide / "core" / "managed-core" / "skills" / "alpha",
        ):
            self.assertEqual(
                (root / "SKILL.md").read_text(encoding="utf-8"),
                "---\nname: alpha\nversion: 1.4.0\n---\n\n# Alpha\n",
            )
            self.assertEqual((root / "notes" / "readme.md").read_text(encoding="utf-8"), "note\n")
        lock = json.loads(
            (self.ide / "core" / "link-integrations" / "skills-lock.json").read_text(encoding="utf-8")
        )
        mirror = json.loads(
            (
                self.ide
                / "core/managed-core/platforms/cursor/skills-lock.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(lock, mirror)
        self.assertEqual(lock["provider"]["commit"], self.sha)
        self.assertEqual(lock["provider"]["tree"], self.tree)
        self.assertRegex(lock["provider"]["syncedAt"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
        row = next(item for item in lock["skills"] if item["skillId"] == "alpha")
        self.assertEqual(row["version"], "1.4.0")
        skill_md = next(item["sha256"] for item in row["files"] if item["path"] == "SKILL.md")
        self.assertEqual(row["entrypointDigest"], skill_md)
        self.assertEqual(
            {item["path"] for item in row["files"]},
            {"SKILL.md", "notes/readme.md"},
        )
        adapter = next(item for item in lock["skills"] if item["skillId"] == "agentsetup")
        retired = next(item for item in lock["skills"] if item["skillId"] == "retired-local")
        self.assertEqual(adapter["version"], "1.3.0")
        self.assertNotIn("files", adapter)
        self.assertEqual(retired["entrypointDigest"], "sha256:" + ("f" * 64))
        self.assertEqual(
            next(item for item in lock["copies"] if item["skillId"] == "retired-local")["digest"],
            "sha256:" + ("2" * 64),
        )
        checked = self._run("--check")
        self.assertEqual(checked.returncode, 0, checked.stderr)
        self.assertIn("PASS", checked.stdout)

    def test_tamper_fails_check(self) -> None:
        written = self._write()
        self.assertEqual(written.returncode, 0, written.stderr)
        target = self.ide / "core" / "skills" / "alpha" / "SKILL.md"
        target.write_text(target.read_text(encoding="utf-8") + "\nlocal edit\n", encoding="utf-8")
        checked = self._run("--check")
        self.assertNotEqual(checked.returncode, 0)
        self.assertIn("mismatch:", checked.stderr)
        self.assertIn("SKILL.md", checked.stderr)

    def test_symlink_rejected(self) -> None:
        skill = self.upstream / "skills" / "alpha"
        (skill / "linked.md").symlink_to("SKILL.md")
        self.sha = _commit_all(self.upstream, "add symlink")
        written = self._write()
        self.assertNotEqual(written.returncode, 0)
        self.assertIn("symlink rejected", written.stderr)
        self.assertFalse((self.ide / "core" / "skills" / "alpha").exists())

    def test_unknown_skill_rejected(self) -> None:
        written = self._write("--skills", "not-a-skill")
        self.assertNotEqual(written.returncode, 0)
        self.assertIn("unknown skill: not-a-skill", written.stderr)

    def test_recorded_tree_mismatch_rejected(self) -> None:
        first = self._write()
        self.assertEqual(first.returncode, 0, first.stderr)
        lock_path = self.ide / "core" / "link-integrations" / "skills-lock.json"
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        lock["provider"]["tree"] = "c" * 40
        text = json.dumps(lock, indent=2) + "\n"
        lock_path.write_text(text, encoding="utf-8")
        mirror = self.ide / "core/managed-core/platforms/cursor/skills-lock.json"
        mirror.write_text(text, encoding="utf-8")
        second = self._write()
        self.assertNotEqual(second.returncode, 0)
        self.assertIn("pinned tree mismatch", second.stderr)

    def test_unsafe_repos_rejected_without_git(self) -> None:
        mod = _load_sync()
        unsafe = (
            "--upload-pack=x",
            "ext::sh -c x",
            "file:///etc",
            "git@github.com:x/y",
        )
        for repo in unsafe:
            with self.subTest(repo=repo):
                err = io.StringIO()
                with mock.patch.object(
                    mod.subprocess, "run", side_effect=AssertionError("git ran")
                ):
                    with contextlib.redirect_stderr(err):
                        rc = mod.main(
                            [f"--repo={repo}", "--commit", "a" * 40, "--write"]
                        )
                self.assertEqual(rc, 1, err.getvalue())
                self.assertIn("refusing repo", err.getvalue())

    def test_github_owner_and_repo_segments_before_git(self) -> None:
        mod = _load_sync()
        rejected = (
            "https://github.com/../x",
            "https://github.com/a/..",
            "https://github.com/a/.",
            "https://github.com/-a/b",
            "https://github.com/a/b/",
            "https://github.com/a/b?x=1",
            "https://user@github.com/a/b",
            "https://github.com:443/a/b",
            "https://github.com/a/b\n",
        )
        for repo in rejected:
            with self.subTest(repo=repo):
                err = io.StringIO()
                with mock.patch.object(
                    mod.subprocess, "run", side_effect=AssertionError("git ran")
                ):
                    with contextlib.redirect_stderr(err):
                        rc = mod.main(
                            ["--repo", repo, "--commit", "a" * 40, "--write"]
                        )
                self.assertEqual(rc, 1, err.getvalue())
                self.assertIn("refusing repo", err.getvalue())

        accepted = (
            "https://github.com/linktrend/LiNKskills",
            "https://github.com/linktrend/LiNKskills.git",
        )
        for repo in accepted:
            with self.subTest(repo=repo):
                with mock.patch.object(
                    mod.subprocess, "run", side_effect=AssertionError("git ran")
                ):
                    argv = mod.git_fetch_command(
                        repo,
                        "ab" * 20,
                        Path("/tmp/linkskills-url-check"),
                        allow_local=False,
                    )
                self.assertIn(repo, argv)

    def test_local_repo_requires_flag(self) -> None:
        mod = _load_sync()
        err = io.StringIO()
        with mock.patch.object(mod.subprocess, "run", side_effect=AssertionError("git ran")):
            with contextlib.redirect_stderr(err):
                rc = mod.main(
                    [
                        "--repo",
                        str(self.upstream),
                        "--commit",
                        self.sha,
                        "--write",
                    ]
                )
        self.assertEqual(rc, 1, err.getvalue())
        self.assertIn("refusing repo", err.getvalue())

    def test_https_fetch_argv_without_network(self) -> None:
        mod = _load_sync()
        dest = Path("/tmp/linkskills-argv-check")
        repo = "https://github.com/linktrend/LiNKskills.git"
        commit = "ab" * 20
        argv = mod.git_fetch_command(repo, commit, dest, allow_local=False)
        self.assertEqual(
            argv,
            [
                "git",
                "-c",
                "protocol.allow=never",
                "-c",
                "protocol.https.allow=always",
                "-C",
                str(dest),
                "fetch",
                "--depth",
                "1",
                "--",
                repo,
                commit,
            ],
        )
        self.assertNotIn("protocol.file.allow=always", argv)
        local_argv = mod.git_fetch_command(
            repo, commit, dest, allow_local=True
        )
        self.assertIn("protocol.file.allow=always", local_argv)


if __name__ == "__main__":
    unittest.main()
