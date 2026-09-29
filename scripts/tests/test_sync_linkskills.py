"""Offline tests for scripts/sync-linkskills.py using a local fake upstream."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "sync-linkskills.py"


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


if __name__ == "__main__":
    unittest.main()
