"""Disposable helpers for Lane E security acceptance (no live mutation)."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "scripts"
ENTRYPOINT = SCRIPTS_DIR / "ide-development.py"
FIXTURE_PACKAGE = SCRIPTS_DIR / "ide_development_tests" / "fixtures" / "package_v2"
SECURITY_FIXTURES = SCRIPTS_DIR / "ide_development_tests" / "fixtures" / "security"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# Absolute checkout / username / Windows drive smells
ABSOLUTE_PATH_RE = re.compile(
    r"(?:^|[\s\"'`=])"
    r"(?:"
    r"/Users/[A-Za-z0-9._-]+/"
    r"|/home/[A-Za-z0-9._-]+/"
    r"|[A-Za-z]:\\\\"
    r"|\\\\[A-Za-z0-9._$-]+\\"
    r")"
)

CREDENTIAL_RES = [
    re.compile(r"(?i)api[_-]?key\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}"),
    re.compile(r"(?i)secret\s*[:=]\s*['\"]?[A-Za-z0-9_\-/+=]{12,}"),
    re.compile(r"(?i)token\s*[:=]\s*['\"]?[A-Za-z0-9_\-\.]{16,}"),
    re.compile(r"(?i)BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
]

LOCAL_USERNAME_RE = re.compile(r"(?i)(?:^|[\s\"'`=])/Users/([A-Za-z0-9._-]+)/")


def make_git_repo(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=str(path), check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "security-acceptance@example.com"],
        cwd=str(path),
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Security Acceptance"],
        cwd=str(path),
        check=True,
        capture_output=True,
    )
    (path / "README.md").write_text("# consumer\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=str(path), check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=str(path),
        check=True,
        capture_output=True,
    )
    return path


def copy_package(dest: Path, *, src: Path | None = None) -> Path:
    source = src or FIXTURE_PACKAGE
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(source, dest, symlinks=False)
    return dest


def load_manifest(package: Path) -> dict[str, Any]:
    path = package / "core" / "managed-core" / "MANIFEST.json"
    return json.loads(path.read_text(encoding="utf-8"))


def write_manifest(package: Path, data: dict[str, Any]) -> None:
    path = package / "core" / "managed-core" / "MANIFEST.json"
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def rewrite_entry_hash(package: Path, entry_id: str, source: Path) -> None:
    from ide_development.hashing import sha256_file

    data = load_manifest(package)
    digest = sha256_file(source)
    for entry in data["files"]:
        if entry["id"] == entry_id:
            entry["sourceHash"] = digest
            break
    else:
        raise KeyError(entry_id)
    write_manifest(package, data)


def run_cli(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    cmd = [sys.executable, str(ENTRYPOINT), *args]
    env = {**os.environ, "PYTHONPATH": str(SCRIPTS_DIR)}
    return subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        cwd=str(cwd) if cwd else None,
        env=env,
    )


def parse_json_stdout(proc: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    text = proc.stdout.strip()
    if "--- json ---" in text:
        text = text.split("--- json ---", 1)[1].strip()
    return json.loads(text)


def scan_text(text: str, *, rel: str) -> list[str]:
    findings: list[str] = []
    if ABSOLUTE_PATH_RE.search(text):
        findings.append(f"{rel}: absolute host/checkout path smell")
    if LOCAL_USERNAME_RE.search(text):
        findings.append(f"{rel}: local username path smell")
    for cre in CREDENTIAL_RES:
        if cre.search(text):
            findings.append(f"{rel}: credential/secret pattern")
            break
    return findings


def scan_tree(root: Path, *, base: Path | None = None) -> list[str]:
    base = base or root
    findings: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico"}:
            continue
        rel = str(path.relative_to(base)).replace("\\", "/")
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = path.read_bytes().decode("latin-1", errors="ignore")
        findings.extend(scan_text(text, rel=rel))
    return findings


class DisposableRepoTestCase(unittest.TestCase):
    """Temp consumer git repo + optional package copy under disposable root."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="lane-e-sec-")
        self.root = Path(self._tmp.name)
        self.target = make_git_repo(self.root / "consumer repo with spaces")
        self.package = copy_package(self.root / "package")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def assert_cli_refusal(
        self,
        *args: str,
        expected_exit: int,
        require_ok_false: bool = True,
    ) -> dict[str, Any]:
        proc = run_cli(*args, "--json")
        self.assertEqual(
            proc.returncode,
            expected_exit,
            msg=f"stdout={proc.stdout!r}\nstderr={proc.stderr!r}",
        )
        payload = parse_json_stdout(proc)
        self.assertIsInstance(payload, dict)
        if require_ok_false:
            # Plan/install conflict payloads may omit ok=False and use conflicts[]
            if "ok" in payload:
                self.assertFalse(payload["ok"])
            if "exitCode" in payload:
                self.assertEqual(payload["exitCode"], expected_exit)
        return payload
