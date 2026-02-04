import json
import typing

from qgis.gui import QgsGui, QgsEditorConfigWidget, QgsEditorWidgetWrapper, QgsEditorWidgetFactory, QgsWidgetWrapper
from qgis.core import QgsVectorLayer, NULL, QgsFieldConstraints

from qgis.PyQt.QtGui import QStandardItemModel, QStandardItem
from qgis.PyQt.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QTextEdit, QVBoxLayout, QGridLayout, QComboBox, QDoubleSpinBox, QCheckBox, QSlider
from qgis.PyQt.QtCore import Qt, QVariant, pyqtSignal


class MetadataFieldEditWidget(QgsEditorWidgetWrapper):

    def __init__(self, vl: QgsVectorLayer, fieldIdx: int, editor: QWidget, parent: QWidget) -> None:
        super().__init__(vl, fieldIdx, editor, parent)
        self.dict_values = {}
        self.loading = False
        self.fields = []

    def value(self) -> QVariant:
        """Will be used to access the widget's value. Read the value from the widget and return it properly formatted to be saved in the attribute.
           If an invalid variant is returned this will be interpreted as no change. Be sure to return a NULL QVariant if it should be set to NULL.

           Returns (Any): The current value the widget represents"""

        if self.loading:
            return json.dumps(self.dict_values)
        data = self.dict_values.get('attributes', {})
        for name, widget in self.widgets.items():
            data[name] = self.get_widget_value(widget)
        self.dict_values['attributes'] = data
        self.current_value = json.dumps(self.dict_values)

        return self.current_value

    def createWidget(self, parent: QWidget) -> QWidget:

        return QWidget(parent)

    def initWidget(self, editor: QWidget):
        """This method should initialize the editor widget with runtime data. Fill your comboboxes here.

           Parameters: editor - The widget which will represent this attribute editor in a form."""

        self.editor_widget = editor if type(editor) is QWidget else editor.findChild(QWidget)
        # Grid layout
        self.vert = QVBoxLayout(self.editor_widget)
        self.editor_widget.setLayout(self.vert)
        self.grid = QGridLayout()
        self.vert.addLayout(self.grid)
        self.widgets = {}
        self.labels = {}
        self.derived_values = {}
        self.saved_values = {}

        self.fields: list = self.config('fields')
        row = 0
        field: dict
        for field in self.fields:
            if field['label'] == 'Photo Path':
                continue

            # generate a label and a widget for each field
            label_text = field['label']
            if field.get('value_required', False):
                 label_text += ' *'
            label = QLabel(label_text)
            self.grid.addWidget(label, row, 0, 1, 1)
            self.labels[field['id']] = label
            
            widget = None
            if 'derived_values' in field.keys():
                widget = DependantComboBox(editor, field['values'], field['derived_values'], field.get('default_value', ''))
                widget.cboValues.currentIndexChanged.connect(self.onValueChanged)
                widget.chkManual.stateChanged.connect(self.onValueChanged)
            elif field['type'] == 'list':
                if 'allow_multiple_values' in field.keys() and str(field['allow_multiple_values']).lower() == 'true':
                    # prepare a widget with checkboxes for each value
                    widget = CheckboxWidget(editor)
                    for value in field['values']:
                        checkbox = widget.add_checkbox(value)
                        checkbox.stateChanged.connect(self.onValueChanged)
                else:
                    widget = QComboBox(editor)
                    widget.addItems(field['values'])
                    widget.currentIndexChanged.connect(self.onValueChanged)
                    if 'allow_custom_values' in field.keys() and str(field['allow_custom_values']).lower() == 'true':
                        widget.setEditable(True)
                        widget.lineEdit().editingFinished.connect(self.onTextChanged)            
            elif field['type'] in ['integer', 'double', 'float']:
                if 'slider' in field.keys():
                    widget = SliderWidget(editor)
                    widget.setRange(field['slider']['min'], field['slider']['max'])
                    widget.setSingleStep(field['slider']['step'])
                else:
                    widget = QDoubleSpinBox(editor)
                    widget.setSingleStep(1)
                    min = field['min'] if 'min' in field else 0
                    max = field['max'] if 'max' in field else 100
                    widget.setRange(min, max)
                    if field['type'] == 'integer':
                        widget.setDecimals(0)
                    elif 'precision' in field.keys():
                        widget.setDecimals(field['precision'])
                widget.valueChanged.connect(self.onValueChanged)
            elif field['type'] == 'text':
                widget = QLineEdit(editor)
                widget.textChanged.connect(self.onTextChanged)
            else:
                widget = QTextEdit(editor)
                widget.textChanged.connect(self.onTextChanged)
            self.grid.addWidget(widget, row, 1, 1, 1)
            widget.setObjectName(field['id'])

            if 'default_value' in field.keys():
                if isinstance(widget, QComboBox):
                    index = widget.findText(field['default_value'])
                    widget.setCurrentIndex(index)
                # if integer field set the value as an integer type
                elif field['type'] == 'integer':
                    widget.setValue(int(field['default_value']))
                # if float field set the value as a float type
                elif field['type'] in ['double', 'float']:
                    widget.setValue(float(field['default_value']))
                else:
                    widget.setValue(field['default_value'])
            
            if 'visibility' in field.keys():
                # we are going to check the value of the field that is being used to determine the visibility of this field later on.
                self.toggle_widget_visibility(widget, False)
            
            self.widgets[field['id']] = widget
            row += 1

    def valid(self) -> bool:
        # This is required for intilaizing the widgets. It does not do anyting or validate the widget values. Don't remove or mess with it!
        return True

    def setValue(self, value):
        """Is called when the value of the widget needs to be changed. Updates the widget representation to reflect the new value or resets it to default if not present."""

        self.loading = True
        if value is None or value == NULL:
            pass
        else:
            values: dict = json.loads(value)
            self.dict_values = values
            
            # Iterate through all widgets, not just those in values['attributes']
            for name, widget in self.widgets.items():
                if 'attributes' in values and name in values['attributes']:
                    val = values['attributes'][name]
                    if isinstance(widget, DependantComboBox):
                        widget.setValueExternal(val, values['attributes'])
                    else:
                        self.set_widget_value(widget, val)
                else:
                    # Reset the widget to its default value if the value is not in values['attributes']
                    self.resetWidgetToDefault(widget)
            
            self.updateDependantWidgets()
            self.validate_required_fields()
            self.loading = False

    def updateDependantWidgets(self):

        widget_values = {}
        for name, widget in self.widgets.items():
            widget_values[name] = self.get_widget_value(widget)

        for widget in self.widgets.values():
            if isinstance(widget, DependantComboBox):
                widget.set_dependent_value(widget_values)
        
        for name, widget in self.widgets.items():
            field = next((f for f in self.fields if f['id'] == widget.objectName()), None)
            if field is None:
                continue
            if 'visibility' in field.keys():
                if field['visibility'] == 'None':
                    self.toggle_widget_visibility(widget, False)
                values_to_check = field['visibility']['values']
                widget_value = widget_values.get(field['visibility']['field_id'], '') 
                if isinstance(widget, QComboBox):
                    if widget_value in values_to_check:
                        self.toggle_widget_visibility(widget, True)
                    else:
                        self.toggle_widget_visibility(widget, False)
                else:
                    widget_value = [widget_value] if not isinstance(widget_value, list) else widget_value
                    if any(value in values_to_check for value in widget_value):
                        self.toggle_widget_visibility(widget, True)
                    else:
                        self.toggle_widget_visibility(widget, False)
            else:
                self.toggle_widget_visibility(widget, True)

    def resetWidgetToDefault(self, widget: QWidget):

        fields: list = self.config('fields')
        for field in fields:
            if field['id'] == widget.objectName():
                default_value = field.get('default_value', '')
                if isinstance(widget, QComboBox):
                    index = widget.findText(default_value)
                    widget.setCurrentIndex(index)
                elif isinstance(widget, CheckboxWidget):
                    widget.reset_checkboxes()
                elif isinstance(widget, QTextEdit) or isinstance(widget, QLineEdit):
                    widget.setText(default_value)
                elif isinstance(widget, QDoubleSpinBox) or isinstance(widget, SliderWidget):
                    if isinstance(default_value, str):
                        if default_value == '' or default_value is None:
                            default_value = 0
                        elif '.' in default_value:
                            default_value = float(default_value)
                        else:
                            default_value = int(default_value)
                        widget.setValue(default_value)
                else:
                    if default_value == '':
                        continue
                    widget.setValue(default_value)

    def onValueChanged(self, value):
        self.updateDependantWidgets()
        self.validate_required_fields()
        self.emitValueChanged()

    def onTextChanged(self):
        self.updateDependantWidgets()
        self.validate_required_fields()
        self.emitValueChanged()

    def validate_required_fields(self):
        """
        Check existing widgets for required fields and validity.
        Update UI feedback style directly and emit constraint status.
        """
        if not hasattr(self, 'widgets') or not self.widgets:
            return

        border_style_error = "border: 1px solid red;"
        border_style_normal = ""

        # We need to find the specific config for each widget again since it's not stored on the widget
        config_fields = self.config('fields')
        
        all_valid = True
        errors = []

        for field in config_fields:
            if field.get('value_required', False):
                widget = self.widgets.get(field['id'])
                
                # If widget is missing, hidden, or disabled it is not 'required' in this context
                if widget and widget.isVisible() and widget.isEnabled():
                    val = self.get_widget_value(widget)
                    
                    is_empty = False
                    if val is None:
                        is_empty = True
                    elif isinstance(val, str) and str(val).strip() == "":
                        is_empty = True
                    elif isinstance(val, list) and len(val) == 0:
                        is_empty = True
                    
                    if is_empty:
                        self.set_widget_style(widget, border_style_error)
                        all_valid = False
                        errors.append(f"{field.get('label', field['id'])} is required.")
                    else:
                        self.set_widget_style(widget, border_style_normal)
        
        if not all_valid:
            # Join errors for the tooltip/message
            error_message = "\n".join(errors)
            self.constraintResultVisibleChanged.emit(True)
            # 2 = ConstraintFailureHard
            self.constraintStatusChanged.emit("Required Fields", "Required fields missing", error_message, 2)
        else:
            self.constraintResultVisibleChanged.emit(False)
            # 0 = ConstraintSuccess
            self.constraintStatusChanged.emit("Required Fields", "All required fields filled", "", 0)

    def set_widget_style(self, widget, style):
        # Apply style to relevant input component
        target = widget
        if isinstance(widget, DependantComboBox):
            target = widget.cboValues
        elif isinstance(widget, QComboBox) and widget.isEditable():
            target = widget.lineEdit()
        
        # Avoid overriding other styles if possible, but for now simple setStyleSheet
        target.setStyleSheet(style)

    def toggle_widget_visibility(self, widget: QWidget, value: bool):
        
        # Get current status to determine if it is changed
        status_changed = True if widget.isEnabled() != value else False

        widget.setEnabled(value)
        widget.setVisible(value)
        label: QLabel = self.labels[widget.objectName()]
        label.setVisible(value)

        if status_changed:
            if value is True:
                if widget.objectName() in self.saved_values:
                    self.set_widget_value(widget, self.saved_values[widget.objectName()])
            else:
                self.saved_values[widget.objectName()] = self.get_widget_value(widget)
                self.set_widget_value(widget, None)

    def set_widget_value(self, widget: QWidget, val):
        # Set the widget's value based on the type of the widget
        if isinstance(widget, QTextEdit) or isinstance(widget, QLineEdit):
            val = '' if val is None else val
            widget.setText(val)
        elif isinstance(widget, QDoubleSpinBox) or isinstance(widget, SliderWidget):
            val = 0 if val is None else val
            widget.setValue(val)
        elif isinstance(widget, QComboBox):
            if widget.isEditable():
                widget.lineEdit().setText(val)
            else:
                index = widget.findText(val)
                widget.setCurrentIndex(index)
        elif isinstance(widget, CheckboxWidget):
            # Better clear all checkboxes first
            widget.reset_checkboxes()
            for checkbox in widget.findChildren(QCheckBox):
                checkbox.setChecked(checkbox.text() in val)
    
    def get_widget_value(self, widget: QWidget):
        if isinstance(widget, QLineEdit):
            return widget.text()
        elif isinstance(widget, QTextEdit):
            return widget.toPlainText()
        elif isinstance(widget, QDoubleSpinBox) or isinstance(widget, SliderWidget):
            return widget.value()
        elif isinstance(widget, QComboBox):
            return widget.currentText()
        elif isinstance(widget, CheckboxWidget):
            return [checkbox.text() for checkbox in widget.findChildren(QCheckBox) if checkbox.isChecked()]
        elif isinstance(widget, DependantComboBox):
            return widget.cboValues.currentText()
        return None
    

