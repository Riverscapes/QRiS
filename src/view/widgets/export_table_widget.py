from qgis.PyQt import QtWidgets

from ..frm_export_table import FrmTableExport
from .export_widget import BaseExportWidget


class TableExportWidget(BaseExportWidget):
    """Drop-in Export button that opens FrmTableExport for provided data."""

    def __init__(self, parent=None, base_name="table_export", get_data_callback=None, project_path=None, export_type=None):
        """Store callbacks/options and create the button menu."""
        super().__init__(parent, base_name=base_name, project_path=project_path, export_type=export_type)

        self.get_data_callback = get_data_callback
        self.setToolTip("Export table values")

    def setup_menu(self):
        """Configure the button drop-down actions."""
        super().setup_menu()
        self.add_export_action("Export Table...", self.export_table)

    def export_table(self):
        """Fetch rows from callback and launch the table export dialog."""
        if not self.get_data_callback:
            return

        data = self.get_data_callback()
        if not data:
            QtWidgets.QMessageBox.information(self, "Export", "No data to export.")
            return

        dlg = FrmTableExport(
            self,
            data=data,
            base_name=self.base_name,
            project_path=self.project_path,
            export_type=self.export_type,
        )
        dlg.exec_()
