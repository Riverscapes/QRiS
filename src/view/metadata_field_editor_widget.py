
import json

from qgis.gui import QgsGui, QgsEditorConfigWidget, QgsEditorWidgetWrapper, QgsEditorWidgetFactory
from qgis.core import QgsVectorLayer, NULL
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QTextEdit, QTableWidget, QTableWidgetItem, QVBoxLayout, QGridLayout, QComboBox, QDoubleSpinBox
from PyQt5.QtCore import Qt, QVariant, QSettings


class MetadataFieldEditWidget(QgsEditorWidgetWrapper):
    # def __init__(self, layer: QgsVectorLayer, fieldIdx: int, editor: QWidget, parent: QWidget):
    #     super().__init__(layer, fieldIdx, editor, parent)

    #     self.mLineEdit = QLineEdit()
    #     self.mLineEdit.textChanged.connect(lambda value: self.valueChanged(value))
    #     self.mLineEdit.textChanged.connect(self.textChanged)

    def value(self) -> QVariant:
        """Will be used to access the widget's value. Read the value from the widget and return it properly formatted to be saved in the attribute.
           If an invalid variant is returned this will be interpreted as no change. Be sure to return a NULL QVariant if it should be set to NULL.

           Returns (Any): The current value the widget represents"""

        json_data = {}
        json_data['city'] = self.cboCity.currentText()
        json_data['age'] = self.dblAge.value()
        self.current_value = json.dumps(json_data)
        return self.current_value

        # #if self.table is not None:
        #     # load json from table
        #     json_data = {}
        #     for i in range(self.table.rowCount()):
        #         json_data[self.table.item(i, 0).text()] = self.table.item(i, 1).text()
        #     return json.dumps(json_data)

    def createWidget(self, parent: QWidget) -> QWidget:

        return QWidget(parent)  # QTableWidget(parent)

    def initWidget(self, editor: QWidget):
        """This method should initialize the editor widget with runtime data. Fill your comboboxes here.

           Parameters: editor – The widget which will represent this attribute editor in a form."""

        # self.spinbox = editor if type(editor) is QDoubleSpinBox else editor.findChild(QDoubleSpinBox)
        # self.table = editor if type(editor) is QTableWidget else editor.findChild(QTableWidget)
        # self.table.cellChanged.connect(self.onValueChanged)
        self.editor_widget = editor if type(editor) is QWidget else editor.findChild(QWidget)
        # Grid layout
        self.vert = QVBoxLayout(self.editor_widget)
        self.editor_widget.setLayout(self.vert)

        self.grid = QGridLayout()
        self.vert.addLayout(self.grid)
        # attributes = self.config('attributes')        #
        self.lblCity = QLabel('City')
        self.grid.addWidget(self.lblCity, 0, 0, 1, 1)

        self.cboCity = QComboBox()
        self.cboCity.addItems(["Seattle", "San Francisco", "Los Angeles", "New York", "Boston"])
        self.grid.addWidget(self.cboCity, 0, 1, 1, 1)

        self.lblAge = QLabel('Age')
        self.grid.addWidget(self.lblAge, 1, 0, 1, 1)

        self.dblAge = QDoubleSpinBox()
        self.dblAge.setRange(0, 100)
        self.dblAge.setDecimals(0)
        self.dblAge.setSingleStep(1)
        self.grid.addWidget(self.dblAge, 1, 1, 1, 1)

        self.cboCity.currentIndexChanged.connect(self.onValueChanged)
        self.dblAge.valueChanged.connect(self.onValueChanged)

    def valid(self) -> bool:
        return True  # self.table is not None

    # def setFeature(self, feature: QgsFeature):

    #     self.setFormFeature(feature)
    #     self.setValue(feature.attribute(self.fieldIdx()))

    def setValue(self, value):
        """Is called when the value of the widget needs to be changed. Updates the widget representation to reflect the new value."""

        if value is None or value == NULL:
            pass
        else:
            parsed_json = json.loads(value)
            if 'city' in parsed_json:
                self.cboCity.setCurrentText(parsed_json['city'])
            if 'age' in parsed_json:
                self.dblAge.setValue(parsed_json['age'])

    # def onCityValueChanged(self, value):
    #     parsed_json = json.loads(self.current_value)
    #     parsed_json['city'] = self.cboCity.currentText()
    #     self.txtJsonCurrent.setText(json.dumps(parsed_json))
    #     self.valueChanged.emit(json.dumps(parsed_json))
    #     self.emitValueChanged()

    # def onAgeValueChanged(self, value):
    #     parsed_json = json.loads(self.current_value)
    #     parsed_json['age'] = value
    #     self.txtJsonCurrent.setText(json.dumps(parsed_json))
    #     self.valueChanged.emit(json.dumps(parsed_json))
    #     self.emitValueChanged()

    def onValueChanged(self, value):
        # self.valueChanged.emit(value)
        self.emitValueChanged()

    # def setHint(self, hintText: str):
    #     if hintText == "":
    #         self.mPlaceholderText = self.mPlaceholderTextBackup
    #     else:
    #         self.mPlaceholderTextBackup = self.mPlaceholderText
    #         self.mPlaceholderText = hintText
    #     if self.mLineEdit:
    #         self.mLineEdit.setPlaceholderText(self.mPlaceholderText)


class MetadataFieldEditConfigWidget(QgsEditorConfigWidget):
    def __init__(self, vl: QgsVectorLayer, fieldIdx: int, parent: QWidget) -> None:
        super().__init__(vl, fieldIdx, parent)

        self.setLayout(QHBoxLayout())
        self.ruleEdit = QLabel(self)
        self.ruleEdit.setText("Metadata Field Editor Test Config")
        self.ruleCheck = QTextEdit(self)
        self.ruleCheck.setText("Metadata Field Editor param")
        self.layout().addWidget(self.ruleEdit)
        self.layout().addWidget(self.ruleCheck)

    def config(self):
        return self.config

    def setConfig(self, config: str):
        self.config = config


class MetadataFieldEditWidgetFactory(QgsEditorWidgetFactory):
    def __init__(self):
        super().__init__("Metadata Field Editor")

    def create(self, layer: QgsVectorLayer, fieldIdx: int, editor: QWidget, parent: QWidget) -> QgsEditorWidgetWrapper:
        return MetadataFieldEditWidget(layer, fieldIdx, editor, parent)

    def configWidget(self, vl: QgsVectorLayer, fieldIdx: int, parent: QWidget) -> QgsEditorConfigWidget:
        return MetadataFieldEditConfigWidget(vl, fieldIdx, parent)


# # check if the widget is already registered and unregister it
# if QgsGui.editorWidgetRegistry().factory("MetadataFieldEdit"):
#     QgsGui.editorWidgetRegistry().factories("MetadataFieldEdit")

factory = MetadataFieldEditWidgetFactory()
QgsGui.editorWidgetRegistry().registerWidget("MetadataFieldEdit", factory)