class CheckboxWidget(QWidget):

    def __init__(self, parent=None):
        super(CheckboxWidget, self).__init__(parent)
        self.initUI()
    
    def initUI(self):
        self.vlayout = QVBoxLayout(self)
        self.setLayout(self.vlayout)

    def add_checkbox(self, label):
        checkbox = QCheckBox(label, self)
        self.vlayout.addWidget(checkbox)
        return checkbox
    
    def reset_checkboxes(self):
        for checkbox in self.findChildren(QCheckBox):
            checkbox.setChecked(False)

class SliderWidget(QWidget):

    valueChanged = pyqtSignal(int or float)

    def __init__(self, parent=None):
        super(SliderWidget, self).__init__(parent)
        self.initUI()

    def initUI(self):
        self.hlayout = QHBoxLayout(self)
        self.setLayout(self.hlayout)

        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setOrientation(Qt.Horizontal)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.hlayout.addWidget(self.slider)

        self.label = QLabel(self)
        self.hlayout.addWidget(self.label)

        self.slider.valueChanged.connect(self.onValueChanged)

    def onValueChanged(self, value):
        self.label.setText(str(value))
        self.valueChanged.emit(value)

    def setValue(self, value):
        self.slider.setValue(value)

    def value(self):
        return self.slider.value()
    
    def setRange(self, min, max):
        self.slider.setRange(min, max)

    def setSingleStep(self, step):
        self.slider.setSingleStep(step)





