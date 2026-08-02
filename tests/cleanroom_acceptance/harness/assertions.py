"""Portability and discovery assertions for clean-room installs."""

from __future__ import annotations

import os
from pathlib import Path

from .paths import REPO_ROOT
from .repo import find_git_root


FORBIDDEN_CHECKOUT_MARKERS = (
    str(REPO_ROOT.resolve()),
    str(REPO_ROOT),
    "/Users/linktrend/Projects/IDE Development",
    "IDE Development/.git/linktrend-worktrees",
)


def iter_installed_files(repo: Path):
    for path in sorted(repo.rglob("*")):
        if not path.is_file():
            continue
        if ".git" in path.parts:
            # Allow git metadata; still skip scanning huge objects by limiting to
            # ide-development transaction text files only when needed by callers.
            continue
        yield path


def assert_no_escape_symlinks(repo: Path) -> list[str]:
    errors: list[str] = []
    root = repo.resolve()
    for path in sorted(repo.rglob("*")):
        if not path.is_symlink():
            continue
        rel = path.relative_to(repo).as_posix()
        # Symlinks under .git/ide-development may exist transiently; flag any
        # working-tree symlink that resolves outside the consumer.
        try:
            resolved = path.resolve()
        except OSError as exc:
            errors.append(f"symlink resolve failed {rel}: {exc}")
            continue
        try:
            resolved.relative_to(root)
        except ValueError:
            # readlink target may intentionally be outside during pre-migrate
            # fixtures; callers should invoke this post-install only.
            errors.append(
                f"installed symlink escapes consumer: {rel} -> {os.readlink(path)}"
            )
    return errors


def assert_no_checkout_paths_in_tree(repo: Path) -> list[str]:
    """Fail if installed working-tree files embed absolute source-checkout paths."""
    errors: list[str] = []
    markers = [m for m in FORBIDDEN_CHECKOUT_MARKERS if m]
    for path in iter_installed_files(repo):
        rel = path.relative_to(repo).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for marker in markers:
            if marker and marker in text:
                errors.append(f"checkout path leaked into {rel}")
                break
    return errors


def assert_cursor_codex_discovery(repo: Path, *, from_nested: Path) -> list[str]:
    """Prove Cursor/Codex managed entrypoints are discoverable from a nested cwd."""
    errors: list[str] = []
    root = find_git_root(from_nested)
    if root is None:
        return [f"no git root above {from_nested}"]
    if root.resolve() != repo.resolve():
        errors.append(f"nested walk found unexpected root {root} (want {repo})")

    cursor_rule = root / ".cursor" / "rules" / "sample-rule.mdc"
    cursor_skill = root / ".cursor" / "skills" / "sample-skill" / "SKILL.md"
    codex_skill = root / ".agents" / "skills" / "sample-skill" / "SKILL.md"
    agents = root / "AGENTS.md"

    for label, path in (
        ("cursor-rule", cursor_rule),
        ("cursor-skill", cursor_skill),
        ("codex-skill", codex_skill),
        ("agents-md", agents),
    ):
        if not path.is_file() or path.is_symlink():
            errors.append(f"{label} missing or not physical: {path.relative_to(root)}")
            continue
        try:
            path.resolve().relative_to(repo.resolve())
        except ValueError:
            errors.append(f"{label} resolves outside consumer: {path}")

    if agents.is_file():
        text = agents.read_text(encoding="utf-8")
        if "BEGIN LINKTREND-IDE-MANAGED" not in text:
            errors.append("AGENTS.md missing managed markers")
    return errors
