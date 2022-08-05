import os
import sqlite3
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QFileDialog, QDialogButtonBox, QMessageBox
from qgis.PyQt.QtCore import pyqtSignal, QVariant, QUrl, QRect
from qgis.PyQt.QtGui import QIcon, QDesktopServices


from qgis.core import (
    QgsField,
    QgsVectorLayer,
    QgsVectorFileWriter
)

from ..model.project import Project

from .ui.new_project import Ui_NewProject

# all spatial layers
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
    ('structure_lines', 'Structure Lines', 'Linestring'),
    ('channel_unit_points', 'Channel Unit Points', 'Point'),
    ('channel_unit_polygons', 'Channel Unit Polygons', 'Polygon')
]


class FrmNewProject(QDialog, Ui_NewProject):

    closingPlugin = pyqtSignal()
    dataChange = pyqtSignal(Project)

    def __init__(self, root_project_folder: str, parent=None, project: Project = None):
        super(FrmNewProject, self).__init__(parent)
        self.setupUi(self)
        self.gridLayoutWidget.setGeometry(QRect(0, 0, self.width(), self.height()))

        # Save the original folder that the user selected so that it can be reused
        self.root_path = root_project_folder
        self.txtPath.setText(root_project_folder)
        self.project = project

        if project is None:
            # Changes to project name change the project folder location
            self.txtProjectName.textChanged.connect(self.update_project_folder)
        else:
            self.setWindowTitle('Edit Project Properties')
            self.txtProjectName.setText(project.name)
            self.txtDescription.setPlainText(project.description)

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

        if isinstance(self.project, Project):
            # Update the existing project
            conn = sqlite3.connect(self.project.project_file)
            cursor = conn.cursor()
            try:
                cursor.execute('UPDATE projects SET name = ?, description = ? WHERE id = ?', [self.txtProjectName.text(), self.txtDescription.toPlainText(), self.project.id])
                conn.commit()
                self.project.name = self.txtProjectName.text()
                self.project.description = self.txtDescription.toPlainText()
            except Exception as ex:
                conn.rollback()
                QMessageBox.warning(self, 'Error Updating Project', str(ex))
                return
        else:
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

            # Create the geopackage feature classes that will in turn cause the project geopackage to get created
            for fc_name, layer_name, geometry_type in layers:
                features_path = '{}|layername={}'.format(self.txtPath.text(), layer_name)
                create_geopackage_table(geometry_type, fc_name, self.txtPath.text(), features_path, None)

            # Run the schema DDL migrations to create lookup tables and relationships
            conn = sqlite3.connect(self.txtPath.text())
            conn.execute('PRAGMA foreign_keys = ON;')
            curs = conn.cursor()

            schema_path = os.path.join(os.path.dirname(__file__), '..', 'db', 'schema.sql')
            schema_file = open(schema_path, 'r')
            sql_commands = schema_file.read()
            curs.executescript(sql_commands)

            # Create the project
            curs.execute('INSERT INTO projects (name, description) VALUES (?, ?)', [self.txtProjectName.text(), self.txtDescription.toPlainText()])
            conn.commit()
            conn.close()
            schema_file.close()

        super(FrmNewProject, self).accept()


def create_geopackage_table(geometry_type: str, table_name: str, geopackage_path: str, full_path: str, field_tuple_list: list = None):
    """
        Creates tables in existing or new geopackages
        geometry_type (string):  NoGeometry, Polygon, Linestring, Point, etc...
        table_name (string): Name for the new table
        geopackage_path (string): full path to the geopackage i.e., dir/package.gpkg
        full_path (string): full path including the layer i.e., dir/package.gpkg|layername=layer
        field_tuple_list (list): a list of tuples as field name and QVariant field types i.e., [('my_field', QVarient.Double)]
        """
    memory_layer = QgsVectorLayer(geometry_type, "memory_layer", "memory")
    if field_tuple_list:
        fields = []
        for field_tuple in field_tuple_list:
            field = QgsField(field_tuple[0], field_tuple[1])
            fields.append(field)
        memory_layer.dataProvider().addAttributes(fields)
        memory_layer.updateFields()
    options = QgsVectorFileWriter.SaveVectorOptions()
    options.layerName = table_name
    options.driverName = 'GPKG'
    if os.path.exists(geopackage_path):
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
    QgsVectorFileWriter.writeAsVectorFormatV2(memory_layer, geopackage_path, options)


def format_layer_name(input_text):
    """Takes raw text from an input and field and returns a GIS friendly text string suitable for naming layers"""
    valid_text = ''.join(e for e in input_text.replace(" ", "_") if e.isalnum() or e == "_")
    return valid_text