class MetadataFieldEditConfigWidget(QgsEditorConfigWidget):
    def __init__(self, vl: QgsVectorLayer, fieldIdx: int, parent: QWidget) -> None:
        super().__init__(vl, fieldIdx, parent)

        self.setLayout(QHBoxLayout())
        self.ruleEdit = QLabel(self)
        self.ruleEdit.setText("Field Configuration")
        self.ruleCheck = QTextEdit(self)
        self.layout().addWidget(self.ruleEdit)
        self.layout().addWidget(self.ruleCheck)

    def config(self):

        config = json.loads(self.ruleCheck.toPlainText())

        return config

    def setConfig(self, config: str):
        values = config
        str_values = json.dumps(values, indent=4)
        self.ruleCheck.setText(str_values)


class MetadataFieldEditWidgetFactory(QgsEditorWidgetFactory):
    def __init__(self):
        super().__init__("Metadata Field Editor")

    def create(self, layer: QgsVectorLayer, fieldIdx: int, editor: QWidget, parent: QWidget) -> QgsEditorWidgetWrapper:
        return MetadataFieldEditWidget(layer, fieldIdx, editor, parent)

    def configWidget(self, vl: QgsVectorLayer, fieldIdx: int, parent: QWidget) -> QgsEditorConfigWidget:
        return MetadataFieldEditConfigWidget(vl, fieldIdx, parent)


