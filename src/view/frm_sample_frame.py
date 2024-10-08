import os
import json

from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtCore import Qt, QSize, QVariant, pyqtSignal
from PyQt5.QtWidgets import QWidget, QDialog, QMessageBox, QVBoxLayout, QHBoxLayout,  QGridLayout, QTabWidget, QGroupBox, QTreeView, QListWidget, QListWidgetItem, QComboBox, QLabel, QTextEdit, QLineEdit, QCheckBox, QPushButton

from qgis.core import Qgis, QgsApplication, QgsVectorLayer, QgsWkbTypes
from qgis.utils import iface

from ..model.project import Project
from ..model.db_item import DBItem, DBItemModel
from ..model.pour_point import PourPoint
from ..model.scratch_vector import ScratchVector
from ..model.mask import Mask, AOI_MASK_TYPE_ID
from ..model.sample_frame import SampleFrame, insert_sample_frame

from .frm_new_attribute import FrmNewAttribute

from ..gp.feature_class_functions import layer_path_parser
from ..gp.import_feature_class import ImportFeatureClass, ImportFieldMap
from ..gp.import_temp_layer import ImportTemporaryLayer
from ..gp.sample_frame import SampleFrameTask

from .widgets.metadata import MetadataWidget
from .utilities import validate_name, validate_name_unique, add_standard_form_buttons

# Text constants
flow_path = 'Flow Path' # level path
attributes_name = 'Categories'
default_flow_path_name = 'unknown'
flow_path_field_name = 'flow_path'
flows_into_field_name = 'flows_into'
label_field_name = 'display_label'


