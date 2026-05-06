from qgis.PyQt import QtWidgets

from .frm_export_base import FrmBaseExport
from .frm_export_table import FrmTableExport


class FrmChartExport(FrmBaseExport):
    """Dialog for exporting chart images or chart values."""

    def __init__(self, parent, mode="values", data=None, figure=None, base_name="export", project_path=None, export_type=None):
        super().__init__(parent, base_name=base_name, project_path=project_path, export_type=export_type)
        self.mode = mode
        self.data = data
        self.figure = figure

        title = "Export Data Table" if self.mode == "values" else "Export Chart Image"
        self.setWindowTitle(title)

        if self.mode == "values":
            self.setup_export_ui(["Comma Separated Values (CSV)", "Excel (*.xlsx)", "JSON (*.json)"])
        else:
            self.setup_export_ui(["PNG Image (*.png)", "JPEG Image (*.jpg)", "SVG Image (*.svg)", "PDF Document (*.pdf)"])

    def export_image(self, filename):
        if not self.figure:
            return False, "No chart figure available."
        try:
            self.figure.savefig(filename, dpi=300, bbox_inches="tight")
            return True, ""
        except Exception as err:
            return False, str(err)

    def export_values(self, filename):
        dlg = FrmTableExport(
            self,
            data=self.data,
            base_name=self.base_name,
            project_path=self.project_path,
            export_type=self.export_type,
        )
        return dlg.export_table(filename)

    def accept(self):
        out_file = self.leFile.text() if self.leFile is not None else ""
        if not out_file:
            QtWidgets.QMessageBox.warning(self, "Error", "Please select an output file.")
            return

        try:
            if self.mode == "values":
                success, msg = self.export_values(out_file)
            else:
                success, msg = self.export_image(out_file)
        except Exception as err:
            success, msg = False, str(err)

        if success:
            super().accept()
            self.show_export_success(out_file)
        else:
            QtWidgets.QMessageBox.critical(self, "Export Failed", f"Error: {msg}")
