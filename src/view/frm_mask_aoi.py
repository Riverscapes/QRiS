import os
from PyQt5 import QtCore, QtGui, QtWidgets
from qgis.core import QgsVectorLayer

from ..model.db_item import DBItem, DBItemModel
from ..model.project import Project
from ..model.mask import Mask, insert_mask, REGULAR_MASK_TYPE_ID

from ..gp.feature_class_functions import import_mask
from .utilities import validate_name, add_standard_form_buttons


class FrmMaskAOI(QtWidgets.QDialog):

    def __init__(self, parent, project: Project, import_source_path: str, mask_type: DBItem, mask: Mask = None):

        self.qris_project = project
        self.mask = mask
        self.import_source_path = import_source_path
        self.mask_type = mask_type

        super(FrmMaskAOI, self).__init__(parent)
        self.setupUi()

        self.setWindowTitle(f'Create New {mask_type.name}' if self.mask is None else f'Edit {mask_type.name} Properties')

        # The attribute picker is only visible when creating a new regular mask
        show_attribute_filter = import_source_path is not None and mask_type.id == REGULAR_MASK_TYPE_ID
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
            self.chkAddToMap.setCheckState(QtCore.Qt.Unchecked)
            self.chkAddToMap.setVisible(False)

        self.grid.setGeometry(QtCore.QRect(0, 0, self.width(), self.height()))
        self.txtName.setFocus()

    def accept(self):

        if not validate_name(self, self.txtName):
            return

        if self.mask is not None:
            try:
                self.mask.update(self.qris_project.project_file, self.txtName.text(), self.txtDescription.toPlainText())
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "A mask with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Error Saving Mask', str(ex))
                return
        else:
            try:
                self.mask = insert_mask(self.qris_project.project_file, self.txtName.text(), self.mask_type, self.txtDescription.toPlainText())
                self.qris_project.masks[self.mask.id] = self.mask
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "A mask with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Error Saving Mask', str(ex))
                return

            if self.import_source_path is not None:
                try:

                    attributes = {self.cboAttribute.currentData(QtCore.Qt.UserRole).name: 'display_label'} if self.cboAttribute.isVisible() else {}
                    import_mask(self.import_source_path, self.qris_project.project_file, self.mask.id, attributes)
                except Exception as ex:
                    try:
                        self.mask.delete(self.qris_project.project_file)
                    except Exception as ex:
                        print('Error attempting to delete mask after the importing of features failed.')
                    QtWidgets.QMessageBox.warning(self, 'Error Importing Mask Features', str(ex))
                    return

        super(FrmMaskAOI, self).accept()

    def setupUi(self):

        self.resize(500, 300)
        self.setMinimumSize(300, 200)

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

        self.lblAttribute = QtWidgets.QLabel()
        self.lblAttribute.setText('Attribute')
        self.grid.addWidget(self.lblAttribute, 1, 0, 1, 1)

        self.cboAttribute = QtWidgets.QComboBox()
        self.grid.addWidget(self.cboAttribute, 1, 1, 1, 1)

        self.lblDescription = QtWidgets.QLabel()
        self.lblDescription.setText('Description')
        self.grid.addWidget(self.lblDescription, 2, 0, 1, 1)

        self.txtDescription = QtWidgets.QPlainTextEdit()
        self.grid.addWidget(self.txtDescription)

        self.chkAddToMap = QtWidgets.QCheckBox()
        self.chkAddToMap.setChecked(True)
        self.chkAddToMap.setText('Add to Map')
        self.grid.addWidget(self.chkAddToMap, 3, 1, 1, 1)

        self.vert.addLayout(add_standard_form_buttons(self, 'masks'))
