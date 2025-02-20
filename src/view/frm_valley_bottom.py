import json

from PyQt5 import QtCore, QtGui, QtWidgets
from qgis.core import Qgis, QgsApplication, QgsVectorLayer
from qgis.utils import iface

from ..model.db_item import DBItem, DBItemModel
from ..model.project import Project
from ..model.pour_point import PourPoint
from ..model.sample_frame import SampleFrame, insert_sample_frame
from ..model.scratch_vector import ScratchVector

from ..gp.feature_class_functions import layer_path_parser
from ..gp.import_feature_class import ImportFeatureClass, ImportFieldMap
from ..gp.import_temp_layer import ImportTemporaryLayer

from .widgets.metadata import MetadataWidget
from .utilities import validate_name, add_standard_form_buttons


class FrmValleyBottom(QtWidgets.QDialog):

    def __init__(self, parent, project: Project, import_source_path: str, valley_bottom: SampleFrame = None):

        self.qris_project = project
        self.valley_bottom = valley_bottom
        self.import_source_path = import_source_path
        self.attribute_filter = None

        super(FrmValleyBottom, self).__init__(parent)
        metadata_json = json.dumps(valley_bottom.metadata) if valley_bottom is not None else None
        self.metadata_widget = MetadataWidget(self, metadata_json)
        self.setupUi()

        if self.valley_bottom is not None:
            self.setWindowTitle(f'Edit Valley Bottom Properties')
        elif import_source_path is not None:
            self.setWindowTitle(f'Import Valley Bottom Features')
        else:
            self.setWindowTitle(f'Create New Valley Bottom')

        show_mask_clip = import_source_path is not None
        self.lblMaskClip.setVisible(show_mask_clip)
        self.cboMaskClip.setVisible(show_mask_clip)

        if import_source_path is not None:
            if isinstance(import_source_path, QgsVectorLayer):
                show_mask_clip = True
            # find if import_source_path is shapefile, geopackage, or other
            self.basepath, self.layer_name, self.layer_id = layer_path_parser(import_source_path)

            self.txtName.setText(self.layer_name)
            self.txtName.selectAll()

            # if show_attribute_filter:
            #     vector_layer = import_source_path if isinstance(import_source_path, QgsVectorLayer) else QgsVectorLayer(import_source_path)
            #     self.attributes = {i: DBItem('None', i, vector_layer.attributeDisplayName(i)) for i in vector_layer.attributeList()}
            #     self.attribute_model = DBItemModel(self.attributes)
            #     self.cboAttribute.setModel(self.attribute_model)
            #     # self.cboAttribute.setModelColumn(1)

            if show_mask_clip:
                # Masks (filtered to just AOI)
                self.clipping_masks = {id: aoi for id, aoi in self.qris_project.aois.items()}
                no_clipping = DBItem('None', 0, 'None - Retain full dataset extent')
                self.clipping_masks[0] = no_clipping
                self.masks_model = DBItemModel(self.clipping_masks)
                self.cboMaskClip.setModel(self.masks_model)
                # Default to no mask clipping
                self.cboMaskClip.setCurrentIndex(self.masks_model.getItemIndex(no_clipping))

        if self.valley_bottom is not None:
            self.txtName.setText(valley_bottom.name)
            self.txtDescription.setPlainText(valley_bottom.description)
            self.chkAddToMap.setCheckState(QtCore.Qt.Unchecked)
            self.chkAddToMap.setVisible(False)

        self.grid.setGeometry(QtCore.QRect(0, 0, self.width(), self.height()))
        self.txtName.setFocus()

    def promote_to_valley_bottom(self, db_item: DBItem):

        self.txtName.setText(db_item.name)
        self.setWindowTitle(f'Promote {db_item.name} to Valley Bottom')

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

    def accept(self):

        if not validate_name(self, self.txtName):
            return

        metadata_json = self.metadata_widget.get_json()
        metadata = json.loads(metadata_json) if metadata_json is not None else None

        try:
            if self.valley_bottom is not None:
                self.valley_bottom.update(self.qris_project.project_file, self.txtName.text(), self.txtDescription.toPlainText(), metadata)
            else:
                self.valley_bottom = insert_sample_frame(self.qris_project.project_file, self.txtName.text(), self.txtDescription.toPlainText(), metadata, sample_frame_type=SampleFrame.VALLEY_BOTTOM_SAMPLE_FRAME_TYPE)
                self.qris_project.valley_bottoms[self.valley_bottom.id] = self.valley_bottom
        except Exception as ex:
            if 'unique' in str(ex).lower():
                QtWidgets.QMessageBox.warning(self, 'Duplicate Name', f"A Valley Bottom with the name '{self.txtName.text()}' already exists. Please choose a unique name.")
                self.txtName.setFocus()
            else:
                QtWidgets.QMessageBox.warning(self, f'Error Saving Valley Bottom', str(ex))
            return

        if self.import_source_path is not None:
            try:
                valley_bottom_layer_name = "sample_frame_features"
                valley_bottom_path = f'{self.qris_project.project_file}|layername={valley_bottom_layer_name}'
                layer_attributes = {'sample_frame_id': self.valley_bottom.id}
                #field_map = [ImportFieldMap(self.cboAttribute.currentData(QtCore.Qt.UserRole).name, 'display_label', direct_copy=True)] if self.cboAttribute.isVisible() else None
                field_map = None
                clip_mask = None
                clip_item = self.cboMaskClip.currentData(QtCore.Qt.UserRole)
                if clip_item is not None:
                    if clip_item.id > 0:        
                        clip_mask = ('sample_frame_features', 'sample_frame_id', clip_item.id)
                
                if self.layer_id == 'memory':
                    import_task = ImportTemporaryLayer(self.import_source_path, valley_bottom_path, layer_attributes, field_map, clip_mask, self.attribute_filter, self.qris_project.project_file)
                else:
                    import_task = ImportFeatureClass(self.import_source_path, valley_bottom_path, layer_attributes, field_map, clip_mask, self.attribute_filter, self.qris_project.project_file)
                # DEBUG
                # result = import_task.run()
                # self.on_import_complete(result)
                # PRODUCTION
                import_task.import_complete.connect(self.on_import_complete)
                QgsApplication.taskManager().addTask(import_task)
            except Exception as ex:
                try:
                    self.valley_bottom.delete(self.qris_project.project_file)
                    QgsApplication.messageLog().logMessage(f'Error Importing Valley Bottom: {str(ex)}', 'QRIS', level=Qgis.Critical)
                    iface.messageBar().pushMessage(f'Error Importing Valley Bottom', str(ex), level=Qgis.Critical, duration=5)
                except Exception as ex_delete:
                    QgsApplication.messageLog().logMessage(f'Error Deleting Valley Bottom: {str(ex_delete)}', 'QRIS', level=Qgis.Critical)
                    iface.messageBar().pushMessage(f'Error Deleting Valley Bottom', str(ex_delete), level=Qgis.Critical, duration=5)
                return
        else:
            super(FrmValleyBottom, self).accept()

    def on_import_complete(self, result: bool):

        if result is True:
            iface.messageBar().pushMessage(f'Valley Bottom Imported', f'Valley Bottom "{self.txtName.text()}" has been imported successfully.', level=Qgis.Success, duration=5)
        else:
            QgsApplication.messageLog().logMessage(f'Error Importing Valley Bottom Features', 'QRIS', level=Qgis.Critical)
            try:
                self.valley_bottom.delete(self.qris_project.project_file)
            except Exception as ex:
                QgsApplication.messageLog().logMessage(f'Error Deleting Valley Bottom: {str(ex)}', 'QRIS', level=Qgis.Critical)
                iface.messageBar().pushMessage(f'Error Deleting Valley Bottom', str(ex), level=Qgis.Critical, duration=5)
            return
        
        super(FrmValleyBottom, self).accept()

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
        self.txtName.setToolTip('The name of the valley bottom')
        self.txtName.setMaxLength(255)
        self.grid.addWidget(self.txtName, 0, 1, 1, 1)

        # self.cboAttribute = QtWidgets.QComboBox()
        # self.grid.addWidget(self.cboAttribute, 1, 1, 1, 1)

        self.lblMaskClip = QtWidgets.QLabel('Clip to AOI')
        self.grid.addWidget(self.lblMaskClip, 2, 0, 1, 1)

        self.cboMaskClip = QtWidgets.QComboBox()
        self.grid.addWidget(self.cboMaskClip, 2, 1, 1, 1)

        self.lblDescription = QtWidgets.QLabel()
        self.lblDescription.setText('Description')
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

        self.vert.addLayout(add_standard_form_buttons(self, 'valley_bottom'))