class FrmSampleFrame(QDialog):

    complete = pyqtSignal(bool)

    def __init__(self, parent, project: Project, import_source_path: str = None, sample_frame: SampleFrame = None, create_sample_frame: bool = False):
        
        self.qris_project = project
        self.sample_frame = sample_frame
        self.import_source_path = import_source_path
        self.create_sample_frame = create_sample_frame

        super(FrmSampleFrame, self).__init__(parent)
        self.setWindowTitle(f'Create New (Empty) Sample Frame')
        
        # Figure out what tabs we need 
        self.tab_inputs = None
        self.tab_attributes = None # just in case
        self.attribute_filter = None

        if self.import_source_path is not None:
            if isinstance(self.import_source_path, QgsVectorLayer):
                self.tab_inputs = SampleFrameInputs(self, self.qris_project, self.import_source_path)
                self.tab_attributes = SampleFrameAttributesAddFields(self, self.import_source_path)
                self.setWindowTitle(f'Import New Sample Frame From Temporary Layer')
            else:
                self.tab_inputs = SampleFrameInputs(self, self.qris_project, self.import_source_path)
                self.tab_attributes = SampleFrameAttributesAddFields(self, self.import_source_path)
                self.setWindowTitle(f'Import New Sample Frame From Feature Class')
        else:
            self.tab_attributes = SampleFrameAttributes(self, self.sample_frame)
        
        if create_sample_frame is True:
            self.tab_inputs = SampleFrameInputsCreate(self, self.qris_project)
            self.setWindowTitle(f'Create New Sample Frame from Existing Layers')
            
        self.tab_properties = SampleFrameProperties(self, self.sample_frame)

        metadata_json = json.dumps(sample_frame.user_metadata) if sample_frame is not None else None
        self.metadata_widget = MetadataWidget(self, metadata_json)

        self.setupUi()
        if sample_frame is not None:
            self.setWindowTitle(f'Sample Frame Properties')
            self.txtName.setText(self.sample_frame.name)
        else:
            self.txtName.setFocus()

    def set_inputs(self, cross_sections=None, polygon=None):
            
        if cross_sections is not None:
            self.tab_inputs.cboCrossSections.setCurrentIndex(self.tab_inputs.cross_sections_model.getItemIndex(cross_sections))
        if polygon is not None:
            self.tab_inputs.cboFramePolygon.setCurrentIndex(self.tab_inputs.polygons_model.getItemIndex(polygon))

    def promote_to_sample_frame(self, db_item: DBItem):

        self.txtName.setText(db_item.name)
        self.setWindowTitle(f'Promote {db_item.name} to Sample Frame')

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

        self.tab_inputs = SampleFrameInputs(self, self.qris_project, self.import_source_path)
        self.tabs.addTab(self.tab_inputs, "Inputs")
        self.basepath, self.layer_name, self.layer_id = layer_path_parser(self.import_source_path)

        metadata_json = json.dumps(db_item.metadata) if db_item.metadata is not None else None
        self.metadata_widget.load_json(metadata_json)

    def accept(self):
         
        # validate name
        if not validate_name(self, self.txtName):
            return  
        
        # validate name is unique
        if self.sample_frame is None:
            if not validate_name_unique(self.qris_project.project_file, 'sample_frames', 'name', self.txtName.text()):
                QMessageBox.warning(self, 'Duplicate Name', f"A sample frame with the name '{self.txtName.text()}' already exists. Please choose a unique name.")
                return

        metadata_json = self.metadata_widget.get_json()
        metadata = json.loads(metadata_json) if metadata_json is not None else None
        fields = self.tab_attributes.get_fields() if self.tab_attributes is not None else None

        out_metadata = {}
        if fields is not None:
            out_metadata['fields'] = fields
        if metadata is not None:
            out_metadata['metadata'] = metadata
        # add other items to the metadata
        out_metadata['default_flow_path_name'] = self.tab_properties.txtDefaultFlowPathName.text()

        try:
            if self.sample_frame is not None:
                self.sample_frame.update(self.qris_project.project_file, self.txtName.text(), self.tab_properties.txtDescription.toPlainText(), out_metadata)
            else:
                self.sample_frame = insert_sample_frame(self.qris_project.project_file, self.txtName.text(), self.tab_properties.txtDescription.toPlainText(), out_metadata)
                self.qris_project.sample_frames[self.sample_frame.id] = self.sample_frame            
        except Exception as ex:
            if 'unique' in str(ex).lower():
                QMessageBox.warning(self, 'Duplicate Name', f"A sample frame with the name '{self.txtName.text()}' already exists. Please choose a unique name.")
                self.txtName.setFocus()
            else:
                QMessageBox.warning(self, 'Error Saving sample frame', str(ex))
            return

        if self.import_source_path is not None:
            try:
                # set the ok and cancel buttons to disabled
                self.buttonBox.setEnabled(False)

                sample_frame_path = f'{self.qris_project.project_file}|layername=sample_frame_features'
                out_field_map = self.get_field_map()
                if self.tab_inputs is not None:
                    if isinstance(self.tab_inputs, SampleFrameInputs):
                        if self.tab_inputs.cboDisplayLabel.currentIndex() > 0:
                            out_field_map.append(ImportFieldMap(self.tab_inputs.cboDisplayLabel.currentText(), 'display_label', direct_copy=True))
                        if self.tab_inputs.cboFlowPathField.currentIndex() > 0:
                            out_field_map.append(ImportFieldMap(self.tab_inputs.cboFlowPathField.currentText(), 'flow_path', direct_copy=True))
                        if self.tab_inputs.cboTopologyField.currentIndex() > 0:
                            out_field_map.append(ImportFieldMap(self.tab_inputs.cboTopologyField.currentText(), 'topology', direct_copy=True))

                clip_mask = None
                if self.tab_inputs is not None:
                    clip_item = self.tab_inputs.cboClipToAOI.currentData(Qt.UserRole)
                    if clip_item is not None:
                        if clip_item.id > 0:        
                            clip_mask = ('aoi_features', 'mask_id', clip_item.id)
                
                attributes = {}
                attributes['sample_frame_id'] = self.sample_frame.id
                
                if isinstance(self.import_source_path, QgsVectorLayer):
                    import_mask_task = ImportTemporaryLayer(self.import_source_path, sample_frame_path, attributes, out_field_map, clip_mask, self.attribute_filter, self.qris_project.project_file)
                else:
                    import_mask_task = ImportFeatureClass(self.import_source_path, sample_frame_path, attributes, out_field_map, clip_mask, attribute_filter=self.attribute_filter, proj_gpkg=self.qris_project.project_file)
                # # DEBUG
                # result = import_mask_task.run()
                # self.on_import_complete(result)
                # PRODUCTION
                import_mask_task.import_complete.connect(self.on_import_complete)
                QgsApplication.taskManager().addTask(import_mask_task)
                return
            except Exception as ex:
                try:
                    self.sample_frame.delete(self.qris_project.project_file)
                except Exception as ex:
                    print(f'Error attempting to delete sample_frame after the importing of features failed.')
                    QMessageBox.warning(self, f'Error Importing Sample Frame Features', str(ex))
                    # enable the buttons
                    self.buttonBox.setEnabled(True)
                return
            # finally:
                # # enable the buttons
                # self.buttonBox.button(QMessageBox.Ok).setEnabled(True)
                # self.buttonBox.button(QMessageBox.Cancel).setEnabled(True)
        if self.create_sample_frame is True:
            try:
                db_item_polygon = self.tab_inputs.cboFramePolygon.currentData(Qt.UserRole)
                if isinstance(db_item_polygon, DBItem):
                    polygon_layer = QgsVectorLayer(f'{self.qris_project.project_file}|layername={db_item_polygon.fc_name}')
                    polygon_layer.setSubsetString(f'{db_item_polygon.fc_id_column_name} = {db_item_polygon.id}')
                else:
                    polygon_layer = QgsVectorLayer(f'{db_item_polygon.gpkg_path}|layername={db_item_polygon.fc_name}')
                cross_sections = self.tab_inputs.cboCrossSections.currentData(Qt.UserRole)
                cross_sections_layer = QgsVectorLayer(f'{self.qris_project.project_file}|layername=cross_section_features')
                cross_sections_layer.setSubsetString(f'cross_section_id = {cross_sections.id}')
                out_path = f'{self.qris_project.project_file}|layername=sample_frame_features'
                task = SampleFrameTask(polygon_layer, cross_sections_layer, out_path, self.sample_frame.id)
                task.sample_frame_complete.connect(self.on_import_complete)
                QgsApplication.taskManager().addTask(task)
                return
            except Exception as ex:
                try:
                    self.sample_frame.delete(self.qris_project.project_file)
                    QgsApplication.messageLog().logMessage(f'Error Importing Sample Frame Features: {str(ex)}', 'QRIS', level=Qgis.Critical)
                except Exception as ex:
                    QgsApplication.messageLog().logMessage(f'Error Deleting sample frame: {str(ex)}', 'QRIS', level=Qgis.Critical)
                return
            
        self.complete.emit(True)
        super(FrmSampleFrame, self).accept()
        return

    def get_field_map(self):

        field_map = []
        # if self.tab_inputs is not None:
        #     for field in self.tab_inputs.load_fields():
        #         field_map.append(ImportFieldMap(field, field, True))
        if self.tab_attributes is not None:
            for field_dict in self.tab_attributes.get_fields():
                field = field_dict['label']
                field_map.append(ImportFieldMap(field, field, parent='attributes'))
        return field_map

    def on_import_complete(self, result):
        if result is True:
            iface.messageBar().pushMessage(f'Sample Frame Imported', f'Sample Frame "{self.txtName.text()}" has been created successfully.', level=Qgis.Success, duration=5)
            self.complete.emit(True)
            super(FrmSampleFrame, self).accept()
        else:
            QgsApplication.messageLog().logMessage(f'Error Importing Sample Frame Features', 'QRIS', level=Qgis.Critical)
            try:
                self.sample_frame.delete(self.qris_project.project_file)
            except Exception as ex:
                QgsApplication.messageLog().logMessage(f'Error Deleting sample frame: {str(ex)}', 'QRIS', level=Qgis.Critical)
                iface.messageBar().pushMessage(f'Error Deleting sample frame', str(ex), level=Qgis.Critical, duration=5)
                super(FrmSampleFrame, self).accept()
            return

    def setupUi(self):

        self.resize(500, 400)
        self.setMinimumSize(QSize(500, 400))

        self.vert = QVBoxLayout(self)
        self.setLayout(self.vert)

        self.horiz_name = QHBoxLayout()
        self.vert.addLayout(self.horiz_name)

        self.lblName = QLabel('Name')
        self.horiz_name.addWidget(self.lblName)
        self.txtName = QLineEdit()
        self.txtName.setToolTip('The name of the sample frame')
        self.horiz_name.addWidget(self.txtName)

        self.tabs = QTabWidget(self)
        self.vert.addWidget(self.tabs)

        if self.tab_inputs is not None:
            self.tabs.addTab(self.tab_inputs, "Inputs")
        self.tabs.addTab(self.tab_properties, "Basic Properties")        
        self.tabs.addTab(self.tab_attributes, attributes_name)
        self.tabs.addTab(self.metadata_widget, "Metadata")

        self.chkAddToMap = QCheckBox('Add to Map')
        self.chkAddToMap.setChecked(True)
        self.vert.addWidget(self.chkAddToMap)

        self.buttonBox = add_standard_form_buttons(self, 'sampling-frames')
        self.vert.addLayout(self.buttonBox)


