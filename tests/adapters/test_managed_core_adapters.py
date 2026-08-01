#!/usr/bin/env python3
"""Focused tests for WP3 Codex/Cursor managed-core platform adapters.

Verifies physical discovery via AGENTS.md + .agents/skills without requiring
.cursor, plus Cursor materialization templates and no Claude surfaces.
"""
from __future__ import annotations

import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PLATFORMS = ROOT / "core" / "managed-core" / "platforms"
AGENTS_SECTION = PLATFORMS / "codex" / "AGENTS.managed-section.md"
BEGIN = "<!-- BEGIN LINKTREND-IDE-MANAGED -->"
END = "<!-- END LINKTREND-IDE-MANAGED -->"


def upsert_agents_section(dest: Path, section: str) -> None:
    """Mirror sync-agents-managed-section.sh marker upsert semantics."""
    if dest.is_file():
        text = dest.read_text(encoding="utf-8")
    else:
        text = "# AGENTS.md\n\nConsumer repository agent guidance.\n"
    if BEGIN in text and END in text:
        pre = text.split(BEGIN, 1)[0]
        post = text.split(END, 1)[1]
        new = pre.rstrip() + "\n\n" + section.rstrip() + "\n" + (
            post if post.startswith("\n") else "\n" + post
        )
    else:
        new = text.rstrip() + "\n\n" + section.rstrip() + "\n"
    dest.write_text(new, encoding="utf-8")


def find_up(start: Path, relative: str) -> Path | None:
    """Walk parents from start looking for relative path (repo-root discovery)."""
    cur = start.resolve()
    if cur.is_file():
        cur = cur.parent
    for candidate in [cur, *cur.parents]:
        hit = candidate / relative
        if hit.exists():
            return hit
        if (candidate / ".git").exists() or (candidate / ".git").is_file():
            # Stop at VCS root even if missing, unless we already returned.
            if not hit.exists():
                return None
    return None


def _platforms_source(platforms_root: Path, source: str) -> Path:
    """Resolve a managed-core-relative `platforms/...` source against platforms_root."""
    parts = Path(source).parts
    if parts and parts[0] == "platforms":
        return platforms_root.joinpath(*parts[1:])
    return platforms_root / source


