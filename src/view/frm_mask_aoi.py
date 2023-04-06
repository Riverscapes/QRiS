import os
from PyQt5 import QtCore, QtGui, QtWidgets
from qgis.core import QgsVectorLayer

from ..model.db_item import DBItem, DBItemModel
from ..model.project import Project
from ..model.mask import Mask, insert_mask, REGULAR_MASK_TYPE_ID, AOI_MASK_TYPE_ID

from ..gp.feature_class_functions import import_mask
from .utilities import validate_name, add_standard_form_buttons


class FrmMaskAOI(QtWidgets.QDialog):

    def __init__(self, parent, project: Project, import_source_path: str, mask_type: DBItem, mask: Mask = None):

        self.qris_project = project
        self.qris_mask = mask
        self.import_source_path = import_source_path
        self.mask_type = mask_type
        self.str_mask_type = "AOI" if self.mask_type.id == AOI_MASK_TYPE_ID else "Sample Frame"

        super(FrmMaskAOI, self).__init__(parent)
        self.setupUi()

        self.setWindowTitle(f'Create New {mask_type.name}' if self.qris_mask is None else f'Edit {mask_type.name} Properties')

        # The attribute picker is only visible when creating a new regular mask
        show_attribute_filter = mask_type.id == REGULAR_MASK_TYPE_ID
        self.lblAttribute.setVisible(show_attribute_filter)
        self.cboAttribute.setVisible(show_attribute_filter)

        show_mask_clip = import_source_path is not None and mask_type.id == REGULAR_MASK_TYPE_ID
        self.lblMaskClip.setVisible(show_mask_clip)
        self.cboMaskClip.setVisible(show_mask_clip)

        if import_source_path is not None:
            self.txtName.setText(os.path.splitext(os.path.basename(import_source_path))[0])
            self.txtName.selectAll()

            if show_attribute_filter:
                vector_layer = QgsVectorLayer(import_source_path)
                self.attributes = {i: DBItem('None', i, vector_layer.attributeDisplayName(i)) for i in vector_layer.attributeList()}
                self.attribute_model = DBItemModel(self.attributes)
                self.cboAttribute.setModel(self.attribute_model)
                # self.cboAttribute.setModelColumn(1)

            if show_mask_clip:
                # Masks (filtered to just AOI)
                self.masks = {id: mask for id, mask in self.qris_project.masks.items() if mask.mask_type.id == AOI_MASK_TYPE_ID}
                no_clipping = DBItem('None', 0, 'None - Retain full dataset extent')
                self.masks[0] = no_clipping
                self.masks_model = DBItemModel(self.masks)
                self.cboMaskClip.setModel(self.masks_model)
                # Default to no mask clipping
                self.cboMaskClip.setCurrentIndex(self.masks_model.getItemIndex(no_clipping))

        if self.qris_mask is not None:
            self.txtName.setText(mask.name)
            self.txtDescription.setPlainText(mask.description)
            self.chkAddToMap.setCheckState(QtCore.Qt.Unchecked)
            self.chkAddToMap.setVisible(False)

        self.grid.setGeometry(QtCore.QRect(0, 0, self.width(), self.height()))
        self.txtName.setFocus()

    def accept(self):

        if not validate_name(self, self.txtName):
            return

        if self.qris_mask is not None:
            try:
                self.qris_mask.update(self.qris_project.project_file, self.txtName.text(), self.txtDescription.toPlainText())
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', f"A {self.str_mask_type} with the name '{self.txtName.text()}' already exists. Please choose a unique name.")
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, f'Error Saving {self.str_mask_type}', str(ex))
                return
        else:
            try:
                self.qris_mask = insert_mask(self.qris_project.project_file, self.txtName.text(), self.mask_type, self.txtDescription.toPlainText())
                self.qris_project.masks[self.qris_mask.id] = self.qris_mask
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', f"A {self.str_mask_type} with the name '{self.txtName.text()}' already exists. Please choose a unique name.")
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, f'Error Saving {self.str_mask_type}', str(ex))
                return

            if self.import_source_path is not None:
                try:
                    clip_mask = self.cboMaskClip.currentData(QtCore.Qt.UserRole)
                    clip_mask_id = None
                    if clip_mask is not None:
                        clip_mask_id = clip_mask.id if clip_mask.id > 0 else None
                    attributes = {self.cboAttribute.currentData(QtCore.Qt.UserRole).name: 'display_label'} if self.cboAttribute.isVisible() else {}
                    import_mask(self.import_source_path, self.qris_project.project_file, self.qris_mask.id, attributes, self.mask_type, clip_mask_id)
                except Exception as ex:
                    try:
                        self.qris_mask.delete(self.qris_project.project_file)
                    except Exception as ex:
                        print(f'Error attempting to delete {self.str_mask_type} after the importing of features failed.')
                    QtWidgets.QMessageBox.warning(self, f'Error Importing {self.str_mask_type} Features', str(ex))
                    return

        super(FrmMaskAOI, self).accept()

    def setupUi(self):

        self.resize(500, 300)
        self.setMinimumSize(300, 200)

        # Top level layout must include parent. Widgets added to this layout do not need parent.
        self.vert = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vert)

        self.grid = QtWidgets.QGridLayout()
        self.vert.addLayout(self.grid)

        self.lblName = QtWidgets.QLabel()
        self.lblName.setText('Name')
        self.grid.addWidget(self.lblName, 0, 0, 1, 1)

        self.txtName = QtWidgets.QLineEdit()
        self.txtName.setMaxLength(255)
        self.grid.addWidget(self.txtName, 0, 1, 1, 1)

        self.lblAttribute = QtWidgets.QLabel('Sample Frame Labels')
        self.grid.addWidget(self.lblAttribute, 1, 0, 1, 1)

        self.cboAttribute = QtWidgets.QComboBox()
        self.grid.addWidget(self.cboAttribute, 1, 1, 1, 1)

        self.lblMaskClip = QtWidgets.QLabel()
        self.lblMaskClip.setText('Clip to AOI')
        self.grid.addWidget(self.lblMaskClip, 2, 0, 1, 1)

        self.cboMaskClip = QtWidgets.QComboBox()
        self.grid.addWidget(self.cboMaskClip, 2, 1, 1, 1)

        self.lblDescription = QtWidgets.QLabel()
        self.lblDescription.setText('Description')
        self.grid.addWidget(self.lblDescription, 3, 0, 1, 1)

        self.txtDescription = QtWidgets.QPlainTextEdit()
        self.grid.addWidget(self.txtDescription)

        self.chkAddToMap = QtWidgets.QCheckBox()
        self.chkAddToMap.setChecked(True)
        self.chkAddToMap.setText('Add to Map')
        self.grid.addWidget(self.chkAddToMap, 4, 1, 1, 1)

        help = 'aoi' if self.mask_type == AOI_MASK_TYPE_ID else 'sampling_frame'
        self.vert.addLayout(add_standard_form_buttons(self, help))
