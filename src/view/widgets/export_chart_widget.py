from qgis.PyQt import QtWidgets

from ..frm_export_chart import FrmChartExport
from ..frm_export_table import FrmTableExport
from .export_widget import BaseExportWidget


class ChartExportWidget(BaseExportWidget):
    def __init__(self, parent=None, base_name="chart_export", get_data_callback=None, get_figure_callback=None, project_path=None, export_type=None):
        super().__init__(parent, base_name=base_name, project_path=project_path, export_type=export_type)
        self.setToolTip("Export chart data or image")

        self.get_data_callback = get_data_callback
        self.get_figure_callback = get_figure_callback

    def setup_menu(self):
        super().setup_menu()
        self.add_export_action("Export Values...", self.export_values)
        self.add_export_action("Export Image...", self.export_image)

    def export_values(self):
        if not self.get_data_callback:
            return

        data = self.get_data_callback()
        if not data:
            QtWidgets.QMessageBox.information(self, "Export", "No data to export.")
            return

        # Create and show dialog
        dlg = FrmTableExport(self, data=data, base_name=self.base_name, project_path=self.project_path, export_type=self.export_type)
        dlg.exec_()

    def export_image(self):
        if not self.get_figure_callback:
            return

        fig = self.get_figure_callback()
        if not fig:
            return

        # Create and show dialog
        dlg = FrmChartExport(self, mode="image", figure=fig, base_name=self.base_name, project_path=self.project_path, export_type=self.export_type)
        dlg.exec_()
