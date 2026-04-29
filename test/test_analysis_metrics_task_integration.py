"""Integration-style test for AnalysisMetricsTask base + derived persistence."""

import os
import sqlite3
import shutil
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

try:
    from utilities import get_qgis_app
except ImportError:
    from .utilities import get_qgis_app

get_qgis_app()

current_dir = os.path.dirname(os.path.abspath(__file__))
plugin_root = os.path.dirname(current_dir)
parent_root = os.path.dirname(plugin_root)

if parent_root not in sys.path:
    sys.path.insert(0, parent_root)

from qris_dev.src.gp.analysis_metrics_task import AnalysisMetricsTask
from qris_dev.src.QRiS.protocol_parser import load_protocool_from_xml
from qris_dev.src.model.analysis import Analysis
from qris_dev.src.model.analysis_metric import AnalysisMetric
from qris_dev.src.model.metric import Metric


class MockSampleFrame:
    def __init__(self):
        self.fc_name = 'sample_frame_features'


class TestAnalysisMetricsTaskIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'task_integration.sqlite')

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE metric_values (
                    analysis_id INTEGER,
                    event_id INTEGER,
                    sample_frame_feature_id INTEGER,
                    metric_id INTEGER,
                    manual_value NUMERIC,
                    automated_value NUMERIC,
                    is_manual INT NOT NULL DEFAULT 1,
                    uncertainty NUMERIC,
                    unit_id INTEGER,
                    metadata TEXT,
                    description TEXT,
                    created_on DATETIME DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT pk_metric_values PRIMARY KEY (analysis_id, event_id, sample_frame_feature_id, metric_id)
                )
                """
            )

        self.base_metric = Metric(
            1,
            'Base Length',
            'base_length',
            'USER_PROTOCOL',
            'Base metric',
            1,
            'count',
            {'inputs': []},
            version='1.0',
        )
        self.derived_metric = Metric(
            2,
            'Derived Ratio',
            'derived_ratio',
            'USER_PROTOCOL',
            'Derived metric',
            1,
            'proportion',
            {
                'metric_dependencies': [
                    {
                        'metric_id_ref': 'base_length',
                        'protocol_machine_code_ref': 'USER_PROTOCOL',
                        'version': '1.0',
                        'usage': 'numerator',
                    }
                ]
            },
            version='1.0',
        )

        sample_frame = MockSampleFrame()
        self.analysis = Analysis(10, 'Integration Analysis', 'Desc', sample_frame, metadata={})
        self.analysis.analysis_metrics = {
            1: AnalysisMetric(self.base_metric, 1),
            2: AnalysisMetric(self.derived_metric, 1),
        }

        event = SimpleNamespace(id=100, name='Integration Event', event_layers=[])

        self.qris_project = SimpleNamespace(
            project_file=self.db_path,
            events={100: event},
            metrics={1: self.base_metric, 2: self.derived_metric},
            analyses={10: self.analysis},
            profiles={},
            rasters={},
            valley_bottoms={},
        )

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_task_persists_base_and_derived_metric_values(self):
        task = AnalysisMetricsTask(
            self.qris_project,
            self.analysis,
            sample_frame_ids=[1],
            event_ids=[100],
            metric_ids=[2],
            overwrite_existing=True,
            force_active=True,
        )

        def fake_count(project_file, sample_frame_feature_id, event_id, metric_params, analysis_params):
            return 10.0

        def fake_proportion(project_file, sample_frame_feature_id, event_id, metric_params, analysis_params):
            deps = analysis_params.get('metric_dependencies', {})
            return deps.get('numerator', 0.0) / 2.0

        with patch('qris_dev.src.gp.analysis_metrics.count', side_effect=fake_count), patch(
            'qris_dev.src.gp.analysis_metrics.proportion', side_effect=fake_proportion
        ):
            success = task.run()

        self.assertTrue(success)

        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT metric_id, automated_value
                FROM metric_values
                WHERE analysis_id = ? AND event_id = ? AND sample_frame_feature_id = ?
                ORDER BY metric_id
                """,
                (10, 100, 1),
            ).fetchall()

        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0][0], 1)
        self.assertAlmostEqual(rows[0][1], 10.0, places=6)
        self.assertEqual(rows[1][0], 2)
        self.assertAlmostEqual(rows[1][1], 5.0, places=6)

    def test_task_with_parsed_system_protocol_metrics(self):
        protocol_path = os.path.join(
            plugin_root,
            'resources',
            'protocols',
            'riverscape_system_protocol.xml',
        )
        protocol = load_protocool_from_xml(protocol_path)
        self.assertIsNotNone(protocol)

        defs_by_id = {m.id: m for m in protocol.metrics}
        length_def = defs_by_id['riverscape_length']
        area_def = defs_by_id['riverscape_area']
        derived_def = defs_by_id['riverscape_integrated_width']

        length_metric = Metric(
            11,
            length_def.label,
            length_def.id,
            protocol.machine_code,
            length_def.description,
            1,
            length_def.calculation_machine_code,
            length_def.parameters,
            version=length_def.version,
        )
        area_metric = Metric(
            12,
            area_def.label,
            area_def.id,
            protocol.machine_code,
            area_def.description,
            1,
            area_def.calculation_machine_code,
            area_def.parameters,
            version=area_def.version,
        )
        derived_metric = Metric(
            13,
            derived_def.label,
            derived_def.id,
            protocol.machine_code,
            derived_def.description,
            1,
            derived_def.calculation_machine_code,
            derived_def.parameters,
            version=derived_def.version,
        )

        sample_frame = MockSampleFrame()
        analysis = Analysis(
            20,
            'Parsed Protocol Analysis',
            'Desc',
            sample_frame,
            metadata={'centerline': 101, 'valley_bottom': 202},
        )
        analysis.analysis_metrics = {
            11: AnalysisMetric(length_metric, 1),
            12: AnalysisMetric(area_metric, 1),
            13: AnalysisMetric(derived_metric, 1),
        }

        event = SimpleNamespace(id=101, name='Parsed Protocol Event', event_layers=[])
        qris_project = SimpleNamespace(
            project_file=self.db_path,
            events={101: event},
            metrics={11: length_metric, 12: area_metric, 13: derived_metric},
            analyses={20: analysis},
            profiles={101: SimpleNamespace(id=101, fc_name='profile_centerlines', fc_id_column_name='profile_id')},
            rasters={},
            valley_bottoms={202: SimpleNamespace(id=202, fc_name='sample_frame_features', fc_id_column_name='sample_frame_id')},
        )

        task = AnalysisMetricsTask(
            qris_project,
            analysis,
            sample_frame_ids=[2],
            event_ids=[101],
            metric_ids=[13],
            overwrite_existing=True,
            force_active=True,
        )

        def fake_length(project_file, sample_frame_feature_id, event_id, metric_params, analysis_params):
            return 100.0

        def fake_area(project_file, sample_frame_feature_id, event_id, metric_params, analysis_params):
            return 20.0

        def fake_proportion(project_file, sample_frame_feature_id, event_id, metric_params, analysis_params):
            deps = analysis_params.get('metric_dependencies', {})
            return deps['numerator'] / deps['denominator']

        with patch('qris_dev.src.gp.analysis_metrics.length', side_effect=fake_length), patch(
            'qris_dev.src.gp.analysis_metrics.area', side_effect=fake_area
        ), patch('qris_dev.src.gp.analysis_metrics.proportion', side_effect=fake_proportion):
            success = task.run()

        self.assertTrue(success)

        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT metric_id, automated_value
                FROM metric_values
                WHERE analysis_id = ? AND event_id = ? AND sample_frame_feature_id = ?
                ORDER BY metric_id
                """,
                (20, 101, 2),
            ).fetchall()

        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[0][0], 11)
        self.assertAlmostEqual(rows[0][1], 100.0, places=6)
        self.assertEqual(rows[1][0], 12)
        self.assertAlmostEqual(rows[1][1], 20.0, places=6)
        self.assertEqual(rows[2][0], 13)
        self.assertAlmostEqual(rows[2][1], 0.2, places=6)

    def test_derived_metric_uses_manual_base_values_without_recalculating(self):
        """Calculating a derived metric should use manual values on base metrics
        and must NOT recalculate (overwrite) those base metrics."""

        # Pre-populate the DB with manual values for both base metrics.
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany(
                """INSERT INTO metric_values
                   (analysis_id, event_id, sample_frame_feature_id, metric_id,
                    manual_value, automated_value, is_manual, uncertainty,
                    unit_id, metadata, description)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    (10, 100, 1, 1, 42.0, None, 1, None, None, None, None),  # base: manual=42, no auto
                ],
            )

        call_log = []

        def fake_count(*args, **kwargs):
            call_log.append('count')
            return 99.0  # should never be called

        def fake_proportion(project_file, sample_frame_feature_id, event_id, metric_params, analysis_params):
            call_log.append('proportion')
            deps = analysis_params.get('metric_dependencies', {})
            return deps.get('numerator', 0.0) / 2.0

        task = AnalysisMetricsTask(
            self.qris_project,
            self.analysis,
            sample_frame_ids=[1],
            event_ids=[100],
            metric_ids=[2],         # only the derived metric is requested
            overwrite_existing=True,
            force_active=True,
        )

        with patch('qris_dev.src.gp.analysis_metrics.count', side_effect=fake_count), \
             patch('qris_dev.src.gp.analysis_metrics.proportion', side_effect=fake_proportion):
            success = task.run()

        self.assertTrue(success)

        # count must never have been called — base metric was manual, not recalculated
        self.assertNotIn('count', call_log, 'Base metric was recalculated despite having a manual value')
        self.assertIn('proportion', call_log)

        with sqlite3.connect(self.db_path) as conn:
            rows = {
                row[0]: row
                for row in conn.execute(
                    """SELECT metric_id, manual_value, automated_value, is_manual
                       FROM metric_values
                       WHERE analysis_id = ? AND event_id = ? AND sample_frame_feature_id = ?""",
                    (10, 100, 1),
                ).fetchall()
            }

        # Base metric manual value must be untouched
        self.assertIn(1, rows)
        self.assertAlmostEqual(rows[1][1], 42.0, places=6)   # manual_value preserved
        self.assertIsNone(rows[1][2])                          # automated_value still None
        self.assertEqual(rows[1][3], 1)                        # is_manual still True

        # Derived metric should have been calculated using the manual base value (42 / 2 = 21)
        self.assertIn(2, rows)
        self.assertAlmostEqual(rows[2][2], 21.0, places=6)

    def test_derived_metric_uses_manual_value_when_both_manual_and_auto_exist(self):
        """When a base metric has both automated and manual values with is_manual=True,
        the derived metric must use the manual value."""

        with sqlite3.connect(self.db_path) as conn:
            conn.executemany(
                """INSERT INTO metric_values
                   (analysis_id, event_id, sample_frame_feature_id, metric_id,
                    manual_value, automated_value, is_manual, uncertainty,
                    unit_id, metadata, description)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    (10, 100, 1, 1, 50.0, 10.0, 1, None, None, None, None),  # manual=50 wins over auto=10
                ],
            )

        captured_deps = {}

        def fake_proportion(project_file, sample_frame_feature_id, event_id, metric_params, analysis_params):
            captured_deps.update(analysis_params.get('metric_dependencies', {}))
            deps = analysis_params.get('metric_dependencies', {})
            return deps.get('numerator', 0.0) / 2.0

        task = AnalysisMetricsTask(
            self.qris_project,
            self.analysis,
            sample_frame_ids=[1],
            event_ids=[100],
            metric_ids=[2],
            overwrite_existing=True,
            force_active=True,
        )

        with patch('qris_dev.src.gp.analysis_metrics.proportion', side_effect=fake_proportion):
            success = task.run()

        self.assertTrue(success)

        # The dependency resolver must have seen manual_value=50, not automated_value=10
        self.assertAlmostEqual(captured_deps.get('numerator', 0.0), 50.0, places=6)

        with sqlite3.connect(self.db_path) as conn:
            derived_row = conn.execute(
                """SELECT automated_value FROM metric_values
                   WHERE analysis_id = ? AND event_id = ? AND sample_frame_feature_id = ? AND metric_id = ?""",
                (10, 100, 1, 2),
            ).fetchone()

        self.assertIsNotNone(derived_row)
        self.assertAlmostEqual(derived_row[0], 25.0, places=6)  # 50 / 2


if __name__ == '__main__':
    unittest.main()
