
import json
import typing

from qgis.gui import QgsGui, QgsEditorConfigWidget, QgsEditorWidgetWrapper, QgsEditorWidgetFactory
from qgis.core import QgsVectorLayer, NULL
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QTextEdit, QVBoxLayout, QGridLayout, QComboBox, QDoubleSpinBox, QCheckBox
from PyQt5.QtCore import Qt, QVariant, QSettings


class MetadataFieldEditWidget(QgsEditorWidgetWrapper):
    # def __init__(self, layer: QgsVectorLayer, fieldIdx: int, editor: QWidget, parent: QWidget):
    #     super().__init__(layer, fieldIdx, editor, parent)

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
            if isinstance(widget, QTextEdit):
                data[name] = widget.toPlainText()
            elif isinstance(widget, QLineEdit):
                data[name] = widget.text()
            elif isinstance(widget, QDoubleSpinBox):
                data[name] = widget.value()
            elif isinstance(widget, QComboBox):
                data[name] = widget.currentText()
            elif isinstance(widget, CheckboxWidget):
                data[name] = [checkbox.text() for checkbox in widget.findChildren(QCheckBox) if checkbox.isChecked()]
        self.dict_values['attributes'] = data
        # formatted_data = {}
        # formatted_data['attributes'] = data
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
        self.derived_values = {}

        self.fields: list = self.config('fields')
        row = 0
        field: dict
        for field in self.fields:
            if field['label'] == 'Photo Path':
                continue
            # generate a label and a widget for each field
            label = QLabel(field['label'])
            self.grid.addWidget(label, row, 0, 1, 1)
            widget = None
            if 'derived_value' in field.keys():
                widget = DependantComboBox(editor, field['derived_value'], field.get('default_value', ''))
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
                widget = QDoubleSpinBox(editor)
                min = field['min'] if 'min' in field else 0
                max = field['max'] if 'max' in field else 100
                widget.setRange(min, max)
                if field['type'] == 'integer':
                    widget.setDecimals(0)
                elif 'precision' in field.keys():
                    widget.setDecimals(field['precision'])
                widget.setSingleStep(1)
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
                widget.setEnabled(False)

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
                    # Set the widget's value based on the type of the widget
                    if isinstance(widget, QTextEdit) or isinstance(widget, QLineEdit):
                        widget.setText(val)
                    elif isinstance(widget, QDoubleSpinBox):
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
                else:
                    # Reset the widget to its default value if the value is not in values['attributes']
                    self.resetWidgetToDefault(widget)
            
            self.updateDependantWidgets()
            self.loading = False

    def updateDependantWidgets(self):

        widget_values = {}
        for name, widget in self.widgets.items():
            if isinstance(widget, QLineEdit):
                widget_values[name] = widget.text()
            elif isinstance(widget, QTextEdit):
                widget_values[name] = widget.toPlainText()
            elif isinstance(widget, QDoubleSpinBox):
                widget_values[name] = widget.value()
            elif isinstance(widget, QComboBox):
                widget_values[name] = widget.currentText()
            elif isinstance(widget, CheckboxWidget):
                widget_values[name] = [checkbox.text() for checkbox in widget.findChildren(QCheckBox) if checkbox.isChecked()]

        for widget in self.widgets.values():
            if isinstance(widget, DependantComboBox):
                widget.set_dependent_value(widget_values)
        
        for name, widget in self.widgets.items():
            field = next((f for f in self.fields if f['id'] == widget.objectName()), None)
            if field is None:
                continue
            if 'visibility' in field.keys():
                if field['visibility'] == 'None':
                    widget.setEnabled(False)
                values_to_check = field['visibility']['values']
                widget_value = widget_values.get(field['visibility']['field_id'], '') 
                if isinstance(widget, QComboBox):
                    if widget_value in values_to_check:
                        widget.setEnabled(True)
                    else:
                        widget.setEnabled(False)
                else:
                    if any(value in values_to_check for value in widget_value):
                        widget.setEnabled(True)
                    else:
                        widget.setEnabled(False)
            else:
                widget.setEnabled(True)

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
                else:
                    if default_value == '':
                        continue
                    widget.setValue(default_value)

    def onValueChanged(self, value):
        self.updateDependantWidgets()
        self.emitValueChanged()

    def onTextChanged(self):
        self.updateDependantWidgets()
        self.emitValueChanged()

    def derived_value(self):

        json_lookup = """[ "dam_capacity",
                "derived_value": [
                    {"value_lookup": [
                        {"id":"streamside_vegtation", 
                         "value": "Unsuitable"},
                        {"id": "riparian_vegetation",
                         "value": "Unsuitable"}
                        ]
                     "output": "None"
                    },
                    {
                    "value_lookup": [
                    {"id":"streamside_vegtation",
                        "value": "Suitable"},
                    {"id": "riparian_vegetation",
                        "value": "Unsuitable"}
                        ]
                    "output": "Rare"
                    },
                    {
                    "value_lookup": [
                    {"id":"streamside_vegtation",
                        "value": "Suitable"},
                    {"id": "riparian_vegetation",
                        "value": "Suitable"}
                        ]
                    "output": "Pervaisive"
                    }
                    ]
            }
        ]"""

        # Create a mapping of id to widgets for efficient lookup
        widget_map = {widget.objectName(): widget for widget in self.widgets}

        for field, value_lookups in self.derived_values:
            widget = widget_map.get(field, None)
            if widget is None:
                continue  # or handle error

            for value_lookup in value_lookups:
                if all(widget_map.get(lookup['id'], {}).text() == lookup['value'] for lookup in value_lookup['value_lookup']):
                    # Assuming widget is a ComboBox, adjust accordingly
                    index = widget.findText(value_lookup['output'])
                    if index != -1:
                        widget.setCurrentIndex(index)
                    break

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

    def __init__(self, parent:MetadataFieldEditWidget=None, dependency_map: typing.Dict[str, typing.List[str]] = {}, default_value=None):
        
        super(DependantComboBox, self).__init__(parent)
        self.dependency_map = dependency_map
        self.default_value = default_value
        self.manual_value = None

        self.initUI()


    def onManual(self, state):
        if state == Qt.Checked:
            self.cboValues.setEnabled(True)
            if self.manual_value is not None:
                self.cboValues.setCurrentText(self.manual_value)
        else:
            self.cboValues.setEnabled(False)
            self.manual_value = self.cboValues.currentText()
            self.parent().updateDependantWidgets()

    def set_dependent_value(self, widget_values: typing.Dict[str, str]):
        if self.chkManual.isChecked():
            return
        for value_lookup in self.dependency_map.items():
            for field, value in value_lookup.items():
                if field in widget_values and widget_values[field] == value:
                    self.cboValues.setCurrentText(value_lookup['output'])
                    return
        self.cboValues.setCurrentText(self.default_value)

    def initUI(self):

        self.hlayout = QHBoxLayout()
        self.setLayout(self.hlayout)

        self.cboValues = QComboBox()
        self.hlayout.addWidget(self.cboValues)

        self.chkManual = QCheckBox("Manual")
        self.chkManual.setChecked(False)
        self.chkManual.stateChanged.connect(self.onManual)
        self.hlayout.addWidget(self.chkManual)

