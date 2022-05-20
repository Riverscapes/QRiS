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

from .ui.mask import Ui_Mask
from ..model.basis import BASIS_PARENT_FOLDER, Basis
from ..model.db_item import DBItemModel, DBItem

from ..model.db_item import load_lookup_table
from ..model.mask import Mask


class FrmMask(QDialog, Ui_Mask):

    def __init__(self, parent, qris_project, basis=None):

        self.qris_project = qris_project
        self.basis = basis

        super(FrmMask, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle('Create New Mask' if self.basis is None else 'Edit Mask Properties')
        self.buttonBox.accepted.connect(super(FrmMask, self).accept)
        self.buttonBox.rejected.connect(super(FrmMask, self).reject)

        self.gridLayout.setGeometry(QRect(0, 0, self.width(), self.height()))

        self.txtName.textChanged.connect(self.on_name_changed)

        # Masks
        self.mask_types = load_lookup_table(qris_project.project_file, 'mask_types')
        self.mask_types_model = DBItemModel(self.mask_types)
        self.cboType.setModel(self.mask_types)

        self.browse_source()

    def accept(self):

        if len(self.txtName.text()) < 1:
            QMessageBox.warning(self, 'Missing Name', 'You must provide a mask name to continue.')
            self.txtName.setFocus()
            return()

        mask_type = self.cboType.currentData(Qt.UserRole)

        conn = sqlite3.connect(self.qris_project.project_file)
        try:
            curs = conn.cursor()
            description = self.txtDescription.toPlainText() if len(self.txtDescription.toPlainText()) > 0 else None
            curs.execute('INSERT INTO masks (name, project_id, mask_type_id, description) VALUES (?, ?, ?, ?)', [self.txtName.text(), self.qris_project.id, mask_type.id, description])
            id = curs.lastrowid
            self.mask = Mask(id, self.txtName.text(), mask_type, description)

            # TODO: copy vector to project
            # self.qris_project.copy_raster_to_project(self.txtSourcePath().text(), mask, self.txtProjectPath.text())

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
            self.txtProjectPath.setText(os.path.join(BASIS_PARENT_FOLDER, self.qris_project.get_safe_file_name(new_name, ext)))
        else:
            self.txtProjectPath.setText('')

    def browse_source(self):
        # https://qgis.org/pyqgis/master/gui/QgsDataSourceSelectDialog.html
        frm_browse = QgsDataSourceSelectDialog(parent=self, setFilterByLayerType=True, layerType=QgsMapLayer.VectorLayer)
        frm_browse.setDescription('Select a polygon dataset to import as a new mask.')

        frm_browse.exec()
        uri = frm_browse.uri()
        # TODO: check only polygon geometry
        if uri is not None and uri.isValid():  # and uri.wkbType == 3:
            self.txtName.setText(os.path.splitext(os.path.basename(uri.uri))[0])
            self.txtName.selectAll()
            self.txtSourcePath.setText(uri.uri)
        else:
            self.reject()
