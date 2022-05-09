import os
import sqlite3
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QFileDialog, QDialogButtonBox
from qgis.PyQt.QtCore import pyqtSignal, QVariant, QUrl
from qgis.PyQt.QtGui import QIcon, QDesktopServices
from qgis.core import Qgis, QgsFeature, QgsVectorLayer

from ..qris_project import QRiSProject
from ..QRiS.functions import create_geopackage_table


DIALOG_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'new_project_dialog.ui'))


class NewProjectDialog(QDialog, DIALOG_CLASS):

    closingPlugin = pyqtSignal()
    dataChange = pyqtSignal(QRiSProject)

    def __init__(self, parent=None):
        """Constructor."""
        QDialog.__init__(self, parent)
        self.setupUi(self)

        self.save_folder = ""
        self.project_name = ""
        self.clean_name = ""

        self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)

        self.txtProjectName.textChanged.connect(self.text_validate)
        self.btnSaveFolder.clicked.connect(self.openFolderDlg)
        self.buttonBox.accepted.connect(self.save_new_project)

        self.show()

    def text_validate(self):
        text = self.txtProjectName.text()

        formatted_text = ''.join(e for e in text.replace(" ", "_") if e.isalnum() or e == "_")
        self.project_name = text
        self.clean_name = formatted_text
        self.updateProjectFolder()

    def openFolderDlg(self):

        dialog_return = QFileDialog.getExistingDirectory(self, "Save Project Folder")

        if dialog_return is not None:
            self.save_folder = dialog_return
            self.updateProjectFolder()

    def updateProjectFolder(self):

        if self.save_folder is not "" and self.clean_name is not "":
            self.project_folder = os.path.join(self.save_folder, self.clean_name)
            self.txtSaveFolder.setText(self.project_folder)
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)
        else:
            self.txtSaveFolder.setText(None)
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)

    def save_new_project(self):
        """Saves the new project from the dialog and creates the master geopackage"""
        # Create new dir
        os.makedirs(self.project_folder)
        qris_project = QRiSProject(self.project_name)
        qris_project.project_path = self.project_folder

        # Create the geopackage and spatial tables
        # TODO make sure you aren't overwriting anything
        self.qris_geopackage = os.path.join(self.project_folder, "qris_project.gpkg")
        if not os.path.exists(self.qris_geopackage):
            mask_features_path = self.qris_geopackage + "|layername=mask_features"
            create_geopackage_table('Polygon', 'mask_features', self.qris_geopackage, mask_features_path,
                                    [
                                        ('name', QVariant.String)
                                    ])

            # and now run the schema ddl
            conn = sqlite3.connect(self.qris_geopackage)
            conn.execute('PRAGMA foreign_keys = ON;')
            curs = conn.cursor()
            sql_path = os.path.dirname(os.path.dirname(__file__))
            schema_path = os.path.join(sql_path, "sql", "schema.sql")
            schema_qry_string = open(schema_path, 'r').read()
            curs.executescript(schema_qry_string)
            conn.commit()
            conn.close()

        # Create .qris
        qris_project_file = os.path.join(self.project_folder, "project.qris")
        qris_project.write_project_xml(qris_project_file)
        self.dataChange.emit(qris_project)
