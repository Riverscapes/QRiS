"""Unit tests for the SQLite lock-file detection helper (GitHub #1160).

These tests are deliberately QGIS-free so they can run in a plain Python
environment: they only exercise ``src.QRiS.path_utilities.find_lock_files`` and
``LOCK_FILE_SUFFIXES`` (no Qt / QGIS imports).
"""

import os
import sys
import tempfile
import unittest

# Add the parent directory to sys.path so we can import the plugin as a package.
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

try:
    # Normal case: imported as a package module (e.g. "qris_dev.test.test_lock_files").
    from ..src.QRiS.path_utilities import LOCK_FILE_SUFFIXES, find_lock_files
except ImportError:
    # ``python3 -m unittest discover -s test`` imports test modules as *top-level*
    # modules (no package), so the relative import above cannot resolve.  Fall back
    # to the absolute import; the repo root is on sys.path under discovery.
    from src.QRiS.path_utilities import LOCK_FILE_SUFFIXES, find_lock_files


def _touch(path: str) -> None:
    """Create an empty file at ``path`` (its parent directory must already exist)."""
    with open(path, "w", encoding="utf-8"):
        pass


class TestFindLockFiles(unittest.TestCase):
    """Tests for :func:`find_lock_files` and the ``LOCK_FILE_SUFFIXES`` constant."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_dir = self._tmp.name
        self.gpkg = os.path.join(self.tmp_dir, "qris.gpkg")
        _touch(self.gpkg)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_suffixes_constant_unchanged(self) -> None:
        """``LOCK_FILE_SUFFIXES`` must stay ``("-wal", "-shm")`` (guards callers)."""
        self.assertEqual(LOCK_FILE_SUFFIXES, ("-wal", "-shm"))

    def test_no_sidecar_files_returns_empty_list(self) -> None:
        """A clean project (no ``-wal``/``-shm``) reports no lock files."""
        self.assertEqual(find_lock_files(self.gpkg), [])

    def test_only_wal_detected(self) -> None:
        """Only a lingering ``-wal`` file is reported, exactly once."""
        _touch(f"{self.gpkg}-wal")
        self.assertEqual(find_lock_files(self.gpkg), [f"{self.gpkg}-wal"])

    def test_only_shm_detected(self) -> None:
        """Only a lingering ``-shm`` file is reported, exactly once."""
        _touch(f"{self.gpkg}-shm")
        self.assertEqual(find_lock_files(self.gpkg), [f"{self.gpkg}-shm"])

    def test_both_detected_in_suffix_order(self) -> None:
        """Both sidecars are reported in ``LOCK_FILE_SUFFIXES`` order."""
        _touch(f"{self.gpkg}-wal")
        _touch(f"{self.gpkg}-shm")
        self.assertEqual(find_lock_files(self.gpkg), [f"{self.gpkg}-wal", f"{self.gpkg}-shm"])

    def test_unrelated_files_are_ignored(self) -> None:
        """Lookalike files anchored elsewhere must NOT be reported."""
        # Same stem but a different suffix (SQLite rollback journal, backup copy).
        _touch(f"{self.gpkg}-journal")
        _touch(f"{self.gpkg}.bak")
        # Similar-looking sidecar belonging to a *sibling* GeoPackage.
        _touch(os.path.join(self.tmp_dir, "other.gpkg-wal"))
        _touch(os.path.join(self.tmp_dir, "other.gpkg-shm"))
        # Prefix collision: another project whose name starts with "qris".
        _touch(os.path.join(self.tmp_dir, "qris.gpkg2-wal"))

        self.assertEqual(find_lock_files(self.gpkg), [])

    def test_path_with_spaces_and_non_ascii_directory(self) -> None:
        """Spaces / non-ASCII in the directory name do not break detection."""
        unicode_dir = os.path.join(self.tmp_dir, "pro ject späce 項目")
        os.makedirs(unicode_dir)
        gpkg = os.path.join(unicode_dir, "my project.gpkg")
        _touch(gpkg)
        _touch(f"{gpkg}-wal")

        self.assertEqual(find_lock_files(gpkg), [f"{gpkg}-wal"])

    def test_returned_paths_actually_exist(self) -> None:
        """Every returned path is a live, absolute path that ``os.path.exists`` confirms."""
        _touch(f"{self.gpkg}-wal")
        _touch(f"{self.gpkg}-shm")

        result = find_lock_files(self.gpkg)

        self.assertEqual(len(result), 2)
        for lock_path in result:
            self.assertTrue(os.path.isabs(lock_path), f"expected absolute path, got {lock_path!r}")
            self.assertTrue(os.path.exists(lock_path), f"expected existing path, got {lock_path!r}")

    def test_missing_geoapackage_still_detects_orphan_sidecar(self) -> None:
        """A sidecar left behind after the GeoPackage itself vanished is still detected."""
        orphan = os.path.join(self.tmp_dir, "gone.gpkg")
        _touch(f"{orphan}-wal")

        self.assertFalse(os.path.exists(orphan))
        self.assertEqual(find_lock_files(orphan), [f"{orphan}-wal"])


if __name__ == "__main__":
    unittest.main()
