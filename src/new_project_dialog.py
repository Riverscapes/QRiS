import os
import json
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QFileDialog, QDialogButtonBox
from qgis.PyQt.QtCore import pyqtSignal, QUrl
from qgis.PyQt.QtGui import QIcon, QDesktopServices
from qgis.core import Qgis

from .ript_project import RiptProject

DIALOG_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui', 'ript_new_project.ui'))


class NewProjectDialog(QDialog, DIALOG_CLASS):

    closingPlugin = pyqtSignal()
    dataChange = pyqtSignal(RiptProject)

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

        # TODO refactor this into seperate classes

        # Create new dir
        os.makedirs(self.project_folder)

        project = RiptProject(self.project_name)

        # Create .ript
        ript_project_file = os.path.join(self.project_folder, "project.ript")

        project.export_project_file(ript_project_file)

        self.dataChange.emit(project)

        # Create riverscapes.rs.xml
        #ript_rs_project_file = os.path.join(self.project_folder, "project.rs.xml")
