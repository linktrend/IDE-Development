"""Focused static checks for the lean workflow/ruleset contract."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LIVE = ROOT / ".github" / "workflows"
MANAGED = ROOT / "core" / "github" / "managed-workflows"
RULESET_REQUIRED_CONTEXTS = ("Linktrend Fast Checks", "Linktrend Branch Source Policy")


def _block(text: str, key: str) -> list[str]:
    lines = text.splitlines()
    try:
        start = lines.index(f"{key}:")
    except ValueError:
        return []
    body: list[str] = []
    for line in lines[start + 1 :]:
        if line.strip() and not line.startswith(" ") and not line.startswith("#"):
            break
        body.append(line)
    return body


def _children(lines: list[str], indent: int) -> dict[str, list[str]]:
    """Group a YAML block into ``key -> nested lines`` at one indentation level."""
    prefix = " " * indent
    key_re = re.compile(rf"^{prefix}([A-Za-z0-9_-]+):(.*)$")
    out: dict[str, list[str]] = {}
    current: str | None = None
    for line in lines:
        match = key_re.match(line)
        if match and not line[indent].isspace():
            current = match.group(1)
            out[current] = [match.group(2)]
        elif current is not None:
            out[current].append(line)
    return out


def _scalar(lines: list[str], key: str, indent: int) -> str | None:
    for line in lines:
        match = re.match(rf"^{' ' * indent}{key}:\s*(.*)$", line)
        if match:
            return match.group(1).strip().strip('"')
    return None


def _branches(lines: list[str]) -> list[str]:
    value = _scalar(lines, "branches", 4) or ""
    return [item.strip().strip('"') for item in value.strip("[]").split(",") if item.strip()]


def _load(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    events = {name: {"branches": _branches(body), "lines": body} for name, body in _children(_block(text, "on"), 2).items()}
    jobs = {
        job_id: {"name": _scalar(body, "name", 4), "lines": body}
        for job_id, body in _children(_block(text, "jobs"), 2).items()
    }
    return {"on": events, "jobs": jobs, "text": text}


class GithubWorkflowContractTests(unittest.TestCase):
    def test_ci_runs_fast_profile_as_required_context(self) -> None:
        document = _load(LIVE / "ci.yml")
        jobs = document["jobs"]
        self.assertEqual(jobs["fast"]["name"], "Linktrend Fast Checks")
        self.assertEqual(jobs["verify"]["name"], "Verify IDE Development")
        self.assertIn(
            "        run: python3 scripts/gitops/run_delivery_profile.py fast",
            jobs["fast"]["lines"],
        )
        self.assertIsNone(_scalar(jobs["fast"]["lines"], "if", 4))
        events = document["on"]
        self.assertEqual(sorted(events["pull_request"]["branches"]), ["development", "main"])
        self.assertEqual(sorted(events["push"]["branches"]), ["development", "main"])
        self.assertIsNone(_scalar(events["pull_request"]["lines"], "branches-ignore", 4))
        self.assertIsNone(_scalar(events["pull_request"]["lines"], "paths", 4))

    def test_ruleset_required_contexts_are_produced_for_development_prs(self) -> None:
        producers: dict[str, list[str]] = {context: [] for context in RULESET_REQUIRED_CONTEXTS}
        for path in sorted(LIVE.glob("*.yml")):
            document = _load(path)
            pull_request = document["on"].get("pull_request")
            if pull_request is None or "development" not in pull_request["branches"]:
                continue
            for job_id, job in document["jobs"].items():
                if job["name"] in producers:
                    producers[str(job["name"])].append(f"{path.name}:{job_id}")
        self.assertEqual(
            producers,
            {
                "Linktrend Fast Checks": ["ci.yml:fast"],
                "Linktrend Branch Source Policy": ["branch-source-policy.yml:branch-source-policy"],
            },
        )

    def test_managed_workflows_have_unique_job_contexts(self) -> None:
        for path in sorted(MANAGED.glob("*.yml")):
            jobs = _load(path)["jobs"]
            contexts = [str(job["name"]) for job in jobs.values() if job["name"]]
            self.assertEqual(len(contexts), len(set(contexts)), path.name)

    def test_required_contexts_have_event_scoped_producers(self) -> None:
        contract = json.loads(
            (ROOT / ".github" / "linktrend-repository-ci-contract.json").read_text()
        )
        required = {
            context
            for profile in contract["profiles"].values()
            for context in profile.get("requiredCheckContexts", [])
        }
        producers: dict[str, list[str]] = {context: [] for context in required}
        for path in sorted(LIVE.glob("*.yml")):
            for job_id, job in _load(path)["jobs"].items():
                context = str(job["name"] or "")
                if context in producers:
                    producers[context].append(f"{path.name}:{job_id}")
        self.assertEqual(
            producers,
            {
                "Linktrend Fast Checks": ["ci.yml:fast"],
                "Linktrend Branch Source Policy": [
                    "branch-source-policy.yml:branch-source-policy",
                ],
                "Verify IDE Development": ["ci.yml:verify"],
            },
        )

    def test_synced_templates_have_live_copies(self) -> None:
        for path in sorted(MANAGED.glob("*.yml")):
            live = LIVE / path.name
            self.assertTrue(live.is_file(), path.name)

    def test_source_policy_and_checkouts_are_bounded(self) -> None:
        source = (LIVE / "branch-source-policy.yml").read_text(encoding="utf-8")
        self.assertIn("branches: [development, main]", source)
        # Synced templates (and their live copies) must stay shallow; system-only
        # workflows such as ci.yml's Full run may need history.
        bounded = [*MANAGED.glob("*.yml"), *(LIVE / path.name for path in MANAGED.glob("*.yml"))]
        for path in bounded:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("fetch-depth: 0", text, path.name)
            for line in text.splitlines():
                if "git fetch" in line:
                    self.assertIn("--depth=1", line, path.name)
        fast = "\n".join(_load(LIVE / "ci.yml")["jobs"]["fast"]["lines"])
        self.assertNotIn("fetch-depth", fast)


if __name__ == "__main__":
    unittest.main()
