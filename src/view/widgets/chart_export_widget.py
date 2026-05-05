import os
import re

from qgis.PyQt import QtWidgets, QtCore, QtGui
from ...QRiS.path_utilities import get_unique_file_path
from ..utilities import add_standard_form_buttons
from .table_export_widget import FrmTableExport


def _format_export_display_name(base_name):
    text = str(base_name or "export")
    text = text.replace('_', ' ').replace('-', ' ')
    text = re.sub(r'(?<=[a-z0-9])(?=[A-Z])', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

class FrmChartExport(QtWidgets.QDialog):
    def __init__(self, parent, mode='values', data=None, figure=None, base_name="export", project_path=None, export_type=None):
        super().__init__(parent)
        base_name_text = str(base_name).strip() if base_name is not None else ''
        export_type_text = str(export_type).strip() if export_type is not None else ''

        self.mode = mode  # 'values' or 'image'
        self.data = data
        self.figure = figure
        self.base_name = base_name_text if base_name_text else 'export'
        self.project_path = project_path
        self.export_display_name = _format_export_display_name(self.base_name)
        self.file_base_name = self.base_name
        self.export_type = export_type_text if export_type_text else None
        self.last_generated_path = None
        
        self.setupUi()
        
    def setupUi(self):
        title = "Export Data Table" if self.mode == 'values' else "Export Chart Image"
        self.setWindowTitle(title)
        self.setMinimumWidth(500)
        
        self.layout = QtWidgets.QVBoxLayout(self)
        self.grid = QtWidgets.QGridLayout()
        self.layout.addLayout(self.grid)
        
        # Info
        lbl_info = QtWidgets.QLabel("Exporting:")
        self.grid.addWidget(lbl_info, 0, 0)
        lbl_name = QtWidgets.QLabel(f"<b>{self.export_display_name}</b>")
        self.grid.addWidget(lbl_name, 0, 1)
        
        # Format
        self.lblFormat = QtWidgets.QLabel("Output Format:")
        self.cmbFormat = QtWidgets.QComboBox()
        
        if self.mode == 'values':
             self.cmbFormat.addItems(["Comma Separated Values (CSV)", "Excel (*.xlsx)", "JSON (*.json)"])
        else:
             self.cmbFormat.addItems(["PNG Image (*.png)", "JPEG Image (*.jpg)", "SVG Image (*.svg)", "PDF Document (*.pdf)"])
             
        self.cmbFormat.currentTextChanged.connect(self.format_changed)
        self.grid.addWidget(self.lblFormat, 1, 0)
        self.grid.addWidget(self.cmbFormat, 1, 1)
        
        # Path
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
        
        # Default Path
        self.update_default_path()
        
        self.layout.addStretch()
        
        # Buttons (using generic help slug for now)
        self.layout.addLayout(add_standard_form_buttons(self, 'analysis/export'))

    def get_extension(self):
        text = self.cmbFormat.currentText()
        if "CSV" in text: return ".csv"
        if "Excel" in text: return ".xlsx"
        if "JSON" in text: return ".json"
        
        if "PNG" in text: return ".png"
        if "JPEG" in text: return ".jpg"
        if "SVG" in text: return ".svg"
        if "PDF" in text: return ".pdf"
        return ""

    def update_default_path(self):
        home = self.project_path
        if not home: return
        
        if os.path.isfile(home):
            home = os.path.dirname(home)
            
        export_dir = os.path.join(home, 'exports')
        if self.export_type:
            export_dir = os.path.join(export_dir, self.export_type)
        if not os.path.exists(export_dir):
            os.makedirs(export_dir, exist_ok=True)
            
        ext = self.get_extension()
        default_path = get_unique_file_path(export_dir, self.file_base_name, ext)
        self.leFile.setText(os.path.normpath(default_path))
        self.last_generated_path = self.leFile.text()

    def format_changed(self, text):
        current = self.leFile.text()
        if not current: return
        
        # If user hasn't customized path, regen default
        if current == self.last_generated_path:
            self.update_default_path()
            return

        # Otherwise just swap extension
        base, _ = os.path.splitext(current)
        new_ext = self.get_extension()
        self.leFile.setText(base + new_ext)

    def browse_file(self):
        ext = self.get_extension()
        filter_str = f"Current Format (*{ext});;All Files (*.*)"
        
        initial = self.leFile.text()
        folder = os.path.dirname(initial) if initial else ""
        
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Select Output File", folder, filter_str)
        if filename:
            self.leFile.setText(os.path.normpath(filename))
            # Sync combo? For now let's assume user picks matching ext or we trust them
            
    def open_location(self, path):
         if os.path.exists(path):
              folder = os.path.dirname(path)
              QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(folder))

    def accept(self):
        out_file = self.leFile.text()
        if not out_file:
            QtWidgets.QMessageBox.warning(self, "Error", "Please select an output file.")
            return
            
        success = False
        msg = ""
        
        try:
            if self.mode == 'values':
                success, msg = self.export_values(out_file)
            else:
                success, msg = self.export_image(out_file)
        except Exception as e:
            success = False
            msg = str(e)
            
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

    def export_image(self, filename):
        if not self.figure: return False, "No chart figure available."
        try:
            self.figure.savefig(filename, dpi=300, bbox_inches='tight')
            return True, ""
        except Exception as e:
            return False, str(e)

    def export_values(self, filename):
        dlg = FrmTableExport(self, data=self.data, base_name=self.base_name, project_path=self.project_path, export_type=self.export_type)
        return dlg.export_table(filename)

class ChartExportWidget(QtWidgets.QPushButton):
    def __init__(self, parent=None, base_name="chart_export", get_data_callback=None, get_figure_callback=None, project_path=None, export_type=None):
        super().__init__(parent)
        self.setText("Export")
        self.setToolTip("Export chart data or image")
        
        self.base_name = base_name
        self.get_data_callback = get_data_callback
        self.get_figure_callback = get_figure_callback
        self.project_path = project_path
        self.export_type = export_type
        
        self.setup_menu()

    def setup_menu(self):
        menu = QtWidgets.QMenu(self)
        
        # Values
        a_values = menu.addAction("Export Values...")
        a_values.triggered.connect(self.export_values)
        
        # Image
        a_image = menu.addAction("Export Image...")
        a_image.triggered.connect(self.export_image)
        
        self.setMenu(menu)

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
        dlg = FrmChartExport(self, mode='image', figure=fig, base_name=self.base_name, project_path=self.project_path, export_type=self.export_type)
        dlg.exec_()
