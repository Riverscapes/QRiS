"""Tests for Metric model features including availability calculation."""
import unittest
import os
import sys
# from unittest.mock import MagicMock

# Use standard test utility to start QGIS
try:
    from utilities import get_qgis_app
except ImportError:
    from .utilities import get_qgis_app

get_qgis_app()

# Add src
current_dir = os.path.dirname(os.path.abspath(__file__)) 
plugin_root = os.path.dirname(current_dir) 
parent_root = os.path.dirname(plugin_root) 

if parent_root not in sys.path:
    sys.path.insert(0, parent_root)

from qris_dev.src.model.metric import Metric

# Mocks
class MockLayer:
    def __init__(self, id, layer_id, name):
        self.id = id
        self.layer_id = layer_id
        self.name = name

class MockDBLayer: # Project layer representation
    def __init__(self, db_id, ref_id):
        self.id = db_id
        self.layer_id = ref_id

class MockEventLayer:
    def __init__(self, db_layer):
        self.layer = db_layer

class MockEvent:
    def __init__(self, id, event_layers):
        self.id = id
        self.event_layers = event_layers # List of MockEventLayer

class TestMetricAvailability(unittest.TestCase):

    def test_availability_case_insensitive_usage_grouping(self):
        """
        Verify that metric layers with same usage but different casing are grouped together,
        allowing 'OR' logic (at least one present) to succeed.
        """
        
        # Metric Definition: Two layers, Mixed Case "Input"
        # Since they are the same logical usage, they should be one group.
        # If one group, only ONE of them is required to satisfy the group (OR logic).
        metric_params = {
            'dce_layers': [
                {
                    'layer_id_ref': 'LAYER_A',
                    'usage': 'Input' 
                },
                {
                    'layer_id_ref': 'LAYER_B',
                    'usage': 'input'
                }
            ]
        }
        
        metric = Metric(1, "Test Metric", "tm", "proto", "desc", 1, "count", metric_params)
        
        # Scenario: Project only has LAYER_A
        # If treated as DIFFERENT groups (Input vs input), check fails (both required).
        # If treated as SAME group, check passes (only one required).
        
        # Mock Event with only Layer A
        layer_a_db = MockDBLayer(10, 'LAYER_A')
        
        # Event has Layer A
        event_layers = [MockEventLayer(layer_a_db)]
        dce = MockEvent(100, event_layers)
        
        # Protocols not strictly needed for loose check
        result = metric.can_calculate_for_dce(dce, protocols={})
        
        self.assertTrue(result, "Metric should be available if one of the 'input' layers is present, ignoring case.")

    def test_availability_strict_different_groups(self):
        """
        Verify that different usage types are still strictly required (AND logic between groups).
        """
        metric_params = {
            'dce_layers': [
                {
                    'layer_id_ref': 'LAYER_A',
                    'usage': 'numerator' 
                },
                {
                    'layer_id_ref': 'LAYER_B',
                    'usage': 'denominator'
                }
            ]
        }
        metric = Metric(2, "Ratio Metric", "tm", "proto", "desc", 1, "proportion", metric_params)

        # 1. Only Numerator -> Fail
        dce_num = MockEvent(101, [MockEventLayer(MockDBLayer(10, 'LAYER_A'))])
        self.assertFalse(metric.can_calculate_for_dce(dce_num, {}))

        # 2. Both -> Pass
        dce_both = MockEvent(102, [
            MockEventLayer(MockDBLayer(10, 'LAYER_A')),
            MockEventLayer(MockDBLayer(11, 'LAYER_B'))
        ])
        self.assertTrue(metric.can_calculate_for_dce(dce_both, {}))

    def test_availability_no_usage_grouping(self):
        """
        Verify that layers with NO usage specified are treated as a group where ONLY ONE is required (OR logic),
        rather than all being required (AND logic).
        """
        metric_params = {
            'dce_layers': [
                { 'layer_id_ref': 'LAYER_A' }, # No usage
                { 'layer_id_ref': 'LAYER_B' }  # No usage
            ]
        }
        metric = Metric(3, "Count Metric", "tm", "proto", "desc", 1, "count", metric_params)
        
        # Scenario: Only Layer A is present
        dce = MockEvent(103, [MockEventLayer(MockDBLayer(10, 'LAYER_A'))])
        
        self.assertTrue(metric.can_calculate_for_dce(dce, {}), "Metric should be available if at least one no-usage layer is present.")

if __name__ == '__main__':
    unittest.main()
