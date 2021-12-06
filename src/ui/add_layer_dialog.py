import os

from osgeo import gdal

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QDialogButtonBox
from qgis.PyQt.QtCore import pyqtSignal
from qgis.core import (
    Qgis,
    QgsVectorLayer,
    QgsVectorFileWriter)

from ..qris_project import QRiSProject, ProjectExtent

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
            self.lineEdit_import_layer_path.setText(self.layer_uri.uri)
            self.lineEdit_display_name.setText(self.layer_uri.name)
        else:
            self.lineEdit_feature_name.setText("Create New Layer")

        self.text_validate()

        # TODO just make this an auto entered field
        self.comboBox_layer_type.addItems(PROJECT_LAYER_TYPES)

        # TODO consider forcing a extent suffix or prefix
        self.lineEdit_display_name.textChanged.connect(self.text_validate)
        self.buttonBox.accepted.connect(self.save_layer)

    # TODO Probably move this somewhere and use it all over the place in layer naming
    def text_validate(self):
        """Validates text entered into the layer name to be GIS friendly"""
        text = self.lineEdit_display_name.text()
        self.validated_text = ''.join(e for e in text.replace(" ", "_") if e.isalnum() or e == "_")
        # TODO Likely remove this and don't show the layer path
        # self.lineEdit_project_layer_path.setText(os.path.join("ProjectLayers.gpkg", validated_text))
        self.lineEdit_feature_name.setText(self.validated_text)
        # TODO Don't think I need this enabled shit
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)

    def save_layer(self):
        # Get form values
        new_display_name = self.lineEdit_display_name.text()
        new_feature_name = self.lineEdit_feature_name.text()
        new_description = self.plainTextEdit_layer_description.toPlainText()

        # Create an instance of the ProjectExtent class
        new_extent_instance = ProjectExtent(new_display_name, new_feature_name, new_description)

        # Create paths
        extent_directory_path = new_extent_instance.directory_path(self.qris_project.project_path)
        extent_geopackage_path = new_extent_instance.geopackage_path(self.qris_project.project_path)
        extent_full_path = new_extent_instance.full_path(self.qris_project.project_path)

        # import or create the layer
        if self.layer_uri is not None:
            new_extent_layer = QgsVectorLayer(self.layer_uri.uri)
        else:
            new_extent_layer = QgsVectorLayer("Polygon", new_feature_name, "memory")

        # Create the geopackage and set write options
        if not os.path.exists(extent_directory_path):
            # layer for creating the geopackage
            # memory_create = QgsVectorLayer("NoGeometry", "memory_create", "memory")
            # options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
            # QgsVectorFileWriter.writeAsVectorFormat(memory_create, extent_geopackage, 'utf-8', driverName='GPKG')
            os.makedirs(extent_directory_path)
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.layerName = new_feature_name
        options.driverName = 'GPKG'
        if os.path.exists(extent_geopackage_path):
            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer

        # TODO consider whether the _out is necessary
        _out = QgsVectorFileWriter.writeAsVectorFormat(new_extent_layer, extent_geopackage_path, options)

        # Add the new feature to the project
        self.qris_project.project_extents[new_feature_name] = new_extent_instance
        # TODO double check on whether you need to call that here? or if it gets tripped somewhere else?
        # TODO Change export_project_file to write_project_xml() throughout
        self.qris_project.write_project_xml()()
        self.dataChange.emit(self.qris_project, new_display_name)
