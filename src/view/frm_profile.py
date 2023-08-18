from PyQt5 import QtCore, QtGui, QtWidgets
from qgis.core import QgsApplication, QgsVectorLayer
from qgis.utils import Qgis, iface

from ..model.db_item import DBItem, DBItemModel
from ..model.project import Project
from ..model.profile import Profile, insert_profile
from ..model.mask import AOI_MASK_TYPE_ID

from ..gp.feature_class_functions import import_existing, layer_path_parser
from ..gp.import_temp_layer import ImportTemporaryLayer
from .utilities import validate_name, add_standard_form_buttons


class FrmProfile(QtWidgets.QDialog):

    def __init__(self, parent, project: Project, import_source_path: str, profile: Profile = None):

        self.qris_project = project
        self.profile = profile
        self.import_source_path = import_source_path
        self.profile_type = Profile.ProfileTypes.GENERIC_PROFILE_TYPE  # mask_type

        super(FrmProfile, self).__init__(parent)
        self.setupUi()

        self.setWindowTitle(f'Create New Profile')

        # The attribute picker is only visible when creating a new regular mask
        show_attribute_filter = import_source_path is not None
        self.lblAttribute.setVisible(show_attribute_filter)
        self.cboAttribute.setVisible(show_attribute_filter)

        show_mask_clip = import_source_path is not None
        self.lblMaskClip.setVisible(show_mask_clip)
        self.cboMaskClip.setVisible(show_mask_clip)

        if import_source_path is not None:
            if isinstance(import_source_path, QgsVectorLayer):
                self.layer_name = import_source_path.name()
                self.layer_id = 'memory'
                show_attribute_filter = False
                show_mask_clip = False
            else:
                # find if import_source_path is shapefile, geopackage, or other
                self.basepath, self.layer_name, self.layer_id = layer_path_parser(import_source_path)

            self.txtName.setText(self.layer_name)
            self.txtName.selectAll()

            if show_attribute_filter:
                vector_layer = import_source_path if isinstance(import_source_path, QgsVectorLayer) else QgsVectorLayer(import_source_path)
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

        if self.profile is not None:
            self.txtName.setText(profile.name)
            self.txtDescription.setPlainText(profile.description)
            self.chkAddToMap.setCheckState(QtCore.Qt.Unchecked)
            self.chkAddToMap.setVisible(False)

        self.grid.setGeometry(QtCore.QRect(0, 0, self.width(), self.height()))
        self.txtName.setFocus()

    def accept(self):

        if not validate_name(self, self.txtName):
            return

        if self.profile is not None:
            try:
                self.profile.update(self.qris_project.project_file, self.txtName.text(), self.txtDescription.toPlainText())
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "A profile with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Error Saving Profile', str(ex))
                return
        else:
            try:
                self.profile = insert_profile(self.qris_project.project_file, self.txtName.text(), self.profile_type, self.txtDescription.toPlainText())
                self.qris_project.profiles[self.profile.id] = self.profile
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "A profile with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Error Saving Profile', str(ex))
                return

            if self.import_source_path is not None:
                try:
                    clip_mask = self.cboMaskClip.currentData(QtCore.Qt.UserRole)
                    clip_mask_id = None
                    if clip_mask is not None:
                        clip_mask_id = clip_mask.id if clip_mask.id > 0 else None
                    if self.layer_id == 'memory':
                        task = ImportTemporaryLayer(self.import_source_path, self.qris_project.project_file, 'profile_features', 'profile_id', self.profile.id, mask_clip_id=clip_mask_id, proj_gpkg=self.qris_project.project_file)
                        # DEBUG task.run()
                        task.import_complete.connect(self.on_import_complete)
                        QgsApplication.taskManager().addTask(task)
                    else:
                        attributes = {self.cboAttribute.currentData(QtCore.Qt.UserRole).name: 'display_label'} if self.cboAttribute.isVisible() else {}
                        import_existing(self.import_source_path, self.qris_project.project_file, 'profile_features', self.profile.id, 'profile_id', attributes, clip_mask_id)
                        super(FrmProfile, self).accept()
                except Exception as ex:
                    try:
                        self.profile.delete(self.qris_project.project_file)
                    except Exception as ex_delete:
                        QtWidgets.QMessageBox.warning(self, 'Error Importing Profile Features', str(ex_delete))
                    QtWidgets.QMessageBox.warning(self, 'Error Importing Profile Features', str(ex))
                    return

    def on_import_complete(self, result: bool):

        if not result:
            QtWidgets.QMessageBox.warning(self, f'Error Importing Profile Features', str(self.exception))
            try:
                self.profile.delete(self.qris_project.project_file)
            except Exception as ex:
                print(f'Error attempting to delete Profile after the importing of features failed.')
            return
        else:
            iface.messageBar().pushMessage('Profile Import Complete.', f"{self.import_source_path} saved successfully.", level=Qgis.Info, duration=5)
            super(FrmProfile, self).accept()

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

        self.lblAttribute = QtWidgets.QLabel()
        self.lblAttribute.setText('Attribute')
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

        self.vert.addLayout(add_standard_form_buttons(self, 'profiles'))
