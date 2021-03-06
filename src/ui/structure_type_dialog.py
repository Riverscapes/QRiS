import os
import sqlite3

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

        # population combo box
        conn = sqlite3.connect(self.geopackage_path)
        curs = conn.cursor()
        curs.execute('SELECT * FROM lkp_structure_mimics')
        mimics = curs.fetchall()
        conn.close()
        for mimic in mimics:
            self.comboBox_structure_mimics.addItem(mimic[1], mimic[0])

        # add signals
        self.buttonBox.accepted.connect(self.save_structure_type)
        self.buttonBox.rejected.connect(self.cancel_structure_type)

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
        new_structure_mimics = self.comboBox_structure_mimics.currentData()
        new_construction_description = self.plainTextEdit_construction_description.toPlainText()
        new_function_description = self.plainTextEdit_function_description.toPlainText()

        new_typical_posts = self.lineEdit_typical_posts.text()
        new_typical_length = self.lineEdit_typical_length.text()
        new_typical_width = self.lineEdit_typical_width.text()
        new_typical_height = self.lineEdit_typical_height.text()

        new_structure_type_feature = QgsFeature(self.structure_type_layer.fields())
        new_structure_type_feature.setAttribute("fid", new_fid)
        new_structure_type_feature.setAttribute("name", new_structure_type_name)
        new_structure_type_feature.setAttribute("mimics_id", new_structure_mimics)
        new_structure_type_feature.setAttribute("construction_description", new_construction_description)
        new_structure_type_feature.setAttribute("function_description", new_function_description)

        new_structure_type_feature.setAttribute("typical_posts", new_typical_posts)
        new_structure_type_feature.setAttribute("typical_length", new_typical_length)
        new_structure_type_feature.setAttribute("typical_width", new_typical_width)
        new_structure_type_feature.setAttribute("typical_height", new_typical_height)
        pr = self.structure_type_layer.dataProvider()
        pr.addFeatures([new_structure_type_feature])

        self.dataChange.emit(self.qris_project, None)
        self.close()

    def cancel_structure_type(self):
        self.close()
