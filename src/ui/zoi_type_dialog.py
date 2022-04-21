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
    os.path.dirname(__file__), 'zoi_type_dialog.ui'))


class ZoiTypeDlg(QDialog, DIALOG_CLASS):

    closingPlugin = pyqtSignal()
    dataChange = pyqtSignal(QRiSProject, str)

    def __init__(self, qris_project):
        """Used to construct the zoi type dialog"""
        QDialog.__init__(self, None)
        self.setupUi(self)
        self.qris_project = qris_project
        # paths to directory geopackage and tables
        self.directory_path = self.qris_project.project_designs.directory_path(self.qris_project.project_path)
        self.geopackage_path = self.qris_project.project_designs.geopackage_path(self.qris_project.project_path)
        self.zoi_types_path = self.geopackage_path + '|layername=zoi_types'

        # add signals
        self.buttonBox.accepted.connect(self.save_zoi_type)
        self.buttonBox.rejected.connect(self.cancel_zoi_type)

    def save_zoi_type(self):
        """Creates and saves a zoi type record to the db"""
        self.zoi_type_layer = QgsVectorLayer(self.zoi_types_path, "zoi_types", "ogr")
        index_fid = self.zoi_type_layer.fields().indexOf("fid")
        if self.zoi_type_layer.featureCount() > 0:
            new_fid = self.zoi_type_layer.maximumValue(index_fid) + 1
        else:
            new_fid = 1
        # grab the form values
        new_zoi_type_name = self.lineEdit_zoi_type_name.text()
        new_zoi_type_description = self.plainTextEdit_zoi_type_description.toPlainText()

        new_zoi_type_feature = QgsFeature(self.zoi_type_layer.fields())
        new_zoi_type_feature.setAttribute("fid", new_fid)
        new_zoi_type_feature.setAttribute("name", new_zoi_type_name)
        new_zoi_type_feature.setAttribute("description", new_zoi_type_description)

        pr = self.zoi_type_layer.dataProvider()
        pr.addFeatures([new_zoi_type_feature])

        self.dataChange.emit(self.qris_project, None)
        self.close()

    def cancel_zoi_type(self):
        self.close()
