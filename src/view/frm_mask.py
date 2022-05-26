import os
import sqlite3
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QFileDialog, QDialogButtonBox, QMessageBox
from qgis.PyQt.QtCore import pyqtSignal, QVariant, QUrl, QRect, Qt
from qgis.PyQt.QtGui import QIcon, QDesktopServices, QStandardItemModel, QStandardItem
from qgis.core import Qgis, QgsFeature, QgsVectorLayer
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel

from ..QRiS.functions import create_geopackage_table
from qgis.gui import QgsDataSourceSelectDialog
from qgis.core import QgsMapLayer

from .ui.mask import Ui_Mask
from ..model.basemap import BASEMAP_PARENT_FOLDER, Basemap
from ..model.db_item import DBItemModel, DBItem, DB_MODE_IMPORT

from ..model.project import Project
from ..model.mask import Mask

<<<<<<< HEAD
# from ..processing_provider.feature_class_functions import check_geometry_type
=======
from ..processing_provider.feature_class_functions import import_mask
>>>>>>> ecac017 (stubbing mask import)


class FrmMask(QDialog, Ui_Mask):

    def __init__(self, parent, project: Project, mode: str, mask: Mask = None):

        self.qris_project = project
        self.mask = mask

        super(FrmMask, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle('Create New Mask' if self.mask is None else 'Edit Mask Properties')
        self.buttonBox.accepted.connect(super(FrmMask, self).accept)
        self.buttonBox.rejected.connect(super(FrmMask, self).reject)

        self.gridLayout.setGeometry(QRect(0, 0, self.width(), self.height()))

        self.txtName.textChanged.connect(self.on_name_changed)

        # Masks
        self.mask_types_model = DBItemModel(project.lookup_tables['mask_types'])
        self.cboType.setModel(self.mask_types_model)

        self.mode = mode
        if mode == DB_MODE_IMPORT:
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
            # if self.mode == DB_MODE_IMPORT:
            # self.qris_project.copy_raster_to_project(self.txtSourcePath().text(), mask, self.txtProjectPath.text())

            if self.mode == DB_MODE_IMPORT:
                import_mask(self.import_source_path, self.qris_project.project_file, id)

            conn.commit()
            super(FrmMask, self).accept()

        except Exception as ex:
            conn.rollback()
            if 'unique' in str(ex).lower():
                QMessageBox.warning(self, 'Duplicate Name', "A mask with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                self.txtName.setFocus()
            else:
                QMessageBox.warning(self, 'Error Saving Mask', str(ex))

    def on_name_changed(self, new_name):

        # if len(new_name) > 0:
        #     _name, ext = os.path.splitext(self.txtSourcePath.text())
        #     self.txtProjectPath.setText(os.path.join(BASIS_PARENT_FOLDER, self.qris_project.get_safe_file_name(new_name, ext)))
        # else:
        #     self.txtProjectPath.setText('')
        print('TODO')

    def browse_source(self):
        # https://qgis.org/pyqgis/master/gui/QgsDataSourceSelectDialog.html
        frm_browse = QgsDataSourceSelectDialog(parent=self, setFilterByLayerType=True, layerType=QgsMapLayer.VectorLayer)
        frm_browse.setDescription('Select a polygon dataset to import as a new mask.')

        frm_browse.exec()
        uri = frm_browse.uri()
        # TODO: check only polygon geometry
        if uri is not None and uri.isValid():

            if uri.wkbType != 3:
                QMessageBox.warning(self, 'Invalid Geometry Type', "Masks can only be of geometry type 'polygon'.")
                self.reject()

            self.txtName.setText(os.path.splitext(os.path.basename(uri.uri))[0])
            self.txtName.selectAll()
            self.import_source_path = uri.uri
        else:
            self.reject()
