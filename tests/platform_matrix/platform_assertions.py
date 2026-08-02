"""Windows-safe filesystem assertions for the platform matrix.

POSIX mode bits and symlink privileges are not portable. Callers must use these
helpers instead of asserting ``stat.S_IMODE(...) == 0o644`` or creating symlinks
unconditionally on Windows.
"""

from __future__ import annotations

import os
import stat
import sys
import tempfile
from pathlib import Path
from typing import Optional, Tuple


def is_windows() -> bool:
    return sys.platform == "win32"


def can_create_symlinks() -> bool:
    """Return True when the process can create a file symlink in a temp dir.

    Justification: Windows requires Developer Mode or elevated privilege for
    ``os.symlink``. When unavailable, symlink-creation tests must be excluded
    and replaced with physical-file / refuse-via-detection equivalents.
    """
    if not hasattr(os, "symlink"):
        return False
    try:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = root / "target.txt"
            target.write_text("probe\n", encoding="utf-8")
            link = root / "link.txt"
            os.symlink(str(target), str(link))
            return link.is_symlink()
    except (OSError, NotImplementedError, AttributeError):
        return False


def assert_physical_file(test_case, path: Path, *, label: str = "") -> None:
    """Assert path is a regular physical file (not a symlink/junction when detectable)."""
    msg = label or str(path)
    test_case.assertTrue(path.exists(), f"missing file: {msg}")
    test_case.assertTrue(path.is_file(), f"not a file: {msg}")
    # is_symlink() is False for ordinary files on all platforms; when True on
    # Windows it usually indicates a symlink (junctions may vary — treat True
    # as failure for managed install destinations).
    test_case.assertFalse(path.is_symlink(), f"managed path must be physical, not symlink: {msg}")


def assert_mode_portable(
    test_case,
    path: Path,
    expected_posix_mode: int,
    *,
    label: str = "",
) -> None:
    """Assert file mode in a platform-correct way.

    - POSIX: exact ``stat.S_IMODE`` match against ``expected_posix_mode``.
    - Windows: do **not** pretend Unix mode bits exist. Assert the file is a
      regular physical file that is readable; optionally writable when the
      expected POSIX mode includes owner-write.
    """
    msg = label or str(path)
    assert_physical_file(test_case, path, label=msg)
    mode = stat.S_IMODE(path.stat().st_mode)
    if is_windows():
        # Equivalent safety: content reachable; write bit intent → writable file.
        test_case.assertTrue(os.access(path, os.R_OK), f"Windows file not readable: {msg}")
        if expected_posix_mode & stat.S_IWUSR:
            test_case.assertTrue(
                os.access(path, os.W_OK),
                f"Windows file expected writable (POSIX intent {expected_posix_mode:04o}): {msg}",
            )
        # Record observed Windows mode for diagnostics without asserting equality.
        test_case.assertIsInstance(mode, int)
        return
    test_case.assertEqual(
        mode,
        expected_posix_mode,
        f"POSIX mode mismatch for {msg}: got {mode:04o}, want {expected_posix_mode:04o}",
    )


def assert_bytes_and_mode_portable(
    test_case,
    path: Path,
    expected_bytes: bytes,
    expected_posix_mode: int,
    *,
    label: str = "",
) -> None:
    """Byte-exact content plus portable mode assertion."""
    msg = label or str(path)
    assert_mode_portable(test_case, path, expected_posix_mode, label=msg)
    test_case.assertEqual(path.read_bytes(), expected_bytes, f"content mismatch: {msg}")


def symlink_probe_status() -> Tuple[bool, Optional[str]]:
    """Return (ok, skip_reason)."""
    if can_create_symlinks():
        return True, None
    if is_windows():
        return (
            False,
            "Windows symlink privilege unavailable (Developer Mode / elevation required); "
            "symlink-creation tests excluded; physical-file + path_is_symlink detection "
            "equivalents run instead",
        )
    return False, "os.symlink unavailable on this platform"
