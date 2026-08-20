"""Adversarial tests for the PKT-08 generated-output closure contract."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.gitops.generated_output_closure import (
    ClosureError,
    candidate_source_tree,
    close_generated_outputs,
    load_graph,
    verify_generated_outputs,
)


def git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode:
        raise AssertionError(result.stderr or result.stdout)
    return result.stdout.strip()


def init_repo() -> tuple[tempfile.TemporaryDirectory[str], Path]:
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name) / "repo"
    root.mkdir()
    git(root, "init", "-q", "-b", "development")
    git(root, "config", "user.email", "pkt08@example.invalid")
    git(root, "config", "user.name", "PKT-08 tests")
    return tmp, root


def write(root: Path, rel: str, value: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def commit(root: Path, message: str) -> None:
    git(root, "add", "-A")
    git(root, "commit", "-qm", message)


def graph(
    *,
    outputs: list[dict[str, object]],
    max_passes: int = 3,
) -> dict[str, object]:
    return {
        "schemaVersion": 1,
        "kind": "generated-output-closure",
        "maxPasses": max_passes,
        "outputs": outputs,
    }


def output(
    output_path: str,
    generator: list[str],
    *,
    invalidating_sources: list[str] | None = None,
    depends_on: list[str] | None = None,
    output_id: str | None = None,
) -> dict[str, object]:
    return {
        "id": output_id or output_path.replace("/", "-"),
        "output": output_path,
        "generator": generator,
        "invalidatingSources": invalidating_sources or ["**/*.txt"],
        "dependsOn": depends_on or [],
    }


def write_graph(root: Path, payload: dict[str, object]) -> None:
    write(root, "closure.json", json.dumps(payload, indent=2) + "\n")


def script(root: Path, rel: str, body: str) -> list[str]:
    write(root, rel, body)
    return [sys.executable, rel]


class GeneratedOutputGraphTests(unittest.TestCase):
    def test_invalidating_source_is_named_and_order_is_deterministic(self) -> None:
        tmp, root = init_repo()
        self.addCleanup(tmp.cleanup)
        order = root / "order.txt"
        first = script(
            root,
            "first.py",
            "from pathlib import Path\n"
            "Path('order.txt').write_text('first\\n', encoding='utf-8')\n",
        )
        second = script(
            root,
            "second.py",
            "from pathlib import Path\n"
            "p=Path('order.txt'); p.write_text(p.read_text()+'second\\n', encoding='utf-8')\n",
        )
        write(root, "source.txt", "source\n")
        write_graph(
            root,
            graph(
                outputs=[
                    output("second.out", second, output_id="second", depends_on=["first"]),
                    output("first.out", first, output_id="first"),
                ]
            ),
        )
        commit(root, "closure graph")
        result = close_generated_outputs(root, graph_path="closure.json")
        self.assertEqual(result["generatorOrder"], ["first", "second"])
        self.assertEqual(order.read_text(encoding="utf-8"), "first\nsecond\n")
        self.assertEqual(result["sourceTree"], candidate_source_tree(root, "closure.json"))
        self.assertEqual(result["invalidatingSources"]["first"], ["source.txt"])
        self.assertEqual(result["invalidatingSources"]["second"], ["source.txt"])

    def test_ambiguous_dependency_and_cycle_fail_closed(self) -> None:
        tmp, root = init_repo()
        self.addCleanup(tmp.cleanup)
        write_graph(
            root,
            graph(
                outputs=[
                    output("same.out", ["true"], output_id="one"),
                    output("same.out", ["true"], output_id="two"),
                ]
            ),
        )
        with self.assertRaisesRegex(ClosureError, "ambiguous_dependency"):
            load_graph(root, "closure.json")
        write_graph(
            root,
            graph(
                outputs=[
                    output("one.out", ["true"], output_id="one", depends_on=["two"]),
                    output("two.out", ["true"], output_id="two", depends_on=["one"]),
                ]
            ),
        )
        with self.assertRaisesRegex(ClosureError, "ambiguous_dependency"):
            load_graph(root, "closure.json")

    def test_post_generation_source_or_output_mutation_is_rejected(self) -> None:
        tmp, root = init_repo()
        self.addCleanup(tmp.cleanup)
        generator = script(
            root,
            "generator.py",
            "from pathlib import Path\n"
            "Path('generated.out').write_text('stable\\n', encoding='utf-8')\n",
        )
        write(root, "source.txt", "source\n")
        write_graph(root, graph([output("generated.out", generator)]))
        commit(root, "closure inputs")

        with self.assertRaisesRegex(ClosureError, "post_generation_mutation"):
            close_generated_outputs(
                root,
                graph_path="closure.json",
                post_generation_hook=lambda: write(root, "source.txt", "mutated\n"),
            )
        with self.assertRaisesRegex(ClosureError, "post_generation_mutation"):
            close_generated_outputs(
                root,
                graph_path="closure.json",
                post_generation_hook=lambda: write(root, "generated.out", "tampered\n"),
            )

    def test_non_convergence_and_generator_failure_include_digests(self) -> None:
        tmp, root = init_repo()
        self.addCleanup(tmp.cleanup)
        toggler = script(
            root,
            "toggle.py",
            "from pathlib import Path\n"
            "p=Path('generated.out'); p.write_text(p.read_text()+'x', encoding='utf-8') if p.exists() else p.write_text('x', encoding='utf-8')\n",
        )
        write(root, "source.txt", "source\n")
        write_graph(root, graph([output("generated.out", toggler)], max_passes=2))
        commit(root, "non-converging generator")
        with self.assertRaisesRegex(ClosureError, "non_convergence"):
            close_generated_outputs(root, graph_path="closure.json")

        failing = script(
            root,
            "failing.py",
            "raise SystemExit('generator boom')\n",
        )
        write_graph(root, graph([output("generated.out", failing)]))
        with self.assertRaisesRegex(ClosureError, "generator_failure"):
            close_generated_outputs(root, graph_path="closure.json")

    def test_dirty_and_stale_output_are_rejected_by_verifier(self) -> None:
        tmp, root = init_repo()
        self.addCleanup(tmp.cleanup)
        generator = script(
            root,
            "generator.py",
            "from pathlib import Path\n"
            "Path('generated.out').write_text(Path('source.txt').read_text(), encoding='utf-8')\n",
        )
        write(root, "source.txt", "one\n")
        write(root, "generated.out", "one\n")
        write_graph(root, graph([output("generated.out", generator)]))
        commit(root, "clean generated output")
        verify_generated_outputs(root, graph_path="closure.json")

        write(root, "source.txt", "two\n")
        with self.assertRaisesRegex(ClosureError, "stale_output"):
            verify_generated_outputs(root, graph_path="closure.json")

        write(root, "generated.out", "dirty\n")
        with self.assertRaisesRegex(ClosureError, "dirty_output"):
            verify_generated_outputs(root, graph_path="closure.json")

    def test_generated_outputs_are_excluded_from_candidate_tree(self) -> None:
        tmp, root = init_repo()
        self.addCleanup(tmp.cleanup)
        write(root, "source.txt", "same\n")
        write(root, "generated.out", "first\n")
        write_graph(root, graph([output("generated.out", ["true"])]))
        commit(root, "candidate tree")
        before = candidate_source_tree(root, "closure.json")
        write(root, "generated.out", "second\n")
        git(root, "add", "generated.out")
        after = candidate_source_tree(root, "closure.json")
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
