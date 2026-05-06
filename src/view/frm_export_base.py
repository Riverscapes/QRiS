import os
import re

from qgis.PyQt import QtCore, QtGui, QtWidgets

from ..QRiS.path_utilities import get_unique_file_path
from .utilities import add_standard_form_buttons


def format_export_display_name(base_name):
    text = str(base_name or "export")
    text = text.replace('_', ' ').replace('-', ' ')
    text = re.sub(r'(?<=[a-z0-9])(?=[A-Z])', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


class FrmBaseExport(QtWidgets.QDialog):
    """Common export dialog UI and file/path behavior."""

    def __init__(self, parent, base_name="export", project_path=None, export_type=None):
        super().__init__(parent)
        base_name_text = str(base_name).strip() if base_name is not None else ""
        export_type_text = str(export_type).strip() if export_type is not None else ""

        self.base_name = base_name_text if base_name_text else "export"
        self.project_path = project_path
        self.export_display_name = format_export_display_name(self.base_name)
        self.file_base_name = self.base_name
        self.export_type = export_type_text if export_type_text else None
        self.last_generated_path = None

        self.layout = None
        self.grid = None
        self.lblFormat = None
        self.cmbFormat = None
        self.lblPath = None
        self.leFile = None
        self.btnBrowse = None

    def setup_export_ui(self, format_items, help_slug="analysis/export"):
        self.setMinimumWidth(500)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.grid = QtWidgets.QGridLayout()
        self.layout.addLayout(self.grid)

        lbl_info = QtWidgets.QLabel("Exporting:")
        self.grid.addWidget(lbl_info, 0, 0)
        lbl_name = QtWidgets.QLabel(f"<b>{self.export_display_name}</b>")
        self.grid.addWidget(lbl_name, 0, 1)

        self.lblFormat = QtWidgets.QLabel("Output Format:")
        self.cmbFormat = QtWidgets.QComboBox()
        self.cmbFormat.addItems(format_items)
        self.cmbFormat.currentTextChanged.connect(self.format_changed)
        self.grid.addWidget(self.lblFormat, 1, 0)
        self.grid.addWidget(self.cmbFormat, 1, 1)

        self.lblPath = QtWidgets.QLabel("Output Path:")
        self.leFile = QtWidgets.QLineEdit()
        self.leFile.setReadOnly(True)
        self.leFile.setPlaceholderText("Select output file...")
        self.btnBrowse = QtWidgets.QPushButton("...")
        self.btnBrowse.clicked.connect(self.browse_file)

        path_layout = QtWidgets.QHBoxLayout()
        path_layout.addWidget(self.leFile)
        path_layout.addWidget(self.btnBrowse)
        self.grid.addWidget(self.lblPath, 2, 0)
        self.grid.addLayout(path_layout, 2, 1)

        self.update_default_path()

        self.layout.addStretch()
        self.layout.addLayout(add_standard_form_buttons(self, help_slug))

    def get_extension(self):
        text = self.cmbFormat.currentText() if self.cmbFormat else ""
        if "CSV" in text:
            return ".csv"
        if "Excel" in text:
            return ".xlsx"
        if "JSON" in text:
            return ".json"
        if "PNG" in text:
            return ".png"
        if "JPEG" in text:
            return ".jpg"
        if "SVG" in text:
            return ".svg"
        if "PDF" in text:
            return ".pdf"
        return ""

    def update_default_path(self):
        home = self.project_path
        if not home or self.leFile is None:
            return

        if os.path.isfile(home):
            home = os.path.dirname(home)

        export_dir = os.path.join(home, "exports")
        if self.export_type:
            export_dir = os.path.join(export_dir, self.export_type)
        if not os.path.exists(export_dir):
            os.makedirs(export_dir, exist_ok=True)

        ext = self.get_extension()
        default_path = get_unique_file_path(export_dir, self.file_base_name, ext)
        self.leFile.setText(os.path.normpath(default_path))
        self.last_generated_path = self.leFile.text()

    def format_changed(self, _text):
        if self.leFile is None:
            return

        current = self.leFile.text()
        if not current:
            return

        if current == self.last_generated_path:
            self.update_default_path()
            return

        base, _ = os.path.splitext(current)
        self.leFile.setText(base + self.get_extension())

    def browse_file(self):
        if self.leFile is None:
            return

        ext = self.get_extension()
        filter_str = f"Current Format (*{ext});;All Files (*.*)"

        initial = self.leFile.text()
        folder = os.path.dirname(initial) if initial else ""

        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Select Output File", folder, filter_str)
        if filename:
            self.leFile.setText(os.path.normpath(filename))

    def open_location(self, path):
        if os.path.exists(path):
            folder = os.path.dirname(path)
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(folder))

    def show_export_success(self, out_file):
        mbox = QtWidgets.QMessageBox()
        mbox.setWindowTitle("Export Successful")
        mbox.setText(f"File saved to:\n{out_file}")
        mbox.setIcon(QtWidgets.QMessageBox.Information)
        btn_fold = mbox.addButton("Open Folder", QtWidgets.QMessageBox.ActionRole)
        btn_open = mbox.addButton("Open File", QtWidgets.QMessageBox.ActionRole)
        mbox.addButton("Close", QtWidgets.QMessageBox.RejectRole)
        mbox.exec_()

        if mbox.clickedButton() == btn_fold:
            self.open_location(out_file)
        elif mbox.clickedButton() == btn_open:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(out_file))
