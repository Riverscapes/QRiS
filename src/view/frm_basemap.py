import os
from PyQt5 import QtCore, QtGui, QtWidgets

from ..model.basemap import BASEMAP_PARENT_FOLDER, Raster, insert_raster, RASTER_TYPE_BASEMAP
from ..model.db_item import DBItemModel, DBItem
from ..model.project import Project
from ..model.mask import AOI_MASK_TYPE_ID

from ..gp.feature_class_functions import copy_raster_to_project


class FrmRaster(QtWidgets.QDialog):

    def __init__(self, parent, project: Project, import_source_path: str, raster_type_id: int, raster: Raster = None):

        self.qris_project = project
        self.raster_type_id = raster_type_id
        self.raster = raster

        super(FrmRaster, self).__init__(parent)
        self.setupUi()

        self.raster_types_model = DBItemModel(project.lookup_tables['lkp_raster_types'])
        self.cboRasterType.setModel(self.raster_types_model)
        self.cboRasterType.setCurrentIndex(self.raster_types_model.getItemIndexById(raster_type_id))
        self.cboRasterType.setEnabled(raster_type_id != RASTER_TYPE_BASEMAP)

        if raster_type_id == RASTER_TYPE_BASEMAP:
            self.setWindowTitle('Create New Basemap' if self.raster is None else 'Edit Basemap Properties')
        else:
            self.setWindowTitle('Create New Scratch Space Raster' if self.raster is None else 'Edit Scratch Space Raster Properties')

        if raster is None:
            self.txtName.textChanged.connect(self.on_name_changed)
            self.txtSourcePath.textChanged.connect(self.on_name_changed)
            self.txtSourcePath.setText(import_source_path)
            self.txtName.setText(os.path.splitext(os.path.basename(import_source_path))[0])

            # Masks (filtered to just AOI)
            self.masks = {id: mask for id, mask in self.qris_project.masks.items() if mask.mask_type.id == AOI_MASK_TYPE_ID}
            self.masks[0] = DBItem('None', 0, 'None - Retain full dataset extent')
            self.masks_model = DBItemModel(self.masks)
            self.cboMask.setModel(self.masks_model)
        else:
            self.txtName.setText(raster.name)
            self.txtDescription.setPlainText(raster.description)

            self.lblSourcePath.setVisible(False)
            self.txtSourcePath.setVisible(False)
            self.lblClipToMask.setVisible(False)
            self.cboMask.setVisible(False)

            self.txtProjectPath.setText(project.get_absolute_path(raster.path))

            self.chkAddToMap.setVisible(False)
            self.chkAddToMap.setCheckState(QtCore.Qt.Unchecked)

        self.txtName.selectAll()

    def accept(self):

        if len(self.txtName.text()) < 1:
            QtWidgets.QtWidgets.QMessageBox.warning(self, 'Missing Basis Name', 'You must provide a basis name to continue.')
            self.txtName.setFocus()
            return()

        if self.raster is not None:
            try:
                self.raster.update(self.qris_project.project_file, self.txtName.text(), self.txtDescription.toPlainText())
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "A basemap with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Error Saving Basemap', str(ex))
                return
        else:
            try:
                self.raster = insert_raster(self.qris_project.project_file, self.txtName.text(), self.txtProjectPath.text(), self.raster_type_id, self.txtDescription.toPlainText())
                self.qris_project.rasters[self.raster.id] = self.raster
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "A basemap with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Error Saving Basemap', str(ex))
                return

            try:
                mask = self.cboMask.currentData(QtCore.Qt.UserRole)
                mask_tuple = (self.qris_project.project_file, mask.id) if mask.id > 0 else None

                project_path = self.qris_project.get_absolute_path(self.txtProjectPath.text())

                if not os.path.isdir(os.path.dirname(project_path)):
                    os.makedirs(os.path.dirname(project_path))

                copy_raster_to_project(self.txtSourcePath.text(), mask_tuple, project_path)
            except Exception as ex:
                try:
                    self.raster.delete(self.qris_project.project_file)
                except Exception as ex:
                    print('Error attempting to delete basemap after the importing raster failed.')
                self.raster = None
                QtWidgets.QMessageBox.warning(self, 'Error Importing Basemap', str(ex))
                return

        super(FrmRaster, self).accept()

    def on_name_changed(self, new_name):
        project_name = self.txtName.text().strip()
        clean_name = ''.join(e for e in project_name.replace(" ", "_") if e.isalnum() or e == "_")

        if len(project_name) > 0:
            _name, ext = os.path.splitext(self.txtSourcePath.text())
            self.txtProjectPath.setText(os.path.join(BASEMAP_PARENT_FOLDER, self.qris_project.get_safe_file_name(clean_name, ext)))
        else:
            self.txtProjectPath.setText('')

    def setupUi(self):

        self.resize(500, 400)
        self.setMinimumSize(400, 300)

        self.vert = QtWidgets.QVBoxLayout()
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

        self.cboRasterType = QtWidgets.QComboBox()
        self.grid.addWidget(self.cboRasterType, 2, 1, 1, 1)

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

        self.horiz = QtWidgets.QHBoxLayout()
        self.vert.addLayout(self.horiz)

        self.cmdHelp = QtWidgets.QPushButton()
        self.cmdHelp.setText('Help')
        self.horiz.addWidget(self.cmdHelp)

        self.spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horiz.addItem(self.spacerItem)

        self.buttonBox = QtWidgets.QDialogButtonBox()
        self.horiz.addWidget(self.buttonBox)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
