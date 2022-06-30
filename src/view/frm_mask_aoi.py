import os
from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QFileDialog, QDialogButtonBox, QMessageBox
from qgis.PyQt.QtCore import pyqtSignal, QVariant, QUrl, QRect, Qt
from qgis.PyQt.QtGui import QIcon, QDesktopServices, QStandardItemModel, QStandardItem
from qgis.core import Qgis, QgsFeature, QgsVectorLayer
from PyQt5.QtSql import QSqlDatabase, QSqlTableModel

from ..model.db_item import DBItem, DBItemModel
from ..model.project import Project
from ..model.mask import Mask, insert_mask

from .ui.mask_aoi import Ui_MaskAOI

from ..processing_provider.feature_class_functions import import_mask


class FrmMaskAOI(QDialog, Ui_MaskAOI):

    def __init__(self, parent, project: Project, import_source_path: str, mask: Mask = None):

        self.qris_project = project
        self.mask = mask
        self.import_source_path = import_source_path

        super(FrmMaskAOI, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle('Create New Area Of Interest Mask' if self.mask is None else 'Edit Area of Interest Mask Properties')
        self.buttonBox.accepted.connect(super(FrmMaskAOI, self).accept)
        self.buttonBox.rejected.connect(super(FrmMaskAOI, self).reject)

        if import_source_path is not None:
            self.txtName.setText(os.path.splitext(os.path.basename(import_source_path))[0])
            self.txtName.selectAll()

        if self.mask is not None:
            self.txtName.setText(mask.name)
            self.txtDescription.setPlainText(mask.description)
            self.chkAddToMap.setCheckState(Qt.Unchecked)

        self.gridLayout.setGeometry(QRect(0, 0, self.width(), self.height()))
        self.txtName.setFocus()

    def accept(self):

        if len(self.txtName.text()) < 1:
            QMessageBox.warning(self, 'Missing Name', 'You must provide a mask name to continue.')
            self.txtName.setFocus()
            return

        if self.mask is not None:
            try:
                self.mask.update(self.qris_project.project_file, self.txtName.text(), self.qris_project.lookup_tables['lkp_mask_types'][3], self.txtDescription.toPlainText())
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QMessageBox.warning(self, 'Duplicate Name', "A mask with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QMessageBox.warning(self, 'Error Saving Mask', str(ex))
                return
        else:
            try:
                self.mask = insert_mask(self.qris_project.project_file, self.txtName.text(), self.qris_project.lookup_tables['lkp_mask_types'][3], self.txtDescription.toPlainText())
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QMessageBox.warning(self, 'Duplicate Name', "A mask with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QMessageBox.warning(self, 'Error Saving Mask', str(ex))
                return

            if self.import_source_path is not None:
                try:
                    import_mask(self.import_source_path, self.qris_project.project_file, self.mask.id)
                except Exception as ex:
                    try:
                        self.mask.delete(self.qris_project.project_file)
                    except Exception as ex:
                        print('Error attempting to delete mask after the importing of features failed.')
                    QMessageBox.warning(self, 'Error Importing Mask Features', str(ex))
                    return

        super(FrmMaskAOI, self).accept()
