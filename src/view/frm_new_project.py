import os
import sqlite3
from PyQt5 import QtCore, QtGui, QtWidgets
from qgis.core import QgsField, QgsVectorLayer, QgsVectorFileWriter, QgsApplication

from ..model.project import Project
from .utilities import validate_name, add_standard_form_buttons
from ..controller.new_project import NewProject

# all spatial layers
# feature class, layer name, geometry


class FrmNewProject(QtWidgets.QDialog):

    closingPlugin = QtCore.pyqtSignal()
    dataChange = QtCore.pyqtSignal(Project)

    def __init__(self, iface, root_project_folder: str, parent, project: Project = None):
        super(FrmNewProject, self).__init__(parent)
        self.setupUi()
        self.iface = iface

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

        task = NewProject(self.iface, self.txtPath.text(), self.txtName.text(), self.txtDescription.toPlainText())
        task.on_complete.connect(self.on_project_created)
        QgsApplication.taskManager().addTask(task)

    def on_project_created(self, bool):
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
