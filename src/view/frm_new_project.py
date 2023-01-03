import os
import uuid
import sqlite3
from PyQt5 import QtCore, QtGui, QtWidgets
from qgis.core import QgsField, QgsVectorLayer, QgsVectorFileWriter

from ..model.project import Project
from .utilities import validate_name, add_standard_form_buttons

# all spatial layers
# feature class, layer name, geometry
layers = [
    ('aoi_features', 'AOI Features', 'Polygon'),
    ('mask_features', 'Mask Features', 'Polygon'),
    ('dam_crests', 'Dam Crests', 'Linestring'),
    ('dams', 'Dam Points', 'Point'),
    ('jams', 'Jam Points', 'Point'),
    ('thalwegs', 'Thalwegs', 'Linestring'),
    ('active_extents', 'Active Extents', 'Polygon'),
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
    ('channel_unit_polygons', 'Channel Unit Polygons', 'Polygon'),
    ('brat_cis', 'BRAT CIS', 'Point'),
    ('pour_points', 'Pour Points', 'Point'),
    ('catchments', 'Catchments', 'Polygon'),
    ('stream_gages', 'Stream Gages', 'Point')
]


class FrmNewProject(QtWidgets.QDialog):

    closingPlugin = QtCore.pyqtSignal()
    dataChange = QtCore.pyqtSignal(Project)

    def __init__(self, root_project_folder: str, parent, project: Project = None):
        super(FrmNewProject, self).__init__(parent)
        self.setupUi()

        # Save the original folder that the user selected so that it can be reused
        self.root_path = root_project_folder
        self.txtPath.setText(root_project_folder)
        self.project = project

        if project is None:
            self.setWindowTitle('Create New Project')
            # Changes to project name change the project folder location
            self.txtName.textChanged.connect(self.update_project_folder)
        else:
            self.setWindowTitle('Edit Project Properties')
            self.txtName.setText(project.name)
            self.txtDescription.setPlainText(project.description)

    def update_project_folder(self):

        text = self.txtName.text().strip()
        clean_name = ''.join(e for e in text.replace(" ", "_") if e.isalnum() or e == "_")

        if len(clean_name) > 0:
            self.project_folder = os.path.join(self.root_path, clean_name, 'qris_project.gpkg')
            self.txtPath.setText(self.project_folder)

    # def save_new_project(self):

    def accept(self):

        if not validate_name(self, self.txtName):
            return

        if isinstance(self.project, Project):
            # Update the existing project
            conn = sqlite3.connect(self.project.project_file)
            cursor = conn.cursor()
            try:
                cursor.execute('UPDATE projects SET name = ?, description = ? WHERE id = ?', [self.txtName.text(), self.txtDescription.toPlainText(), self.project.id])
                conn.commit()
                self.project.name = self.txtName.text()
                self.project.description = self.txtDescription.toPlainText()
            except Exception as ex:
                conn.rollback()
                QtWidgets.QMessageBox.warning(self, 'Error Updating Project', str(ex))
                return
        else:
            # Saves the new project from the dialog and creates the master geopackage
            # Create new project directory
            self.project_dir = os.path.dirname(self.txtPath.text())
            if (os.path.isdir(self.project_dir)):
                QtWidgets.QMessageBox.warning(self, 'Directory Already Exists',
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
            description = self.txtDescription.toPlainText() if len(self.txtDescription.toPlainText()) > 0 else None
            curs.execute('INSERT INTO projects (name, description, map_guid) VALUES (?, ?, ?)', [self.txtName.text(), description, str(uuid.uuid4())])
            conn.commit()
            conn.close()
            schema_file.close()

        super(FrmNewProject, self).accept()

    def setupUi(self):

        self.resize(500, 300)
        self.setMinimumSize(300, 200)

        # Top level layout must include parent. Widgets added to this layout do not need parent.
        self.vert = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vert)

        self.grid = QtWidgets.QGridLayout()
        self.vert.addLayout(self.grid)

        self.lblName = QtWidgets.QLabel()
        self.lblName.setText('Name')
        self.grid.addWidget(self.lblName, 0, 0, 1, 1)

        self.txtName = QtWidgets.QLineEdit()
        self.txtName.setMaxLength(255)
        self.grid.addWidget(self.txtName, 0, 1, 1, 1)

        self.lblPath = QtWidgets.QLabel()
        self.lblPath.setText('Project Path')
        self.grid.addWidget(self.lblPath, 1, 0, 1, 1)

        self.txtPath = QtWidgets.QLineEdit()
        self.txtPath.setReadOnly(True)
        self.grid.addWidget(self.txtPath, 1, 1, 1, 1)

        self.lblDescription = QtWidgets.QLabel()
        self.lblDescription.setText('Description')
        self.grid.addWidget(self.lblDescription, 2, 0, 1, 1)

        self.txtDescription = QtWidgets.QPlainTextEdit()
        self.grid.addWidget(self.txtDescription, 2, 1, 1, 1)

        self.vert.addLayout(add_standard_form_buttons(self, 'projects'))


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
    QgsVectorFileWriter.writeAsVectorFormat(memory_layer, geopackage_path, options)


def format_layer_name(input_text):
    """Takes raw text from an input and field and returns a GIS friendly text string suitable for naming layers"""
    valid_text = ''.join(e for e in input_text.replace(" ", "_") if e.isalnum() or e == "_")
    return valid_text
