from qgis.PyQt import QtCore, QtWidgets

from ..frm_export_map import FrmMapExport
from .export_widget import BaseExportWidget


class MapExportWidget(BaseExportWidget):
    """Export widget for exporting map images (e.g., QGIS map canvas)."""

    exportPathSelected = QtCore.pyqtSignal(str, str, object)

    def __init__(self, parent=None, base_name="map_export", get_map_image_callback=None, project_path=None, export_type=None):
        super().__init__(parent, base_name, project_path, export_type)
        self.get_map_image_callback = get_map_image_callback
        self.setToolTip("Export map image")

    def setup_menu(self):
        super().setup_menu()
        self.add_export_action("Export Map Image...", self.export_map_image)

    def export_map_image(self):
        dlg = FrmMapExport(
            self,
            base_name=self.base_name,
            project_path=self.project_path,
            export_type=self.export_type,
        )
        if dlg.exec_() != QtWidgets.QDialog.Accepted:
            return None

        file_path = dlg.leFile.text() if dlg.leFile is not None else ""
        selected_format = dlg.cmbFormat.currentText() if dlg.cmbFormat is not None else ""
        render_params = dlg.render_params
        if not file_path:
            return None

        self.exportPathSelected.emit(file_path, selected_format, render_params)

        # If a callback exists, perform immediate export. Otherwise caller can use dialog path in async flow.
        if not self.get_map_image_callback:
            return file_path

        img = self.get_map_image_callback()
        if img is None:
            QtWidgets.QMessageBox.warning(self, "Export Map", "No map image available.")
            return None

        success = img.save(file_path)
        if not success:
            QtWidgets.QMessageBox.critical(self, "Export Map", f"Failed to save map image to:\n{file_path}")
            return None

        QtWidgets.QMessageBox.information(self, "Export Map", f"Map image saved to {file_path}")
        return file_path
