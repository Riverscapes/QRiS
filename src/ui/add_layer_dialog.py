import os

from osgeo import gdal

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QDialogButtonBox
from qgis.PyQt.QtCore import pyqtSignal
from qgis.core import (
    Qgis,
    QgsVectorLayer,
    QgsVectorFileWriter)

from ..qris_project import QRiSProject, Layer

DIALOG_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'add_layer_dialog.ui'))

# TODO Put this somewhere else once
PROJECT_LAYER_TYPES = ['Project_Extent']


class AddLayerDlg(QDialog, DIALOG_CLASS):

    closingPlugin = pyqtSignal()
    dataChange = pyqtSignal(QRiSProject, str)

    def __init__(self, layer_uri, qris_project):
        """Constructor."""
        QDialog.__init__(self, None)
        self.setupUi(self)

        self.layer_uri = layer_uri
        self.qris_project = qris_project

        if self.layer_uri is not None:
            self.txtLayerSource.setText(self.layer_uri.uri)
            self.txtLayerName.setText(self.layer_uri.name)
        else:
            # TODO Make the new layer name non editable
            self.txtLayerSource.setText("Create New Layer")

        # TODO just make this an auto entered field
        self.cboLayerType.addItems(PROJECT_LAYER_TYPES)

        # TODO test if you need to call this or just add it to the field
        self.text_validate()
        # consider forcing a extent suffix or prefix
        self.txtLayerName.textChanged.connect(self.text_validate)
        self.buttonBox.accepted.connect(self.save_layer)

    def text_validate(self):
        """Validates text entered into the layer name to be GIS friendly"""
        text = self.txtLayerName.text()
        out_text = ''.join(e for e in text.replace(" ", "_") if e.isalnum() or e == "_")
        self.txtProjectLayerPath.setText(os.path.join("ProjectLayers.gpkg", out_text))
        self.layer_path_name = out_text
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)

    def save_layer(self):
        out_name = self.txtLayerName.text()
        out_gpkg = os.path.join(self.qris_project.project_path, "ProjectLayers.gpkg")
        if self.layer_uri is not None:
            original_layer = QgsVectorLayer(self.txtLayerSource.text())
        else:
            original_layer = QgsVectorLayer("Polygon", self.txtLayerName.text(), "memory")
        if not os.path.exists(os.path.dirname(out_gpkg)):
            os.makedirs(os.path.dirname(os.path.dirname(out_gpkg)))
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.layerName = self.layer_path_name
        options.driverName = 'GPKG'
        if os.path.exists(out_gpkg):
            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer

        _out = QgsVectorFileWriter.writeAsVectorFormat(original_layer, out_gpkg, options)

        self.qris_project.project_extents[out_name] = Layer(out_name, self.txtProjectLayerPath.text(), self.cboLayerType.currentText())
        self.qris_project.export_project_file()

        self.dataChange.emit(self.qris_project, out_name)
