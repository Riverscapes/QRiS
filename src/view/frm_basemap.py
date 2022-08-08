import os

from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QFileDialog, QDialogButtonBox, QMessageBox
from qgis.PyQt.QtCore import pyqtSignal, QVariant, QUrl, QRect, Qt
from qgis.PyQt.QtGui import QIcon, QDesktopServices, QStandardItemModel, QStandardItem

from .ui.basis import Ui_Basis
from ..model.basemap import BASEMAP_PARENT_FOLDER, Basemap, insert_basemap
from ..model.db_item import DBItemModel, DBItem
from ..model.project import Project

from ..gp.feature_class_functions import copy_raster_to_project


class FrmBasemap(QDialog, Ui_Basis):

    def __init__(self, parent, qris_project: Project, import_source_path: str, basemap: Basemap = None):

        self.qris_project = qris_project
        self.basemap = basemap

        super(FrmBasemap, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle('Create New Basemap' if self.basemap is None else 'Edit Basemap Properties')
        self.buttonBox.accepted.connect(super(FrmBasemap, self).accept)
        self.buttonBox.rejected.connect(super(FrmBasemap, self).reject)

        self.gridLayout.setGeometry(QRect(0, 0, self.width(), self.height()))

        if basemap is None:
            self.txtName.textChanged.connect(self.on_name_changed)
            self.txtSourcePath.textChanged.connect(self.on_name_changed)
            self.txtSourcePath.setText(import_source_path)
            self.txtName.setText(os.path.splitext(os.path.basename(import_source_path))[0])

            # Masks
            self.masks = self.qris_project.masks
            self.masks[0] = DBItem('None', 0, 'None - Retain full dataset extent')
            self.masks_model = DBItemModel(self.masks)
            self.cboMask.setModel(self.masks_model)
        else:
            self.txtName.setText(basemap.name)
            self.txtDescription.setPlainText(basemap.description)

            self.lblSourcePath.setVisible(False)
            self.txtSourcePath.setVisible(False)
            self.lblProjectPath.setVisible(False)
            self.txtProjectPath.setVisible(False)
            self.lblClipToMask.setVisible(False)
            self.cboMask.setVisible(False)

            self.chkAddToMap.setCheckState(Qt.Unchecked)

        self.txtName.selectAll()

    def accept(self):

        if len(self.txtName.text()) < 1:
            QMessageBox.warning(self, 'Missing Basis Name', 'You must provide a basis name to continue.')
            self.txtName.setFocus()
            return()

        if self.basemap is not None:
            try:
                self.basemap.update(self.qris_project.project_file, self.txtName.text(), self.txtDescription.toPlainText())
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QMessageBox.warning(self, 'Duplicate Name', "A basemap with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QMessageBox.warning(self, 'Error Saving Basemap', str(ex))
                return
        else:
            try:
                self.basemap = insert_basemap(self.qris_project.project_file, self.txtName.text(), self.txtProjectPath.text(), self.txtDescription.toPlainText())
                self.qris_project.basemaps[self.basemap.id] = self.basemap
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QMessageBox.warning(self, 'Duplicate Name', "A basemap with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QMessageBox.warning(self, 'Error Saving Basemap', str(ex))
                return

            try:
                mask = self.cboMask.currentData(Qt.UserRole)
                mask_tuple = (self.qris_project.project_file, mask.id) if mask.id > 0 else None

                project_path = self.qris_project.get_absolute_path(self.txtProjectPath.text())

                if not os.path.isdir(os.path.dirname(project_path)):
                    os.makedirs(os.path.dirname(project_path))

                copy_raster_to_project(self.txtSourcePath.text(), mask_tuple, project_path)
            except Exception as ex:
                try:
                    self.basemap.delete(self.qris_project.project_file)
                except Exception as ex:
                    print('Error attempting to delete basemap after the importing raster failed.')
                self.basemap = None
                QMessageBox.warning(self, 'Error Importing Basemap', str(ex))
                return

        super(FrmBasemap, self).accept()

    def on_name_changed(self, new_name):

        project_name = self.txtName.text()
        if len(project_name) > 0:
            _name, ext = os.path.splitext(self.txtSourcePath.text())
            self.txtProjectPath.setText(os.path.join(BASEMAP_PARENT_FOLDER, self.qris_project.get_safe_file_name(project_name, ext)))
        else:
            self.txtProjectPath.setText('')
