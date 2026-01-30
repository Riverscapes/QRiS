import unittest
from unittest.mock import MagicMock, patch
import json
import sys
import os

# Mock QGIS modules immediately
sys.modules['qgis'] = MagicMock()
sys.modules['qgis.core'] = MagicMock()
sys.modules['qgis.gui'] = MagicMock()
sys.modules['qgis.PyQt'] = MagicMock()

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from qris_dev.src.model.analysis import Analysis
from qris_dev.src.model.metric import Metric
from qris_dev.src.model.layer import Layer
from qris_dev.src.model.event import Event
from qris_dev.src.model.event_layer import EventLayer

class MockProject:
    def __init__(self):
        self.project_file = ':memory:'
        self.layers = {}
        self.events = {}
        self.analyses = {}

class MockSampleFrame:
    def __init__(self):
        self.fc_name = 'sample_frame_layer'

class TestMetricFeasibility(unittest.TestCase):

    def setUp(self):
        self.project = MockProject()
        self.sample_frame = MockSampleFrame()
        self.analysis = Analysis(1, "Test Analysis", "Desc", self.sample_frame, {})
        
        # Setup common Layers
        self.layer_dem = MagicMock(spec=Layer)
        self.layer_dem.id = 101
        self.layer_dem.layer_id = 'dem_layer'
        self.layer_dem.name = 'DEM'
        self.layer_dem.geom_type = 'Polygon'
        self.layer_dem.DCE_LAYER_NAMES = {'Polygon': 'dce_polygons', 'Point': 'dce_points'}

        self.layer_centerline = MagicMock(spec=Layer)
        self.layer_centerline.id = 102
        self.layer_centerline.layer_id = 'centerline_layer'
        self.layer_centerline.name = 'Centerline'
        self.layer_centerline.geom_type = 'Linestring'
        self.layer_centerline.DCE_LAYER_NAMES = {'Linestring': 'dce_lines'}
        
        self.project.layers = {
            'dem_layer': self.layer_dem,
            'centerline_layer': self.layer_centerline
        }

        # Setup Event
        self.event = MagicMock(spec=Event)
        self.event.id = 1
        self.event.event_layers = []
        
        self.project.events = {1: self.event}

    def create_metric(self, params):
        return Metric(1, "Test Metric", "test_metric", "PROTO", "Desc", 1, "func", params)

    def test_manual_only(self):
        """Test a metric with no automation parameters."""
        metric = self.create_metric(None)
        result = self.analysis.check_metric_feasibility(metric, self.project, self.event)
        self.assertEqual(result['status'], 'MANUAL_ONLY')

    def test_missing_input(self):
        """Test missing input in Analysis metadata."""
        params = {'inputs': [{'input_ref': 'dem_input'}]}
        metric = self.create_metric(params)
        
        # Analysis metadata empty
        self.analysis.metadata = {}
        
        result = self.analysis.check_metric_feasibility(metric, self.project, self.event)
        
        self.assertEqual(result['status'], 'NOT_FEASIBLE')
        self.assertIn("Missing Input: dem_input", result['reasons'])
        
        # Fix input
        self.analysis.metadata = {'dem_input': 123}
        result = self.analysis.check_metric_feasibility(metric, self.project, self.event)
        self.assertEqual(result['status'], 'FEASIBLE') # Assuming no layers required

    def test_missing_layer_config_in_project(self):
        """Test layer ref not existing in project."""
        params = {'dce_layers': [{'layer_id_ref': 'missing_layer'}]}
        metric = self.create_metric(params)
        
        result = self.analysis.check_metric_feasibility(metric, self.project, self.event)
        
        self.assertEqual(result['status'], 'NOT_FEASIBLE')
        # Updated to check for aggregated message format
        self.assertTrue(any("Missing Required Layer(s)" in r and "Layer Not Found in Project: missing_layer" in r for r in result['reasons']), 
                        f"Expected aggregated missing error, got {result['reasons']}")

    def test_missing_layer_in_dce(self):
        """Test layer exists in project but not in DCE."""
        params = {'dce_layers': [{'layer_id_ref': 'dem_layer'}]}
        metric = self.create_metric(params)
        
        # Event has no layers
        self.event.event_layers = []
        
        result = self.analysis.check_metric_feasibility(metric, self.project, self.event)
        
        self.assertEqual(result['status'], 'NOT_FEASIBLE')
        # Updated to check for aggregated message format
        self.assertTrue(any("Missing Required Layer(s)" in r and "Layer Not Included in DCE: dem_layer" in r for r in result['reasons']),
                        f"Expected aggregated missing error, got {result['reasons']}")

    @patch('sqlite3.connect')
    def test_feasible_empty_data(self, mock_connect):
        """Test layer in DCE, but has 0 features."""
        params = {'dce_layers': [{'layer_id_ref': 'dem_layer'}]}
        metric = self.create_metric(params)
        
        # Add layer to DCE
        el = MagicMock(spec=EventLayer)
        el.layer = self.layer_dem
        self.event.event_layers = [el]
        
        # Mock SQLite to return 0 count
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [0] # Count 0
        mock_connect.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        result = self.analysis.check_metric_feasibility(metric, self.project, self.event)
        
        # Verify check was attempted
        mock_cursor.execute.assert_called()
        
        self.assertEqual(result['status'], 'FEASIBLE_EMPTY', f"Status was {result['status']}, Reasons: {result['reasons']}")
        # Updated to check for generic empty message
        self.assertIn("All required layers are empty", result['reasons'])

    @patch('sqlite3.connect')
    def test_feasible_populated(self, mock_connect):
        """Test layer in DCE and populated."""
        params = {'dce_layers': [{'layer_id_ref': 'dem_layer'}]}
        metric = self.create_metric(params)
        
        # Add layer to DCE
        el = MagicMock(spec=EventLayer)
        el.layer = self.layer_dem
        self.event.event_layers = [el]
        
        # Mock SQLite to return > 0 count
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [5]
        mock_connect.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        result = self.analysis.check_metric_feasibility(metric, self.project, self.event)
        
        self.assertEqual(result['status'], 'FEASIBLE')
        self.assertEqual(result['reasons'], [])

    @patch('sqlite3.connect')
    def test_usage_groups_or_logic(self, mock_connect):
        """Test that if one layer in a usage group is present, it is feasible."""
        params = {'dce_layers': [
            {'layer_id_ref': 'dem_layer', 'usage': 'elevation'},
            {'layer_id_ref': 'centerline_layer', 'usage': 'elevation'}
        ]}
        metric = self.create_metric(params)
        
        # Scenario 1: ONLY dem_layer present
        el_dem = MagicMock(spec=EventLayer)
        el_dem.layer = self.layer_dem
        self.event.event_layers = [el_dem]
        
        # Mock SQLite (dem populated)
        mock_cursor = MagicMock()
        def side_effect(query, params):
            # If query is for dem_layer, return 5. If centerline, won't be called because not in DCE loop?
            # Actually, check_single_layer calls DB only if in DCE.
            return [5]
            
        mock_cursor.fetchone.return_value = [5]
        mock_connect.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        result = self.analysis.check_metric_feasibility(metric, self.project, self.event)
        
        self.assertEqual(result['status'], 'FEASIBLE')
        self.assertEqual(result['reasons'], [])

    @patch('sqlite3.connect')
    def test_usage_groups_fail(self, mock_connect):
        """Test that if NO layer in a usage group is present, it fails."""
        params = {'dce_layers': [
            {'layer_id_ref': 'dem_layer', 'usage': 'elevation'},
            {'layer_id_ref': 'centerline_layer', 'usage': 'elevation'}
        ]}
        metric = self.create_metric(params)
        
        self.event.event_layers = [] # None present
        
        result = self.analysis.check_metric_feasibility(metric, self.project, self.event)
        
        self.assertEqual(result['status'], 'NOT_FEASIBLE')
        self.assertTrue(any("Usage 'elevation' Missing" in r for r in result['reasons']))

    @patch('sqlite3.connect')
    def test_usage_groups_empty_data(self, mock_connect):
        """Test usage group valid (layer present) but empty data."""
        params = {'dce_layers': [
            {'layer_id_ref': 'dem_layer', 'usage': 'elevation'}
        ]}
        metric = self.create_metric(params)
        
        el_dem = MagicMock(spec=EventLayer)
        el_dem.layer = self.layer_dem
        self.event.event_layers = [el_dem]
        
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [0] # Empty
        mock_connect.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        result = self.analysis.check_metric_feasibility(metric, self.project, self.event)
        
        self.assertEqual(result['status'], 'FEASIBLE_EMPTY')
        self.assertIn("Usage 'elevation' Layers Empty", result['reasons'])

    @patch('sqlite3.connect')
    def test_individual_layers_any_logic(self, mock_connect):
        """
        Test new logic: If multiple individual layers are listed (no usage param),
        at least one must be present (OR logic), not all.
        """
        params = {'dce_layers': [
            {'layer_id_ref': 'dem_layer'},       # Individual Layre 1
            {'layer_id_ref': 'centerline_layer'} # Individual Layer 2
        ]}
        metric = self.create_metric(params)
        
        # Scenario 1: Both Missing -> NOT_FEASIBLE
        self.event.event_layers = []
        result = self.analysis.check_metric_feasibility(metric, self.project, self.event)
        self.assertEqual(result['status'], 'NOT_FEASIBLE', "Both missing should be NOT_FEASIBLE")
        self.assertIn("Missing Required Layer(s): Layer Not Included in DCE: centerline_layer, Layer Not Included in DCE: dem_layer", result['reasons'])
        
        # Scenario 2: One Present (DEM) -> FEASIBLE
        el_dem = MagicMock(spec=EventLayer)
        el_dem.layer = self.layer_dem
        self.event.event_layers = [el_dem]
        
        # Mock DB for populated DEM
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = [10] 
        mock_connect.return_value.__enter__.return_value.cursor.return_value = mock_cursor
        
        result_one = self.analysis.check_metric_feasibility(metric, self.project, self.event)
        self.assertEqual(result_one['status'], 'FEASIBLE', "One present should be FEASIBLE")
        self.assertEqual(result_one['reasons'], [], "Should have no failure reasons")
        
        # Scenario 3: One Present but Empty -> FEASIBLE_EMPTY
        mock_cursor.fetchone.return_value = [0] # Empty
        result_empty = self.analysis.check_metric_feasibility(metric, self.project, self.event)
        self.assertEqual(result_empty['status'], 'FEASIBLE_EMPTY', "One present but empty should be FEASIBLE_EMPTY")
        self.assertIn("All required layers are empty", result_empty['reasons'])

if __name__ == '__main__':
    unittest.main()
