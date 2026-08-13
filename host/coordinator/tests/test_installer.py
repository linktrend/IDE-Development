import tempfile
import unittest
from pathlib import Path

from host.coordinator.service import SERVICE_LABEL, install_version, render_plist, rollback, uninstall


class InstallerTests(unittest.TestCase):
    def test_dry_run_is_secret_free_and_scoped(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "install"
            plist = Path(directory) / (SERVICE_LABEL + ".plist")
            plan = install_version(Path.cwd(), root, "2.0.0", plist, database=Path(directory) / "state.sqlite3", dry_run=True)
            self.assertTrue(plan.dry_run)
            text = render_plist(install_root=root, database=Path(directory) / "state.sqlite3")
            self.assertNotIn("TOKEN", text.upper())
            self.assertNotIn("SECRET", text.upper())

    def test_atomic_activation_retains_previous_and_rolls_back(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "install"
            plist = Path(directory) / (SERVICE_LABEL + ".plist")
            install_version(Path.cwd(), root, "1.0.0", plist, database=Path(directory) / "state.sqlite3")
            install_version(Path.cwd(), root, "2.0.0", plist, database=Path(directory) / "state.sqlite3")
            self.assertEqual((root / "current").resolve().name, "2.0.0")
            self.assertEqual((root / "previous").resolve().name, "1.0.0")
            rollback(root)
            self.assertEqual((root / "current").resolve().name, "1.0.0")

    def test_uninstall_is_scoped_and_dry_run_does_not_delete(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "install"
            plist = Path(directory) / (SERVICE_LABEL + ".plist")
            root.mkdir()
            sentinel = Path(directory) / "keep.txt"
            sentinel.write_text("keep")
            result = uninstall(root, plist, dry_run=True)
            self.assertTrue(result["dryRun"])
            self.assertTrue(root.exists())
            uninstall(root, plist)
            self.assertFalse(root.exists())
            self.assertTrue(sentinel.exists())

    def test_uninstall_rejects_other_plist(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                uninstall(Path(directory) / "install", Path(directory) / "other.plist", dry_run=True)


if __name__ == "__main__":
    unittest.main()
