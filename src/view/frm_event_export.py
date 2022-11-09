
import os
from PyQt5 import QtCore, QtGui, QtWidgets
from qgis.core import QgsApplication

from ..model.db_item import DBItemModel
from ..model.project import Project
from ..model.event import Event
from ..model.method import Method
from ..model.basemap import BASEMAP_PARENT_FOLDER

from .utilities import validate_name, add_standard_form_buttons

from ..controller.event_export import EventExportTask
from ..gp.copy_raster import CopyRaster

LAST_EXPORT_FOLDER = 'LAST_EXPORT_FOLDER'


class FrmEventExport(QtWidgets.QDialog):

    def __init__(self, iface, parent, project: Project, event: Event, organization: str, app_name: str):
        super().__init__(parent)
        self.setupUi()

        self.setWindowTitle('Export Data Capture Event to Riverscapes Project')
        self.iface = iface
        self.project = project
        self.the_event = event

        # Only used to save and retrieve settings
        self.organization = organization
        self.app_name = app_name

        self.txtName.setText(event.name)

        self.project_types = {method.id: method for method in project.methods.values() if method.rs_project_type_name is not None}
        self.project_type_model = DBItemModel(self.project_types)
        self.cboProjectType.setModel(self.project_type_model)

        settings = QtCore.QSettings(organization, app_name)
        self.set_output_folder(os.path.dirname(settings.value(LAST_EXPORT_FOLDER)) if settings.value(LAST_EXPORT_FOLDER) is not None else None)

    def set_output_folder(self, output_folder):

        if output_folder is not None and len(output_folder) > 0 and os.path.isdir(output_folder):
            self.txtPath.setText(os.path.join(output_folder, 'project.rs.xml'))

    def accept(self):

        if not validate_name(self, self.txtName):
            return

        if len(self.txtPath.text()) < 1:
            QtWidgets.QMessageBox.warning(self, 'Missing Output Path', 'You must select an output path to continue.')
            return

        # Ensure the output directory is empty
        if os.path.isdir(os.path.dirname(self.txtPath.text())):
            if len(os.listdir(os.path.dirname(self.txtPath.text()))) != 0:
                QtWidgets.QMessageBox.warning(self, 'Output Path Not Empty', 'The output path already contains files. You must choose an empty directory to continue.')
                return

        try:
            method: Method = self.cboProjectType.currentData()

            # Build a list of asynchronous tasks to copy the raster basemaps
            basemap_raster_paths = {}
            basemap_copy_tasks = {}
            for basemap in self.the_event.basemaps:
                new_raster_path = os.path.join(os.path.dirname(self.txtPath.text()), BASEMAP_PARENT_FOLDER, os.path.basename(basemap.path))
                basemap_copy_tasks[basemap.id] = CopyRaster(basemap.path, None, new_raster_path)
                basemap_raster_paths[basemap.id] = new_raster_path

            task = EventExportTask(self.iface, self.project.project_file, self.the_event.id, self.txtName.text(), self.txtPath.text(), method.id, basemap_raster_paths)
            task.on_complete.connect(self.on_export_complete)

            # Add the raster copy subtasks
            [task.addSubTask(raster_copy_task) for raster_copy_task in basemap_copy_tasks.values()]

            # Call the run command directly during development to run the process synchronousely.
            # DO NOT DEPLOY WITH run() UNCOMMENTED
            self.on_complete(task.run())
            return

            # Call the addTask() method to run the process asynchronously. Deploy with this method uncommented.
            QgsApplication.taskManager().addTask(task)

        except Exception as ex:
            # TODO log the export
            print('handle exception')

    @ QtCore.pyqtSlot(bool)
    def on_export_complete(self, result: bool):

        if result is True:
            # Update the last used export folder
            settings = QtCore.QSettings(self.organization, self.app_name)
            settings.setValue(LAST_EXPORT_FOLDER, os.path.dirname(self.txtPath.text()))
            settings.sync()

        # TODO: open the project in QRAVE
        super().accept()

    @QtCore.pyqtSlot(bool)
    def on_complete(self, result: bool):
        print('here')

    def on_browse_output_folder(self):

        existing_path = None
        if len(self.txtPath.text()) > 0 and os.path.isdir(os.path.dirname(os.path.dirname(self.txtPath.text()))):
            existing_path = os.path.dirname(self.txtPath.text())

        dialog_return = QtWidgets.QFileDialog.getExistingDirectory(self, 'QRiS Event Export Folder', existing_path)
        if len(dialog_return) > 0:
            self.set_output_folder(dialog_return)

    def setupUi(self):

        self.resize(500, 200)
        self.setMinimumSize(500, 200)

        # Top level layout must include parent. Widgets added to this layout do not need parent.
        self.vert = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vert)

        self.grid = QtWidgets.QGridLayout(self)
        self.vert.addLayout(self.grid)

        self.lblName = QtWidgets.QLabel(self)
        self.lblName.setText('Name')
        self.grid.addWidget(self.lblName, 0, 0, 1, 1)

        self.txtName = QtWidgets.QLineEdit(self)
        self.txtName.setMaxLength(255)
        self.grid.addWidget(self.txtName, 0, 1, 1, 1)

        self.lblProjectType = QtWidgets.QLabel(self)
        self.lblProjectType.setText('Project Type')
        self.grid.addWidget(self.lblProjectType, 1, 0, 1, 1)

        self.cboProjectType = QtWidgets.QComboBox(self)
        self.grid.addWidget(self.cboProjectType, 1, 1, 1, 1)

        self.lblPath = QtWidgets.QLabel(self)
        self.lblPath.setText('Export Path')
        self.grid.addWidget(self.lblPath, 2, 0, 1, 1)

        self.txtPath = QtWidgets.QLineEdit(self)
        self.txtPath.setReadOnly(True)
        self.grid.addWidget(self.txtPath, 2, 1, 1, 1)

        self.cmdBrowse = QtWidgets.QPushButton(self)
        self.cmdBrowse.setIcon(QtGui.QIcon(':/plugins/qris_toolbar/folder'))
        self.cmdBrowse.clicked.connect(self.on_browse_output_folder)
        self.grid.addWidget(self.cmdBrowse, 2, 2, 1, 1)

        verticalSpacer = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.vert.addItem(verticalSpacer)

        self.vert.addLayout(add_standard_form_buttons(self, 'events'))