class SampleFrameInputs(QWidget):

    def __init__(self, parent, qris_project, import_feature_class = None):
        super(SampleFrameInputs, self).__init__(parent)

        self.qris_project = qris_project
        self.import_feature_class = import_feature_class
        name = self.import_feature_class.name() if isinstance(self.import_feature_class, QgsVectorLayer) else self.import_feature_class

        self.setupUi()
        self.txtImport.setText(name)
        self.load_fields()
        self.load_clip_to_aoi()


    def load_fields(self):
            
            # clear fields
            self.cboDisplayLabel.clear()
            self.cboFlowPathField.clear()
            self.cboTopologyField.clear()

            # add None option
            self.cboDisplayLabel.addItem('None')
            self.cboFlowPathField.addItem('None')
            self.cboTopologyField.addItem('None')

            # use QgsVectorLayer to get fields
            if self.import_feature_class is not None:
                if isinstance(self.import_feature_class, QgsVectorLayer):
                    layer = self.import_feature_class
                else:
                    layer = QgsVectorLayer(self.import_feature_class, 'temp', 'ogr')
                fields = layer.fields()
                for field in fields:
                    self.cboDisplayLabel.addItem(field.name())
                    self.cboFlowPathField.addItem(field.name())
                    if field.type() in [QVariant.Int, QVariant.Double]: # integer
                        self.cboTopologyField.addItem(field.name())

    def load_clip_to_aoi(self):
        # get the aoi from the project
        self.cboClipToAOI.clear()

        aois = {id: mask for id, mask in self.qris_project.aois.items()}
        no_aoi = DBItem('None', 0, 'None - Retain full dataset extent')
        aois[0] = no_aoi
        aoi_model = DBItemModel(aois)
        self.cboClipToAOI.setModel(aoi_model)


    def setupUi(self):

        self.vert = QVBoxLayout(self)
        self.setLayout(self.vert)

        self.grid = QGridLayout(self)
        self.vert.addLayout(self.grid)

        self.lblImport = QLabel('Import Path')
        self.grid.addWidget(self.lblImport, 0, 0)
        self.txtImport = QLineEdit()
        self.txtImport.setEnabled(False)
        self.grid.addWidget(self.txtImport, 0, 1)
        # self.cmdImport = QPushButton('...')
        # self.cmdImport.clicked.connect(self.cmdImport_clicked)
        # self.grid.addWidget(self.cmdImport, 0, 2)

        self.lblName = QLabel('Display Labels Field')
        self.grid.addWidget(self.lblName, 1, 0)
        self.cboDisplayLabel = QComboBox()
        self.cboDisplayLabel.setToolTip('Field to use for display labels.')
        self.grid.addWidget(self.cboDisplayLabel, 1, 1, 1, 2)
        
        self.lblFlowPathField = QLabel(f'{flow_path} Field')
        self.grid.addWidget(self.lblFlowPathField, 2, 0)
        self.cboFlowPathField = QComboBox()
        self.cboFlowPathField.setToolTip('Field to specify unique flow path names.')
        self.grid.addWidget(self.cboFlowPathField, 2, 1, 1, 2)

        self.lblTopologyField = QLabel('Topology Field')
        self.grid.addWidget(self.lblTopologyField, 3, 0)
        self.cboTopologyField = QComboBox()
        self.cboTopologyField.setToolTip('Field to use for topology inference. Should be an integer field with unique ordered values.')
        self.grid.addWidget(self.cboTopologyField, 3, 1, 1, 2)

        self.lblClipToAOI = QLabel('Clip to AOI')
        self.grid.addWidget(self.lblClipToAOI, 4, 0)
        self.cboClipToAOI = QComboBox()
        self.cboClipToAOI.setToolTip('Optionally clip the sample frame to the selected AOI')
        self.grid.addWidget(self.cboClipToAOI, 4, 1, 1, 2)

        self.vert.addStretch()