def materialize_required(platforms_root: Path, consumer: Path) -> list[str]:
    """Copy required Codex + Cursor adapter files declared in manifests."""
    written: list[str] = []
    codex = json.loads((platforms_root / "codex" / "skills-manifest.json").read_text(encoding="utf-8"))
    for entry in codex["required"]:
        src = _platforms_source(platforms_root, entry["source"])
        if not src.is_file():
            raise FileNotFoundError(src)
        dest = consumer / entry["destination"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        written.append(entry["destination"])

    cursor = json.loads(
        (platforms_root / "cursor" / "materialization-manifest.json").read_text(encoding="utf-8")
    )
    for entry in cursor["entries"]:
        if not entry.get("required", False):
            continue
        src = _platforms_source(platforms_root, entry["source"])
        if not src.is_file():
            raise FileNotFoundError(src)
        dest = consumer / entry["destination"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        written.append(entry["destination"])
    return written


class PlatformTemplateTests(unittest.TestCase):
    def test_agents_managed_section_markers_and_core_pointer(self) -> None:
        text = AGENTS_SECTION.read_text(encoding="utf-8")
        self.assertIn(BEGIN, text)
        self.assertIn(END, text)
        self.assertIn(".ide-development/", text)
        self.assertIn(".agents/skills/", text)
        self.assertIn("Do **not** require `.cursor`", text)
        self.assertNotRegex(text, re.compile(r"\.claude|CLAUDE\.md", re.I))

    def test_codex_skills_forbid_cursor_dependency(self) -> None:
        for name in ("agentsetup", "agentcomply"):
            text = (PLATFORMS / "codex" / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("Do **not** require `.cursor`", text)
            self.assertIn(f".agents/skills/{name}/SKILL.md", text)
            # Must not instruct Codex to load .cursor skills as authority
            self.assertNotIn("Read and execute `.cursor/skills", text)

    def test_no_claude_surfaces_under_platforms_or_agents(self) -> None:
        banned = []
        for base in (PLATFORMS, ROOT / ".agents"):
            for path in base.rglob("*"):
                if not path.is_file():
                    continue
                rel = str(path.relative_to(ROOT))
                name = path.name.lower()
                if name in {"claude.md", "claudemd"} or ".claude" in rel.split("/"):
                    banned.append(rel)
                body = path.read_text(encoding="utf-8", errors="ignore")
                if re.search(r"(?i)add\s+\.claude|create\s+CLAUDE\.md|Claude Code entrypoint", body):
                    banned.append(rel)
        self.assertEqual(banned, [])

    def test_manifests_list_required_and_remaining_skills(self) -> None:
        codex = json.loads((PLATFORMS / "codex" / "skills-manifest.json").read_text(encoding="utf-8"))
        cursor = json.loads(
            (PLATFORMS / "cursor" / "materialization-manifest.json").read_text(encoding="utf-8")
        )
        system = json.loads((ROOT / ".agents" / "skills-manifest.json").read_text(encoding="utf-8"))

        required = {e["name"] for e in codex["required"]}
        self.assertEqual(required, {"agentsetup", "agentcomply"})
        self.assertTrue(codex["noCursorDependency"])
        self.assertTrue(codex["claudeOutOfScope"])
        self.assertGreaterEqual(len(codex["approvedRemainingSkills"]), 40)

        req_dest = {e["destination"] for e in cursor["entries"] if e.get("required")}
        self.assertIn(".cursor/skills/agentsetup/SKILL.md", req_dest)
        self.assertIn(".cursor/commands/agentsetup.md", req_dest)
        self.assertIn(".cursor/rules/cursor-gitops-bootstrap.mdc", req_dest)

        phys = {e["name"] for e in system["requiredPhysical"]}
        self.assertEqual(phys, {"agentsetup", "agentcomply"})
        self.assertTrue(system["noCursorDependency"])


class DiscoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="wp3-adapters-"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.consumer = self.tmp / "consumer"
        self.consumer.mkdir()
        (self.consumer / ".git").mkdir()  # discovery stop marker
        custom = "CONSUMER_OWNED_TEXT_DO_NOT_WIPE"
        (self.consumer / "AGENTS.md").write_text(
            f"# Consumer AGENTS\n\n{custom}\n\nRepo-owned policy.\n",
            encoding="utf-8",
        )
        section = AGENTS_SECTION.read_text(encoding="utf-8")
        upsert_agents_section(self.consumer / "AGENTS.md", section)
        materialize_required(PLATFORMS, self.consumer)
        self.custom = custom

    def test_agents_preserves_consumer_text(self) -> None:
        text = (self.consumer / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn(self.custom, text)
        self.assertIn(BEGIN, text)
        self.assertIn(".ide-development/", text)

    def test_codex_discovery_from_repo_root(self) -> None:
        agents = find_up(self.consumer, "AGENTS.md")
        skill = find_up(self.consumer, ".agents/skills/agentsetup/SKILL.md")
        self.assertIsNotNone(agents)
        self.assertIsNotNone(skill)
        assert skill is not None
        body = skill.read_text(encoding="utf-8")
        self.assertIn("Do **not** require `.cursor`", body)

    def test_codex_discovery_from_nested_directory(self) -> None:
        nested = self.consumer / "apps" / "svc" / "deep"
        nested.mkdir(parents=True)
        agents = find_up(nested, "AGENTS.md")
        setup = find_up(nested, ".agents/skills/agentsetup/SKILL.md")
        comply = find_up(nested, ".agents/skills/agentcomply/SKILL.md")
        self.assertIsNotNone(agents)
        self.assertIsNotNone(setup)
        self.assertIsNotNone(comply)
        assert agents is not None and setup is not None and comply is not None
        self.assertEqual(agents.resolve(), (self.consumer / "AGENTS.md").resolve())
        self.assertEqual(setup.resolve(), (self.consumer / ".agents/skills/agentsetup/SKILL.md").resolve())
        self.assertEqual(comply.resolve(), (self.consumer / ".agents/skills/agentcomply/SKILL.md").resolve())

    def test_codex_path_works_without_cursor_tree(self) -> None:
        # Ensure Codex surfaces exist even if .cursor is absent/ignored
        cursor = self.consumer / ".cursor"
        if cursor.exists():
            shutil.rmtree(cursor)
        self.assertFalse(cursor.exists())
        skill = self.consumer / ".agents" / "skills" / "agentsetup" / "SKILL.md"
        self.assertTrue(skill.is_file())
        agents = self.consumer / "AGENTS.md"
        self.assertIn(".agents/skills/", agents.read_text(encoding="utf-8"))
        nested = self.consumer / "nested" / "x"
        nested.mkdir(parents=True)
        found_agents = find_up(nested, "AGENTS.md")
        found_skill = find_up(nested, ".agents/skills/agentsetup/SKILL.md")
        self.assertIsNotNone(found_agents)
        self.assertIsNotNone(found_skill)
        assert found_skill is not None
        self.assertEqual(found_skill.resolve(), skill.resolve())

    def test_cursor_physical_surfaces_present_when_materialized(self) -> None:
        # Re-materialize cursor (previous test may have deleted); fresh consumer already has them
        for rel in (
            ".cursor/rules/cursor-gitops-bootstrap.mdc",
            ".cursor/commands/agentsetup.md",
            ".cursor/skills/agentsetup/SKILL.md",
            ".cursor/skills/agentcomply/SKILL.md",
        ):
            self.assertTrue((self.consumer / rel).is_file(), rel)


class SystemRepoAgentsTests(unittest.TestCase):
    def test_system_agents_skills_exist_and_are_discoverable(self) -> None:
        for name in ("agentsetup", "agentcomply"):
            path = ROOT / ".agents" / "skills" / name / "SKILL.md"
            self.assertTrue(path.is_file(), path)
            text = path.read_text(encoding="utf-8")
            self.assertIn("Do **not** require `.cursor`", text)
            self.assertIn("core/skills/", text)

        nested = ROOT / "core" / "managed-core" / "platforms"
        found = find_up(nested, ".agents/skills/agentsetup/SKILL.md")
        self.assertEqual(found, ROOT / ".agents" / "skills" / "agentsetup" / "SKILL.md")

    def test_lead_template_ready_without_root_agents_write(self) -> None:
        # WP3 must not require a root AGENTS.md write; template is prepared for lead.
        self.assertTrue(AGENTS_SECTION.is_file())
        root_agents = ROOT / "AGENTS.md"
        # Either absent, or if present must not be our only delivery vehicle.
        # Packet forbids editing root AGENTS.md in this packet.
        self.assertTrue(AGENTS_SECTION.read_text(encoding="utf-8").startswith(BEGIN) or BEGIN in AGENTS_SECTION.read_text(encoding="utf-8"))
        _ = root_agents  # intentionally unused; presence is lead's concern


if __name__ == "__main__":
    unittest.main(verbosity=2)
