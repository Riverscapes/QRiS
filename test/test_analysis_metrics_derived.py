"""Tests for derived metric calculations using metric dependencies."""

import os
import sys
import unittest

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

from qris_dev.src.gp.analysis_metrics import proportion, MetricInputMissingError


class TestDerivedMetrics(unittest.TestCase):

    def test_proportion_from_metric_dependencies(self):
        metric_params = {
            'metric_dependencies': [
                {
                    'metric_id_ref': 'base_numerator',
                    'protocol_machine_code_ref': 'USER_PROTOCOL',
                    'version': '1.0',
                    'usage': 'numerator',
                },
                {
                    'metric_id_ref': 'base_denominator',
                    'protocol_machine_code_ref': 'USER_PROTOCOL',
                    'version': '1.0',
                    'usage': 'denominator',
                },
            ]
        }
        analysis_params = {
            'metric_dependencies': {
                'numerator': 12.0,
                'denominator': 3.0,
            }
        }

        result = proportion('unused.gpkg', 1, 1, metric_params, analysis_params)
        self.assertEqual(result, 4.0)

    def test_proportion_from_metric_dependencies_div_by_zero(self):
        metric_params = {
            'metric_dependencies': [
                {'metric_id_ref': 'a', 'usage': 'numerator'},
                {'metric_id_ref': 'b', 'usage': 'denominator'},
            ]
        }
        analysis_params = {
            'metric_dependencies': {
                'numerator': 7.0,
                'denominator': 0.0,
            }
        }

        result = proportion('unused.gpkg', 1, 1, metric_params, analysis_params)
        self.assertEqual(result, 0.0)

    def test_proportion_from_metric_dependencies_missing_usage(self):
        metric_params = {
            'metric_dependencies': [
                {'metric_id_ref': 'a', 'usage': 'numerator'},
                {'metric_id_ref': 'b', 'usage': 'denominator'},
            ]
        }
        analysis_params = {
            'metric_dependencies': {
                'numerator': 10.0,
            }
        }

        with self.assertRaises(MetricInputMissingError):
            proportion('unused.gpkg', 1, 1, metric_params, analysis_params)


if __name__ == '__main__':
    unittest.main()