class SampleFrameInputsCreate(QWidget):

    def __init__(self, parent, project: Project = None):
        super(SampleFrameInputsCreate, self).__init__(parent)

        self.qris_project = project

        self.setupUi()
        self.load_layers()

    def load_layers(self):

        self.cboFramePolygon.clear()
        self.cboCenterline.clear()
        self.cboCrossSections.clear()

        # Set Cross Sections, set init if exists
        cross_sections = {id: xsection for id, xsection in self.qris_project.cross_sections.items()}
        self.cross_sections_model = DBItemModel(cross_sections)
        self.cboCrossSections.setModel(self.cross_sections_model)
        # if cross_sections_init is not None:
        #     self.cboCrossSections.setCurrentIndex(self.cross_sections_model.getItemIndex(cross_sections_init))

        # Masks (filtered to just AOI)
        aois = {f'aoi_{id}': aoi for id, aoi in self.qris_project.aois.items()}
        valley_bottoms = {f'valley_bottom_{id}': valley_bottom for id, valley_bottom in self.qris_project.valley_bottoms.items()}
        # context = {f'context_{id}': layer for id, layer in self.qris_project.scratch_vectors.items() if QgsVectorLayer(f'{layer.gpkg_path}|layername={layer.fc_name}').geometryType() == QgsWkbTypes.PolygonGeometry}
        self.polygons = {**valley_bottoms, **aois}
        self.polygons_model = DBItemModel(self.polygons)
        self.cboFramePolygon.setModel(self.polygons_model)
        # if polygon_init is not None:
        #     index = self.polygons_model.getItemIndex(polygon_init)
        #     if index is not None:
        #         self.cboFramePolygon.setCurrentIndex(index)

        # Centerlines
        centerlines = {id: centerline for id, centerline in self.qris_project.profiles.items()}
        self.centerlines_model = DBItemModel(centerlines)
        self.cboCenterline.setModel(self.centerlines_model)


    def setupUi(self):
            
            self.vert = QVBoxLayout(self)
            self.setLayout(self.vert)
    
            self.grid = QGridLayout(self)
            self.vert.addLayout(self.grid)
    
            self.lblPolygon = QLabel('Polygon Layer')
            self.grid.addWidget(self.lblPolygon, 0, 0)
            self.cboFramePolygon = QComboBox()
            self.grid.addWidget(self.cboFramePolygon, 0, 1, 1, 2)

            self.lblCenterline = QLabel('Centerline')
            self.grid.addWidget(self.lblCenterline, 1, 0)
            self.cboCenterline = QComboBox()
            self.grid.addWidget(self.cboCenterline, 1, 1, 1, 2)

            self.lblCrossSections = QLabel('Cross Sections')
            self.grid.addWidget(self.lblCrossSections, 2, 0)
            self.cboCrossSections = QComboBox()
            self.grid.addWidget(self.cboCrossSections, 2, 1, 1, 2)

            self.chkInferTopology = QCheckBox('Infer Topology from Centerline')
            self.grid.addWidget(self.chkInferTopology, 3, 0)
    
            self.vert.addStretch()


