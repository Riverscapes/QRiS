import unittest
from unittest.mock import MagicMock
import sys
import os

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from qris_dev.src.view.widgets.analysis_table import MetricStatusWidget_Labels
from qris_dev.src.model.metric import Metric
from qris_dev.src.model.metric_value import MetricValue
from qris_dev.test.utilities import get_qgis_app
from qgis.PyQt import QtWidgets

# Ensure QGIS is running
QGIS_APP = get_qgis_app()
if QGIS_APP[0] is None:
    from PyQt5.QtWidgets import QApplication
    if QApplication.instance() is None:
        app = QApplication(sys.argv)

class TestMetricThresholds(unittest.TestCase):
    
    def create_metric(self, tolerance):
        m = MagicMock(spec=Metric)
        m.tolerance = tolerance
        return m
        
    def create_value(self, manual, automated):
        mv = MagicMock(spec=MetricValue)
        mv.manual_value = manual
        mv.automated_value = automated
        mv.metadata = {}
        return mv

    def test_threshold_exceeded(self):
        widget = MetricStatusWidget_Labels()
        widget.btn_warning = MagicMock()
        
        metric = self.create_metric(tolerance=5.0)
        value = self.create_value(manual=20.0, automated=10.0) # Diff = 10 > 5
        
        # is_manual=True, can_calc=True, feasibility=FEASIBLE (no errors)
        feasibility = {'status': 'FEASIBLE', 'reasons': []}
        
        widget.update_state(True, True, feasibility, metric, value)
        
        # Should have icon set (Blue Information)
        widget.btn_warning.setIcon.assert_called()
        widget.btn_warning.setVisible.assert_called_with(True)
        widget.btn_warning.setToolTip.assert_called()
        
        args, _ = widget.btn_warning.setToolTip.call_args
        self.assertIn("differs from automated value by more than tolerance", args[0])

    def test_threshold_within_limits(self):
        widget = MetricStatusWidget_Labels()
        widget.btn_warning = MagicMock()
        
        metric = self.create_metric(tolerance=5.0)
        value = self.create_value(manual=12.0, automated=10.0) # Diff = 2 < 5
        
        feasibility = {'status': 'FEASIBLE', 'reasons': []}
        
        widget.update_state(True, True, feasibility, metric, value)
        
        # Should hide button
        widget.btn_warning.setVisible.assert_called_with(False)

    def test_not_manual_mode(self):
        """If automated is selected, do not warn about manual diff."""
        widget = MetricStatusWidget_Labels()
        widget.btn_warning = MagicMock()
        
        metric = self.create_metric(tolerance=5.0)
        value = self.create_value(manual=20.0, automated=10.0)
        
        feasibility = {'status': 'FEASIBLE', 'reasons': []}
        
        # is_manual = False
        widget.update_state(False, True, feasibility, metric, value)
        
        widget.btn_warning.setVisible.assert_called_with(False)

if __name__ == '__main__':
    unittest.main()
