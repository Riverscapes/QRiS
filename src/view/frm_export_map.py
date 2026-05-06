from qgis.PyQt import QtWidgets

from .frm_export_base import FrmBaseExport


class FrmMapExport(FrmBaseExport):
    """Dialog for selecting map export output path and format."""

    def __init__(self, parent, base_name="map_export", project_path=None, export_type=None):
        super().__init__(parent, base_name=base_name, project_path=project_path, export_type=export_type)
        self.setWindowTitle("Export Map Image")
        self.setup_export_ui(["PNG Image (*.png)", "JPEG Image (*.jpg)"])

    def accept(self):
        out_file = self.leFile.text() if self.leFile is not None else ""
        if not out_file:
            QtWidgets.QMessageBox.warning(self, "Export Map", "Please select an output file.")
            return

        super().accept()