class SampleFrameProperties(QWidget):

    def __init__(self, parent, sample_frame: SampleFrame = None):
        super(SampleFrameProperties, self).__init__(parent)

        self.sample_frame = sample_frame

        self.setupUi()

        self.txtLabelField.setText(label_field_name)
        self.txtFlowField.setText(flow_path_field_name)

        if self.sample_frame is not None:
            self.txtDescription.setText(self.sample_frame.description)
            self.txtDefaultFlowPathName.setText(self.sample_frame.default_flow_path_name)
            self.txtDefaultFlowPathName.setEnabled(False)
        else:
            self.txtDefaultFlowPathName.setText(default_flow_path_name)
                        
    def setupUi(self):

        self.vert = QVBoxLayout(self)
        self.grid = QGridLayout()
        self.vert.addLayout(self.grid)

        self.lblLabelField = QLabel('Labels Field Name')
        self.grid.addWidget(self.lblLabelField, 1, 0)
        self.txtLabelField = QLineEdit()
        self.txtLabelField.setEnabled(False)
        self.grid.addWidget(self.txtLabelField, 1, 1)

        self.lblFlowField = QLabel('Flow Into Field Name')
        self.grid.addWidget(self.lblFlowField, 2, 0)
        self.txtFlowField = QLineEdit()
        self.txtFlowField.setEnabled(False)
        self.grid.addWidget(self.txtFlowField, 2, 1)

        self.lblDefaultFlowPathName = QLabel(f'Default {flow_path} Name')
        self.grid.addWidget(self.lblDefaultFlowPathName, 3, 0)
        self.txtDefaultFlowPathName = QLineEdit()
        self.grid.addWidget(self.txtDefaultFlowPathName, 3, 1)

        self.lblDescription = QLabel('Description')
        self.grid.addWidget(self.lblDescription, 4, 0)
        self.txtDescription = QTextEdit()
        self.grid.addWidget(self.txtDescription, 4, 1)


