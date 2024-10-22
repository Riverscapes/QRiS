
import json

from qgis.core import QgsVectorLayer, QgsVectorLayerCache,  QgsAttributeTableConfig
from qgis.gui import QgsAttributeTableView, QgsAttributeTableModel, QgsAttributeTableFilterModel
from qgis.utils import iface

from PyQt5.QtWidgets import QWidget, QDialog, QLabel, QLineEdit, QTextEdit, QTextEdit, QVBoxLayout, QGridLayout, QHBoxLayout, QComboBox, QDoubleSpinBox, QPushButton
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QStandardItem, QStandardItemModel

from .utilities import add_help_button


class FrmBatchAttributeEditor(QDialog):


    def __init__(self, layer: QgsVectorLayer) -> None:
        super().__init__()
        
        self.canvas = iface.mapCanvas()
        self.layer = layer
        self.view_mode = QgsAttributeTableFilterModel.ShowAll


        self.setupUI()
        self.setWindowTitle('Batch Attribute Editor')

        self.widget: QWidget = None
    
        metadata_field_idx = self.layer.fields().indexOf('metadata')
        self.config = self.layer.editorWidgetSetup(metadata_field_idx).config()

        field_items = []
        if 'fields' not in self.config:
            return
        for field in self.config['fields']:
            field_item = QStandardItem(field['label'])
            field_item.setData(field, Qt.UserRole)
            field_items.append(field_item)


        model = QStandardItemModel(self)
        model.appendColumn(field_items)
        self.cboField.setModel(model)
        self.cboField.currentIndexChanged.connect(self.on_field_changed)

        self.on_field_changed()
        self.set_tableview()

        self.btn_apply_text()
        self.layer.selectionChanged.connect(self.btn_apply_text)

    def set_tableview(self):

        self.layerCache = QgsVectorLayerCache(self.layer, self.layer.featureCount())
        self.tableModel = QgsAttributeTableModel(self.layerCache)
        self.tableModel.loadLayer()

        self.tableFilterModel = QgsAttributeTableFilterModel(self.canvas, self.tableModel, parent=self.tableModel)
        self.tableFilterModel.setFilterMode(self.view_mode)
        self.tableView.setModel(self.tableFilterModel)

        # hide the Metadata field if it exists
        metadata_field_idx = self.layer.fields().indexOf('metadata')
        if metadata_field_idx != -1:
            self.tableView.hideColumn(metadata_field_idx)

        event_id_field_idx = self.layer.fields().indexOf('event_id')
        if event_id_field_idx != -1:
            self.tableView.hideColumn(event_id_field_idx)

        layer_id_field_idx = self.layer.fields().indexOf('event_layer_id')
        if layer_id_field_idx != -1:
            self.tableView.hideColumn(layer_id_field_idx)
        

    def on_field_changed(self) -> None:
  
        # Get the field configuration
        field = self.cboField.currentData(Qt.UserRole)

        if field is None:
            return
        
        if self.widget is not None:
            self.grid.removeWidget(self.widget)
            self.widget.deleteLater()

        if field['type'] == 'list':
            self.widget = QComboBox()
            self.widget.addItems(field['values'])
            # widget.currentIndexChanged.connect(self.onValueChanged)
            if 'allow_custom_values' in field.keys() and str(field['allow_custom_values']).lower() == 'true':
                self.widget.setEditable(True)
                # widget.lineEdit().editingFinished.connect(self.onTextChanged)            
        elif field['type'] in ['integer', 'double', 'float']:
            self.widget = QDoubleSpinBox()
            min = field['min'] if 'min' in field else 0
            max = field['max'] if 'max' in field else 100
            self.widget.setRange(min, max)
            if field['type'] == 'integer':
                self.widget.setDecimals(0)
            elif 'precision' in field.keys():
                self.widget.setDecimals(field['precision'])
            self.widget.setSingleStep(1)
            # widget.valueChanged.connect(self.onValueChanged)
        elif field['type'] == 'text':
            self.widget = QLineEdit()
            # widget.textChanged.connect(self.onTextChanged)
        else:
            self.widget = QTextEdit()
            self.widget.setFixedHeight(100)
            # widget.textChanged.connect(self.onTextChanged)
        
        self.grid.addWidget(self.widget, 2, 1, 1, 1)

    
    def update_attributes(self) -> None:

        field = self.cboField.currentData(Qt.UserRole)
        value = None
        if field['type'] == 'list':
            value = self.widget.currentText()
        elif field['type'] in ['integer', 'double', 'float']:
            value = self.widget.value()
        elif field['type'] == 'text':
            value = self.widget.text()
        else:
            value = self.widget.toPlainText()

        # Start an editing session
        self.layer.startEditing()

        for feature in self.layer.selectedFeatures():
            metadata_value = json.loads(feature['metadata'])
            if 'attributes' not in metadata_value:
                metadata_value['attributes'] = {}
            metadata_value['attributes'][field['label']] = value
            feature['metadata'] = json.dumps(metadata_value)
            self.layer.updateFeature(feature)

        # Commit the changes
        self.layer.commitChanges()

        # Update the table
        self.set_tableview()


    def btn_apply_text(self) -> None:

        # get the number of selected features
        selected_features = len(self.layer.selectedFeatures())

        if selected_features == 0:
            self.btnUpdate.setEnabled(False)
            text = 'No features selected'
        else:
            self.btnUpdate.setEnabled(True)
            if selected_features == 1:
                text = 'Apply to 1 selected feature'
            else:
                text = f'Apply to {selected_features} selected features'
        
        self.btnUpdate.setText(text)


    def btn_show_all(self) -> None:

        self.view_mode = QgsAttributeTableFilterModel.ShowAll
        self.tableFilterModel.setFilterMode(QgsAttributeTableFilterModel.ShowAll)


    def btn_show_selected(self) -> None:
        
        self.view_mode = QgsAttributeTableFilterModel.ShowSelected
        self.tableFilterModel.setFilterMode(QgsAttributeTableFilterModel.ShowSelected)


    def setupUI(self):
        
        self.resize(750, 500)
        self.setMinimumSize(300, 200)

        self.vert = QVBoxLayout()
        self.setLayout(self.vert)

        self.grid = QGridLayout()
        self.vert.addLayout(self.grid)

        self.lblLayer = QLabel('Layer')
        self.grid.addWidget(self.lblLayer, 0, 0, 1, 1)

        self.txtLayerName = QLineEdit()
        self.txtLayerName.setReadOnly(True)
        self.txtLayerName.setText(self.layer.name())
        self.grid.addWidget(self.txtLayerName, 0, 1, 1, 1)

        self.lblField = QLabel('Attribute')
        self.grid.addWidget(self.lblField, 1, 0, 1, 1)

        self.cboField = QComboBox()
        self.grid.addWidget(self.cboField, 1, 1, 1, 1)

        self.lblValue = QLabel('Value')
        self.grid.addWidget(self.lblValue, 2, 0, 1, 1)

        self.horiz_apply = QHBoxLayout()
        self.grid.addLayout(self.horiz_apply, 3, 1, 1, 2)

        self.horiz_apply.addStretch()

        self.btnUpdate = QPushButton('Apply')
        self.btnUpdate.clicked.connect(self.update_attributes)
        self.horiz_apply.addWidget(self.btnUpdate)

        self.vert.addStretch

        self.table_config = QgsAttributeTableConfig()
        self.layer.attributeTableConfig()
        
        self.tableView = QgsAttributeTableView(self)
        # self.tableView.verticalHeader().setVisible(False) # we need this enabled in order to select rows
        self.vert.addWidget(self.tableView)

        self.horiz_table_buttons = QHBoxLayout() 
        self.vert.addLayout(self.horiz_table_buttons)

        self.btnShowAll = QPushButton('Show All')
        self.btnShowAll.clicked.connect(self.btn_show_all)
        self.horiz_table_buttons.addWidget(self.btnShowAll)

        self.btnShowSelected = QPushButton('Show Selected')
        self.btnShowSelected.clicked.connect(self.btn_show_selected)
        self.horiz_table_buttons.addWidget(self.btnShowSelected)

        self.horiz_table_buttons.addStretch()

        self.horiz_buttons = QHBoxLayout()
        self.vert.addLayout(self.horiz_buttons)

        self.cmdHelp = add_help_button(self, 'batch-attribute-editor')
        self.horiz_buttons.addWidget(self.cmdHelp)

        self.horiz_buttons.addStretch()
        
        self.btnClose = QPushButton('Close')
        self.btnClose.clicked.connect(self.close)
        self.horiz_buttons.addWidget(self.btnClose)
