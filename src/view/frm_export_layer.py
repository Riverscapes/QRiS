import os

from qgis.PyQt import QtWidgets, QtCore, QtGui
from qgis.core import QgsVectorLayer, QgsVectorFileWriter, QgsCoordinateTransformContext, QgsFeature, QgsField, QgsProject

from .utilities import add_standard_form_buttons
from ..QRiS.path_utilities import get_unique_file_path

class FrmExportLayer(QtWidgets.QDialog):
    def __init__(self, parent, layer: QgsVectorLayer, base_name: str = None, project_path: str = None):
        super(FrmExportLayer, self).__init__(parent)
        self.layer = layer
        self.base_name = base_name or self.layer.name()
        self.project_path = project_path
        self.last_generated_path = None
        self.setupUi()

    def setupUi(self):
        self.setWindowTitle("Export Layer Attributes")
        self.setMinimumWidth(500)
        
        # Layout
        self.vert = QtWidgets.QVBoxLayout(self)
        self.grid = QtWidgets.QGridLayout()
        self.vert.addLayout(self.grid)
        
        # Layer Info
        lbl_info = QtWidgets.QLabel(f"Exporting layer:" )
        self.grid.addWidget(lbl_info, 0, 0)
        lbl_layer_name = QtWidgets.QLabel(f"<b>{self.layer.name()}</b>")
        self.grid.addWidget(lbl_layer_name, 0, 1)

        # Format Selection
        self.lblFormat = QtWidgets.QLabel("Output Format:")
        self.cmbFormat = QtWidgets.QComboBox()
        self.cmbFormat.addItems(["Comma Separated Values (CSV)", "Tab Separated Values (TSV)", "JSON", "GeoJSON", "Excel"])
        self.cmbFormat.currentTextChanged.connect(self.format_changed)
        
        self.grid.addWidget(self.lblFormat, 1, 0)
        self.grid.addWidget(self.cmbFormat, 1, 1)

        # Output File Selection
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
         
        # Options
        self.chkIncludeGeom = QtWidgets.QCheckBox("Include Geometries")
        self.chkIncludeGeom.setChecked(False)
        self.grid.addWidget(self.chkIncludeGeom, 3, 1)

        # Set default output path
        self.update_default_path()

        self.vert.addStretch()

        # Dialog Buttons
        self.vert.addLayout(add_standard_form_buttons(self, 'export-layer-attributes'))

    def update_default_path(self):
        project_home = self.project_path or QgsProject.instance().homePath()
        if project_home:
            export_directory = os.path.join(project_home, 'exports')
            if not os.path.exists(export_directory):
                os.makedirs(export_directory, exist_ok=True)
            
            # Determine extension
            ext = ".csv"
            text = self.cmbFormat.currentText()
            if text == "Comma Separated Values (CSV)":
                ext = ".csv"
            elif text == "Tab Separated Values (TSV)":
                ext = ".tsv"
            elif text == "JSON":
                ext = ".json"
            elif text == "GeoJSON":
                ext = ".geojson"
            elif text == "Excel":
                ext = ".xlsx"
            
            # Use utility to generate unique path
            default_path = get_unique_file_path(export_directory, self.base_name, ext)
            default_path = os.path.normpath(default_path)  # Normalize path separators
            self.leFile.setText(default_path)
            self.last_generated_path = default_path

    def format_changed(self, text):
        current_path = self.leFile.text()
        
        if text in ["JSON", "GeoJSON"]:
            self.chkIncludeGeom.setEnabled(False)
            self.chkIncludeGeom.setChecked(text == "GeoJSON")
        else:
            self.chkIncludeGeom.setEnabled(True)

        if not current_path:
            return
            
        # If the user hasn't modified the path (or it matches the last generated one),
        # regenerate it to ensure uniqueness and proper base name usage.
        if current_path == self.last_generated_path:
             self.update_default_path()
             return

        import os
        base, ext = os.path.splitext(current_path)
        
        new_ext = ""
        if text == "Comma Separated Values (CSV)":
            new_ext = ".csv"
        elif text == "Tab Separated Values (TSV)":
            new_ext = ".tsv"
        elif text == "JSON":
            new_ext = ".json"
        elif text == "GeoJSON":
            new_ext = ".geojson"
        elif text == "Excel":
            new_ext = ".xlsx"
            
        if new_ext:
            self.leFile.setText(base + new_ext)

    def browse_file(self):
        # Determine filter based on combo box
        current_format = self.cmbFormat.currentText()
        filter_str = "All Files (*.*)"
        if current_format == "Comma Separated Values (CSV)":
            filter_str = "Comma Separated Values (*.csv);;All Files (*.*)"
        elif current_format == "Tab Separated Values (TSV)":
            filter_str = "Tab Separated Values (*.tsv);;All Files (*.*)"
        elif current_format == "JSON":
            filter_str = "JSON (*.json);;All Files (*.*)"
        elif current_format == "GeoJSON":
            filter_str = "GeoJSON (*.geojson);;All Files (*.*)"
        elif current_format == "Excel":
            filter_str = "Excel (*.xlsx);;All Files (*.*)"

        # Set initial directory for browse dialog
        initial_path = self.leFile.text()
        initial_dir = os.path.dirname(initial_path) if initial_path else ""

        filename, selected_filter = QtWidgets.QFileDialog.getSaveFileName(self, "Select Output File", initial_dir, filter_str)
        if filename:
            filename = os.path.normpath(filename)  # Normalize path separators
            self.leFile.setText(filename)
            # Update combo box if extension doesn't match
            lower_file = filename.lower()
            if lower_file.endswith('.csv'):
                self.cmbFormat.setCurrentText("Comma Separated Values (CSV)")
            elif lower_file.endswith('.tsv'):
                self.cmbFormat.setCurrentText("Tab Separated Values (TSV)")
            elif lower_file.endswith('.json'):
                 # Check if we were already in GeoJSON mode, otherwise default to JSON
                 if self.cmbFormat.currentText() == "GeoJSON":
                      self.cmbFormat.setCurrentText("GeoJSON")
                 else:
                      self.cmbFormat.setCurrentText("JSON")
            elif lower_file.endswith('.geojson'):
                self.cmbFormat.setCurrentText("GeoJSON")
            elif lower_file.endswith('.xlsx'):
                self.cmbFormat.setCurrentText("Excel")


    def accept(self):
        out_file = self.leFile.text()
        if not out_file:
            QtWidgets.QMessageBox.warning(self, "Error", "Please select an output file.")
            return

        if self.export_layer(out_file, self.chkIncludeGeom.isChecked()):
            super().accept()
            msg_box = QtWidgets.QMessageBox()
            msg_box.setWindowTitle("Export Successful")
            msg_box.setText(f"Layer exported successfully to:\n{out_file}")
            msg_box.setIcon(QtWidgets.QMessageBox.Information)

            btn_folder = msg_box.addButton("View in Folder", QtWidgets.QMessageBox.ActionRole)
            btn_open = msg_box.addButton("Open File", QtWidgets.QMessageBox.ActionRole)
            btn_close = msg_box.addButton("Close", QtWidgets.QMessageBox.RejectRole)
            
            msg_box.exec_()
            
            clicked = msg_box.clickedButton()
            if clicked == btn_folder:
                self.open_folder(out_file)
            elif clicked == btn_open:
                self.open_file(out_file)

    def open_folder(self, path):
        path = os.path.normpath(path)
        if os.name == 'nt':
            import subprocess
            subprocess.Popen(f'explorer /select,"{path}"')
        else:
            folder = os.path.dirname(path)
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(folder))

    def open_file(self, path):
         QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(path))
        
    def export_layer(self, out_file, include_geometries):
        driver_name = 'CSV'
        layer_options = ['STRING_QUOTING=IF_NEEDED']
        
        lower_file = out_file.lower()
        if lower_file.endswith('.tsv'):
            driver_name = 'CSV'
            layer_options.append('SEPARATOR=TAB')
        elif lower_file.endswith('.json') or lower_file.endswith('.geojson'):
            driver_name = 'GeoJSON'
            layer_options = []
        elif lower_file.endswith('.xlsx'):
            driver_name = 'XLSX'
            layer_options = ['OGR_XLSX_HEADERS=FORCE']
        elif lower_file.endswith('.csv'):
            driver_name = 'CSV'
            
        export_layer = self.layer
        temp_layer = None

        if include_geometries:
            if driver_name == 'CSV':
                layer_options.append('GEOMETRY=AS_WKT')
            elif driver_name == 'XLSX':
                # Create a memory layer with WKT geometry field for XLSX
                crs = self.layer.crs().authid()
                if not crs:
                    crs = self.layer.crs().toWkt()
                
                temp_layer = QgsVectorLayer(f"None?crs={crs}", self.layer.name(), "memory")
                temp_data = temp_layer.dataProvider()
                
                # Add original fields
                temp_data.addAttributes(self.layer.fields().toList())
                # Add geometry field
                temp_data.addAttributes([QgsField("geometry", QtCore.QVariant.String)])
                temp_layer.updateFields()
                
                features = []
                for f in self.layer.getFeatures():
                    feat = QgsFeature(temp_layer.fields())
                    feat.setAttributes(f.attributes() + [f.geometry().asWkt()])
                    features.append(feat)
                
                temp_data.addFeatures(features)
                export_layer = temp_layer
        else:
            # Create a memory layer without geometry for any format when geometry is excluded
            # This handles CSV (avoiding unsupported GEOMETRY=NONE), GeoJSON, XLSX, etc. reliably
            crs = self.layer.crs().authid()
            if not crs:
                crs = self.layer.crs().toWkt()
            
            temp_layer = QgsVectorLayer(f"None?crs={crs}", self.layer.name(), "memory")
            temp_data = temp_layer.dataProvider()
            temp_data.addAttributes(self.layer.fields().toList())
            temp_layer.updateFields()

            features = []
            for f in self.layer.getFeatures():
                feat = QgsFeature(f)
                feat.clearGeometry()
                features.append(feat)
            temp_data.addFeatures(features)
            export_layer = temp_layer

        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = driver_name
        options.layerOptions = layer_options
        options.fieldNameSource = QgsVectorFileWriter.FieldNameSource.PreferAlias
        
        # Exclude "Metadata" field from export
        attributes = []
        for i in range(export_layer.fields().count()):
            if export_layer.fields().at(i).name().lower() != 'metadata':
                attributes.append(i)
        options.attributes = attributes

        context = QgsCoordinateTransformContext()
        
        # Returns (error, new_filename, new_layer_name, error_message)
        result = QgsVectorFileWriter.writeAsVectorFormatV3(export_layer, out_file, context, options)
        error = result[0]
        
        # Clean up temp layer if used
        if temp_layer:
            del temp_layer
            
        if error != QgsVectorFileWriter.NoError:
            error_msg = result[3]
            QtWidgets.QMessageBox.critical(self, "Export Failed", f"Error exporting layer:\n{error_msg}")
            return False
            
        return True
