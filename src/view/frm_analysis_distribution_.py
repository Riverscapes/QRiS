
from qgis.PyQt import QtWidgets, QtCore

from ..model.project import Project
from .utilities import add_standard_form_buttons
from .widgets.analysis_distribution_widget import DistributionAnalysisWidget

try:
    from qgis.utils import iface
except ImportError:
    iface = None

class FrmDistributionAnalysis(QtWidgets.QDialog):

    def __init__(self, parent, qris_project: Project, map_manager):
        super().__init__(parent)
        self.setWindowTitle("Distribution Analysis")
        self.resize(800, 500)
        
        self.layout = QtWidgets.QVBoxLayout(self)
        
        # Instantiate common widget
        self.widget = DistributionAnalysisWidget(iface, qris_project, map_manager, self, orientation=QtCore.Qt.Vertical)
        
        self.layout.addWidget(self.widget)
        
        # Add buttons
        self.layout.addLayout(add_standard_form_buttons(self, 'distribution-analysis'))
        
    def showEvent(self, event):
        super().showEvent(event)
        self.activateWindow()
