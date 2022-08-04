from qgis.PyQt.QtWidgets import QDialog, QDialogButtonBox, QFileDialog, QDialogButtonBox, QMessageBox
from qgis.PyQt.QtCore import pyqtSignal, QVariant, QUrl, QRect, Qt
from qgis.PyQt.QtGui import QIcon, QDesktopServices, QStandardItemModel, QStandardItem

from ..model.db_item import DBItemModel
from ..model.project import Project
from ..model.mask import Mask, insert_mask

from .ui.mask_attribute import Ui_MaskAttribute

from ..gp.feature_class_functions import import_mask


class FrmMaskAttribute(QDialog, Ui_MaskAttribute):

    def __init__(self, parent, project: Project, import_source_path: str, mask: Mask = None):

        self.qris_project = project
        self.mask = mask
        self.import_source_path = import_source_path

        super(FrmMaskAttribute, self).__init__(parent)
        self.setupUi(self)
        self.setWindowTitle('Create New Mask' if self.mask is None else 'Edit Mask Properties')
        self.buttonBox.accepted.connect(super(FrmMaskAttribute, self).accept)
        self.buttonBox.rejected.connect(super(FrmMaskAttribute, self).reject)

        if import_source_path is not None:
            self.txtName.setText(os.path.splitext(os.path.basename(import_source_path))[0])
            self.txtName.selectAll()

        self.gridLayout.setGeometry(QRect(0, 0, self.width(), self.height()))

        # Masks
        self.mask_types_model = DBItemModel(project.lookup_tables['mask_types'])
        self.cboType.setModel(self.mask_types_model)

        self.txtName.setFocus()

    def accept(self):

        if len(self.txtName.text()) < 1:
            QMessageBox.warning(self, 'Missing Name', 'You must provide a mask name to continue.')
            self.txtName.setFocus()
            return()

        mask_type = self.cboType.currentData(Qt.UserRole)

        self.mask = None
        try:
            self.mask = insert_mask(self.qris_project.project_file, self.txtName.text(), mask_type, self.txtDescription.toPlainText())
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

        super(FrmMaskAttribute, self).accept()
