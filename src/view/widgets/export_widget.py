from qgis.PyQt import QtWidgets

class BaseExportWidget(QtWidgets.QPushButton):
    """Base export widget for export actions."""
    def __init__(self, parent=None, base_name="export", project_path=None, export_type=None):
        super().__init__(parent)
        self.base_name = base_name
        self.project_path = project_path
        self.export_type = export_type
        self.setText("Export")
        self.setToolTip("Export data")
        self.setup_menu()

    def setup_menu(self):
        self.menu = QtWidgets.QMenu(self)
        self.setMenu(self.menu)

    def add_export_action(self, label, callback):
        action = self.menu.addAction(label)
        action.triggered.connect(callback)
