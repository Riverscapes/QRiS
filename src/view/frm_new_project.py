import os
import json
import uuid
import sqlite3

from PyQt5 import QtCore, QtGui, QtWidgets
from qgis.utils import iface
from qgis.core import QgsApplication

from ..QRiS.path_utilities import parse_posix_path
from ..model.project import Project, project_layers
from .utilities import validate_name, add_standard_form_buttons
from ..gp.new_project import NewProjectTask
from .widgets.metadata import MetadataWidget


class FrmNewProject(QtWidgets.QDialog):

    closingPlugin = QtCore.pyqtSignal()
    dataChange = QtCore.pyqtSignal(Project)
    newProjectComplete = QtCore.pyqtSignal(str, str)

    def __init__(self, root_project_folder: str, parent, project: Project = None):
        super(FrmNewProject, self).__init__(parent)

        metadata_json = json.dumps(project.metadata) if project is not None else None
        
        # Pull the tags out of metadata if the exist
        self.tags = []
        if metadata_json is not None:
            metadata = json.loads(metadata_json)
            if 'tags' in metadata:
                self.tags = metadata['tags']
                # Remove the tags from the metadata so that they are not duplicated
                del metadata['tags']
                metadata_json = json.dumps(metadata)
        
        self.metadata_widget = MetadataWidget(self, metadata_json)
        self.setupUi()

        # Save the original folder that the user selected so that it can be reused
        self.root_path = parse_posix_path(root_project_folder)
        self.txtPath.setText(root_project_folder)
        self.project = project

        if self.tags is not None:
            self.txtTags.setText(', '.join(self.tags))

        if project is None:
            self.setWindowTitle('Create New Project')
            # Changes to project name change the project folder location
            self.txtName.textChanged.connect(self.update_project_folder)
        else:
            self.setWindowTitle('Edit Project Properties')
            self.txtName.setText(project.name)
            self.txtDescription.setPlainText(project.description)

        self.txtName.setFocus()

    def update_project_folder(self):

        text = self.txtName.text().strip()
        clean_name = ''.join(e for e in text.replace(" ", "_") if e.isalnum() or e == "_")

        if len(clean_name) > 0:
            self.project_folder = parse_posix_path(os.path.join(self.root_path, clean_name, f'{clean_name}.gpkg'))
            self.txtPath.setText(self.project_folder)

    def get_tags(self):
        """Returns a list of tags from the tags text box"""
        tags = self.txtTags.text().split(',')
        return [tag.strip() for tag in tags]

    def accept(self):

        if not validate_name(self, self.txtName):
            return

        if not self.metadata_widget.validate():
            return

        metadata_json = self.metadata_widget.get_json()
        if self.tags is not None:
            metadata_json = json.dumps({'tags': self.get_tags(), **json.loads(metadata_json)})
        metadata = json.loads(metadata_json) if metadata_json is not None else None

        if isinstance(self.project, Project):
            # Update the existing project
            conn = sqlite3.connect(self.project.project_file)
            cursor = conn.cursor()
            try:
                cursor.execute('UPDATE projects SET name = ?, description = ?, metadata = ? WHERE id = ?', [self.txtName.text(), self.txtDescription.toPlainText(), metadata_json, self.project.id])
                conn.commit()
                self.project.name = self.txtName.text()
                self.project.description = self.txtDescription.toPlainText()
                self.project.metadata = metadata
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

            new_project_task = NewProjectTask(self.txtName.text(), self.txtPath.text(), self.txtDescription.toPlainText(), str(uuid.uuid4()), project_layers, metadata)
            new_project_task.project_complete.connect(self.on_complete)
            new_project_task.project_create_layers.connect(self.on_creating_layers)
            new_project_task.project_create_schema.connect(self.on_creating_schema)

            QgsApplication.taskManager().addTask(new_project_task)
        super(FrmNewProject, self).accept()

    def on_complete(self, result):
        if result is True:
            iface.mainWindow().statusBar().showMessage(None)
            self.newProjectComplete.emit(self.project_dir, self.txtPath.text())

    def on_creating_layers(self, layer_number, count_layers):
        iface.mainWindow().statusBar().showMessage('New QRIS Project: creating layer {} of {} layers in project.'.format(layer_number, count_layers))

    def on_creating_schema(self):
        iface.mainWindow().statusBar().showMessage('New QRIS Project: applying project schema (this may take several moments...)')

    def setupUi(self):

        self.resize(500, 300)
        self.setMinimumSize(300, 200)

        # Top level layout must include parent. Widgets added to this layout do not need parent.
        self.vert = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vert)
        self.tabs = QtWidgets.QTabWidget()
        self.vert.addWidget(self.tabs)

        self.grid = QtWidgets.QGridLayout()

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

        self.lblTags = QtWidgets.QLabel("Tags")
        self.grid.addWidget(self.lblTags, 2, 0, 1, 1)

        self.txtTags = QtWidgets.QLineEdit()
        self.toolTip = "Comma separated list of tags for the project"
        self.txtTags.setToolTip(self.toolTip)
        self.grid.addWidget(self.txtTags, 2, 1, 1, 1)

        self.lblDescription = QtWidgets.QLabel()
        self.lblDescription.setText('Description')
        self.grid.addWidget(self.lblDescription, 3, 0, 1, 1)

        self.txtDescription = QtWidgets.QPlainTextEdit()
        self.grid.addWidget(self.txtDescription, 3, 1, 1, 1)

        self.tabProperties = QtWidgets.QWidget()
        self.tabs.addTab(self.tabProperties, 'Project Properties')
        self.tabProperties.setLayout(self.grid)

        # metadata Tab
        self.tabs.addTab(self.metadata_widget, 'Metadata')

        self.vert.addLayout(add_standard_form_buttons(self, 'projects'))


def format_layer_name(input_text):
    """Takes raw text from an input and field and returns a GIS friendly text string suitable for naming layers"""
    valid_text = ''.join(e for e in input_text.replace(" ", "_") if e.isalnum() or e == "_")
    return valid_text
