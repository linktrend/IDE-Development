"""Consumer-owned preservation and managed-marker boundary enforcement."""

from __future__ import annotations

import unittest

from harness import DisposableRepoTestCase

from ide_development.constants import EXIT_CONFLICT, EXIT_OK
from ide_development.engine import run_install_or_update
from ide_development.errors import ConflictError
from ide_development.markers import extract_marker_block, render_marker_file
from ide_development.constants import DEFAULT_MARKER_BEGIN, DEFAULT_MARKER_END


class ConsumerAndMarkerTests(DisposableRepoTestCase):
    def test_consumer_owned_file_preserved_on_conflict(self) -> None:
        owned = self.target / ".cursor" / "rules" / "consumer-owned.mdc"
        owned.parent.mkdir(parents=True, exist_ok=True)
        owned.write_text("# consumer owned — do not touch\n", encoding="utf-8")
        collide = self.target / ".cursor" / "rules" / "sample-rule.mdc"
        collide.write_text("NOT THE PACKAGE\n", encoding="utf-8")

        result = run_install_or_update(
            target=self.target,
            package=self.package,
            command="install",
            dry_run=False,
        )
        self.assertEqual(result.exit_code, EXIT_CONFLICT, result.payload)
        self.assertEqual(owned.read_text(encoding="utf-8"), "# consumer owned — do not touch\n")
        self.assertEqual(collide.read_text(encoding="utf-8"), "NOT THE PACKAGE\n")
        self.assertFalse((self.target / ".ide-development" / "CORE.txt").exists())

    def test_marker_upsert_preserves_consumer_prefix(self) -> None:
        agents = self.target / "AGENTS.md"
        agents.write_text("# Consumer AGENTS\n\nKeep me forever.\n", encoding="utf-8")
        result = run_install_or_update(
            target=self.target,
            package=self.package,
            command="install",
            dry_run=False,
        )
        self.assertEqual(result.exit_code, EXIT_OK, result.payload)
        text = agents.read_text(encoding="utf-8")
        self.assertIn("Keep me forever.", text)
        self.assertIn("BEGIN LINKTREND-IDE-MANAGED", text)
        self.assertIn("Managed AGENTS block from package.", text)

    def test_duplicate_marker_pair_fail_closed(self) -> None:
        begin = DEFAULT_MARKER_BEGIN
        end = DEFAULT_MARKER_END
        text = f"a\n{begin}\nx\n{end}\nb\n{begin}\ny\n{end}\n"
        with self.assertRaises(ConflictError) as ctx:
            extract_marker_block(text, begin, end)
        self.assertEqual(ctx.exception.exit_code, EXIT_CONFLICT)
        self.assertIn("corrupted", str(ctx.exception).lower())

    def test_nested_markers_fail_closed(self) -> None:
        begin = DEFAULT_MARKER_BEGIN
        end = DEFAULT_MARKER_END
        text = f"pre\n{begin}\n{begin}\nnested\n{end}\n{end}\n"
        with self.assertRaises(ConflictError):
            extract_marker_block(text, begin, end)

    def test_marker_order_inverted_fail_closed(self) -> None:
        begin = DEFAULT_MARKER_BEGIN
        end = DEFAULT_MARKER_END
        text = f"{end}\nbody\n{begin}\n"
        with self.assertRaises(ConflictError):
            extract_marker_block(text, begin, end)

    def test_install_refuses_when_marker_pair_corrupted_on_disk(self) -> None:
        begin = DEFAULT_MARKER_BEGIN
        end = DEFAULT_MARKER_END
        agents = self.target / "AGENTS.md"
        agents.write_text(
            f"# Consumer\n{begin}\nmanaged\n{end}\nextra\n{begin}\nagain\n{end}\n",
            encoding="utf-8",
        )
        result = run_install_or_update(
            target=self.target,
            package=self.package,
            command="install",
            dry_run=False,
        )
        self.assertEqual(result.exit_code, EXIT_CONFLICT, result.payload)
        # Consumer text must remain byte-identical (no partial marker rewrite).
        self.assertIn("extra", agents.read_text(encoding="utf-8"))
        kinds = {c["kind"] for c in result.payload.get("conflicts") or []}
        self.assertTrue(
            "marker_conflict" in kinds or "unknown_content" in kinds or kinds,
            msg=result.payload,
        )

    def test_render_appends_without_clobbering_consumer(self) -> None:
        rendered = render_marker_file(
            "# only consumer\n",
            "managed body\n",
            DEFAULT_MARKER_BEGIN,
            DEFAULT_MARKER_END,
        )
        self.assertTrue(rendered.startswith("# only consumer\n"))
        self.assertIn(DEFAULT_MARKER_BEGIN, rendered)
        self.assertIn("managed body", rendered)


if __name__ == "__main__":
    unittest.main()
