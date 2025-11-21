import os
import re
import json

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import pyqtSlot
from qgis.core import Qgis, QgsApplication, QgsVectorLayer
from qgis.gui import QgisInterface

from .utilities import validate_name_unique, validate_name, add_standard_form_buttons
from .widgets.metadata import MetadataWidget

from ..model.scratch_vector import ScratchVector, insert_scratch_vector, scratch_gpkg_path, get_unique_scratch_fc_name
from ..model.db_item import DBItemModel, DBItem
from ..model.project import Project

from ..gp.feature_class_functions import layer_path_parser
from ..gp.import_feature_class import ImportFeatureClass
from ..gp.import_temp_layer import ImportMapLayer


class FrmScratchVector(QtWidgets.QDialog):

    def __init__(self, parent, iface: QgisInterface, qris_project: Project, import_source_path: str, vector_type_id: int, scratch_vector: ScratchVector = None):

        self.iface = iface
        self.qris_project = qris_project
        self.vector_type_id = vector_type_id
        self.scratch_vector = scratch_vector
        self.import_source_path = import_source_path
        self.metadata = None

        super(FrmScratchVector, self).__init__(parent)
        metadata_json = json.dumps(scratch_vector.metadata) if scratch_vector is not None else None
        self.metadata_widget = MetadataWidget(self, metadata_json)
        self.setupUi()

        self.vector_types_model = DBItemModel(qris_project.lookup_tables['lkp_scratch_vector_types'])
        self.cboVectorType.setModel(self.vector_types_model)

        self.setWindowTitle('Import Existing Context Vector' if self.scratch_vector is None else 'Edit Context Vector Properties')

        if scratch_vector is None:

            self.txtName.textChanged.connect(self.on_name_changed)
            self.txtSourcePath.textChanged.connect(self.on_name_changed)

            if isinstance(self.import_source_path, QgsVectorLayer):
                self.layer_name = import_source_path.name()
                self.txtSourcePath.setText(f'Temporary Layer: {self.layer_name}')
            else:
                _path, self.layer_name, *_ = layer_path_parser(self.import_source_path)
                self.txtSourcePath.setText(self.import_source_path)

            self.txtName.setText(self.layer_name)

            # Masks (filtered to just AOI)
            self.clipping_masks = {id: aoi for id, aoi in self.qris_project.aois.items()}
            no_clipping = DBItem('None', 0, 'None - Retain full dataset extent')
            self.clipping_masks[0] = no_clipping
            self.masks_model = DBItemModel(self.clipping_masks)
            self.cboMask.setModel(self.masks_model)
            # Default to no mask clipping
            self.cboMask.setCurrentIndex(self.masks_model.getItemIndex(no_clipping))
        else:
            self.txtName.setText(scratch_vector.name)
            self.txtDescription.setPlainText(scratch_vector.description)

            self.lblSourcePath.setVisible(False)
            self.txtSourcePath.setVisible(False)
            self.lblMask.setVisible(False)
            self.cboMask.setVisible(False)

            self.txtProjectPath.setText(qris_project.get_absolute_path(scratch_vector.gpkg_path))

            self.chkAddToMap.setVisible(False)
            self.chkAddToMap.setCheckState(QtCore.Qt.Unchecked)

        self.txtName.selectAll()

    def accept(self):

        if not validate_name(self, self.txtName):
            return

        metadata_json = self.metadata_widget.get_json()
        self.metadata = json.loads(metadata_json) if metadata_json is not None else None

        if self.scratch_vector is not None:
            try:
                self.scratch_vector.update(self.qris_project.project_file, self.txtName.text(), self.txtDescription.toPlainText(), self.metadata)
                self.qris_project.project_changed.emit()
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "A context vector with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Error Saving Context Vector', str(ex))
                return

            super().accept()

        else:
            # Inserting a new item. Check name uniqueness before copying the dataset
            if validate_name_unique(self.qris_project.project_file, 'scratch_vectors', 'name', self.txtName.text()) is False:
                QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "A context vector with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                self.txtName.setFocus()
                return

            try:
                # Ensure that the scratch feature class name doesn't exist in scratch geopackage
                # Do this because an error might have left a lingering feature class table etc
                _out_path, self.fc_name, _layer_id = layer_path_parser(self.txtProjectPath.text())

                clip_mask = None
                clip_item = self.cboMask.currentData(QtCore.Qt.UserRole)
                if clip_item is not None:
                    if clip_item.id > 0:        
                        clip_mask = ('sample_frame_features', 'sample_frame_id', clip_item.id)

                if isinstance(self.import_source_path, QgsVectorLayer):
                    task = ImportMapLayer(self.import_source_path, self.txtProjectPath.text(), clip_mask=clip_mask, proj_gpkg=self.qris_project.project_file)
                else:
                    task = ImportFeatureClass(self.import_source_path, self.txtProjectPath.text(), clip_mask=clip_mask, proj_gpkg=self.qris_project.project_file, explode_geometries=False)
                # Call the run command directly during development to run the process synchronousely.
                # DO NOT DEPLOY WITH run() UNCOMMENTED
                # result = task.run()
                # self.on_copy_complete(result)
                
                # Call the addTask() method to run the process asynchronously. Deploy with this method uncommented.
                self.buttonBox.setEnabled(False)
                task.import_complete.connect(self.on_copy_complete)
                QgsApplication.taskManager().addTask(task)

            except Exception as ex:
                self.buttonBox.setEnabled(True)
                self.scratch_vector = None
                QtWidgets.QMessageBox.warning(self, 'Error Importing Context Vector', str(ex))
                return

    @pyqtSlot(bool)
    def on_copy_complete(self, result: bool):

        if result is True:
            self.iface.messageBar().pushMessage('Feature Class Copy Complete.', f"{self.txtProjectPath.text()} saved successfully.", level=Qgis.Info, duration=5)

            try:
                self.scratch_vector = insert_scratch_vector(
                    self.qris_project.project_file,
                    self.txtName.text(),
                    self.fc_name,
                    scratch_gpkg_path(self.qris_project.project_file),
                    self.cboVectorType.currentData(QtCore.Qt.UserRole).id,
                    self.txtDescription.toPlainText(),
                    self.metadata)
                self.qris_project.add_db_item(self.scratch_vector)

            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "A context vector with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Error Saving Context Vector', str(ex))
                return

            super(FrmScratchVector, self).accept()
        else:
            self.iface.messageBar().pushMessage('Feature Class Copy Error', 'Review the QGIS log.', level=Qgis.Critical, duration=5)
            self.buttonBox.setEnabled(True)

    def on_name_changed(self, new_name):

        clean_name = re.sub('[^A-Za-z0-9]+', '', self.txtName.text())
        unique_name = get_unique_scratch_fc_name(self.qris_project.project_file, clean_name)
        if len(clean_name) > 0:
            self.txtProjectPath.setText(f'{scratch_gpkg_path(self.qris_project.project_file)}|layername={unique_name}')
        else:
            self.txtProjectPath.setText('')

    def setupUi(self):

        self.resize(500, 400)
        self.setMinimumSize(400, 300)

        # Top level layout must include parent. Widgets added to this layout do not need parent.
        self.vert = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vert)
        self.tabs = QtWidgets.QTabWidget()
        self.vert.addWidget(self.tabs)

        self.grid = QtWidgets.QGridLayout()

        self.lblName = QtWidgets.QLabel('Name')
        self.grid.addWidget(self.lblName, 0, 0, 1, 1)

        self.txtName = QtWidgets.QLineEdit()
        self.txtName.setToolTip('Name of the context layer')
        self.txtName.setMaxLength(255)
        self.grid.addWidget(self.txtName, 0, 1, 1, 1)

        self.lblSourcePath = QtWidgets.QLabel('Source Path')
        self.grid.addWidget(self.lblSourcePath, 1, 0, 1, 1)

        self.txtSourcePath = QtWidgets.QLineEdit()
        self.txtSourcePath.setReadOnly(True)
        self.grid.addWidget(self.txtSourcePath, 1, 1, 1, 1)

        self.lblScratchLayerType = QtWidgets.QLabel('Context Layer Type')
        self.grid.addWidget(self.lblScratchLayerType, 2, 0, 1, 1)

        self.cboVectorType = QtWidgets.QComboBox()
        self.cboVectorType.setToolTip('Type of context layer')
        self.grid.addWidget(self.cboVectorType, 2, 1, 1, 1)

        self.lblProjectPath = QtWidgets.QLabel('Project Path')
        self.grid.addWidget(self.lblProjectPath, 3, 0, 1, 1)

        self.txtProjectPath = QtWidgets.QLineEdit()
        self.txtProjectPath.setReadOnly(True)
        self.grid.addWidget(self.txtProjectPath, 3, 1, 1, 1)

        self.lblMask = QtWidgets.QLabel('Clip to AOI')
        self.grid.addWidget(self.lblMask, 4, 0, 1, 1)

        self.cboMask = QtWidgets.QComboBox()
        self.cboMask.setToolTip('Optionally clip the context layer to an Area of Interest')
        self.grid.addWidget(self.cboMask, 4, 1, 1, 1)

        self.lblDescription = QtWidgets.QLabel('Description')
        self.lblDescription.setAlignment(QtCore.Qt.AlignTop)
        self.grid.addWidget(self.lblDescription, 5, 0, 1, 1)

        self.txtDescription = QtWidgets.QPlainTextEdit()
        self.grid.addWidget(self.txtDescription, 5, 1, 1, 1)

        self.tabProperties = QtWidgets.QWidget()
        self.tabs.addTab(self.tabProperties, 'Basic Properties')
        self.tabProperties.setLayout(self.grid)

        # Metadata Tab
        self.tabs.addTab(self.metadata_widget, 'Metadata')

        self.chkAddToMap = QtWidgets.QCheckBox('Add to Map')
        self.chkAddToMap.setChecked(True)
        self.grid.addWidget(self.chkAddToMap, 6, 1, 1, 1)

        self.vert.addLayout(add_standard_form_buttons(self, 'context/vector-layers'))
