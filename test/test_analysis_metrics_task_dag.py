"""Tests for DAG planning in AnalysisMetricsTask."""

import os
import sys
import unittest
from types import SimpleNamespace

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


def build_metric(mid, machine_name, protocol='USER_PROTOCOL', version='1.0', dependencies=None):
    return SimpleNamespace(
        id=mid,
        machine_name=machine_name,
        protocol_machine_code=protocol,
        version=version,
        metric_params={'metric_dependencies': dependencies} if dependencies else {},
    )


def build_metric_value(metric, value):
    return SimpleNamespace(
        metric=metric,
        current_value=lambda display_unit=None: value,
    )


def build_analysis_metric(metric):
    return SimpleNamespace(metric=metric)


class TestAnalysisMetricsTaskDag(unittest.TestCase):

    def test_plans_dependencies_before_requested_metric(self):
        m1 = build_metric(1, 'base_length')
        m2 = build_metric(2, 'derived_ratio', dependencies=[{'metric_id_ref': 'base_length'}])

        analysis_metrics = {
            1: build_analysis_metric(m1),
            2: build_analysis_metric(m2),
        }

        ordered = AnalysisMetricsTask.plan_metric_execution(analysis_metrics, [2])
        ordered_ids = [am.metric.id for am in ordered]

        self.assertEqual(ordered_ids, [1, 2])

    def test_raises_for_missing_dependency(self):
        m2 = build_metric(2, 'derived_ratio', dependencies=[{'metric_id_ref': 'missing_metric'}])

        analysis_metrics = {
            2: build_analysis_metric(m2),
        }

        with self.assertRaises(ValueError) as context:
            AnalysisMetricsTask.plan_metric_execution(analysis_metrics, [2])

        self.assertIn('not available', str(context.exception))

    def test_raises_for_cycle(self):
        m1 = build_metric(1, 'metric_a', dependencies=[{'metric_id_ref': 'metric_b'}])
        m2 = build_metric(2, 'metric_b', dependencies=[{'metric_id_ref': 'metric_a'}])

        analysis_metrics = {
            1: build_analysis_metric(m1),
            2: build_analysis_metric(m2),
        }

        with self.assertRaises(ValueError) as context:
            AnalysisMetricsTask.plan_metric_execution(analysis_metrics, [1])

        self.assertIn('cycle', str(context.exception).lower())

    def test_resolves_runtime_dependency_values(self):
        base = build_metric(1, 'base_length', protocol='USER_PROTOCOL', version='1.0')
        derived = build_metric(
            2,
            'derived_ratio',
            dependencies=[{
                'metric_id_ref': 'base_length',
                'protocol_machine_code_ref': 'USER_PROTOCOL',
                'version': '1.0',
                'usage': 'denominator',
            }],
        )

        metric_values = {
            1: build_metric_value(base, 42.0),
        }

        resolved = AnalysisMetricsTask._resolve_runtime_dependency_values(derived, metric_values)
        self.assertEqual(resolved['denominator'], 42.0)
        self.assertEqual(resolved['USER_PROTOCOL::base_length::1.0'], 42.0)
        self.assertEqual(resolved['USER_PROTOCOL::base_length::'], 42.0)

    def test_runtime_dependency_missing_raises(self):
        derived = build_metric(
            2,
            'derived_ratio',
            dependencies=[{'metric_id_ref': 'base_length'}],
        )

        with self.assertRaises(Exception) as context:
            AnalysisMetricsTask._resolve_runtime_dependency_values(derived, {})

        self.assertIn('Missing dependency value', str(context.exception))

    def test_resolves_runtime_dependency_values_with_numeric_version_format_mismatch(self):
        base = build_metric(1, 'base_length', protocol='RIVERSCAPE_SYSTEM_PROTOCOL', version=1)
        derived = build_metric(
            2,
            'derived_ratio',
            protocol='USER_PROTOCOL',
            dependencies=[{
                'metric_id_ref': 'base_length',
                'protocol_machine_code_ref': 'RIVERSCAPE_SYSTEM_PROTOCOL',
                'version': '1.0',
                'usage': 'denominator',
            }],
        )

        metric_values = {
            1: build_metric_value(base, 42.0),
        }

        resolved = AnalysisMetricsTask._resolve_runtime_dependency_values(derived, metric_values)
        self.assertEqual(resolved['denominator'], 42.0)

    def test_plan_metric_execution_with_numeric_version_format_mismatch(self):
        base = build_metric(1, 'base_length', protocol='RIVERSCAPE_SYSTEM_PROTOCOL', version=1)
        derived = build_metric(
            2,
            'derived_ratio',
            protocol='USER_PROTOCOL',
            dependencies=[{
                'metric_id_ref': 'base_length',
                'protocol_machine_code_ref': 'RIVERSCAPE_SYSTEM_PROTOCOL',
                'version': '1.0',
                'usage': 'denominator',
            }],
        )

        analysis_metrics = {
            1: build_analysis_metric(base),
            2: build_analysis_metric(derived),
        }

        ordered = AnalysisMetricsTask.plan_metric_execution(analysis_metrics, [2])
        ordered_ids = [am.metric.id for am in ordered]
        self.assertEqual(ordered_ids, [1, 2])


if __name__ == '__main__':
    unittest.main()
