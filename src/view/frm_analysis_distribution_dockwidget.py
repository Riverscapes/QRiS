from qgis.PyQt import QtWidgets, QtCore

from ..model.project import Project
from .widgets.analysis_distribution_widget import DistributionAnalysisWidget

class FrmDistributionAnalysisDockWidget(QtWidgets.QDockWidget):
    """
    Dockable version of the Disbrituion Analysis Tool.
    Refactored to use shared DistributionAnalysisWidget.
    """

    def __init__(self, iface, qris_project: Project, map_manager):
        # Parent to MainWindow so it docks properly
        super().__init__("Distribution Analysis", iface.mainWindow())
        self.setObjectName("DistributionAnalysisDock")
        self.iface = iface
        
        # Dock Specific Settings
        self.setAllowedAreas(QtCore.Qt.BottomDockWidgetArea | QtCore.Qt.TopDockWidgetArea)
        
        # Instantiate common widget
        self.widget = DistributionAnalysisWidget(iface, qris_project, map_manager, self)
        self.setWidget(self.widget)
