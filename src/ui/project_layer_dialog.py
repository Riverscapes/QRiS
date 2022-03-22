import os
from PyQt5.QtWidgets import QMessageBox

from osgeo import gdal

from qgis import processing

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QDialogButtonBox
from qgis.PyQt.QtCore import pyqtSignal
from qgis.core import (
    Qgis,
    QgsVectorLayer,
    QgsVectorFileWriter)

from ..qris_project import QRiSProject, ProjectVectorLayer, ProjectRasterLayer

from ..QRiS.functions import format_layer_name


DIALOG_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'project_layer_dialog.ui'))


class ProjectLayerDlg(QDialog, DIALOG_CLASS):

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
        self.lineEdit_import_layer.setStyleSheet(background_color)
        self.lineEdit_feature_name.setStyleSheet(background_color)

        # Add layer values to fields
        self.lineEdit_import_layer.setText(self.layer_uri.uri)
        self.lineEdit_display_name.setText(self.layer_uri.name)

        self.set_valid_layer_name()
        self.lineEdit_display_name.textChanged.connect(self.set_valid_layer_name)

        # setup the clip combobox
        extent_layer_list = []
        for extent in self.qris_project.project_extents.values():
            extent_layer_list.append(extent.display_name)
        self.comboBox_clip_extent.addItems(extent_layer_list)

        # Turn on the save layer button
        self.buttonBox.accepted.connect(self.save_layer)

    # TODO Probably move this somewhere and use it all over the place in layer naming
    def set_valid_layer_name(self):
        """Sets GIS friendly layername"""
        text = self.lineEdit_display_name.text()
        self.validated_text = format_layer_name(text)
        # TODO Likely remove this and don't show the layer path
        # self.lineEdit_project_layer_path.setText(os.path.join("ProjectLayers.gpkg", validated_text))
        self.lineEdit_feature_name.setText(self.validated_text)
        # TODO Don't think I need this enabled shit
        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)

    def save_layer(self):
        """Saves the imported layer and clips it by a specified extent"""
        # Get form values
        new_display_name = self.lineEdit_display_name.text()
        new_feature_name = self.lineEdit_feature_name.text()
        new_description = self.plainTextEdit_layer_description.toPlainText()
        clip_extent_name = self.comboBox_clip_extent.currentText()

        # Create an instance of the ProjectExtent class
        new_vector_instance = ProjectVectorLayer(new_display_name, new_feature_name, new_description)

        # Create paths
        vector_directory_path = new_vector_instance.directory_path(self.qris_project.project_path)
        vector_geopackage_path = new_vector_instance.geopackage_path(self.qris_project.project_path)
        # TODO create rastor paths

        # import or create the layer
        if self.layer_uri is not None:
            new_vector_layer = QgsVectorLayer(self.layer_uri.uri)
        else:
            # TODO hmmmm...this shouldn't be possible here. consider removing later
            QMessageBox.information(None, "No Layer to Import", "Please select a valid layer to import")
            return

        # CLIP THE FEATURE
        # get the extent feature by value
        clip_extent_feature_name = ''
        for key, value in self.qris_project.project_extents.items():
            if value.display_name == clip_extent_name:
                clip_extent_feature_name = key

        extent_instance = self.qris_project.project_extents[clip_extent_feature_name]
        extent_path = extent_instance.full_path(self.qris_project.project_path)
        # reference the extent layer
        extent_layer = QgsVectorLayer(extent_path, 'clip_layer', 'ogr')

        # clip the layer
        new_layer_clipped = self.clip_layer(new_vector_layer, extent_layer)

        # Create the geopackage and set write options
        if not os.path.exists(vector_directory_path):
            os.makedirs(vector_directory_path)
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.layerName = new_feature_name
        options.driverName = 'GPKG'
        if os.path.exists(vector_geopackage_path):
            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
        QgsVectorFileWriter.writeAsVectorFormat(new_layer_clipped, vector_geopackage_path, options)

        # Add the new feature to the project vector dictionary
        self.qris_project.project_vector_layers[new_feature_name] = new_vector_instance
        # TODO double check on whether you need to call the write_project_xml here? or if it gets tripped somewhere else?
        self.qris_project.write_project_xml()
        self.dataChange.emit(self.qris_project, new_display_name)

    def clip_layer(self, input_layer, mask_layer):
        """Applies a clip to the imported layer based on the selected project extent layer"""
        p_clipped_layer = processing.run("native:clip",
                                         {'INPUT': input_layer,
                                          'OVERLAY': mask_layer,
                                          'OUTPUT': 'TEMPORARY_OUTPUT'})

        clipped_layer = p_clipped_layer['OUTPUT']
        return clipped_layer
