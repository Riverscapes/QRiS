from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QFileDialog, QDialogButtonBox, QMessageBox
from qgis.PyQt.QtCore import pyqtSignal, QVariant, QUrl, QRect, Qt
from qgis.PyQt.QtGui import QIcon, QDesktopServices, QStandardItemModel, QStandardItem
from qgis.core import QgsVectorLayer

from ..model.db_item import DBItem, DBItemModel
from ..model.project import Project
from ..model.mask import Mask, insert_mask

from .ui.mask_aoi import Ui_MaskAOI

from ..gp.feature_class_functions import import_mask

import os

REGULAR_MASK_ID = 1


class FrmMaskAOI(QDialog, Ui_MaskAOI):

    def __init__(self, parent, project: Project, import_source_path: str, mask_type: DBItem, mask: Mask = None):

        self.qris_project = project
        self.mask = mask
        self.import_source_path = import_source_path
        self.mask_type = mask_type

        super(FrmMaskAOI, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle(f'Create New {mask_type.name}' if self.mask is None else f'Edit {mask_type.name} Properties')
        self.buttonBox.accepted.connect(super(FrmMaskAOI, self).accept)
        self.buttonBox.rejected.connect(super(FrmMaskAOI, self).reject)

        # The attribute picker is only visible when creating a new regular mask
        show_attribute_filter = import_source_path is not None and mask_type == project.lookup_tables['lkp_mask_types'][REGULAR_MASK_ID]
        self.lblAttribute.setVisible(show_attribute_filter)
        self.cboAttribute.setVisible(show_attribute_filter)

        if import_source_path is not None:
            self.txtName.setText(os.path.splitext(os.path.basename(import_source_path))[0])
            self.txtName.selectAll()

            if show_attribute_filter:
                vector_layer = QgsVectorLayer(import_source_path)
                self.attributes = {i: DBItem('None', i, vector_layer.attributeDisplayName(i)) for i in vector_layer.attributeList()}
                self.attribute_model = DBItemModel(self.attributes)
                self.cboAttribute.setModel(self.attribute_model)
                # self.cboAttribute.setModelColumn(1)

        if self.mask is not None:
            self.txtName.setText(mask.name)
            self.txtDescription.setPlainText(mask.description)
            self.chkAddToMap.setCheckState(Qt.Unchecked)
            self.chkAddToMap.setVisible(False)

        self.gridLayout.setGeometry(QRect(0, 0, self.width(), self.height()))
        self.txtName.setFocus()

    def accept(self):

        if len(self.txtName.text()) < 1:
            QMessageBox.warning(self, 'Missing Name', 'You must provide a mask name to continue.')
            self.txtName.setFocus()
            return

        if self.mask is not None:
            try:
                self.mask.update(self.qris_project.project_file, self.txtName.text(), self.txtDescription.toPlainText())
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QMessageBox.warning(self, 'Duplicate Name', "A mask with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QMessageBox.warning(self, 'Error Saving Mask', str(ex))
                return
        else:
            try:
                self.mask = insert_mask(self.qris_project.project_file, self.txtName.text(), self.mask_type, self.txtDescription.toPlainText())
                self.qris_project.masks[self.mask.id] = self.mask
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QMessageBox.warning(self, 'Duplicate Name', "A mask with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QMessageBox.warning(self, 'Error Saving Mask', str(ex))
                return

            if self.import_source_path is not None:
                try:

                    attributes = {self.cboAttribute.currentData(Qt.UserRole).name: 'display_label'} if self.cboAttribute.isVisible() else None
                    import_mask(self.import_source_path, self.qris_project.project_file, self.mask.id, attributes)
                except Exception as ex:
                    try:
                        self.mask.delete(self.qris_project.project_file)
                    except Exception as ex:
                        print('Error attempting to delete mask after the importing of features failed.')
                    QMessageBox.warning(self, 'Error Importing Mask Features', str(ex))
                    return

        super(FrmMaskAOI, self).accept()
