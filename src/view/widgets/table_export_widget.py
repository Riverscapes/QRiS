import csv
import json
import os
import re

import xlwt

from qgis.PyQt import QtCore, QtGui, QtWidgets

from ...QRiS.path_utilities import get_unique_file_path
from ..utilities import add_standard_form_buttons

"""Reusable table export dialog and button control for list-of-dict data."""


def _format_export_display_name(base_name):
    """Convert a machine-ish base name into readable label text."""
    text = str(base_name or "export")
    text = text.replace('_', ' ').replace('-', ' ')
    text = re.sub(r'(?<=[a-z0-9])(?=[A-Z])', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


class FrmTableExport(QtWidgets.QDialog):
    """Dialog for exporting tabular rows to CSV, Excel, or JSON files."""

    def __init__(self, parent, data=None, base_name="table_export", project_path=None, export_type=None):
        """Initialize export state and build the form controls."""
        super().__init__(parent)

        base_name_text = str(base_name).strip() if base_name is not None else ''
        export_type_text = str(export_type).strip() if export_type is not None else ''

        self.data = data
        self.base_name = base_name_text if base_name_text else 'export'
        self.project_path = project_path
        self.export_display_name = _format_export_display_name(self.base_name)
        self.file_base_name = self.base_name
        self.export_type = export_type_text if export_type_text else None
        self.last_generated_path = None

        self.setWindowTitle("Export Table")
        self.setupUi()

    def setupUi(self):
        """Create the export UI controls and wire button/menu events."""

        self.setMinimumWidth(500)

        self.layout = QtWidgets.QVBoxLayout(self)
        self.grid = QtWidgets.QGridLayout()
        self.layout.addLayout(self.grid)

        self.lbl_info = QtWidgets.QLabel("Exporting:")
        self.grid.addWidget(self.lbl_info, 0, 0)

        self.lbl_name = QtWidgets.QLabel(f"<b>{self.export_display_name}</b>")
        self.grid.addWidget(self.lbl_name, 0, 1)

        self.lbl_format = QtWidgets.QLabel("Output Format:")
        self.combo_format = QtWidgets.QComboBox()
        self.combo_format.addItems(["CSV", "Excel", "JSON"])
        self.combo_format.currentTextChanged.connect(self.format_change)
        self.grid.addWidget(self.lbl_format, 1, 0)
        self.grid.addWidget(self.combo_format, 1, 1)

        self.lbl_path = QtWidgets.QLabel("Output Path:")
        self.txt_outpath = QtWidgets.QLineEdit()
        self.txt_outpath.setReadOnly(True)
        self.txt_outpath.setPlaceholderText("Select output file...")
        self.btn_browse = QtWidgets.QPushButton("...")
        self.btn_browse.clicked.connect(self.browse_path)

        self.horiz_path = QtWidgets.QHBoxLayout()
        self.horiz_path.addWidget(self.txt_outpath)
        self.horiz_path.addWidget(self.btn_browse)

        self.grid.addWidget(self.lbl_path, 2, 0)
        self.grid.addLayout(self.horiz_path, 2, 1)

        self.update_default_path()

        self.layout.addStretch()
        self.layout.addLayout(add_standard_form_buttons(self, 'analysis/export'))

    def get_extension(self):
        """Return the file extension for the selected output format."""
        output_format = self.combo_format.currentText()
        if output_format == "CSV":
            return ".csv"
        if output_format == "Excel":
            return ".xlsx"
        if output_format == "JSON":
            return ".json"
        return ""

    def update_default_path(self):
        """Set a suggested export file path under the project exports folder."""

        home = self.project_path
        if not home:
            return

        if os.path.isfile(home):
            home = os.path.dirname(home)

        export_dir = os.path.join(home, 'exports')
        if self.export_type:
            export_dir = os.path.join(export_dir, self.export_type)
        if not os.path.exists(export_dir):
            os.makedirs(export_dir, exist_ok=True)

        ext = self.get_extension()
        default_path = get_unique_file_path(export_dir, self.file_base_name, ext)
        self.txt_outpath.setText(os.path.normpath(default_path))
        self.last_generated_path = self.txt_outpath.text()

    def format_change(self):
        """Update the output extension when the user changes export format."""
        current = self.txt_outpath.text()
        if not current:
            return

        if current == self.last_generated_path:
            self.update_default_path()
            return

        base, _ = os.path.splitext(current)
        self.txt_outpath.setText(base + self.get_extension())

    def browse_path(self):
        """Open a save dialog and store the selected output path."""
        ext = self.get_extension()
        filter_str = f"Current Format (*{ext});;All Files (*.*)"

        initial = self.txt_outpath.text()
        folder = os.path.dirname(initial) if initial else ""

        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Select Output File", folder, filter_str)
        if filename:
            self.txt_outpath.setText(os.path.normpath(filename))

    def open_location(self, path):
        """Open the output folder in the desktop file browser."""
        if os.path.exists(path):
            folder = os.path.dirname(path)
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(folder))

    def get_headers(self):
        """Build ordered header names from all row keys in the dataset."""
        if not self.data:
            return []

        headers = list(self.data[0].keys())
        for row in self.data[1:]:
            for key in row.keys():
                if key not in headers:
                    headers.append(key)
        return headers

    def export_table(self, filename):
        """Write the current dataset to the requested file format."""
        if not self.data:
            return False, "No data available."

        headers = self.get_headers()
        if len(headers) < 1:
            return False, "No export columns were found."

        lower = filename.lower()
        if lower.endswith('.csv'):
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers, extrasaction='ignore')
                writer.writeheader()
                for row in self.data:
                    writer.writerow({key: row.get(key, '') for key in headers})
            return True, ""

        if lower.endswith('.json'):
            normalized = [{key: row.get(key, '') for key in headers} for row in self.data]
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(normalized, f, ensure_ascii=False, indent=2)
            return True, ""

        if lower.endswith('.xlsx') or lower.endswith('.xls'):
            wb = xlwt.Workbook()
            ws = wb.add_sheet('Export')

            for col, key in enumerate(headers):
                ws.write(0, col, key)

            for row_idx, row in enumerate(self.data):
                for col_idx, key in enumerate(headers):
                    ws.write(row_idx + 1, col_idx, row.get(key, ''))

            wb.save(filename)
            return True, ""

        return False, "Unsupported output format."

    def accept(self):
        """Run export, then display success/failure feedback to the user."""
        out_file = self.txt_outpath.text()
        if not out_file:
            QtWidgets.QMessageBox.warning(self, "Export Table", "Please select an output file.")
            return

        success, msg = self.export_table(out_file)
        if success:
            super().accept()

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
        else:
            QtWidgets.QMessageBox.critical(self, "Export Failed", f"Error: {msg}")


class TableExportWidget(QtWidgets.QPushButton):
    """Drop-in Export button that opens FrmTableExport for provided data."""

    def __init__(self, parent=None, base_name="table_export", get_data_callback=None, project_path=None, export_type=None):
        """Store callbacks/options and create the button menu."""
        super().__init__(parent)

        self.setText("Export")
        self.setToolTip("Export table values")

        self.base_name = base_name
        self.get_data_callback = get_data_callback
        self.project_path = project_path
        self.export_type = export_type

        self.setup_menu()

    def setup_menu(self):
        """Configure the button drop-down actions."""
        menu = QtWidgets.QMenu(self)

        action_export = menu.addAction("Export Table...")
        action_export.triggered.connect(self.export_table)

        self.setMenu(menu)

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