def initialize_metadata_widget():

    # check if the widget is already registered and unregister it
    widget = QgsGui.editorWidgetRegistry().factory("MetadataFieldEdit")
    if widget.name() != "Metadata Field Editor":
        factory = MetadataFieldEditWidgetFactory()
        QgsGui.editorWidgetRegistry().registerWidget("MetadataFieldEdit", factory)

class DependantComboBox(QWidget):

    def __init__(self, parent:MetadataFieldEditWidget=None, values=[], dependency_map: typing.Dict[str, typing.List[str]] = {}, default_value=None):
        
        super(DependantComboBox, self).__init__(parent)
        self.dependency_map = dependency_map
        self.default_value = default_value
        self.manual_value = None

        self.initUI()

        self.model = QStandardItemModel()
        for value in values:
            item = QStandardItem(value)
            self.model.appendRow(item)
        self.cboValues.setModel(self.model)

    def setValue(self, value):
        index = self.cboValues.findText(value)
        self.cboValues.setCurrentIndex(index)

    def setValueExternal(self, value, widget_values: typing.Dict[str, str]):

        # we want to set the value of the combobox but we also want to check if the value is derived and set the checkbox accordingly
        self.manual_value = value
        self.chkManual.setChecked(True)
        self.cboValues.setEnabled(True)

        # Reverse lookup the value to see if it is derived
        for value_lookup in self.dependency_map:
            inputs: list = [(key, value) for input_map in value_lookup['inputs'] for key, value in input_map.items()]
            if all(widget_values.get(field, '') == value for field, value in inputs) and value_lookup['output'] == value:
                self.chkManual.setChecked(False)
                self.cboValues.setEnabled(False)
                break
        self.setValue(value)
        return

    def onManual(self, state):
        if state == Qt.Checked:
            self.cboValues.setEnabled(True)
            if self.manual_value is not None:
                self.setValue(self.manual_value)
        else:
            self.cboValues.setEnabled(False)
            self.manual_value = self.cboValues.currentText()

    def set_dependent_value(self, widget_values: typing.Dict[str, str]):
        if self.chkManual.isChecked():
            return
        for value_lookup in self.dependency_map:
            inputs: list = [(key, value) for input_map in value_lookup['inputs'] for key, value in input_map.items()]
            if all(widget_values.get(field, '') == value for field, value in inputs):
                self.setValue(value_lookup['output'])
                return
        # If no match found, set to default value
        self.setValue(self.default_value)
        return

    def initUI(self):

        self.hlayout = QHBoxLayout()
        self.setLayout(self.hlayout)

        self.cboValues = QComboBox()
        self.cboValues.setEnabled(False)
        self.hlayout.addWidget(self.cboValues)

        self.chkManual = QCheckBox("Override (Set Value Manually)")
        self.chkManual.setChecked(False)
        self.chkManual.stateChanged.connect(self.onManual)
        self.hlayout.addWidget(self.chkManual)

