import json

from PyQt5 import QtCore, QtWidgets
from qgis.core import QgsApplication, QgsVectorLayer
from qgis.utils import Qgis, iface

from ..model.db_item import DBItem, DBItemModel
from ..model.project import Project
from ..model.profile import Profile, insert_profile
from ..model.scratch_vector import ScratchVector

from ..gp.feature_class_functions import import_existing, layer_path_parser
from ..gp.import_temp_layer import ImportTemporaryLayer

from .widgets.metadata import MetadataWidget
from .utilities import validate_name, add_standard_form_buttons


class FrmProfile(QtWidgets.QDialog):

    def __init__(self, parent, project: Project, import_source_path: str, profile: Profile = None):

        self.qris_project = project
        self.profile = profile
        self.import_source_path = import_source_path
        self.profile_type = Profile.ProfileTypes.GENERIC_PROFILE_TYPE  # mask_type

        super(FrmProfile, self).__init__(parent)
        metadata_json = json.dumps(profile.metadata) if profile is not None else None
        self.metadata_widget = MetadataWidget(self, metadata_json)
        self.setupUi()

        self.setWindowTitle(f'Create New Profile' if self.profile is None else f'Edit Profile Properties')

        # Masks (filtered to just AOI)
        self.aois = {id: aoi for id, aoi in self.qris_project.aois.items()}
        no_clipping = DBItem('None', 0, 'None - Retain full dataset extent')
        self.aois[0] = no_clipping
        self.aoi_model = DBItemModel(self.aois)
        self.cboMaskClip.setModel(self.aoi_model)
        # Default to no mask clipping
        self.cboMaskClip.setCurrentIndex(self.aoi_model.getItemIndex(no_clipping))

        self.cboMaskClip.setVisible(False)
        self.lblMaskClip.setVisible(False)

        if import_source_path is not None:
            if isinstance(import_source_path, QgsVectorLayer):
                self.layer_name = import_source_path.name()
                self.layer_id = 'memory'
                #  show_mask_clip = False
            else:
                # find if import_source_path is shapefile, geopackage, or other
                self.basepath, self.layer_name, self.layer_id = layer_path_parser(import_source_path)

            self.txtName.setText(self.layer_name)
            self.txtName.selectAll()

            self.lblMaskClip.setVisible(True)
            self.cboMaskClip.setVisible(True)

        if self.profile is not None:
            self.txtName.setText(profile.name)
            self.txtDescription.setPlainText(profile.description)
            self.chkAddToMap.setCheckState(QtCore.Qt.Unchecked)
            self.chkAddToMap.setVisible(False)

        self.grid.setGeometry(QtCore.QRect(0, 0, self.width(), self.height()))
        self.txtName.setFocus()

    def promote_to_profile(self, db_item: DBItem):
        self.txtName.setText(db_item.name)
        self.setWindowTitle(f'Promote {db_item.name} to Profile')

        db_path = self.qris_project.project_file
        id_field = None
        if isinstance(db_item, ScratchVector):
            layer_name = db_item.fc_name
            db_path = db_item.gpkg_path
        else:
            layer_name = db_item.db_table_name
            id_field = db_item.id_column_name
        self.import_source_path = f'{db_path}|layername={layer_name}'
        self.attribute_filter = f'{id_field} = {db_item.id}' if id_field is not None else None

        self.lblMaskClip.setVisible(True)
        self.cboMaskClip.setVisible(True)

        self.basepath, self.layer_name, self.layer_id = layer_path_parser(self.import_source_path)

        metadata_json = json.dumps(db_item.metadata) if db_item.metadata is not None else None
        self.metadata_widget.load_json(metadata_json)

    def accept(self):

        if not validate_name(self, self.txtName):
            return

        metadata_json = self.metadata_widget.get_json()
        metadata = json.loads(metadata_json) if metadata_json is not None else None

        if self.profile is not None:
            try:
                self.profile.update(self.qris_project.project_file, self.txtName.text(), self.txtDescription.toPlainText(), metadata)
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "A profile with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Error Saving Profile', str(ex))
                return
            super(FrmProfile, self).accept()

        else:
            try:
                self.profile = insert_profile(self.qris_project.project_file, self.txtName.text(), self.profile_type, self.txtDescription.toPlainText(), metadata)
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
                    fc_path = f'{self.qris_project.project_file}|layername=profile_features'
                    
                    clip_mask = None
                    clip_item = self.cboMaskClip.currentData(QtCore.Qt.UserRole)
                    if clip_item is not None:
                        if clip_item.id > 0:        
                            clip_mask = ('sample_frame_features', 'sample_frame_id', clip_item.id)
                    if self.layer_id == 'memory':
                        task = ImportTemporaryLayer(self.import_source_path, fc_path, {'profile_id': self.profile.id}, clip_mask=clip_mask, proj_gpkg=self.qris_project.project_file)
                        # DEBUG task.run()
                        task.import_complete.connect(self.on_import_complete)
                        QgsApplication.taskManager().addTask(task)
                    else:
                        import_existing(self.import_source_path, self.qris_project.project_file, 'profile_features', self.profile.id, 'profile_id', clip_mask=clip_mask)
                        super(FrmProfile, self).accept()
                except Exception as ex:
                    try:
                        self.profile.delete(self.qris_project.project_file)
                    except Exception as ex_delete:
                        # add to message bar and log
                        iface.messageBar().pushMessage('Error Deleting Profile', str(ex_delete), level=Qgis.Critical, duration=5)
                        QgsApplication.messageLog().logMessage(f'Error Deleting Profile: {str(ex_delete)}', 'QRIS')
                    # add to message bar and log
                    iface.messageBar().pushMessage('Error Importing Profile Features', str(ex), level=Qgis.Critical, duration=5)
                    QgsApplication.messageLog().logMessage(f'Error Importing Profile Features: {str(ex)}', 'QRIS', level=Qgis.Critical)
                    return

    def on_import_complete(self, result: bool):

        if not result:
            QtWidgets.QMessageBox.warning(self, f'Error Importing Profile Features', str(self.exception))
            try:
                self.profile.delete(self.qris_project.project_file)
            except Exception as ex:
                # add to message bar and log
                iface.messageBar().pushMessage('Error Deleting Profile', str(ex), level=Qgis.Critical, duration=5)
                QgsApplication.messageLog().logMessage(f'Error Deleting Profile: {str(ex)}', 'QRIS', level=Qgis.Critical)
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
        self.tabs = QtWidgets.QTabWidget()
        self.vert.addWidget(self.tabs)

        self.grid = QtWidgets.QGridLayout()

        self.lblName = QtWidgets.QLabel('Name')
        self.grid.addWidget(self.lblName, 0, 0, 1, 1)

        self.txtName = QtWidgets.QLineEdit()
        self.txtName.setToolTip('The name of the profile')
        self.txtName.setMaxLength(255)
        self.grid.addWidget(self.txtName, 0, 1, 1, 1)

        self.lblMaskClip = QtWidgets.QLabel('Clip to AOI')
        self.grid.addWidget(self.lblMaskClip, 2, 0, 1, 1)

        self.cboMaskClip = QtWidgets.QComboBox()
        self.cboMaskClip.setToolTip('Optionally clip the profile to the selected AOI')
        self.grid.addWidget(self.cboMaskClip, 2, 1, 1, 1)

        self.lblDescription = QtWidgets.QLabel('Description')
        self.grid.addWidget(self.lblDescription, 3, 0, 1, 1)

        self.txtDescription = QtWidgets.QPlainTextEdit()
        self.grid.addWidget(self.txtDescription)

        self.tabProperties = QtWidgets.QWidget()
        self.tabs.addTab(self.tabProperties, 'Basic Properties')
        self.tabProperties.setLayout(self.grid)

        # Metadata Tab
        self.tabs.addTab(self.metadata_widget, 'Metadata')

        self.chkAddToMap = QtWidgets.QCheckBox('Add to Map')
        self.chkAddToMap.setChecked(True)
        self.grid.addWidget(self.chkAddToMap, 4, 1, 1, 1)

        self.vert.addLayout(add_standard_form_buttons(self, 'profiles'))
