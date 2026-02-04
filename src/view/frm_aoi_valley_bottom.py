import json
from PyQt5 import QtCore, QtWidgets
from qgis.gui import QgisInterface
from qgis.core import Qgis, QgsApplication, QgsVectorLayer
from qgis.utils import iface

from ..model.db_item import DBItem, DBItemModel
from ..model.project import Project
from ..model.sample_frame import SampleFrame, insert_sample_frame
from ..model.pour_point import PourPoint
from ..model.scratch_vector import ScratchVector

from ..gp.feature_class_functions import layer_path_parser
from ..gp.import_feature_class import ImportFeatureClass, ImportFieldMap
from ..gp.import_temp_layer import ImportMapLayer

from .widgets.metadata import MetadataWidget
from .utilities import validate_name, add_standard_form_buttons


class FrmAOIValleyBottom(QtWidgets.QDialog):

    def __init__(self, parent, qris_project: Project, import_source_path: str, sample_frame: SampleFrame = None, sample_frame_type: int = SampleFrame.AOI_SAMPLE_FRAME_TYPE):

        self.iface: QgisInterface = iface
        self.qris_project = qris_project
        self.sample_frame = sample_frame
        self.import_source_path = import_source_path
        self.attribute_filter = None
        
        # Determine type from object or argument
        if self.sample_frame:
            self.sample_frame_type = self.sample_frame.sample_frame_type
        else:
            self.sample_frame_type = sample_frame_type

        # Feature Type helpers
        self.is_aoi = self.sample_frame_type == SampleFrame.AOI_SAMPLE_FRAME_TYPE
        self.type_name = "AOI" if self.is_aoi else "Valley Bottom"

        super(FrmAOIValleyBottom, self).__init__(parent)
        metadata_json = json.dumps(sample_frame.metadata) if sample_frame is not None else None
        self.metadata_widget = MetadataWidget(self, metadata_json)
        self.setupUi()

        if self.sample_frame is not None:
            self.setWindowTitle(f'Edit {self.type_name} Properties')
        elif import_source_path is not None:
            self.setWindowTitle(f'Import {self.type_name} Features')
        else:
            self.setWindowTitle(f'Create New {self.type_name}')

        # Visibility Logic
        show_attribute_filter = False
        show_mask_clip = False
        
        if import_source_path is not None:
            if isinstance(import_source_path, QgsVectorLayer):
                # Layer is already loaded (memory or similar)
                self.layer_name = import_source_path.name()
                self.layer_id = 'memory'
                
                # FrmValleyBottom logic: Show mask clip even for QgsVectorLayer
                if not self.is_aoi: # is VB
                     show_mask_clip = True

            else:
                # File path import
                self.basepath, self.layer_name, self.layer_id = layer_path_parser(import_source_path)
                
                # FrmAOI showed attribute filter here (ONLY for AOI)
                if self.is_aoi:
                    show_attribute_filter = True
                
                # Both allow mask clip for file imports? 
                # FrmValleyBottom: YES. FrmAOI: NO (according to old file). 
                # We will enable for VB. For AOI we keep it disabled as per FrmAOI Reference, 
                # UNLESS user wants it. But let's stick to previous behavior: VB gets clip, AOI doesn't.
                if not self.is_aoi:
                    show_mask_clip = True

            self.txtName.setText(self.layer_name)
            self.txtName.selectAll()

            if show_attribute_filter:
                vector_layer = import_source_path if isinstance(import_source_path, QgsVectorLayer) else QgsVectorLayer(import_source_path)
                self.attributes = {i: DBItem('None', i, vector_layer.attributeDisplayName(i)) for i in vector_layer.attributeList()}
                self.attribute_model = DBItemModel(self.attributes)
                self.cboAttribute.setModel(self.attribute_model)
            
            # Setup Mask Clipping Models if visible
            if show_mask_clip:
                self.clipping_masks = {id: aoi for id, aoi in self.qris_project.aois.items()}
                no_clipping = DBItem('None', 0, 'None - Retain full dataset extent')
                self.clipping_masks[0] = no_clipping
                self.masks_model = DBItemModel(self.clipping_masks)
                self.cboMaskClip.setModel(self.masks_model)
                self.cboMaskClip.setCurrentIndex(self.masks_model.getItemIndex(no_clipping))

        # Apply visibility
        self.lblAttribute.setVisible(show_attribute_filter)
        self.cboAttribute.setVisible(show_attribute_filter)
        self.lblMaskClip.setVisible(show_mask_clip)
        self.cboMaskClip.setVisible(show_mask_clip)

        # Tab Settings now contains Project Bounds, so we keep it.

        if self.sample_frame is not None:
            self.txtName.setText(sample_frame.name)
            self.txtDescription.setPlainText(sample_frame.description)
            self.chkAddToMap.setCheckState(QtCore.Qt.Unchecked)
            self.chkAddToMap.setVisible(False)
            
            self.chkProjectBounds.setChecked(getattr(self.sample_frame, "project_bounds", False))
        else:
            # Check if any bounds exist across both types
            has_bounds = False
            for sf_set in [self.qris_project.aois, self.qris_project.valley_bottoms]:
                 if sf_set is None: continue
                 for sf in sf_set.values():
                      if getattr(sf, "project_bounds", False):
                           has_bounds = True
                           break
            
            if not has_bounds:
                 self.chkProjectBounds.setChecked(True)
            else:
                 self.chkProjectBounds.setChecked(False)

        self.txtName.setFocus()

    def promote_to_sample_frame(self, db_item: DBItem):

        self.txtName.setText(db_item.name)
        self.setWindowTitle(f'Promote {db_item.name} to {self.type_name}')

        db_path = self.qris_project.project_file
        id_field = None
        if isinstance(db_item, PourPoint):
            layer_name = 'catchments'
            id_field = 'pour_point_id'
        elif isinstance(db_item, ScratchVector):
            layer_name = db_item.fc_name
            db_path = db_item.gpkg_path
        else:
            layer_name = db_item.db_table_name
            id_field = db_item.id_column_name
        self.import_source_path = f'{db_path}|layername={layer_name}'
        self.attribute_filter = f'{id_field} = {db_item.id}' if id_field is not None else None

        self.basepath, self.layer_name, self.layer_id = layer_path_parser(self.import_source_path)

        metadata_json = json.dumps(db_item.metadata) if db_item.metadata is not None else None
        self.metadata_widget.load_json(metadata_json)
        self.metadata_widget.add_system_metadata('source_layer', layer_name)
        self.metadata_widget.add_system_metadata('source_layer_id', db_item.id)

    def accept(self):

        if not validate_name(self, self.txtName):
            return

        # Check for unique name in the respective collection
        collection = self.qris_project.aois if self.is_aoi else self.qris_project.valley_bottoms
        current_id = self.sample_frame.id if self.sample_frame is not None else None
        
        if collection is not None:
            for sf in collection.values():
                if sf.name == self.txtName.text() and sf.id != current_id:
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Name', f"A {self.type_name} with the name '{self.txtName.text()}' already exists. Please choose a unique name.")
                    self.txtName.setFocus()
                    return

        self.metadata_widget.add_system_metadata('project_bounds', self.chkProjectBounds.isChecked())

        metadata_json = self.metadata_widget.get_json()
        metadata = json.loads(metadata_json) if metadata_json is not None else None

        try:
            if self.sample_frame is not None:
                self.sample_frame.project_bounds = self.chkProjectBounds.isChecked()
                self.sample_frame.update(self.qris_project.project_file, self.txtName.text(), self.txtDescription.toPlainText(), metadata)
                self.qris_project.project_changed.emit()
            else:
                self.sample_frame = insert_sample_frame(self.qris_project.project_file, self.txtName.text(), self.txtDescription.toPlainText(), metadata, sample_frame_type=self.sample_frame_type)
                self.sample_frame.project_bounds = self.chkProjectBounds.isChecked()
                self.qris_project.add_db_item(self.sample_frame)

        except Exception as ex:
            if 'unique' in str(ex).lower():
                QtWidgets.QMessageBox.warning(self, 'Duplicate Name', f"A {self.type_name} with the name '{self.txtName.text()}' already exists. Please choose a unique name.")
                self.txtName.setFocus()
            else:
                QtWidgets.QMessageBox.warning(self, f'Error Saving {self.type_name}', str(ex))
            return

        # Import Logic
        if self.import_source_path is not None:
            try:
                dest_layer_name = "sample_frame_features"
                dest_path = f'{self.qris_project.project_file}|layername={dest_layer_name}'
                layer_attributes = {'sample_frame_id': self.sample_frame.id}
                
                field_map = None
                if self.cboAttribute.isVisible() and self.cboAttribute.currentData(QtCore.Qt.UserRole) is not None:
                     field_map = [ImportFieldMap(self.cboAttribute.currentData(QtCore.Qt.UserRole).name, 'display_label', direct_copy=True)]
                
                clip_mask = None
                if self.cboMaskClip.isVisible():
                    clip_item = self.cboMaskClip.currentData(QtCore.Qt.UserRole)
                    if clip_item is not None and clip_item.id > 0:
                        clip_mask = ('sample_frame_features', 'sample_frame_id', clip_item.id)
                
                if self.layer_id == 'memory':
                    import_task = ImportMapLayer(self.import_source_path, dest_path, layer_attributes, field_map, clip_mask, self.attribute_filter, self.qris_project.project_file)
                else:
                    explode = not self.is_aoi
                    import_task = ImportFeatureClass(self.import_source_path, dest_path, layer_attributes, field_map, clip_mask, self.attribute_filter, self.qris_project.project_file, explode_geometries=explode)

                import_task.import_complete.connect(self.on_import_complete)
                QgsApplication.taskManager().addTask(import_task)
            except Exception as ex:
                self.rollback_creation(ex)
                return
        else:
            self.finalize_accept()

    def rollback_creation(self, ex):
        QgsApplication.messageLog().logMessage(f'Error Importing {self.type_name}: {str(ex)}', 'QRIS', level=Qgis.Critical)
        self.iface.messageBar().pushMessage(f'Error Importing {self.type_name}', str(ex), level=Qgis.Critical, duration=5)
        try:
             self.sample_frame.delete(self.qris_project.project_file)
        except Exception as ex_delete:
             QgsApplication.messageLog().logMessage(f'Error Deleting {self.type_name}: {str(ex_delete)}', 'QRIS', level=Qgis.Critical)

    def on_import_complete(self, result: bool):
        if result is True:
            self.iface.messageBar().pushMessage(f'{self.type_name} Imported', f'{self.type_name} "{self.txtName.text()}" has been imported successfully.', level=Qgis.Success, duration=5)
            self.finalize_accept()
        else:
             self.rollback_creation("Import Task Failed")

    def finalize_accept(self):
         # Handle Project Bounds Exclusivity
         if self.chkProjectBounds.isChecked():
              # Clear all others in both containers
              for collection in [self.qris_project.aois, self.qris_project.valley_bottoms]:
                   if collection is None: continue
                   for sf in collection.values():
                        # Skip self
                        if sf.id == self.sample_frame.id and sf.sample_frame_type == self.sample_frame_type:
                             continue
                        
                        if getattr(sf, "project_bounds", False):
                             sf.project_bounds = False
                             if sf.metadata is None: sf.metadata = {}
                             if 'system' not in sf.metadata: sf.metadata['system'] = {}
                             sf.metadata['system']['project_bounds'] = False
                             sf.update(self.qris_project.project_file, sf.name, sf.description, sf.metadata)
         
         super(FrmAOIValleyBottom, self).accept()

    def setupUi(self):

        self.resize(500, 350)
        self.setMinimumSize(300, 250)

        self.vert = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vert)

        # Name (Top)
        self.top_grid = QtWidgets.QGridLayout()
        self.vert.addLayout(self.top_grid)

        self.lblName = QtWidgets.QLabel('Name')
        self.top_grid.addWidget(self.lblName, 0, 0)
        self.txtName = QtWidgets.QLineEdit()
        self.txtName.setToolTip(f'The name of the {self.type_name}')
        self.txtName.setMaxLength(255)
        self.top_grid.addWidget(self.txtName, 0, 1)

        # Tabs
        self.tabs = QtWidgets.QTabWidget()
        self.vert.addWidget(self.tabs)

        # Tab: Settings (Bounds / Attributes / Clip)
        self.tabSettings = QtWidgets.QWidget()
        self.settings_grid = QtWidgets.QGridLayout(self.tabSettings)
        
        # Project Bounds - Row 0
        self.chkProjectBounds = QtWidgets.QCheckBox()
        self.chkProjectBounds.setText('Set as Project Bounds')
        self.settings_grid.addWidget(self.chkProjectBounds, 0, 0, 1, 2)

        # Attribute - Row 1
        self.lblAttribute = QtWidgets.QLabel('Sample Frame Labels')
        self.settings_grid.addWidget(self.lblAttribute, 1, 0)
        self.cboAttribute = QtWidgets.QComboBox()
        self.cboAttribute.setToolTip('The attribute field to use for labeling')
        self.settings_grid.addWidget(self.cboAttribute, 1, 1)
        
        # Clip - Row 2
        self.lblMaskClip = QtWidgets.QLabel('Clip to AOI')
        self.settings_grid.addWidget(self.lblMaskClip, 2, 0)
        self.cboMaskClip = QtWidgets.QComboBox()
        self.cboMaskClip.setToolTip('Clip to the boundary of an existing AOI')
        self.settings_grid.addWidget(self.cboMaskClip, 2, 1)
        
        # Spacer
        self.settings_grid.setRowStretch(3, 1)
        
        self.tabs.addTab(self.tabSettings, 'Settings')
        
        # Tab: Description
        self.tabDescription = QtWidgets.QWidget()
        self.desc_layout = QtWidgets.QVBoxLayout(self.tabDescription)
        self.desc_layout.setContentsMargins(9, 9, 9, 9)
        self.txtDescription = QtWidgets.QPlainTextEdit()
        self.desc_layout.addWidget(self.txtDescription)
        self.tabs.addTab(self.tabDescription, 'Description')
        self.tabs.addTab(self.metadata_widget, 'Metadata')

        # Add To Map (Bottom)
        self.chkAddToMap = QtWidgets.QCheckBox()
        self.chkAddToMap.setChecked(True)
        self.chkAddToMap.setText('Add to Map')
        self.vert.addWidget(self.chkAddToMap)
        
        help_slug = 'inputs/aoi' if self.is_aoi else 'inputs/valley-bottoms'
        self.vert.addLayout(add_standard_form_buttons(self, help_slug))
