import os

from osgeo import gdal

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QDialogButtonBox
from qgis.PyQt.QtCore import pyqtSignal
from qgis.core import (
    Qgis,
    QgsVectorLayer,
    QgsVectorFileWriter)

from .ript_project import RiptProject, Layer

DIALOG_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui', 'ript_add_layer_dlg.ui'))

PROJECT_LAYER_TYPES = ['Project_Extent']


class AddLayerDlg(QDialog, DIALOG_CLASS):

    closingPlugin = pyqtSignal()
    dataChange = pyqtSignal(RiptProject, str)

    def __init__(self, layer_uri, ript_project):
        """Constructor."""
        QDialog.__init__(self, None)
        self.setupUi(self)

        self.project = ript_project

        self.txtLayerName.setText(layer_uri.name)
        self.txtLayerSource.setText(layer_uri.uri)
        self.cboLayerType.addItems(PROJECT_LAYER_TYPES)
        self.text_validate()

        self.txtLayerName.textChanged.connect(self.text_validate)
        self.buttonBox.accepted.connect(self.save_layer)

    def text_validate(self):

        text = self.txtLayerName.text()
        out_text = ''.join(e for e in text.replace(" ", "_") if e.isalnum() or e == "_")
        self.txtProjectLayerPath.setText(os.path.join("ProjectLayers.gpkg", out_text))
        self.layer_path_name = out_text

        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)

    def save_layer(self):
        out_name = self.txtLayerName.text()
        out_gpkg = os.path.join(self.project.project_path, "ProjectLayers.gpkg")
        original_layer = QgsVectorLayer(self.txtLayerSource.text())
        if not os.path.exists(os.path.dirname(out_gpkg)):
            os.makedirs(os.path.dirname(os.path.dirname(out_gpkg)))
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.layerName = self.layer_path_name
        options.driverName = 'GPKG'
        if os.path.exists(out_gpkg):
            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer

        _out = QgsVectorFileWriter.writeAsVectorFormat(original_layer, out_gpkg, options)

        self.project.project_layers[out_name] = Layer(out_name, self.txtProjectLayerPath.text(), self.cboLayerType.currentText())
        self.project.export_project_file()

        self.dataChange.emit(self.project, out_name)
