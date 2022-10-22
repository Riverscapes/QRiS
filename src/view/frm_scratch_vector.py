import os
import re
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import pyqtSlot
from qgis.core import Qgis, QgsApplication

from ..model.scratch_vector import ScratchVector, insert_scratch_vector, scratch_gpkg_path, get_unique_scratch_fc_name
from ..model.db_item import DBItemModel, DBItem
from ..model.project import Project
from ..model.mask import AOI_MASK_TYPE_ID

from .utilities import validate_name_unique, validate_name, add_standard_form_buttons

from ..gp.copy_feature_class import CopyFeatureClass


class FrmScratchVector(QtWidgets.QDialog):

    def __init__(self, parent, iface, project: Project, import_source_path: str, vector_type_id: int, scratch_vector: ScratchVector = None):

        self.iface = iface
        self.project = project
        self.vector_type_id = vector_type_id
        self.scratch_vector = scratch_vector

        super(FrmScratchVector, self).__init__(parent)
        self.setupUi()

        self.vector_types_model = DBItemModel(project.lookup_tables['lkp_scratch_vector_types'])
        self.cboVectorType.setModel(self.vector_types_model)

        self.setWindowTitle('Create New Scratch Space Vector' if self.scratch_vector is None else 'Edit Scratch Space Vector Properties')

        if scratch_vector is None:

            self.txtName.textChanged.connect(self.on_name_changed)
            self.txtSourcePath.textChanged.connect(self.on_name_changed)
            self.txtSourcePath.setText(import_source_path)
            self.txtName.setText(os.path.splitext(os.path.basename(import_source_path))[0])

            # Masks (filtered to just AOI)
            self.masks = {id: mask for id, mask in self.project.masks.items() if mask.mask_type.id == AOI_MASK_TYPE_ID}
            no_clipping = DBItem('None', 0, 'None - Retain full dataset extent')
            self.masks[0] = no_clipping
            self.masks_model = DBItemModel(self.masks)
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

            self.txtProjectPath.setText(project.get_absolute_path(scratch_vector.gpkg_path))

            self.chkAddToMap.setVisible(False)
            self.chkAddToMap.setCheckState(QtCore.Qt.Unchecked)

        self.txtName.selectAll()

    def accept(self):

        if not validate_name(self, self.txtName):
            return

        if self.scratch_vector is not None:
            try:
                self.scratch_vector.update(self.project.project_file, self.txtName.text(), self.txtDescription.toPlainText())
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "A scratch vector with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Error Saving Scratch Vector', str(ex))
                return

            super().accept()

        else:
            # Inserting a new item. Check name uniqueness before copying the dataset
            if validate_name_unique(self.project.project_file, 'scratch_vectors', 'name', self.txtName.text()) is False:
                QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "A scratch vector with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                self.txtName.setFocus()
                return

            try:
                mask = self.cboMask.currentData(QtCore.Qt.UserRole)
                mask_tuple = (self.project.project_file, mask.id) if mask.id > 0 else None

                # Ensure that the scratch feature class name doesn't exist in scratch geopackage
                # Do this because an error might have left a lingering feature class table etc
                self.fc_name = get_unique_scratch_fc_name(self.project.project_file, self.txtName.text())

                copy_vector = CopyFeatureClass(self.txtSourcePath.text(), None, os.path.dirname(self.txtProjectPath.text()), self.fc_name)
                copy_vector.copy_complete.connect(self.on_copy_complete)

                # Call the run command directly during development to run the process synchronousely.
                # DO NOT DEPLOY WITH run() UNCOMMENTED
                # self.on_copy_complete(copy_vector.run())
                # return

                # Call the addTask() method to run the process asynchronously. Deploy with this method uncommented.
                self.buttonBox.setEnabled(False)
                QgsApplication.taskManager().addTask(copy_vector)

            except Exception as ex:
                self.buttonBox.setEnabled(True)

                # try:
                #     self.raster.delete(self.project.project_file)
                # except Exception as ex:
                #     print('Error attempting to delete basemap after the importing raster failed.')
                self.scratch_vector = None
                QtWidgets.QMessageBox.warning(self, 'Error Importing Basemap', str(ex))
                return

    @pyqtSlot(bool)
    def on_copy_complete(self, result: bool):

        if result is True:
            self.iface.messageBar().pushMessage('Feature Class Copy Complete.', 'self.txt.', level=Qgis.Info, duration=5)

            try:
                self.scratch_vector = insert_scratch_vector(
                    self.project.project_file,
                    self.txtName.text(),
                    self.fc_name,
                    os.path.dirname(self.txtProjectPath.text()),
                    self.cboVectorType.currentData(QtCore.Qt.UserRole).id,
                    self.txtDescription.toPlainText())
                self.project.scratch_vectors[self.scratch_vector.id] = self.scratch_vector

            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "A scratch vector with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Error Saving Basemap', str(ex))
                return

            super(FrmScratchVector, self).accept()
        else:
            self.iface.messageBar().pushMessage('Raster Copy Error', 'Review the QGIS log.', level=Qgis.Critical, duration=5)
            self.buttonBox.setEnabled(True)

    def on_name_changed(self, new_name):

        clean_name = re.sub('[^A-Za-z0-9]+', '', self.txtName.text())
        if len(clean_name) > 0:
            self.txtProjectPath.setText(os.path.join(scratch_gpkg_path(self.project.project_file), clean_name))
        else:
            self.txtProjectPath.setText('')

    def setupUi(self):

        self.resize(500, 400)
        self.setMinimumSize(400, 300)

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

        self.lblSourcePath = QtWidgets.QLabel()
        self.lblSourcePath.setText('Source Path')
        self.grid.addWidget(self.lblSourcePath, 1, 0, 1, 1)

        self.txtSourcePath = QtWidgets.QLineEdit()
        self.txtSourcePath.setReadOnly(True)
        self.grid.addWidget(self.txtSourcePath, 1, 1, 1, 1)

        self.lblRasterType = QtWidgets.QLabel()
        self.lblRasterType.setText('Raster Type')
        self.grid.addWidget(self.lblRasterType, 2, 0, 1, 1)

        self.cboVectorType = QtWidgets.QComboBox()
        self.grid.addWidget(self.cboVectorType, 2, 1, 1, 1)

        self.lblProjectPath = QtWidgets.QLabel()
        self.lblProjectPath.setText('Project Path')
        self.grid.addWidget(self.lblProjectPath, 3, 0, 1, 1)

        self.txtProjectPath = QtWidgets.QLineEdit()
        self.txtProjectPath.setReadOnly(True)
        self.grid.addWidget(self.txtProjectPath, 3, 1, 1, 1)

        self.lblMask = QtWidgets.QLabel()
        self.lblMask.setText('Clip to Mask')
        self.grid.addWidget(self.lblMask, 4, 0, 1, 1)

        self.cboMask = QtWidgets.QComboBox()
        self.grid.addWidget(self.cboMask, 4, 1, 1, 1)

        self.lblDescription = QtWidgets.QLabel()
        self.lblDescription.setText('Description')
        self.grid.addWidget(self.lblDescription, 5, 0, 1, 1)

        self.txtDescription = QtWidgets.QPlainTextEdit()
        self.grid.addWidget(self.txtDescription, 5, 1, 1, 1)

        self.chkAddToMap = QtWidgets.QCheckBox()
        self.chkAddToMap.setText('Add to Map')
        self.chkAddToMap.setChecked(True)
        self.grid.addWidget(self.chkAddToMap, 6, 1, 1, 1)

        self.vert.addLayout(add_standard_form_buttons(self, 'basemaps'))
