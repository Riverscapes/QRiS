import os
import json
import csv
from PyQt5 import QtCore, QtGui, QtWidgets
import numpy as np

try:
    import pandas as pd
except ImportError:
    pd = None

from .frm_geospatial_metrics_options import FrmOptions
from .utilities import add_help_button


class FrmGeospatialMetricsExport(QtWidgets.QDialog):
    def __init__(self, parent, project, mask, polygons, metrics):
        super().__init__(parent)
        self.setWindowTitle("Export Geospatial Metrics")
        self.metrics = metrics
        self.polygons = polygons

        self.setupUi()

    def browse_path(self):
        
        output_type = self.formatGroup.checkedButton().text()
        if output_type == "JSON":
            filter = "JSON Files (*.json)"
        elif output_type == "CSV":
            filter = "CSV Files (*.csv)"
        else:
            filter = "Excel Files (*.xlsx)"
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Export File", "", filter)
        if path:
            self.txtOutpath.setText(path)

    def on_type_changed(self):
        current_path = self.txtOutpath.text()
        file, _ext = os.path.splitext(current_path)
        if current_path:
            # change the file extension based on the selected format
            if self.radioJson.isChecked():
                new_ext = ".json"
            elif self.radioCsv.isChecked():
                new_ext = ".csv"
            else:
                new_ext = ".xlsx"
            self.txtOutpath.setText(file + new_ext)

    def export(self):
        
        path = self.txtOutpath.text()
        if not path:
            QtWidgets.QMessageBox.warning(self, "Export", "Please specify an export file path.")
            return
        
        selected = [self.listWidget.item(i).data(QtCore.Qt.UserRole)
                    for i in range(self.listWidget.count())
                    if self.listWidget.item(i).checkState() == QtCore.Qt.Checked]
        if not selected:
            QtWidgets.QMessageBox.warning(self, "Export", "No metrics selected.")
            return

        # Gather selected data
        export_data = []
        for layer_name, polygon_id, metric_name in selected:
            value = self.metrics[layer_name][polygon_id][metric_name]
            # Convert numpy types to native Python types for JSON serialization
            if isinstance(value, (np.generic,)):
                value = value.item()
            export_data.append({
                "layer": layer_name,
                "polygon": self.polygons[polygon_id]['display_label'],
                "metric": metric_name,
                "value": value
            })

        # Choose file
        if self.radioJson.isChecked():
            fmt = "json"
        elif self.radioCsv.isChecked():
            fmt = "csv"
        else:
            fmt = "xlsx"

        # Export
        try:
            if fmt == "json":
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(export_data, f, indent=2)
            elif fmt == "csv":
                with open(path, "w", newline='', encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=["layer", "polygon", "metric", "value"])
                    writer.writeheader()
                    writer.writerows(export_data)
            else:  # xlsx
                if pd is None:
                    QtWidgets.QMessageBox.warning(self, "Export", "pandas is required for XLSX export.")
                    return
                df = pd.DataFrame(export_data)
                df.to_excel(path, index=False)
            QtWidgets.QMessageBox.information(self, "Export", "Export successful!")
            self.accept()
        except Exception as ex:
            QtWidgets.QMessageBox.critical(self, "Export Error", str(ex))

    def setupUi(self):
        self.resize(400, 400)
        layout = QtWidgets.QVBoxLayout(self)

        # List of metrics as checkboxes
        self.lblInstructions = QtWidgets.QLabel("Select metrics to export:")
        layout.addWidget(self.lblInstructions)
        self.listWidget = QtWidgets.QListWidget(self)
        for layer_name, values in self.metrics.items():
            for polygon_id, poly_values in values.items():
                polygon_label = self.polygons[polygon_id]['display_label']
                for metric_name, metric_value in poly_values.items():
                    item = QtWidgets.QListWidgetItem(f"{layer_name} - {polygon_label} - {metric_name}")
                    item.setData(QtCore.Qt.UserRole, (layer_name, polygon_id, metric_name))
                    item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                    item.setCheckState(QtCore.Qt.Checked)
                    self.listWidget.addItem(item)
        layout.addWidget(self.listWidget)
        self.listWidget.setMinimumHeight(200)
        self.listWidget.setMinimumWidth(300)

        # add select all and select none buttons
        btnLayout = QtWidgets.QHBoxLayout()
        btnSelectAll = QtWidgets.QPushButton("Select All")
        btnSelectAll.clicked.connect(lambda: [
            self.listWidget.item(i).setCheckState(QtCore.Qt.Checked)
            for i in range(self.listWidget.count())
        ])
        btnSelectNone = QtWidgets.QPushButton("Select None")
        btnSelectNone.clicked.connect(lambda: [
            self.listWidget.item(i).setCheckState(QtCore.Qt.Unchecked)
            for i in range(self.listWidget.count())
        ])
        btnLayout.addSpacerItem(QtWidgets.QSpacerItem(20, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))
        btnLayout.addWidget(btnSelectAll)
        btnLayout.addWidget(btnSelectNone)
        layout.addLayout(btnLayout)

        # Export format
        self.lblFormat = QtWidgets.QLabel("Select export format:")
        self.formatGroup = QtWidgets.QButtonGroup(self)
        self.radioJson = QtWidgets.QRadioButton("JSON")
        self.radioCsv = QtWidgets.QRadioButton("CSV")
        self.radioXls = QtWidgets.QRadioButton("XLSX")
        self.radioJson.setChecked(True)
        self.formatGroup.addButton(self.radioJson)
        self.formatGroup.addButton(self.radioCsv)
        self.formatGroup.addButton(self.radioXls)
        self.formatGroup.buttonClicked.connect(self.on_type_changed)
        fmtLayout = QtWidgets.QHBoxLayout()
        fmtLayout.addWidget(self.lblFormat)
        fmtLayout.addStretch()
        fmtLayout.addWidget(self.radioJson)
        fmtLayout.addWidget(self.radioCsv)
        fmtLayout.addWidget(self.radioXls)
        layout.addLayout(fmtLayout)

        horizontalLayout = QtWidgets.QHBoxLayout()
        self.lblPath = QtWidgets.QLabel("Export Path:")
        horizontalLayout.addWidget(self.lblPath)
        self.txtOutpath = QtWidgets.QLineEdit(self)
        self.txtOutpath.setPlaceholderText("Choose export file path")
        self.txtOutpath.setReadOnly(True)
        horizontalLayout.addWidget(self.txtOutpath)
        self.btnBrowse = QtWidgets.QPushButton("Browse")
        self.btnBrowse.clicked.connect(lambda: self.txtOutpath.setText(
            QtWidgets.QFileDialog.getSaveFileName(self, "Save Export File", "", "JSON Files (*.json);;CSV Files (*.csv);;Excel Files (*.xlsx)")[0]))
        horizontalLayout.addWidget(self.btnBrowse)
        layout.addLayout(horizontalLayout)

        horiz_bottom = QtWidgets.QHBoxLayout()
        layout.addLayout(horiz_bottom)

        horiz_bottom.addWidget(add_help_button(self, "zonal-statistics#export"))
        horiz_bottom.addStretch()

        # Export button
        btnExport = QtWidgets.QPushButton("Export")
        btnExport.clicked.connect(self.export)
        horiz_bottom.addWidget(btnExport)
        
        # Add cancel button
        self.btnCancel = QtWidgets.QPushButton("Cancel")
        self.btnCancel.clicked.connect(self.reject)
        horiz_bottom.addWidget(self.btnCancel)