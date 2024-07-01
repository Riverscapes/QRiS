
import json
import typing

from qgis.gui import QgsGui, QgsEditorConfigWidget, QgsEditorWidgetWrapper, QgsEditorWidgetFactory
from qgis.core import QgsVectorLayer, NULL
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QTextEdit, QTextEdit, QVBoxLayout, QGridLayout, QComboBox, QDoubleSpinBox
from PyQt5.QtCore import Qt, QVariant, QSettings


class MetadataFieldEditWidget(QgsEditorWidgetWrapper):
    # def __init__(self, layer: QgsVectorLayer, fieldIdx: int, editor: QWidget, parent: QWidget):
    #     super().__init__(layer, fieldIdx, editor, parent)

    def __init__(self, vl: QgsVectorLayer, fieldIdx: int, editor: QWidget, parent: QWidget) -> None:
        super().__init__(vl, fieldIdx, editor, parent)
        self.dict_values = {}
        self.loading = False

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
            elif isinstance(widget, QDoubleSpinBox):
                data[name] = widget.value()
            elif isinstance(widget, QComboBox):
                data[name] = widget.currentText()
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

        fields: list = self.config('fields')
        row = 0
        field: dict
        for field in fields:
            if field['label'] == 'Photo Path':
                continue
            # generate a label and a widget for each field
            label = QLabel(field['label'])
            self.grid.addWidget(label, row, 0, 1, 1)
            widget = None
            if field['type'] == 'list':
                widget = QComboBox(editor)
                widget.addItems(field['values'])
                widget.currentIndexChanged.connect(self.onValueChanged)
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
            else:
                widget = QTextEdit(editor)
                widget.textChanged.connect(self.onTextChanged)
            self.grid.addWidget(widget, row, 1, 1, 1)
            widget.setObjectName(field['machine_code'])

            if 'default' in field.keys():
                if isinstance(widget, QComboBox):
                    index = widget.findText(field['default'])
                    widget.setCurrentIndex(index)
                else:
                    widget.setValue(field['default'])

            self.widgets[field['label']] = widget
            row += 1

    def valid(self) -> bool:
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
                    if isinstance(widget, QTextEdit):
                        widget.setText(val)
                    elif isinstance(widget, QDoubleSpinBox):
                        widget.setValue(val)
                    elif isinstance(widget, QComboBox):
                        index = widget.findText(val)
                        widget.setCurrentIndex(index)
                else:
                    # Reset the widget to its default value if the value is not in values['attributes']
                    self.resetWidgetToDefault(widget)
            self.loading = False

    def resetWidgetToDefault(self, widget: QWidget):

        fields: list = self.config('fields')
        for field in fields:
            if field['machine_code'] == widget.objectName():
                default_value = field.get('default', '')
                if isinstance(widget, QComboBox):
                    index = widget.findText(default_value)
                    widget.setCurrentIndex(index)
                if isinstance(widget, QTextEdit):
                    widget.setText(default_value)
                else:
                    widget.setValue(default_value)

    def onValueChanged(self, value):
        # self.valueChanged.emit(value)
        self.emitValueChanged()

    def onTextChanged(self):
        self.emitValueChanged()


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
