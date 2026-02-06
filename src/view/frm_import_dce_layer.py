from PyQt5 import QtCore, QtWidgets

from qgis.core import Qgis, QgsApplication, QgsVectorLayer
from qgis.utils import iface

from ..model.project import Project
from ..model.db_item import DBItem, DBItemModel
from ..gp.feature_class_functions import get_field_names, get_field_values
from ..gp.import_feature_class import ImportFeatureClass, ImportFieldMap
from ..gp.import_temp_layer import ImportMapLayer

from .frm_import_dce_field_values import FrmAssignFieldValues
from .utilities import add_standard_form_buttons

from typing import List


retain_text = 'Retain original values as metadata'
map_text = 'Map values to target fields'

class FrmImportDceLayer(QtWidgets.QDialog):

    import_complete = QtCore.pyqtSignal(bool)

    def __init__(self, parent, project: Project, db_item: DBItem, import_path: str):

        self.qris_project = project
        self.db_item = db_item
        self.temp_layer = None
        if isinstance(import_path, QgsVectorLayer):
            self.import_path = import_path.name()
            self.temp_layer = import_path
        else:
            self.import_path = import_path
        source = 'dce_points' if db_item.layer.geom_type == 'Point' else 'dce_lines' if db_item.layer.geom_type == 'Linestring' else 'dce_polygons'
        self.target_path = f'{project.project_file}|layername={source}'
        self.qris_event = next((event for event in self.qris_project.events.values() if event.id == db_item.event_id), None)
        self.field_status = None
        self.field_maps: List[ImportFieldMap] = []
        if self.temp_layer is None:
            self.input_fields, self.input_field_types = get_field_names(self.import_path)
        else:
            self.input_fields = [field.name() for field in self.temp_layer.fields()]
            self.input_field_types = [field.typeName() for field in self.temp_layer.fields()]

        # Get the fields from the layer metadata if it exists
        self.target_fields = {}
        if self.db_item.layer.metadata is not None:
            if 'fields' in self.db_item.layer.metadata.keys():
                for field in self.db_item.layer.metadata['fields']:
                    self.target_fields[field['id']] = field
        self.target_fields['notes'] = {'id': 'notes', 'label': 'Notes', 'type': 'string', 'required': False}

        super(FrmImportDceLayer, self).__init__(parent)
        self.setupUi()

        self.setWindowTitle('Import DCE Layer From Existing Feature Class')
        self.txtInputFC.setText(self.import_path)
        self.txtTargetFC.setText(self.db_item.layer.layer_id)
        self.txtEvent.setText(self.qris_event.name)

        # Masks (filtered to just AOI)
        self.clipping_masks = {id: aoi for id, aoi in self.qris_project.aois.items()}
        no_clipping = DBItem('None', 0, 'None - Retain full dataset extent')
        self.clipping_masks[0] = no_clipping
        self.masks_model = DBItemModel(self.clipping_masks)
        self.cboMaskClip.setModel(self.masks_model)
        # Default to no mask clipping
        self.cboMaskClip.setCurrentIndex(self.masks_model.getItemIndex(no_clipping))

        self.load_fields()

    def load_fields(self):

        self.tblFields.clearContents()

        # create a row for each target field and load the field name
        self.tblFields.setRowCount(len(self.input_fields))
        for i, input_field in enumerate(self.input_fields):
            input_field_type = self.input_field_types[i]
            input_field_type = input_field_type.lower() if isinstance(input_field_type, str) else input_field_type
            self.tblFields.setItem(i, 0, QtWidgets.QTableWidgetItem(input_field))
            self.tblFields.setItem(i, 1, QtWidgets.QTableWidgetItem(input_field_type))

            # add button to open value map dialog
            chk_retain = QtWidgets.QCheckBox(f'{input_field} (metadata)')
            chk_retain.setToolTip(retain_text)
            chk_retain.setChecked(True)
            self.tblFields.setCellWidget(i, 2, chk_retain)

            transfer_widget = QtWidgets.QWidget()
            layout = QtWidgets.QHBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
            layout.setSpacing(0)                   # Remove spacing
            transfer_widget.setLayout(layout)
            transfer_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)  # Expand vertically

            chk_map = QtWidgets.QCheckBox()
            chk_map.setChecked(False)
            chk_map.setToolTip(map_text)
            chk_map.clicked.connect(lambda checked, row=i: self.open_value_map_dialog(row) if checked else None)
            layout.addWidget(chk_map)
            
            btn = QtWidgets.QPushButton('Assign...')
            btn.setToolTip(map_text)
            btn.clicked.connect(lambda _, row=i: self.open_value_map_dialog(row))
            layout.addWidget(btn)

            self.tblFields.setCellWidget(i, 3, transfer_widget)
            
            copy_widget = QtWidgets.QWidget()
            copy_layout = QtWidgets.QHBoxLayout()
            copy_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
            copy_layout.setSpacing(0)                   # Remove spacing
            copy_widget.setLayout(copy_layout)
            copy_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)  # Expand vertically
            # checkbox to copy the value to the target field. add a combobox to select the target field
            chk_copy = QtWidgets.QCheckBox()
            chk_copy.setToolTip('Copy value to target field')
            chk_copy.setChecked(False)
            copy_layout.addWidget(chk_copy)

            combo = QtWidgets.QComboBox()
            input_fields = [field['label'] for field in self.target_fields.values() if field.get('type', None) == input_field_type and field['id'] != 'event_id']
            if len(input_fields) == 0:
                combo.setToolTip('No target fields available for this input data type')
                combo.addItem('- No Target Fields for Input Data Type -', None)
                chk_copy.setEnabled(False)  # Disable checkbox if no target fields available
            else:
                combo.setToolTip('Select target field to copy value to')
                for field in self.target_fields.values():
                    if field.get('type', None) == input_field_type and field['id'] != 'event_id':
                        combo.addItem(field['label'], field['id'])
                chk_copy.toggled.connect(lambda checked, c=combo: c.setEnabled(checked))  # Enable/disable combo based on checkbox state
            combo.setEnabled(False)  # Initially disabled
            copy_layout.addWidget(combo)
            self.tblFields.setCellWidget(i, 4, copy_widget)

        self.tblFields.resizeColumnsToContents()

    def open_value_map_dialog(self, row: int):
        # get the field name
        input_field = self.tblFields.item(row, 0).text()

        # get the field values
        if self.temp_layer is not None:
            # iterate through the features in the layer and get the unique values for the field
            values = []
            for feature in self.temp_layer.getFeatures():
                value = feature[input_field]
                if value not in values:
                    values.append(value)
        else:
            values = get_field_values(self.import_path, input_field)
        # get dict of target fields and values
        fields = {}
        for target_field_name, target_field in self.target_fields.items():
            if target_field_name in ['event_id', 'metadata']:
                continue
            # find the lookup table in the project that matches the field name
            if target_field.get('type', None) == 'list':
                fields[target_field_name] = target_field.get('values', [])

        # open the value map dialog
        frm = FrmAssignFieldValues(input_field, values, fields)
        if input_field in [field.src_field for field in self.field_maps]:
            in_field = next((field for field in self.field_maps if field.src_field == input_field), None)
            frm.load_field_value_map(in_field.map)
        frm.field_value_map_signal.connect(self.on_field_value_map)
        frm.exec_()

    def on_field_value_map(self, field_name: str, field_value_map: dict):

        # add or replace the field value map for the field
        if field_name in [field.src_field for field in self.field_maps]:
            self.field_maps.remove(next((field for field in self.field_maps if field.src_field == field_name), None))
        field_map = ImportFieldMap(field_name, map=field_value_map, parent='attributes')
        self.field_maps.append(field_map)

        # check the map checkbox
        for i in range(self.tblFields.rowCount()):
            if self.tblFields.item(i, 0).text() == field_name:
                transfer_widget: QtWidgets.QWidget = self.tblFields.cellWidget(i, 3)
                chk_map: QtWidgets.QCheckBox = transfer_widget.layout().itemAt(0).widget()
                chk_map.setChecked(True)
                break

    def validate_fields(self, field_maps):

        # check that none of the input fields are duplicated, except for the 'Do Not Import' option
        input_fields = []
        valid = True

        # make sure that the destination fields in the field maps are not duplicated
        for field in field_maps:
            if field.map is None:
                continue
            # get the destination fields from the keys of the first entry in the field map. 
            # All entries in the field map should have the same destination fields
            map_keys = list(field.map.keys())
            if len(map_keys) == 0:
                continue
            for dest_field in field.map[map_keys[0]].keys():
                if dest_field in input_fields:
                    # display a message box to the user
                    QtWidgets.QMessageBox.critical(self, 'Duplicate Field', f'The field {dest_field} is mapped to more than one input field. Please correct and try again.')
                    valid = False
                    break
                input_fields.append(dest_field)

        return valid

    def accept(self):

        # make a local copy of the field maps. do not modify the field maps in the layer metadata
        field_maps = self.field_maps.copy()
        # remove the field maps where the map checkbox is not checked
        for i in range(self.tblFields.rowCount()):
            transfer_widget: QtWidgets.QWidget = self.tblFields.cellWidget(i, 3)
            chk_map: QtWidgets.QCheckBox = transfer_widget.layout().itemAt(0).widget()
            if not chk_map.isChecked():
                field_name = self.tblFields.item(i, 0).text()
                # remove the field map from the list if it exists
                if field_name in [field.src_field for field in field_maps]:
                    field_maps.remove(next((field for field in field_maps if field.src_field == field_name), None))

        # Add the copy values to the field maps
        for i in range(self.tblFields.rowCount()):
            copy_widget: QtWidgets.QWidget = self.tblFields.cellWidget(i, 4)
            chk_copy: QtWidgets.QCheckBox = copy_widget.layout().itemAt(0).widget()
            if chk_copy.isChecked():
                field_name = self.tblFields.item(i, 0).text()
                target_field = copy_widget.layout().itemAt(1).widget().currentData(QtCore.Qt.UserRole)
                if target_field != '- No Target Fields for Input Data Type -':
                    field_map = ImportFieldMap(field_name, target_field, parent='attributes', direct_copy=False)
                    field_maps.append(field_map)

        if not self.validate_fields(field_maps):
            return

        # get list of fields where the retain checkbox is checked and add the field to the metadata
        for i in range(self.tblFields.rowCount()):
            chk_retain: QtWidgets.QCheckBox = self.tblFields.cellWidget(i, 2)
            if chk_retain.isChecked():
                field_name = self.tblFields.item(i, 0).text()
                field_map = ImportFieldMap(field_name, field_name, parent='metadata')
                field_maps.append(field_map)

        try:
            layer_attributes = {'event_id': self.db_item.event_id, 'event_layer_id': self.db_item.layer.id}
            
            clip_mask = None
            clip_item = self.cboMaskClip.currentData(QtCore.Qt.UserRole)
            if clip_item is not None:
                if clip_item.id > 0:        
                    clip_mask = ('sample_frame_features', 'sample_frame_id', clip_item.id)


            if self.temp_layer is not None:
                import_task = ImportMapLayer(self.temp_layer, self.target_path, layer_attributes, field_maps, clip_mask)
            else:
                import_task = ImportFeatureClass(self.import_path, self.target_path, layer_attributes, field_maps, clip_mask)
            # self.buttonBox.setEnabled(False)
            # DEBUG
            # result = import_task.run()
            # source_feats = import_task.in_feats
            # out_feats = import_task.out_feats
            # skip_feats = import_task.skipped_feats
            # self.on_import_complete(result, source_feats, out_feats, skip_feats)
            # PRODUCTION
            import_task.import_complete.connect(self.on_import_complete)
            QgsApplication.taskManager().addTask(import_task)
        except Exception as ex:
            self.exception = ex
            self.buttonBox.setEnabled(True)
            return False

    def on_import_complete(self, result: bool, source_feats: int, out_feats: int, skip_feats: int):

        if result is True:
            severity = Qgis.Success if source_feats == out_feats else Qgis.Warning
            extra_message = '' if source_feats == out_feats else f' (additional features were created due to exploding multi-part geometries.)'
            extra_message += f' {skip_feats} features were skipped due to missing or invalid geometry.'
            iface.messageBar().pushMessage('Import Feature Class Complete.', f"Successfully imported {source_feats} features from {self.import_path} to {out_feats} features in {self.db_item.layer.layer_id}.{extra_message}", level=severity, duration=5)
            iface.mapCanvas().refreshAllLayers()
            iface.mapCanvas().refresh()
            self.import_complete.emit(result)
            super(FrmImportDceLayer, self).accept()
        else:
            iface.messageBar().pushMessage('Feature Class Import Error', 'Review the QGIS log.', level=Qgis.Critical, duration=5)
            self.buttonBox.setEnabled(True)

    def on_rdoImport_clicked(self):

        # if radio button is checked then enable the table
        if self.rdoImport.isChecked():
            self.tblFields.setEnabled(True)
            self.load_fields()
        else:
            self.field_status = []
            # set all combo boxes to 'Do Not Import'
            for i in range(self.tblFields.rowCount()):
                chk_retain: QtWidgets.QCheckBox = self.tblFields.cellWidget(i, 2)
                chk_retain.setChecked(False)
            self.tblFields.setEnabled(False)

    def setupUi(self):

        self.resize(600, 500)
        self.setMinimumSize(300, 200)

        self.vert = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.vert)

        self.grid = QtWidgets.QGridLayout()
        self.vert.addLayout(self.grid)

        self.lblInputFC = QtWidgets.QLabel('Input Feature Class') if self.temp_layer is None else QtWidgets.QLabel('Input Temporary Layer')
        self.grid.addWidget(self.lblInputFC, 0, 0)
        self.txtInputFC = QtWidgets.QLineEdit()
        self.txtInputFC.setReadOnly(True)
        self.grid.addWidget(self.txtInputFC, 0, 1)

        self.lblEvent = QtWidgets.QLabel('Data Capture Event')
        self.grid.addWidget(self.lblEvent, 1, 0)
        self.txtEvent = QtWidgets.QLineEdit()
        self.txtEvent.setReadOnly(True)
        self.grid.addWidget(self.txtEvent, 1, 1)

        self.lblMaskClip = QtWidgets.QLabel('Clip to AOI')
        self.grid.addWidget(self.lblMaskClip, 2, 0)

        self.cboMaskClip = QtWidgets.QComboBox()
        self.grid.addWidget(self.cboMaskClip, 2, 1)

        self.lblTargetFC = QtWidgets.QLabel('Target Layer')
        self.grid.addWidget(self.lblTargetFC, 3, 0)
        self.txtTargetFC = QtWidgets.QLineEdit()
        self.txtTargetFC.setReadOnly(True)
        self.grid.addWidget(self.txtTargetFC, 3, 1)

        self.lblFields = QtWidgets.QLabel('Fields')
        self.grid.addWidget(self.lblFields, 4, 0)

        self.horiz = QtWidgets.QHBoxLayout()
        self.grid.addLayout(self.horiz, 4, 1)

        self.rdoImport = QtWidgets.QRadioButton('Import Fields')
        self.rdoImport.setChecked(True)
        self.rdoImport.clicked.connect(self.on_rdoImport_clicked)
        self.horiz.addWidget(self.rdoImport)

        self.rdoIgnore = QtWidgets.QRadioButton('Ignore Fields')
        self.rdoIgnore.clicked.connect(self.on_rdoImport_clicked)
        self.horiz.addWidget(self.rdoIgnore)

        self.horiz.addSpacerItem(QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum))

        self.tblFields = QtWidgets.QTableWidget()
        self.tblFields.setColumnCount(5)
        self.tblFields.setHorizontalHeaderLabels(['Input Field', 'Data Type', 'Retain Values', 'Transfer Values', 'Copy Values'])
        self.tblFields.verticalHeader().setVisible(False)
        self.tblFields.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.tblFields.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tblFields.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.vert.addWidget(self.tblFields)

        self.vert.addLayout(add_standard_form_buttons(self, 'dce/import-dce-layer'))
