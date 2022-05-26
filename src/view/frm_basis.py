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
from ..model.basemap import BASEMAP_PARENT_FOLDER, Basemap
from ..model.db_item import DBItemModel, DBItem

from ..model.mask import load_masks, Mask


class FrmBasis(QDialog, Ui_Basis):

    def __init__(self, parent, qris_project, basis=None):

        self.qris_project = qris_project
        self.basis = basis

        super(FrmBasis, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle('Create New Basemap' if self.basis is None else 'Edit Basemap Properties')
        self.buttonBox.accepted.connect(super(FrmBasis, self).accept)
        self.buttonBox.rejected.connect(super(FrmBasis, self).reject)

        self.gridLayout.setGeometry(QRect(0, 0, self.width(), self.height()))

        self.txtName.textChanged.connect(self.on_name_changed)

        # Masks
        self.masks = self.qris_project.masks
        self.masks[0] = DBItem(0, 'None - Retain full dataset extent')
        self.masks_model = DBItemModel(self.masks)
        self.cboMask.setModel(self.masks_model)

        self.browse_source()

    def accept(self):

        if len(self.txtName.text()) < 1:
            QMessageBox.warning(self, 'Missing Basis Name', 'You must provide a basis name to continue.')
            self.txtName.setFocus()
            return()

        conn = sqlite3.connect(self.qris_project.project_file)
        try:
            curs = conn.cursor()
            description = self.txtDescription.toPlainText() if len(self.txtDescription.toPlainText()) > 0 else None
            curs.execute('INSERT INTO bases (name, path, description) VALUES (?, ?, ?)', [self.txtName.text(), self.txtProjectPath.text(), description])
            id = curs.lastrowid
            self.Basis = Basemap(id, self.txtName.text(), self.txtProjectPath.text(), description)

            mask = self.cboMask.currentData(Qt.UserRole)
            mask_path = self.qris_project.get_absolute_ath(mask.path) if mask.id > 0 else None

            # mask = self.cboMask.
            self.qris_project.copy_raster_to_project(self.txtSourcePath().text(), mask, self.txtProjectPath.text())

            conn.commit()
            super(FrmBasis, self).accept()

        except Exception as ex:
            conn.rollback()
            if 'unique' in str(ex).lower():
                QMessageBox.warning(self, 'Duplicate Name', "A basis dataset with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                self.txtName.setFocus()
            else:
                QMessageBox.warning(self, 'Error Saving Basis', str(ex))

    def on_name_changed(self, new_name):

        if len(new_name) > 0:
            _name, ext = os.path.splitext(self.txtSourcePath.text())
            self.txtProjectPath.setText(os.path.join(BASEMAP_PARENT_FOLDER, self.qris_project.get_safe_file_name(new_name, ext)))
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
