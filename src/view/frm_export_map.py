from qgis.PyQt import QtWidgets

from .frm_export_base import FrmBaseExport


class FrmMapExport(FrmBaseExport):
    """Dialog for selecting map export output path and format."""

    def __init__(self, parent, base_name="map_export", project_path=None, export_type=None):
        super().__init__(parent, base_name=base_name, project_path=project_path, export_type=export_type)
        self.setWindowTitle("Export Map Image")
        self.spnWidth = None
        self.spnHeight = None
        self.spnDpi = None
        self.setup_export_ui(["PNG Image (*.png)", "SVG Image (*.svg)"])
        self._add_render_params()

    def _add_render_params(self):
        """Insert width/height/DPI controls into the grid before the stretch/buttons."""
        row = self.grid.rowCount()

        self.grid.addWidget(QtWidgets.QLabel("Width (px):"), row, 0)
        self.spnWidth = QtWidgets.QSpinBox()
        self.spnWidth.setRange(100, 10000)
        self.spnWidth.setValue(1600)
        self.spnWidth.setSingleStep(100)
        self.spnWidth.setFixedWidth(100)
        w_row = QtWidgets.QHBoxLayout()
        w_row.addWidget(self.spnWidth)
        w_row.addStretch()
        self.grid.addLayout(w_row, row, 1)
        row += 1

        self.grid.addWidget(QtWidgets.QLabel("Height (px):"), row, 0)
        self.spnHeight = QtWidgets.QSpinBox()
        self.spnHeight.setRange(100, 10000)
        self.spnHeight.setValue(1200)
        self.spnHeight.setSingleStep(100)
        self.spnHeight.setFixedWidth(100)
        h_row = QtWidgets.QHBoxLayout()
        h_row.addWidget(self.spnHeight)
        h_row.addStretch()
        self.grid.addLayout(h_row, row, 1)
        row += 1

        self.grid.addWidget(QtWidgets.QLabel("DPI:"), row, 0)
        self.spnDpi = QtWidgets.QSpinBox()
        self.spnDpi.setRange(72, 600)
        self.spnDpi.setValue(150)
        self.spnDpi.setSingleStep(25)
        self.spnDpi.setFixedWidth(100)
        d_row = QtWidgets.QHBoxLayout()
        d_row.addWidget(self.spnDpi)
        d_row.addStretch()
        self.grid.addLayout(d_row, row, 1)

    @property
    def render_params(self):
        return {
            "width": self.spnWidth.value() if self.spnWidth else 1600,
            "height": self.spnHeight.value() if self.spnHeight else 1200,
            "dpi": self.spnDpi.value() if self.spnDpi else 150,
        }

    def accept(self):
        out_file = self.leFile.text() if self.leFile is not None else ""
        if not out_file:
            QtWidgets.QMessageBox.warning(self, "Export Map", "Please select an output file.")
            return

        super().accept()
