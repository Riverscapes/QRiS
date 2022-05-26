import os
import sqlite3
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QFileDialog, QDialogButtonBox, QMessageBox
from qgis.PyQt.QtCore import pyqtSignal, QVariant, QUrl, QRect, Qt
from qgis.PyQt.QtGui import QIcon, QDesktopServices, QStandardItemModel, QStandardItem
from qgis.core import Qgis, QgsFeature, QgsVectorLayer
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel

from ..qris_project import QRiSProject
from ..QRiS.functions import create_geopackage_table
from qgis.gui import QgsDataSourceSelectDialog
from qgis.core import QgsMapLayer

from .ui.basis import Ui_Basis
from ..model.basemap import BASEMAP_PARENT_FOLDER, Basemap, insert_basemap
from ..model.db_item import DBItemModel, DBItem
from ..model.project import Project

from ..model.mask import load_masks, Mask

from ..processing_provider.feature_class_functions import copy_raster_to_project


class FrmBasemap(QDialog, Ui_Basis):

    def __init__(self, parent, qris_project: Project, basis=None):

        self.qris_project = qris_project
        self.basis = basis

        super(FrmBasemap, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle('Create New Basemap' if self.basis is None else 'Edit Basemap Properties')
        self.buttonBox.accepted.connect(super(FrmBasemap, self).accept)
        self.buttonBox.rejected.connect(super(FrmBasemap, self).reject)

        self.gridLayout.setGeometry(QRect(0, 0, self.width(), self.height()))

        self.txtName.textChanged.connect(self.on_name_changed)
        self.txtSourcePath.textChanged.connect(self.on_name_changed)

        # Masks
        self.masks = self.qris_project.masks
        self.masks[0] = DBItem('None', 0, 'None - Retain full dataset extent')
        self.masks_model = DBItemModel(self.masks)
        self.cboMask.setModel(self.masks_model)

        self.browse_source()

    def accept(self):

        if len(self.txtName.text()) < 1:
            QMessageBox.warning(self, 'Missing Basis Name', 'You must provide a basis name to continue.')
            self.txtName.setFocus()
            return()

        self.basemap = None
        try:
            self.basemap = insert_basemap(self.qris_project.project_file, self.txtName.text(), self.txtProjectPath.text(), self.txtDescription.toPlainText())
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

    def browse_source(self):
        # https://qgis.org/pyqgis/master/gui/QgsDataSourceSelectDialog.html
        frm_browse = QgsDataSourceSelectDialog(parent=self, setFilterByLayerType=True, layerType=QgsMapLayer.RasterLayer)
        frm_browse.setDescription('Select a raster dataset to import as a new basis dataset.')
        # frm_browse.setLayerTypeFilter(layerType)

        frm_browse.exec()
        uri = frm_browse.uri()
        if uri is not None and uri.isValid():  # and uri.wkbType == 3:
            self.txtName.setText(os.path.splitext(os.path.basename(uri.uri))[0])
            self.txtName.selectAll()
            self.txtSourcePath.setText(uri.uri)
        else:
            self.reject()