class SampleFrameAttributes(QWidget):
        
        def __init__(self, parent, sample_frame: SampleFrame = None):
            super(SampleFrameAttributes, self).__init__(parent)
    
            self.sample_frame = sample_frame
            self.model = EditableTreeModel()

            self.setupUi()

            if sample_frame is not None:
                self.load_attributes()

        def load_attributes(self):
                
            # add to model
            for field in self.sample_frame.fields:
                name = field if isinstance(field, str) else field['label']
                values = list() if isinstance(field, str) else field['values']
                item = QStandardItem(name)
                item.setData(values, Qt.UserRole)
                self.model.appendRow(item)
                # add attributes as children
                for attribute in values:
                    child_item = QStandardItem(str(attribute))
                    item.appendRow(child_item)

        def selection_changed(self, selected, deselected):

            if self.sample_frame is None:
                self.cmdEdit.setEnabled(len(selected.indexes()) > 0)
                self.cmdDelete.setEnabled(len(selected.indexes()) > 0)

        def cmdAdd_clicked(self):

            # get list of field names in the model
            existing_fields = [self.model.item(i).text() for i in range(self.model.rowCount())]

            frm = FrmNewAttribute(self, self.sample_frame, existing_fields=existing_fields)
            frm.exec_()

            if frm.result() == QDialog.Accepted:
                if frm.name is not None:
                    self.add_attribute(frm.name, frm.attributes)

        def cmdEdit_clicked(self):
                
                # get list of field names in the model
                existing_fields = [self.model.item(i).text() for i in range(self.model.rowCount())]

                # get selected item
                index = self.treeView.currentIndex()
                item = self.model.itemFromIndex(index)
                field_name = item.text()
    
                # get attributes These are the child nodes of this item
                attributes = [item.child(i).text() for i in range(item.rowCount())]
    
                frm = FrmNewAttribute(self, field_name, attributes, existing_fields)
                frm.exec_()
    
                if frm.result() == QDialog.Accepted:
                    if frm.name is not None:
                        # remove existing item
                        self.model.removeRow(index.row())
    
                        # add new item
                        self.add_attribute(frm.name, frm.attributes)

        def cmdDelete_clicked(self):
                    
                    # get selected item
                    index = self.treeView.currentIndex()
                    item = self.model.itemFromIndex(index)
        
                    # remove existing item
                    self.model.removeRow(index.row())

        def add_attribute(self, field_name: str, attributes: list):
                
                # add to model
                item = QStandardItem(field_name)
                item.setData(attributes, Qt.UserRole)
                self.model.appendRow(item)
    
                # add attributes as children
                for attribute in attributes:
                    child_item = QStandardItem(attribute)
                    item.appendRow(child_item)

                # add to sample frame
                # self.sample_frame.add_attribute(field_name, attributes)
    
        def get_fields(self):

            fields = []
            for row in range(self.model.rowCount()):
                item = self.model.item(row)
                field_name = item.text()
                machine_code = field_name.lower().replace(' ', '_')
                attributes = [item.child(i).text() for i in range(item.rowCount())]
                fields.append({'machine_code': machine_code, 'label': field_name, 'type': 'list', 'values': attributes})
            return fields

        def setupUi(self):
    
            self.horiz = QHBoxLayout()
            self.setLayout(self.horiz)

            self.treeView = QTreeView(self)
            self.treeView.header().hide()
            self.treeView.setModel(self.model)
            self.treeView.selectionModel().selectionChanged.connect(self.selection_changed)
            self.tree_state = {}

            self.cmdAdd = QPushButton('Add')
            if self.sample_frame is not None:
                self.cmdAdd.setEnabled(False)
            self.cmdAdd.clicked.connect(self.cmdAdd_clicked)

            self.cmdEdit = QPushButton('Edit')
            self.cmdEdit.setEnabled(False)
            self.cmdEdit.clicked.connect(self.cmdEdit_clicked)

            self.cmdDelete = QPushButton('Delete')
            self.cmdDelete.setEnabled(False)
            self.cmdDelete.clicked.connect(self.cmdDelete_clicked)

            # add buttons to layout on left side, then table on right side
            self.vert = QVBoxLayout()
            self.vert.addWidget(self.cmdAdd)
            self.vert.addWidget(self.cmdEdit)
            self.vert.addWidget(self.cmdDelete)
            self.vert.addStretch()

            self.horiz.addLayout(self.vert)
            self.horiz.addWidget(self.treeView)


