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
from ..QRiS.functions import format_layer_name

DIALOG_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'project_extent_dialog.ui'))


class ProjectExtentDlg(QDialog, DIALOG_CLASS):

    closingPlugin = pyqtSignal()
    dataChange = pyqtSignal(QRiSProject, str)

    def __init__(self, layer_uri, qris_project):
        """Constructor."""
        QDialog.__init__(self, None)
        self.setupUi(self)

        self.layer_uri = layer_uri
        self.qris_project = qris_project

        # Add any styling
        background_color = 'background-color: silver;'
        self.lineEdit_import_layer_path.setStyleSheet(background_color)
        self.lineEdit_feature_name.setStyleSheet(background_color)

        if self.layer_uri is not None:
            self.lineEdit_import_layer_path.setText(self.layer_uri.uri)
            self.lineEdit_display_name.setText(self.layer_uri.name)
        else:
            self.lineEdit_import_layer_path.setText("Create New Layer")

        self.set_valid_layername()

        # TODO consider forcing a extent suffix or prefix
        self.lineEdit_display_name.textChanged.connect(self.set_valid_layername)
        self.buttonBox.accepted.connect(self.save_layer)

    # TODO Probably move this somewhere and use it all over the place in layer naming
    def set_valid_layername(self):
        """Validates text entered into the layer name to be GIS friendly"""
        text = self.lineEdit_display_name.text()
        self.validated_text = format_layer_name(text)
        # TODO Likely remove this and don't show the layer path
        # self.lineEdit_project_layer_path.setText(os.path.join("ProjectLayers.gpkg", validated_text))
        self.lineEdit_feature_name.setText(self.validated_text)
        # TODO Don't think I need this enabled shit
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)

    def save_layer(self):
        # TODO move these up to the init method
        # Get form values
        new_display_name = self.lineEdit_display_name.text()
        new_feature_name = self.lineEdit_feature_name.text()
        new_description = self.plainTextEdit_layer_description.toPlainText()

        # Create an instance of the ProjectExtent class
        new_extent_instance = ProjectExtent(new_display_name, new_feature_name, new_description)

        # Create paths
        extent_directory_path = new_extent_instance.directory_path(self.qris_project.project_path)
        extent_geopackage_path = new_extent_instance.geopackage_path(self.qris_project.project_path)

        # import or create the layer
        if self.layer_uri is not None:
            new_extent_layer = QgsVectorLayer(self.layer_uri.uri)
        else:
            new_extent_layer = QgsVectorLayer("Polygon", new_feature_name, "memory")

        # Create the geopackage and set write options
        if not os.path.exists(extent_directory_path):
            os.makedirs(extent_directory_path)
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.layerName = new_feature_name
        options.driverName = 'GPKG'
        if os.path.exists(extent_geopackage_path):
            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
        QgsVectorFileWriter.writeAsVectorFormatV2(new_extent_layer, extent_geopackage_path, options)

        # Add the new feature to the project
        self.qris_project.project_extents[new_feature_name] = new_extent_instance
        # TODO double check on whether you need to call that here? or if it gets tripped somewhere else?
        self.qris_project.write_project_xml()
        self.dataChange.emit(self.qris_project, new_display_name)
