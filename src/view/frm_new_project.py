import os
import sqlite3
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QFileDialog, QDialogButtonBox, QMessageBox
from qgis.PyQt.QtCore import pyqtSignal, QVariant, QUrl, QRect
from qgis.PyQt.QtGui import QIcon, QDesktopServices
from qgis.core import Qgis, QgsFeature, QgsVectorLayer

from ..qris_project import QRiSProject
from ..QRiS.functions import create_geopackage_table

from .ui.new_project import Ui_NewProject

# feature class, layer name, geometry
layers = [
    ('mask_features', 'Mask Features', 'Polygon'),
    ('dam_crests', 'Dam Crests', 'Linestring'),
    ('dams', 'Dam Points', 'Point'),
    ('jams', 'Jam Points', 'Point'),
    ('thalwegs', 'Thalwegs', 'Linestring'),
    ('riverscape_units', 'Riverscape Units', 'Polygon'),
    ('centerlines', 'Centerlines', 'Linestring'),
    ('inundation_extents', 'Inundation Extents', 'Polygon'),
    ('valley_bottoms', 'Valley Bottoms', 'Polygon'),
    ('junctions', 'Junctions', 'Point'),
    ('geomorphic_unit_extents', 'Geomorphic Unit Extents', 'Polygon'),
    ('geomorphic_units', 'Geomorphic Unit Points', 'Point'),
    ('geomorphic_units_tier3', 'Tier 3 Geomorphic Units', 'Point'),
    ('cem_phases', 'Channel Evolution Model Stages', 'Polygon'),
    ('vegetation_extents', 'Riparian Vegetation', 'Polygon'),
    ('floodplain_accessibilities', 'Floodplain Accessibility', 'Polygon'),
    ('brat_vegetation', 'BRAT Vegetation', 'Polygon'),
    ('zoi', 'Zones of Influence', 'Polygon'),
    ('complexes', 'Complexes', 'Polygon'),
    ('structure_points', 'Structure Points', 'Point'),
    ('structure_lines', 'Structure Lines', 'Linestring')
]


class FrmNewProject(QDialog, Ui_NewProject):

    closingPlugin = pyqtSignal()
    dataChange = pyqtSignal(QRiSProject)

    def __init__(self, root_project_folder: str, parent=None):
        super(FrmNewProject, self).__init__(parent)
        self.setupUi(self)
        self.gridLayoutWidget.setGeometry(QRect(0, 0, self.width(), self.height()))

        # Save the original folder that the user selected so that it can be reused
        self.root_path = root_project_folder
        self.txtPath.setText(root_project_folder)

        self.txtProjectName.textChanged.connect(self.update_project_folder)
        # self.btnSaveFolder.clicked.connect(self.openFolderDlg)
        # self.buttonBox.accepted.connect(self.save_new_project)

        # self.buttonBox.button(QDialogButtonBox.Ok).

    def update_project_folder(self):

        text = self.txtProjectName.text().strip()
        clean_name = ''.join(e for e in text.replace(" ", "_") if e.isalnum() or e == "_")

        if len(clean_name) > 0:
            self.project_folder = os.path.join(self.root_path, clean_name, 'qris_project.gpkg')
            self.txtPath.setText(self.project_folder)

    # def save_new_project(self):

    def accept(self):

        # Verify project name
        if len(self.txtProjectName.text().strip()) < 1:
            QMessageBox.warning(self, 'Missing Project Name',
                                'You must provide a project name to continue.')
            self.txtProjectName.setFocus()
            return

        # Saves the new project from the dialog and creates the master geopackage
        # Create new project directory
        self.project_dir = os.path.dirname(self.txtPath.text())
        if (os.path.isdir(self.project_dir)):
            QMessageBox.warning(self, 'Directory Already Exists',
                                'The specified directory already exists. Choose a different root directory or change the project name.')
            return

        os.makedirs(self.project_dir)
        # qris_project = QRiSProject(self.project_name)
        # qris_project.project_path = self.project_folder

        # Create the geopackage and spatial tables

        for fc_name, layer_name, geometry_type in layers:
            features_path = '{}|layername={}'.format(self.txtPath.text(), layer_name)
            create_geopackage_table(geometry_type, fc_name, self.txtPath.text(), features_path, None)

        # Run the schema DDL to create lookup tables and relationships
        conn = sqlite3.connect(self.txtPath.text())
        conn.execute('PRAGMA foreign_keys = ON;')
        curs = conn.cursor()
        sql_path = os.path.dirname(os.path.dirname(__file__))
        schema_path = os.path.join(sql_path, "sql", "schema.sql")
        schema_qry_string = open(schema_path, 'r').read()
        curs.executescript(schema_qry_string)
        # design schema
        schema_path = os.path.join(sql_path, "sql", "schema_design.sql")
        schema_qry_string = open(schema_path, 'r').read()
        curs.executescript(schema_qry_string)

        # Create the project
        curs.execute('INSERT INTO projects (name) VALUES (?)', [self.txtProjectName.text()])

        conn.commit()
        conn.close()

        # Create .qris
        # qris_project_file = os.path.join(self.project_folder, "project.qris")
        # qris_project.write_project_xml(qris_project_file)
        # self.dataChange.emit(self.txtPath.text())

        super(FrmNewProject, self).accept()