class SampleFrameAttributesAddFields(QWidget):

    def __init__(self, parent, import_feature_class = None):
        super(SampleFrameAttributesAddFields, self).__init__(parent)

        self.import_feature_class = import_feature_class
        self.fields = self.load_fields()
        self.chk_fields = []

        self.setupUi()

    def load_fields(self):

        # use QgsVectorLayer to get fields
        if self.import_feature_class is not None:
            if isinstance(self.import_feature_class, QgsVectorLayer):
                self.layer: QgsVectorLayer = self.import_feature_class
            else:
                self.layer = QgsVectorLayer(self.import_feature_class, 'temp', 'ogr')
            return self.layer.fields().names()
        
    def get_fields(self):
    
        fields = [chk.text() for chk in self.chk_fields if chk.isChecked()]
        outfields = []
        for field in fields:
            outfield = {'machine_code': field.replace(' ', '_').lower(), 'label': field}
            values = []
            for feature in self.layer.getFeatures():
                value = feature[field]
                if isinstance(value, QVariant):
                    value = None
                if value not in values:
                    values.append(value)
            outfield['values'] = values
            outfields.append(outfield)

        return outfields

    def setupUi(self):

        self.vert = QVBoxLayout(self)
        self.setLayout(self.vert)

        # List of checkboxes for each field in the feature class
        self.lbl_fields = QLabel(f'Import Fields for Sample Frame {attributes_name}')
        self.vert.addWidget(self.lbl_fields)

        self.box = QGroupBox()
        self.box_layout = QVBoxLayout()
        self.box_layout.setAlignment(Qt.AlignTop)
        self.box.setLayout(self.box_layout)

        for field in self.fields:
            chk = QCheckBox(field)
            chk.setChecked(True)
            self.chk_fields.append(chk)
            self.box_layout.addWidget(chk)

        self.vert.addWidget(self.box)

        self.vert.addStretch()


class EditableTreeModel(QStandardItemModel):
    def flags(self, index):
        default_flags = super().flags(index)

        if index.parent().isValid():  # If the item has a parent, it's not a top-level item
            return default_flags & ~Qt.ItemIsSelectable  # Remove the selectable flag
        else:
            return default_flags | Qt.ItemIsEditable  # Add the editable flag for top-level items
        