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

DIALOG_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'phase_dialog.ui'))


class PhaseDlg(QDialog, DIALOG_CLASS):

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
        self.phase_path = self.geopackage_path + '|layername=phases'

        # populate combo boxes
        conn = sqlite3.connect(self.geopackage_path)
        curs = conn.cursor()
        curs.execute('SELECT * FROM lkp_phase_action')
        actions = curs.fetchall()
        conn.close()
        for action in actions:
            self.comboBox_primary_action.addItem(action[1], action[0])

        # add signals to buttons
        self.buttonBox.accepted.connect(self.save_phase)
        self.buttonBox.rejected.connect(self.close_dialog)

    def save_phase(self):
        """Creates and saves a new design record to the db from the design dialog"""
        self.phase_layer = QgsVectorLayer(self.phase_path, "phases", "ogr")
        index_fid = self.phase_layer.fields().indexOf("fid")
        if self.phase_layer.featureCount() > 0:
            new_fid = self.phase_layer.maximumValue(index_fid) + 1
        else:
            new_fid = 1
        # grab the form values
        new_phase_name = self.lineEdit_phase_name.text()
        new_primary_action = self.comboBox_primary_action.currentData()
        new_implementation_date = self.dateEdit_implementation_date.date()
        new_phase_description = self.plainTextEdit_phase_description.toPlainText()

        # create a blank QgsFeature that copies the deployemnt table
        new_phase_feature = QgsFeature(self.phase_layer.fields())
        # set the form values to the feature
        new_phase_feature.setAttribute("fid", new_fid)
        new_phase_feature.setAttribute("name", new_phase_name)
        new_phase_feature.setAttribute("primary_action_id", new_primary_action)
        new_phase_feature.setAttribute("implementation_date", new_implementation_date)
        new_phase_feature.setAttribute("description", new_phase_description)

        pr = self.phase_layer.dataProvider()
        pr.addFeatures([new_phase_feature])

        self.dataChange.emit(self.qris_project, None)
        self.close()

    def close_dialog(self):
        self.close()
