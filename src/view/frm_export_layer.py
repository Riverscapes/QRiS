from PyQt5 import QtWidgets, QtCore
from qgis.core import QgsVectorLayer, QgsVectorFileWriter, QgsCoordinateTransformContext, QgsFeature, QgsGeometry, Qgis
from .utilities import add_standard_form_buttons

class FrmExportLayer(QtWidgets.QDialog):
    def __init__(self, parent, layer: QgsVectorLayer):
        super(FrmExportLayer, self).__init__(parent)
        self.layer = layer
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

        self.vert.addStretch()

        # Dialog Buttons
        self.vert.addLayout(add_standard_form_buttons(self, 'export-layer-attributes'))

    def format_changed(self, text):
        current_path = self.leFile.text()
        
        if text in ["JSON", "GeoJSON"]:
            self.chkIncludeGeom.setEnabled(False)
            self.chkIncludeGeom.setChecked(text == "GeoJSON")
        else:
            self.chkIncludeGeom.setEnabled(True)

        if not current_path:
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

        filename, selected_filter = QtWidgets.QFileDialog.getSaveFileName(self, "Select Output File", "", filter_str)
        if filename:
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
            QtWidgets.QMessageBox.information(self, "Success", "Layer exported successfully.")
        
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
