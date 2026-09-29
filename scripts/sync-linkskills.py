#!/usr/bin/env python3
"""Pin LiNKskills-owned skills into IDE Development.

Stdlib only. ``--write`` shallow-fetches one commit over git (https or a local
path) and replaces each ``authority: linkskills`` skill with that tree's
``skills/<id>/`` bytes. ``--check`` stays offline and compares those bytes to
the lock's per-file sha256 records.

Local edits to synced skills are not allowed. Skills that are not
``authority: linkskills`` are left unchanged.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_REPO = "https://github.com/linktrend/LiNKskills"
LOCK_RELS = (
    "core/link-integrations/skills-lock.json",
    "core/managed-core/platforms/cursor/skills-lock.json",
    "core/managed-core/platforms/codex/skills-lock.json",
)
REQUIRED_MIRROR_ROOTS = (
    "core/skills",
    "core/managed-core/skills",
)
OPTIONAL_MIRROR_ROOTS = (
    ".agents/skills",
    "core/managed-core/platforms/cursor/skills",
    "core/managed-core/platforms/codex/skills",
)
SHA_RE = r"^[0-9a-f]{40}$"
SKILL_ID_RE = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"


class SyncError(Exception):
    """A pin, copy, or hash failure."""


def _sha256(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _run_git(args: list[str], *, cwd: Path | None = None) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise SyncError(f"git {' '.join(args)} failed: {detail}")
    return completed.stdout.strip()


def _find_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / LOCK_RELS[0]).is_file():
            return candidate
    raise SyncError(
        f"skills lock not found from {start} ({LOCK_RELS[0]})"
    )


def _load_lock(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SyncError(f"cannot read skills lock {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SyncError(f"skills lock is not an object: {path}")
    return data


def _dump_lock(data: dict) -> str:
    return json.dumps(data, indent=2) + "\n"


def _lock_paths(root: Path) -> list[Path]:
    canonical = root / LOCK_RELS[0]
    if not canonical.is_file():
        raise SyncError(f"missing skills lock: {canonical}")
    paths = [canonical]
    for rel in LOCK_RELS[1:]:
        path = root / rel
        if path.is_file():
            paths.append(path)
    return paths


def _linkskills_ids(lock: dict) -> list[str]:
    skills = lock.get("skills")
    if not isinstance(skills, list):
        raise SyncError("skills lock has no skills array")
    ids: list[str] = []
    for row in skills:
        if isinstance(row, dict) and row.get("authority") == "linkskills":
            skill_id = row.get("skillId")
            if not isinstance(skill_id, str):
                raise SyncError("linkskills row is missing skillId")
            ids.append(skill_id)
    if not ids:
        raise SyncError("skills lock has no authority: linkskills entries")
    return ids


def _parse_skills(raw: str | None, default: list[str]) -> list[str]:
    if raw is None or raw.strip() == "":
        return list(default)
    ids = [part.strip() for part in raw.split(",") if part.strip()]
    if not ids:
        raise SyncError("empty --skills list")
    return ids


def _validate_skill_id(skill_id: str, allowed: set[str]) -> None:
    import re

    if not re.fullmatch(SKILL_ID_RE, skill_id) or skill_id not in allowed:
        raise SyncError(f"unknown skill: {skill_id}")


def _frontmatter_version(text: str, skill_id: str) -> str:
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        raise SyncError(f"{skill_id}: SKILL.md has no YAML frontmatter")
    newline = "\r\n" if text.startswith("---\r\n") else "\n"
    end = text.find(f"{newline}---", 3)
    if end < 0:
        raise SyncError(f"{skill_id}: SKILL.md frontmatter is not closed")
    block = text[text.find(newline) + len(newline) : end]
    for line in block.splitlines():
        if line.startswith("version:"):
            value = line.split(":", 1)[1].strip().strip("\"'")
            if value:
                return value
            break
    raise SyncError(f"{skill_id}: SKILL.md frontmatter has no version")


def _reject_symlinks(root: Path) -> None:
    if root.is_symlink():
        raise SyncError(f"symlink rejected: {root}")
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        current = Path(dirpath)
        kept: list[str] = []
        for name in dirnames:
            path = current / name
            if path.is_symlink():
                raise SyncError(f"symlink rejected: {path}")
            kept.append(name)
        dirnames[:] = kept
        for name in filenames:
            path = current / name
            if path.is_symlink():
                raise SyncError(f"symlink rejected: {path}")


def _iter_files(root: Path) -> list[Path]:
    _reject_symlinks(root)
    files: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        current = Path(dirpath)
        dirnames[:] = sorted(name for name in dirnames if not (current / name).is_symlink())
        for name in sorted(filenames):
            path = current / name
            if path.is_symlink() or not path.is_file():
                raise SyncError(f"symlink rejected: {path}")
            files.append(path)
    return files


def _relative_files(root: Path) -> list[tuple[str, bytes]]:
    records: list[tuple[str, bytes]] = []
    for path in _iter_files(root):
        rel = path.relative_to(root).as_posix()
        records.append((rel, path.read_bytes()))
    records.sort(key=lambda item: item[0])
    return records


def _copy_tree(src: Path, dest: Path) -> None:
    if dest.is_symlink():
        raise SyncError(f"symlink rejected: {dest}")
    parent = dest.parent
    parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{dest.name}.", dir=parent))
    try:
        for rel, _data in _relative_files(src):
            source = src / rel
            target = staging / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
            os.chmod(target, stat.S_IMODE(source.stat().st_mode))
        if dest.exists():
            if dest.is_symlink():
                raise SyncError(f"symlink rejected: {dest}")
            shutil.rmtree(dest)
        os.rename(staging, dest)
    except Exception:
        if staging.exists():
            shutil.rmtree(staging, ignore_errors=True)
        raise


def _mirror_dirs(root: Path, skill_id: str, *, create_required: bool) -> list[Path]:
    paths: list[Path] = []
    for rel in REQUIRED_MIRROR_ROOTS:
        paths.append(root / rel / skill_id)
    for rel in OPTIONAL_MIRROR_ROOTS:
        candidate = root / rel / skill_id
        if candidate.exists():
            paths.append(candidate)
    unique: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        if not create_required and not path.exists() and path.parent.name != Path(REQUIRED_MIRROR_ROOTS[0]).name:
            continue
        key = path.resolve() if path.exists() else path.parent.resolve() / path.name
        if key in seen:
            continue
        seen.add(key)
        unique.append(path)
    if create_required:
        return unique
    return [path for path in unique if path.exists() or path.parent.exists()]


def _fetch_pin(repo: str, commit: str) -> tuple[tempfile.TemporaryDirectory[str], Path, str]:
    import re

    if not re.fullmatch(SHA_RE, commit):
        raise SyncError(f"commit must be a 40-character sha: {commit}")
    temp = tempfile.TemporaryDirectory(prefix="linkskills-pin-")
    dest = Path(temp.name)
    try:
        _run_git(["init", "-q", str(dest)])
        _run_git(["-C", str(dest), "fetch", "--depth", "1", repo, commit])
        _run_git(["-C", str(dest), "checkout", "--detach", "--quiet", "FETCH_HEAD"])
        head = _run_git(["-C", str(dest), "rev-parse", "HEAD"])
        if head != commit:
            raise SyncError(f"fetched HEAD {head} is not {commit}")
        tree = _run_git(["-C", str(dest), "rev-parse", f"{commit}^{{tree}}"])
        if not re.fullmatch(SHA_RE, tree):
            raise SyncError(f"fetched tree is not a sha: {tree}")
    except Exception:
        temp.cleanup()
        raise
    return temp, dest, tree


def _skill_row(lock: dict, skill_id: str) -> dict:
    for row in lock["skills"]:
        if isinstance(row, dict) and row.get("skillId") == skill_id:
            return row
    raise SyncError(f"unknown skill: {skill_id}")


def _verify_recorded_tree(lock: dict, commit: str, tree: str) -> None:
    provider = lock.get("provider")
    if not isinstance(provider, dict):
        raise SyncError("skills lock provider is missing")
    recorded_tree = provider.get("tree")
    recorded_commit = provider.get("commit")
    if isinstance(recorded_tree, str) and recorded_tree and recorded_commit == commit:
        if recorded_tree != tree:
            raise SyncError(
                f"pinned tree mismatch: lock {recorded_tree} fetched {tree}"
            )


def _apply_lock(
    lock: dict,
    *,
    commit: str,
    tree: str,
    synced: dict[str, dict],
) -> None:
    provider = lock.get("provider")
    if not isinstance(provider, dict):
        raise SyncError("skills lock provider is missing")
    provider["commit"] = commit
    provider["tree"] = tree
    provider["syncedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for skill_id, payload in synced.items():
        row = _skill_row(lock, skill_id)
        if row.get("authority") != "linkskills":
            raise SyncError(f"refusing to rewrite non-linkskills skill: {skill_id}")
        row["version"] = payload["version"]
        row["entrypointDigest"] = payload["entrypointDigest"]
        row["files"] = payload["files"]
        files_by_path = {item["path"]: item["sha256"] for item in payload["files"]}
        fragments = row.get("fragments")
        if isinstance(fragments, list):
            kept = []
            for fragment in fragments:
                if not isinstance(fragment, dict):
                    kept.append(fragment)
                    continue
                rel = fragment.get("path")
                if isinstance(rel, str) and rel in files_by_path:
                    fragment["digest"] = files_by_path[rel]
                    kept.append(fragment)
            row["fragments"] = kept
        marker = f"/{skill_id}/"
        for section in ("copies", "packageMirrors"):
            rows = lock.get(section)
            if not isinstance(rows, list):
                continue
            for copy in rows:
                if not isinstance(copy, dict) or copy.get("skillId") != skill_id:
                    continue
                path = copy.get("path")
                if not isinstance(path, str) or marker not in f"/{path}":
                    continue
                rel = path.split(marker, 1)[1]
                if rel in files_by_path:
                    copy["digest"] = files_by_path[rel]


def _expected_files(row: dict, skill_id: str) -> list[dict]:
    files = row.get("files")
    if not isinstance(files, list) or not files:
        raise SyncError(f"{skill_id}: lock has no files list")
    seen: set[str] = set()
    normalized: list[dict] = []
    for item in files:
        if not isinstance(item, dict):
            raise SyncError(f"{skill_id}: malformed files entry")
        rel = item.get("path")
        digest = item.get("sha256")
        if (
            not isinstance(rel, str)
            or not rel
            or rel.startswith("/")
            or ".." in Path(rel).parts
            or "\\" in rel
            or not isinstance(digest, str)
            or not digest.startswith("sha256:")
            or len(digest) != 7 + 64
        ):
            raise SyncError(f"{skill_id}: malformed files entry for {rel!r}")
        if rel in seen:
            raise SyncError(f"{skill_id}: duplicate lock path {rel}")
        seen.add(rel)
        normalized.append({"path": rel, "sha256": digest})
    return normalized


def _check(root: Path, skill_ids: list[str], lock: dict, *, commit: str | None) -> list[str]:
    provider = lock.get("provider") if isinstance(lock.get("provider"), dict) else {}
    mismatches: list[str] = []
    if commit is not None and provider.get("commit") != commit:
        mismatches.append(
            f"provider commit {provider.get('commit')} != {commit}"
        )
    for other in _lock_paths(root)[1:]:
        other_lock = _load_lock(other)
        if _dump_lock(other_lock) != _dump_lock(lock):
            mismatches.append(f"lock drift: {other.relative_to(root)}")
    for skill_id in skill_ids:
        row = _skill_row(lock, skill_id)
        if row.get("authority") != "linkskills":
            mismatches.append(f"unknown skill: {skill_id}")
            continue
        try:
            expected = _expected_files(row, skill_id)
        except SyncError as exc:
            mismatches.append(str(exc))
            continue
        expected_map = {item["path"]: item["sha256"] for item in expected}
        skill_md = expected_map.get("SKILL.md")
        if skill_md is None:
            mismatches.append(f"{skill_id}: lock files list has no SKILL.md")
        elif row.get("entrypointDigest") != skill_md:
            mismatches.append(
                f"{skill_id}: entrypointDigest does not match SKILL.md"
            )
        mirrors = [
            path
            for path in _mirror_dirs(root, skill_id, create_required=False)
            if path.exists()
        ]
        required = [root / rel / skill_id for rel in REQUIRED_MIRROR_ROOTS]
        for path in required:
            if not path.exists():
                mismatches.append(f"missing mirror: {path.relative_to(root)}")
        seen_resolved: set[Path] = set()
        for mirror in mirrors:
            resolved = mirror.resolve()
            if resolved in seen_resolved:
                continue
            seen_resolved.add(resolved)
            label = str(mirror.relative_to(root))
            if mirror.is_symlink():
                mismatches.append(f"symlink rejected: {label}")
                continue
            try:
                actual = {rel: _sha256(data) for rel, data in _relative_files(mirror)}
            except SyncError as exc:
                mismatches.append(str(exc))
                continue
            for rel, digest in expected_map.items():
                got = actual.get(rel)
                if got is None:
                    mismatches.append(f"missing: {label}/{rel}")
                elif got != digest:
                    mismatches.append(
                        f"mismatch: {label}/{rel} expected {digest} actual {got}"
                    )
            for rel in sorted(set(actual) - set(expected_map)):
                mismatches.append(f"extra: {label}/{rel}")
    return mismatches


def _write(root: Path, repo: str, commit: str, skill_ids: list[str], lock: dict) -> None:
    allowed = set(_linkskills_ids(lock))
    for skill_id in skill_ids:
        _validate_skill_id(skill_id, allowed)
    holder, fetched, tree = _fetch_pin(repo, commit)
    try:
        _verify_recorded_tree(lock, commit, tree)
        upstream = fetched / "skills"
        payloads: dict[str, dict] = {}
        sources: dict[str, Path] = {}
        for skill_id in skill_ids:
            src = upstream / skill_id
            if not src.is_dir() or src.is_symlink():
                raise SyncError(f"unknown skill: {skill_id}")
            records = _relative_files(src)
            by_path = {rel: data for rel, data in records}
            if "SKILL.md" not in by_path:
                raise SyncError(f"{skill_id}: upstream skill has no SKILL.md")
            version = _frontmatter_version(by_path["SKILL.md"].decode("utf-8"), skill_id)
            files = [{"path": rel, "sha256": _sha256(data)} for rel, data in records]
            payloads[skill_id] = {
                "version": version,
                "entrypointDigest": _sha256(by_path["SKILL.md"]),
                "files": files,
            }
            sources[skill_id] = src
        for skill_id in skill_ids:
            for dest in _mirror_dirs(root, skill_id, create_required=True):
                if not dest.parent.is_dir():
                    raise SyncError(f"missing mirror root: {dest.parent}")
                _copy_tree(sources[skill_id], dest)
        _apply_lock(lock, commit=commit, tree=tree, synced=payloads)
        text = _dump_lock(lock)
        for path in _lock_paths(root):
            path.write_text(text, encoding="utf-8")
    finally:
        holder.cleanup()
    print(
        f"synced {', '.join(skill_ids)} from {commit} tree {tree}"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", help="Pinned upstream commit SHA")
    parser.add_argument("--repo", default=DEFAULT_REPO, help="Upstream git URL or local path")
    parser.add_argument(
        "--skills",
        help="Comma-separated skill ids (default: lock entries with authority linkskills)",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="Fetch the pin and replace synced skills")
    mode.add_argument("--check", action="store_true", help="Offline hash check against the lock")
    args = parser.parse_args(argv)

    try:
        root = _find_root(Path.cwd())
        lock = _load_lock(root / LOCK_RELS[0])
        allowed = _linkskills_ids(lock)
        skill_ids = _parse_skills(args.skills, allowed)
        for skill_id in skill_ids:
            _validate_skill_id(skill_id, set(allowed))
        if args.check:
            mismatches = _check(root, skill_ids, lock, commit=args.commit)
            if mismatches:
                print("FAIL: sync-linkskills --check", file=sys.stderr)
                for item in mismatches:
                    print(f" - {item}", file=sys.stderr)
                return 1
            print(f"PASS: sync-linkskills --check ({len(skill_ids)} skills)")
            return 0
        if not args.commit:
            raise SyncError("--write requires --commit")
        _write(root, args.repo, args.commit.lower(), skill_ids, lock)
        return 0
    except SyncError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
