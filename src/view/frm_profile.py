import json

from qgis.PyQt import QtCore, QtWidgets
from qgis.gui import QgisInterface
from qgis.core import QgsApplication, QgsVectorLayer
from qgis.utils import Qgis, iface

from ..model.db_item import DBItem, DBItemModel
from ..model.project import Project
from ..model.profile import Profile, insert_profile
from ..model.scratch_vector import ScratchVector

from ..gp.feature_class_functions import import_existing, layer_path_parser
from ..gp.import_temp_layer import ImportMapLayer

from .widgets.metadata import MetadataWidget
from .widgets.stats_widget import StatsWidget
from .utilities import validate_name, add_standard_form_buttons


class FrmProfile(QtWidgets.QDialog):

    def __init__(self, parent, qris_project: Project, import_source_path, profile: Profile = None,
                 profile_type=None, fc_name: str = 'profile_features', system_metadata: dict = None, metrics: dict = None):

        self.iface: QgisInterface = iface
        self.qris_project = qris_project
        self.profile = profile
        self.import_source_path = import_source_path
        self.profile_type = profile_type if profile_type is not None else Profile.ProfileTypes.GENERIC_PROFILE_TYPE
        self.fc_name = fc_name
        self.metrics = metrics

        super(FrmProfile, self).__init__(parent)
        metadata_json = json.dumps(profile.metadata) if profile is not None else None
        self.metadata_widget = MetadataWidget(self, metadata_json)
        if system_metadata is not None:
            for key, value in system_metadata.items():
                self.metadata_widget.add_system_metadata(key, value)
        self.stats_widget = StatsWidget(db_item=profile, db_path=qris_project.project_file, parent=self)
        if metrics is not None:
            self.stats_widget.load_from_dict(metrics)
        self.setupUi()

        self.setWindowTitle(f'Create New Profile' if self.profile is None else f'Edit Profile Properties')

        # Masks (AOIs and valley bottoms)
        clip_items = {**self.qris_project.aois, **self.qris_project.valley_bottoms}
        no_clipping = DBItem('None', 0, 'None - Retain full dataset extent')
        clip_items[0] = no_clipping
        self.clip_model = DBItemModel(clip_items)
        self.cboMaskClip.setModel(self.clip_model)
        # Default to no mask clipping
        self.cboMaskClip.setCurrentIndex(self.clip_model.getItemIndex(no_clipping))

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

            if self.tabs.indexOf(self.tabProperties) == -1:
                self.tabs.insertTab(0, self.tabProperties, 'Basic Properties')
            self.tabs.setCurrentIndex(0)

        if self.profile is not None:
            self.txtName.setText(profile.name)
            self.txtDescription.setPlainText(profile.description)
            self.chkAddToMap.setCheckState(QtCore.Qt.Unchecked)
            self.chkAddToMap.setVisible(False)
            self.chkStartEditSession.setVisible(False)

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

        if self.tabs.indexOf(self.tabProperties) == -1:
            self.tabs.insertTab(0, self.tabProperties, 'Basic Properties')
        self.tabs.setCurrentIndex(0)

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
                self.qris_project.project_changed.emit()
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
                if self.metrics is not None:
                    for key, value in self.metrics.items():
                        self.metadata_widget.add_attribute_metadata(key, value)
                    metadata_json = self.metadata_widget.get_json()
                    metadata = json.loads(metadata_json) if metadata_json is not None else None
                self.profile = insert_profile(self.qris_project.project_file, self.txtName.text(), self.profile_type, self.txtDescription.toPlainText(), metadata)
                self.qris_project.add_db_item(self.profile)
            except Exception as ex:
                if 'unique' in str(ex).lower():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', "A profile with the name '{}' already exists. Please choose a unique name.".format(self.txtName.text()))
                    self.txtName.setFocus()
                else:
                    QtWidgets.QMessageBox.warning(self, 'Error Saving Profile', str(ex))
                return

            if self.import_source_path is not None:
                try:
                    fc_path = f'{self.qris_project.project_file}|layername={self.fc_name}'
                    
                    clip_mask = None
                    clip_item = self.cboMaskClip.currentData(QtCore.Qt.UserRole)
                    if clip_item is not None:
                        if clip_item.id > 0:        
                            clip_mask = ('sample_frame_features', 'sample_frame_id', clip_item.id)
                    if self.layer_id == 'memory':
                        task = ImportMapLayer(self.import_source_path, fc_path, {'profile_id': self.profile.id}, clip_mask=clip_mask, proj_gpkg=self.qris_project.project_file)
                        # DEBUG task.run()
                        task.import_complete.connect(self.on_import_complete)
                        QgsApplication.taskManager().addTask(task)
                    else:
                        import_existing(self.import_source_path, self.qris_project.project_file, self.fc_name, self.profile.id, 'profile_id', clip_mask=clip_mask)
                        super(FrmProfile, self).accept()
                except Exception as ex:
                    try:
                        self.profile.delete(self.qris_project.project_file)
                    except Exception as ex_delete:
                        # add to message bar and log
                        self.iface.messageBar().pushMessage('Error Deleting Profile', str(ex_delete), level=Qgis.Critical, duration=5)
                        QgsApplication.messageLog().logMessage(f'Error Deleting Profile: {str(ex_delete)}', 'QRIS')
                    # add to message bar and log
                    self.iface.messageBar().pushMessage('Error Importing Profile Features', str(ex), level=Qgis.Critical, duration=5)
                    QgsApplication.messageLog().logMessage(f'Error Importing Profile Features: {str(ex)}', 'QRIS', level=Qgis.Critical)
                    return

    def on_import_complete(self, result: bool):

        if not result:
            QtWidgets.QMessageBox.warning(self, f'Error Importing Profile Features', str(self.exception))
            try:
                self.profile.delete(self.qris_project.project_file)
            except Exception as ex:
                # add to message bar and log
                self.iface.messageBar().pushMessage('Error Deleting Profile', str(ex), level=Qgis.Critical, duration=5)
                QgsApplication.messageLog().logMessage(f'Error Deleting Profile: {str(ex)}', 'QRIS', level=Qgis.Critical)
            return
        else:
            self.iface.messageBar().pushMessage('Profile Import Complete.', f"{self.import_source_path} saved successfully.", level=Qgis.Info, duration=5)
            super(FrmProfile, self).accept()

    def setupUi(self):

        self.resize(500, 300)
        self.setMinimumSize(300, 200)

        # Top level layout must include parent. Widgets added to this layout do not need parent.
        self.vert = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vert)

        # Name
        horiz_name = QtWidgets.QHBoxLayout()
        self.lblName = QtWidgets.QLabel('Name')
        horiz_name.addWidget(self.lblName)
        self.txtName = QtWidgets.QLineEdit()
        self.txtName.setToolTip('The name of the profile')
        self.txtName.setMaxLength(255)
        horiz_name.addWidget(self.txtName)
        self.vert.addLayout(horiz_name)

        self.tabs = QtWidgets.QTabWidget()
        self.vert.addWidget(self.tabs)

        # Properties Tab
        self.grid = QtWidgets.QGridLayout()

        self.lblMaskClip = QtWidgets.QLabel('Clip to AOI / Valley Bottom')
        self.grid.addWidget(self.lblMaskClip, 0, 0, 1, 1)

        self.cboMaskClip = QtWidgets.QComboBox()
        self.cboMaskClip.setToolTip('Optionally clip the profile to the selected AOI or valley bottom')
        self.grid.addWidget(self.cboMaskClip, 0, 1, 1, 1)

        self.grid.setRowStretch(1, 1)

        self.tabProperties = QtWidgets.QWidget()
        self.tabProperties.setLayout(self.grid)
        # tabProperties is inserted at position 0 only when clipping is available

        # Description Tab
        description_tab = QtWidgets.QWidget()
        self.txtDescription = QtWidgets.QPlainTextEdit()
        description_tab_layout = QtWidgets.QVBoxLayout()
        description_tab_layout.addWidget(self.txtDescription)
        description_tab.setLayout(description_tab_layout)
        self.tabs.addTab(description_tab, 'Description')

        # Statistics Tab
        self.stats_widget.add_stats_tab(self.tabs)

        # Metadata Tab
        self.tabs.addTab(self.metadata_widget, 'Metadata')

        self.chkAddToMap = QtWidgets.QCheckBox('Add to Map')
        self.chkAddToMap.setChecked(True)

        # Add to Map and Start Edit Session checkboxes
        self.chkStartEditSession = QtWidgets.QCheckBox('Start Edit Session')
        self.chkStartEditSession.setChecked(False)
        self.chkAddToMap.stateChanged.connect(lambda state: (
            self.chkStartEditSession.setEnabled(state == QtCore.Qt.Checked),
            self.chkStartEditSession.setChecked(False) if state != QtCore.Qt.Checked else None
        ))

        add_to_map_row = QtWidgets.QHBoxLayout()
        add_to_map_row.addWidget(self.chkAddToMap)
        add_to_map_row.addWidget(self.chkStartEditSession)
        add_to_map_row.addStretch()
        self.vert.addLayout(add_to_map_row)

        self.vert.addLayout(add_standard_form_buttons(self, 'inputs/profiles'))
