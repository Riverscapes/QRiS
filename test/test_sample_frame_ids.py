# coding=utf-8
"""Tests for generic sample frame ID retrieval safeguards."""

import os
import sqlite3
import tempfile
import unittest


class TestSampleFrameIds(unittest.TestCase):

    def test_duplicate_labels_are_preserved_and_disambiguated(self):
        try:
            from src.model.sample_frame import get_sample_frame_ids
        except ImportError:
            from qris_dev.src.model.sample_frame import get_sample_frame_ids

        fd, db_path = tempfile.mkstemp(suffix='.gpkg')
        os.close(fd)

        try:
            with sqlite3.connect(db_path) as conn:
                cur = conn.cursor()
                cur.execute(
                    'CREATE TABLE sample_frame_features ('
                    'fid INTEGER PRIMARY KEY, '
                    'sample_frame_id INTEGER, '
                    'display_label TEXT, '
                    'flows_into INTEGER)'
                )
                cur.executemany(
                    'INSERT INTO sample_frame_features (fid, sample_frame_id, display_label, flows_into) '
                    'VALUES (?, ?, ?, ?)',
                    [
                        (101, 10, 'Untreated USFS', None),
                        (102, 10, 'Untreated USFS', None),
                        (103, 10, None, None),
                    ]
                )
                conn.commit()

            items = get_sample_frame_ids(db_path, 10)

            self.assertEqual(set(items.keys()), {101, 102, 103})
            self.assertEqual(items[101].name, 'Untreated USFS')
            self.assertEqual(items[102].name, 'Untreated USFS (Feature 102)')
            self.assertEqual(items[103].name, 'Feature 103')

        finally:
            if os.path.exists(db_path):
                try:
                    os.remove(db_path)
                except PermissionError:
                    # Transient file locks on Windows should not fail logic tests.
                    pass


if __name__ == '__main__':
    unittest.main()
