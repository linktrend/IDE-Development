import json
import os
import plistlib
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from host.coordinator.daemon import CoordinatorDaemon
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

    def test_rendered_launchd_arguments_start_safe_service_command(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "install"
            database = Path(directory) / "state.sqlite3"
            rendered = render_plist(install_root=root, database=database)
            plist = plistlib.loads(rendered.encode("utf-8"))
            self.assertEqual(
                plist["ProgramArguments"],
                ["/usr/bin/python3", "-m", "host.coordinator", "--db", str(database), "run"],
            )
            self.assertNotIn("--execute", plist["ProgramArguments"])

    def test_run_once_is_healthy_without_credentials_and_interrupt_stops_loop(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / "state.sqlite3"
            environment = dict(os.environ)
            environment.pop("LINKTREND_AUTOMATION_TOKEN", None)
            daemon = CoordinatorDaemon(database)
            daemon.register("owner/repo", directory)
            daemon.close()
            command = [sys.executable, "-m", "host.coordinator", "--db", str(database), "run", "--once"]
            one_shot = subprocess.run(command, capture_output=True, text=True, env=environment, check=False)
            self.assertEqual(one_shot.returncode, 0, one_shot.stderr)
            one_shot_payload = json.loads(one_shot.stdout)
            self.assertEqual(one_shot_payload["status"], "healthy")
            self.assertEqual(one_shot_payload["polls"][0]["status"], "failed-closed")

            persistent = subprocess.Popen(
                [sys.executable, "-m", "host.coordinator", "--db", str(database), "run", "--interval", "0.1"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=environment,
            )
            try:
                deadline = time.time() + 5
                while persistent.poll() is None and time.time() < deadline:
                    time.sleep(0.01)
                self.assertIsNone(persistent.poll(), "persistent service exited before interrupt")
                persistent.send_signal(signal.SIGINT)
                stdout, stderr = persistent.communicate(timeout=5)
                self.assertEqual(persistent.returncode, 0, stderr)
                self.assertIn('"reason": "interrupt"', stdout)
            finally:
                if persistent.poll() is None:
                    persistent.kill()
                    persistent.communicate(timeout=5)

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

    def test_install_includes_all_multi_host_runtime_modules(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "install"
            plist = Path(directory) / (SERVICE_LABEL + ".plist")
            install_version(Path.cwd(), root, "2.0.0", plist, database=Path(directory) / "state.sqlite3")
            installed = root / "current" / "host" / "coordinator"
            for name in ("daemon.py", "multihost.py", "workers.py", "queue.py"):
                self.assertTrue((installed / name).is_file(), name)

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
