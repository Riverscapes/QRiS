import os
# from typing_extensions import ParamSpecKwargs

from osgeo import gdal

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QDialogButtonBox, QMessageBox
from qgis.PyQt.QtCore import pyqtSignal, QVariant, QDate
from qgis.core import (
    Qgis,
    QgsProject,
    QgsField,
    QgsFeature,
    QgsVectorLayer,
    QgsVectorFileWriter
)

from ..qris_project import QRiSProject

from ..QRiS.functions import create_geopackage_table

DIALOG_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'structure_type_dialog.ui'))


class StructureTypeDlg(QDialog, DIALOG_CLASS):

    closingPlugin = pyqtSignal()
    dataChange = pyqtSignal(QRiSProject, str)

    def __init__(self, qris_project):
        """Used to construct the design dialog"""
        QDialog.__init__(self, None)
        self.setupUi(self)
        self.qris_project = qris_project
        # paths to directory geopackage and tables
        self.directory_path = self.qris_project.project_designs.directory_path(self.qris_project.project_path)
        self.geopackage_path = self.qris_project.project_designs.geopackage_path(self.qris_project.project_path)
        self.structure_types_path = self.geopackage_path + '|layername=structure_types'

        # population combo boxes
        list_of_structure_mimics = ['Beaver Dam', 'Woody Debris', 'Other']
        self.comboBox_structure_mimics.addItems(list_of_structure_mimics)

        # add signals
        self.buttonBox.accepted.connect(self.save_structure_type)
        self.buttonBox.rejected.connect(self.cancel_structure_type)
        self.lineEdit_post_spacing.textChanged.connect(self.estimate_posts)
        self.lineEdit_average_length.textChanged.connect(self.estimate_posts)

        # run the post estimate
        self.estimate_posts()

    def save_structure_type(self):
        """Creates and saves a new design record to the db from the design dialog"""
        self.structure_type_layer = QgsVectorLayer(self.structure_types_path, "structure_types", "ogr")
        index_fid = self.structure_type_layer.fields().indexOf("fid")
        if self.structure_type_layer.featureCount() > 0:
            new_fid = self.structure_type_layer.maximumValue(index_fid) + 1
        else:
            new_fid = 1
        # grab the form values
        new_structure_type_name = self.lineEdit_structure_type_name.text()
        new_structure_mimics = self.comboBox_structure_mimics.currentText()
        new_construction_description = self.plainTextEdit_construction_description.toPlainText()
        new_function_description = self.plainTextEdit_function_description.toPlainText()
        # create a blank QgsFeature that copies the deployemnt table

        # TODO Add validation for only numbers
        new_post_spacing = self.lineEdit_post_spacing.text()
        new_average_length = self.lineEdit_average_length.text()
        new_average_width = self.lineEdit_average_width.text()
        new_average_height = self.lineEdit_average_height.text()

        new_structure_type_feature = QgsFeature(self.structure_type_layer.fields())
        # set the form values to the feature
        new_structure_type_feature.setAttribute("fid", new_fid)
        new_structure_type_feature.setAttribute("structure_type_name", new_structure_type_name)
        new_structure_type_feature.setAttribute("structure_mimics", new_structure_mimics)
        new_structure_type_feature.setAttribute("construction_description", new_construction_description)
        new_structure_type_feature.setAttribute("function_description", new_function_description)

        new_structure_type_feature.setAttribute("post_spacing", float(new_post_spacing))
        new_structure_type_feature.setAttribute("average_length", float(new_average_length))
        new_structure_type_feature.setAttribute("average_width", float(new_average_width))
        new_structure_type_feature.setAttribute("average_height", float(new_average_height))
        pr = self.structure_type_layer.dataProvider()
        pr.addFeatures([new_structure_type_feature])

        self.dataChange.emit(self.qris_project, None)
        self.close()

    def estimate_posts(self):
        """Validates text entered into the layer name to be GIS friendly"""
        posts = float(self.lineEdit_post_spacing.text())
        length = float(self.lineEdit_average_length.text())
        post_estimate = posts * length
        self.label_total_posts.setText(str(post_estimate))

    def cancel_structure_type(self):
        self.close()
