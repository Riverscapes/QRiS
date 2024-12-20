import json

from PyQt5 import QtCore, QtGui, QtWidgets
from qgis.core import Qgis, QgsApplication, QgsVectorLayer
from qgis.utils import iface

from ..model.db_item import DBItem, DBItemModel
from ..model.project import Project
from ..model.mask import Mask, insert_mask, REGULAR_MASK_TYPE_ID, AOI_MASK_TYPE_ID
from ..model.pour_point import PourPoint
from ..model.scratch_vector import ScratchVector

from ..gp.feature_class_functions import layer_path_parser
from ..gp.import_feature_class import ImportFeatureClass, ImportFieldMap
from ..gp.import_temp_layer import ImportTemporaryLayer

from .widgets.metadata import MetadataWidget
from .utilities import validate_name, add_standard_form_buttons


class FrmMaskAOI(QtWidgets.QDialog):

    def __init__(self, parent, project: Project, import_source_path: str, mask_type: DBItem, mask: Mask = None):

        self.qris_project = project
        self.qris_mask = mask
        self.import_source_path = import_source_path
        self.attribute_filter = None
        self.mask_type = mask_type
        self.str_mask_type = "AOI" if self.mask_type.id == AOI_MASK_TYPE_ID else "Sample Frame"

        super(FrmMaskAOI, self).__init__(parent)
        metadata_json = json.dumps(mask.metadata) if mask is not None else None
        self.metadata_widget = MetadataWidget(self, metadata_json)
        self.setupUi()

        if self.qris_mask is not None:
            self.setWindowTitle(f'Edit {mask_type.name} Properties')
        elif import_source_path is not None:
            self.setWindowTitle(f'Import {mask_type.name} Features')
        else:
            self.setWindowTitle(f'Create New {mask_type.name}')

        # The attribute picker is only visible when creating a new regular mask
        show_attribute_filter = mask_type.id == REGULAR_MASK_TYPE_ID
        self.lblAttribute.setVisible(show_attribute_filter)
        self.cboAttribute.setVisible(show_attribute_filter)

        show_mask_clip = import_source_path is not None and mask_type.id == REGULAR_MASK_TYPE_ID
        self.lblMaskClip.setVisible(show_mask_clip)
        self.cboMaskClip.setVisible(show_mask_clip)

        if import_source_path is not None:
            if isinstance(import_source_path, QgsVectorLayer):
                self.layer_name = import_source_path.name()
                self.layer_id = 'memory'
                show_attribute_filter = False
                show_mask_clip = False
                self.cboMaskClip.setVisible(False)
                self.cboAttribute.setVisible(False)
                self.lblMaskClip.setVisible(False)
                self.lblAttribute.setVisible(False)
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

        if self.qris_mask is not None:
            self.txtName.setText(mask.name)
            self.txtDescription.setPlainText(mask.description)
            self.chkAddToMap.setCheckState(QtCore.Qt.Unchecked)
            self.chkAddToMap.setVisible(False)

        self.grid.setGeometry(QtCore.QRect(0, 0, self.width(), self.height()))
        self.txtName.setFocus()

    def promote_to_aoi(self, db_item: DBItem):

        self.txtName.setText(db_item.name)
        self.setWindowTitle(f'Promote {db_item.name} to AOI')

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
        # add layer name and id to system metadata
        self.metadata_widget.add_system_metadata('source_layer', layer_name)
        self.metadata_widget.add_system_metadata('source_layer_id', db_item.id)

    def accept(self):

        if not validate_name(self, self.txtName):
            return

        metadata_json = self.metadata_widget.get_json()
        metadata = json.loads(metadata_json) if metadata_json is not None else None

        try:
            if self.qris_mask is not None:
                self.qris_mask.update(self.qris_project.project_file, self.txtName.text(), self.txtDescription.toPlainText(), metadata)
            else:
                self.qris_mask = insert_mask(self.qris_project.project_file, self.txtName.text(), self.mask_type, self.txtDescription.toPlainText(), metadata)
                self.qris_project.masks[self.qris_mask.id] = self.qris_mask
                self.qris_project.aois[self.qris_mask.id] = self.qris_mask
        except Exception as ex:
            if 'unique' in str(ex).lower():
                QtWidgets.QMessageBox.warning(self, 'Duplicate Name', f"A {self.str_mask_type} with the name '{self.txtName.text()}' already exists. Please choose a unique name.")
                self.txtName.setFocus()
            else:
                QtWidgets.QMessageBox.warning(self, f'Error Saving {self.str_mask_type}', str(ex))
            return

        if self.import_source_path is not None:
            try:
                mask_layer_name = "aoi_features" if self.mask_type.id == AOI_MASK_TYPE_ID else "mask_features"
                mask_path = f'{self.qris_project.project_file}|layername={mask_layer_name}'
                layer_attributes = {'mask_id': self.qris_mask.id}
                field_map = [ImportFieldMap(self.cboAttribute.currentData(QtCore.Qt.UserRole).name, 'display_label', direct_copy=True)] if self.cboAttribute.isVisible() else None
                clip_mask = None
                clip_item = self.cboMaskClip.currentData(QtCore.Qt.UserRole)
                if clip_item is not None:
                    if clip_item.id > 0:        
                        clip_mask = ('aoi_features', 'mask_id', clip_item.id)
                
                if self.layer_id == 'memory':
                    import_mask_task = ImportTemporaryLayer(self.import_source_path, mask_path, layer_attributes, field_map, clip_mask, self.attribute_filter, self.qris_project.project_file)
                else:
                    import_mask_task = ImportFeatureClass(self.import_source_path, mask_path, layer_attributes, field_map, clip_mask, self.attribute_filter, self.qris_project.project_file, explode_geometries=False)
                # DEBUG
                # result = import_mask_task.run()
                # self.on_import_complete(result)
                # PRODUCTION
                import_mask_task.import_complete.connect(self.on_import_complete)
                QgsApplication.taskManager().addTask(import_mask_task)
            except Exception as ex:
                try:
                    self.qris_mask.delete(self.qris_project.project_file)
                    QgsApplication.messageLog().logMessage(f'Error Importing {self.str_mask_type}: {str(ex)}', 'QRIS', level=Qgis.Critical)
                    iface.messageBar().pushMessage(f'Error Importing {self.str_mask_type}', str(ex), level=Qgis.Critical, duration=5)
                except Exception as ex_delete:
                    QgsApplication.messageLog().logMessage(f'Error Deleting {self.str_mask_type}: {str(ex_delete)}', 'QRIS', level=Qgis.Critical)
                    iface.messageBar().pushMessage(f'Error Deleting {self.str_mask_type}', str(ex_delete), level=Qgis.Critical, duration=5)
                return
        else:
            super(FrmMaskAOI, self).accept()

    def on_import_complete(self, result: bool):

        if result is True:
            iface.messageBar().pushMessage(f'{self.str_mask_type} Imported', f'{self.str_mask_type} "{self.txtName.text()}" has been imported successfully.', level=Qgis.Success, duration=5)
        else:
            QgsApplication.messageLog().logMessage(f'Error Importing {self.str_mask_type} Features', 'QRIS', level=Qgis.Critical)
            try:
                self.qris_mask.delete(self.qris_project.project_file)
            except Exception as ex:
                QgsApplication.messageLog().logMessage(f'Error Deleting {self.str_mask_type}: {str(ex)}', 'QRIS', level=Qgis.Critical)
                iface.messageBar().pushMessage(f'Error Deleting {self.str_mask_type}', str(ex), level=Qgis.Critical, duration=5)
            return
        super(FrmMaskAOI, self).accept()

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
        self.txtName.setToolTip('The name of the AOI or Sample Frame')
        self.txtName.setMaxLength(255)
        self.grid.addWidget(self.txtName, 0, 1, 1, 1)

        self.lblAttribute = QtWidgets.QLabel('Sample Frame Labels')
        self.grid.addWidget(self.lblAttribute, 1, 0, 1, 1)

        self.cboAttribute = QtWidgets.QComboBox()
        self.cboAttribute.setToolTip('The attribute field to use for labeling the Sample Frames')
        self.grid.addWidget(self.cboAttribute, 1, 1, 1, 1)

        self.lblMaskClip = QtWidgets.QLabel('Clip to AOI')
        self.grid.addWidget(self.lblMaskClip, 2, 0, 1, 1)

        self.cboMaskClip = QtWidgets.QComboBox()
        self.cboMaskClip.setToolTip('Clip the AOI to the boundary of another AOI')
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

        self.chkAddToMap = QtWidgets.QCheckBox()
        self.chkAddToMap.setChecked(True)
        self.chkAddToMap.setText('Add to Map')
        self.grid.addWidget(self.chkAddToMap, 4, 1, 1, 1)

        help = 'aoi' if self.mask_type.id == AOI_MASK_TYPE_ID else 'sample-frames'
        self.vert.addLayout(add_standard_form_buttons(self, help))
