import unittest
import sys
import os
import logging

# Add src to path
# We need to add the folder CONTAINING qris_dev to the path so we can import qris_dev.src...
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from qris_dev.src.view.frm_metric_value import FrmMetricValue
from qris_dev.src.model.metric import Metric
from qris_dev.src.model.metric_value import MetricValue
from qris_dev.test.utilities import get_qgis_app
from qgis.core import QgsUnitTypes

# Ensure QGIS is running
QGIS_APP = get_qgis_app()

if QGIS_APP[0] is None:
    print("Warning: QGIS App not initialized via utilities. Trying bare QApplication.")
    from PyQt5.QtWidgets import QApplication
    if QApplication.instance() is None:
        app = QApplication(sys.argv)
else:
    app = QGIS_APP[0]

class MockAnalysis:
    def __init__(self):
        self.id = 1
        # Use QgsUnitTypes to get the correct string key
        feet_str = QgsUnitTypes.toString(QgsUnitTypes.DistanceFeet)
        self.units = {'distance': feet_str, 'area': 'Acres'} 
        print(f"MockAnalysis using distance unit: '{feet_str}'")
        self.metadata = {}

class MockProject:
    def __init__(self):
        self.project_file = ':memory:'
        self.rasters = {}
        self.profiles = {}
        self.valley_bottoms = {}
        self.events = {}
        self.analyses = {}

class MockEvent:
    def __init__(self):
        self.id = 1
        self.event_layers = []

class TestMetricConstraints(unittest.TestCase):
    
    def test_constraints_propagation(self):
        print("Testing Metric Value Form Constraints...")
        
        # 1. Setup Metric with Constraints (SI: Meters)
        # Min: 10m, Max: 200m, Precision: 2
        metric_metadata = {
            'minimum_value': 10.0,
            'maximum_value': 200.0,
            'precision': 2
        }
        
        # We manually constructed the object to simulate a loaded metric
        # Metric constructor logic:
        # self.unit_type = analysis_metric_unit_type.get(self.metric_function, None)
        # "length" -> "distance" -> base "meters"
        
        metric = Metric(
            id=1,
            name="Test Metric",
            machine_name="test_metric",
            protocol_machine_code="TEST",
            description="A test metric",
            default_level_id=1,
            metric_function="length", # Should map to distance/meters
            metric_params={},
            default_unit_id=None,
            definition_url="http://test",
            metadata=metric_metadata
        )
        
        # Verify assumptions about metric setup
        self.assertEqual(metric.min_value, 10.0)
        self.assertEqual(metric.max_value, 200.0)
        self.assertEqual(metric.base_unit, 'meters') # From default_units mapping in metric.py

        # 2. Metric Value
        metric_value = MetricValue(
            metric=metric,
            manual_value=None, 
            automated_value=None,
            is_manual=True,
            uncertainty=None,
            description="",
            unit_id=None,
            metadata={}
        )

        # 3. Mocks
        analysis = MockAnalysis()
        project = MockProject()
        event = MockEvent()
        
        project.events[event.id] = event
        project.analyses[analysis.id] = analysis

        # 4. Create Form
        # Using a parent widget prevents some focus issues in tests
        from PyQt5.QtWidgets import QWidget
        parent = QWidget()
        form = FrmMetricValue(parent, project, analysis, event, 1, metric_value)

        # Mock conversion to isolate form logic from QGIS environment issues
        def mock_conversion(value, base, target, invert=False):
            if not value: return value
            # Simple mock: 1m = 3.28ft
            # We assume inputs are correct for 'meters' and 'feet' keys
            factor = 1.0
            if 'feet' in str(target).lower() and 'meters' in str(base).lower():
                factor = 3.28084
            elif 'meters' in str(target).lower() and 'feet' in str(base).lower():
                # converting TO meters FROM feet
                factor = 1.0/3.28084
            
            if invert:
                return value / factor
            return value * factor
        
        form._do_conversion = mock_conversion
        
        # Re-run update_constraints to apply mock
        form.update_constraints()

        # 5. Assertions - Initial Load (Feet)
        
        feet_str = QgsUnitTypes.toString(QgsUnitTypes.DistanceFeet)
        meter_str = QgsUnitTypes.toString(QgsUnitTypes.DistanceMeters)

        # Check current unit selection
        current_data = form.cboUnits.currentData()
        self.assertEqual(current_data, feet_str)

        # Precision set?
        self.assertEqual(form.valManual.decimals(), 2)

        # Constraints converted?
        # 10m to Feet
        # 1 meter = 3.28084 feet
        expected_min = 10.0 * 3.28084
        expected_max = 200.0 * 3.28084
        
        min_val = form.valManual.minimum()
        max_val = form.valManual.maximum()
        
        print(f"Feet - Expected Min: {expected_min}, Actual: {min_val}")
        print(f"Feet - Expected Max: {expected_max}, Actual: {max_val}")

        # Allow small float diff (delta=0.01)
        self.assertAlmostEqual(min_val, expected_min, delta=0.01)
        self.assertAlmostEqual(max_val, expected_max, delta=0.01)

        # 6. Change Unit to Meters
        # Find index for Meters
        idx = form.cboUnits.findData(meter_str) 
        
        self.assertNotEqual(idx, -1, f"Could not find {meter_str} in combobox")
        
        form.cboUnits.setCurrentIndex(idx)
        
        # Check new unit
        self.assertEqual(form.current_unit, meter_str)

        # Check constraints (Should be exactly 10 and 100)
        min_val_m = form.valManual.minimum()
        max_val_m = form.valManual.maximum()
        
        print(f"Meters - Expected Min: 10.0, Actual: {min_val_m}")
        print(f"Meters - Expected Max: 200.0, Actual: {max_val_m}")
        
        self.assertAlmostEqual(min_val_m, 10.0, places=4)
        self.assertAlmostEqual(max_val_m, 200.0, places=4)

if __name__ == '__main__':
    unittest.main()
