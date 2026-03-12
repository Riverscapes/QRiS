from qgis.PyQt import QtWidgets

from ..model.layer import Layer
from ..model.project import Project
from .utilities import add_standard_form_buttons

class FrmQueryBuilder(QtWidgets.QDialog):

    def __init__(self, parent, layer_definition: Layer, project: Project=None, layer_name: str=None):
        super(FrmQueryBuilder, self).__init__(parent)
        self.layer_definition = layer_definition
        self.project = project
        self.query_string = None
        self.layer_name = layer_name if layer_name else layer_definition.name
        
        self.setWindowTitle("Query Builder")
        self.setMinimumWidth(500)
        
        self.setupUi()
        

    def setupUi(self):
        self.vert = QtWidgets.QVBoxLayout(self)
        
        # Layer Name Input
        horiz = QtWidgets.QHBoxLayout()
        lblLayerName = QtWidgets.QLabel("Layer Name:")
        self.txtLayerName = QtWidgets.QLineEdit()
        self.txtLayerName.setText(f"{self.layer_name} (Filtered)")
        horiz.addWidget(lblLayerName)
        horiz.addWidget(self.txtLayerName)
        self.vert.addLayout(horiz)

        # Instructions
        self.lblInfo = QtWidgets.QLabel("Build a filter query for this layer.")
        self.vert.addWidget(self.lblInfo)
        
        # Filter Construction Row
        self.hbox_builder = QtWidgets.QHBoxLayout()
        
        # Logic Operator - Moved to front
        self.cmbLogic = QtWidgets.QComboBox()
        self.cmbLogic.addItems(["OR", "AND", "OR NOT", "AND NOT"])
        # Initially disabled and no selection (simulate blank or just disabled)
        # Using a blank item to simulate "nothing selected" initially
        self.cmbLogic.insertItem(0, "")
        self.cmbLogic.setCurrentIndex(0)
        self.cmbLogic.setEnabled(False) 
        self.hbox_builder.addWidget(self.cmbLogic)

        # Field Combo
        self.cmbField = QtWidgets.QComboBox()
        self.fields = self.layer_definition.metadata.get('fields', [])
        # Filter out fields that shouldn't be queried or handled easily?
        # Just list all for now
        for field in self.fields:
            self.cmbField.addItem(field.get('label', field.get('id')), field['id'])
            
        self.cmbField.currentIndexChanged.connect(self.field_changed)
        self.hbox_builder.addWidget(self.cmbField)
        
        # Operator Combo
        self.cmbOperator = QtWidgets.QComboBox()
        self.cmbOperator.addItems(["=", "!=", "LIKE", "IN", ">", "<", ">=", "<="])
        self.hbox_builder.addWidget(self.cmbOperator)
        
        # Value Input (Text or Combo)
        self.stkValue = QtWidgets.QStackedWidget()
        self.txtValue = QtWidgets.QLineEdit()
        self.cmbValue = QtWidgets.QComboBox()
        self.stkValue.addWidget(self.txtValue)
        self.stkValue.addWidget(self.cmbValue)
        self.hbox_builder.addWidget(self.stkValue)

        # Add to Query Button
        self.btnAdd = QtWidgets.QPushButton("Add to Query")
        self.btnAdd.clicked.connect(self.add_clause)
        self.hbox_builder.addWidget(self.btnAdd)
        
        self.vert.addLayout(self.hbox_builder)
        
        # Initialize inputs
        self.field_changed()
        
        # Query Text Area
        self.lblQuery = QtWidgets.QLabel("Query (SQL WHERE clause):")
        self.vert.addWidget(self.lblQuery)
        self.txtQuery = QtWidgets.QPlainTextEdit()
        self.vert.addWidget(self.txtQuery)

        self.vert.addStretch()

        # Dialog Buttons
        self.vert.addLayout(add_standard_form_buttons(self, 'query-builder'))

    def field_changed(self):
        # Check if selected field has values/lookup
        field_id = self.cmbField.currentData()
        field_def = next((f for f in self.fields if f['id'] == field_id), None)
        
        if not field_def:
            return

        values = field_def.get('values', [])
        # If empty, try lookup if project is available
        if not values and 'lookup' in field_def and self.project:
            lookup_key = field_def['lookup']
            if lookup_key in self.project.lookup_values:
                # lookup_values is typically a dict or list of dicts?
                # Need to check structure. Assuming simple list or list of objects
                # qris_map_manager uses explicit assignment
                # project.lookup_values seems to be {key: [{'id':..., 'label':...}, ...]}
                values = self.project.lookup_values[lookup_key]

        if values:
            self.cmbValue.clear()
            self.cmbValue.addItem("", None) # Empty selection
            for v in values:
                if isinstance(v, dict):
                    # assume id/label
                    val = v.get('id', '')
                    label = v.get('label', str(val))
                    self.cmbValue.addItem(label, val)
                else:
                    self.cmbValue.addItem(str(v), v)
            self.stkValue.setCurrentWidget(self.cmbValue)
        else:
            self.stkValue.setCurrentWidget(self.txtValue)

    def add_clause(self):
        field_id = self.cmbField.currentData()
        operator = self.cmbOperator.currentText()
        
        # Get Value
        if self.stkValue.currentWidget() == self.cmbValue:
            value = self.cmbValue.currentData()
            if value is None:
                value = "" # Should handle empty selection
        else:
            value = self.txtValue.text()

        # Build Expression
        # json_extract(metadata, '$.attributes.<field_id>')
        attr_expr = f"json_extract(metadata, '$.attributes.{field_id}')"
        
        # Quote string values
        # For strings, numbers might need handling but SQLite is flexible.
        # JSON values are typically strings or numbers.
        # If user picked from lookup, use that ID.
        # Ideally we know the type.
        
        sql_val = str(value)
        if isinstance(value, str):
             # Escape single quotes
             safe_val = value.replace("'", "''")
             sql_val = f"'{safe_val}'"
        
        clause = f"{attr_expr} {operator} {sql_val}"
        
        current_text = self.txtQuery.toPlainText().strip()
        if current_text:
            logic = self.cmbLogic.currentText()
            if not logic: logic = "OR" # Fallback, though ideally handled by enabling logic
            current_text += f"\n{logic} {clause}"
        else:
            current_text = clause
            # Now enable logic combo for next addition
            if self.cmbLogic.findText("OR") != -1: # Ensure we have clean items
                 # Remove blank if present
                 idx = self.cmbLogic.findText("")
                 if idx != -1:
                     self.cmbLogic.removeItem(idx)
            
            self.cmbLogic.setEnabled(True)
            self.cmbLogic.setCurrentText("OR") # Default to OR
            
        self.txtQuery.setPlainText(current_text)

    def accept(self):
        self.query_string = self.txtQuery.toPlainText().strip()
        super().accept()
