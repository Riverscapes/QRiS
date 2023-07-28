from PyQt5 import QtCore, QtWidgets

from .utilities import add_standard_form_buttons


class FrmFieldValueMap(QtWidgets.QDialog):

    # signal to send field value map to parent
    field_value_map = QtCore.pyqtSignal(dict)

    def __init__(self, parent, field: str, values: list, fields: dict):

        self.field = field
        self.values = values
        self.fields = fields

        super(FrmFieldValueMap, self).__init__(parent)
        self.setupUi()

        self.setWindowTitle('Field Value Map')
        self.txtField.setText(self.field)

        self.load_fields()

    def load_fields(self):

        # add rows for each value
        self.tblFields.setRowCount(len(self.values))

        # add values to first column
        for i, value in enumerate(self.values):
            self.tblFields.setItem(i, 0, QtWidgets.QTableWidgetItem(str(value)))
            # add drop down to each column with the values in self.fields
            for j, field in enumerate(self.fields.keys()):
                combo = QtWidgets.QComboBox()
                combo.addItem('- NULL -', None)
                for value, display in self.fields[field].items():
                    # add the value and display name to the combo box
                    combo.addItem(str(display), value)

                self.tblFields.setCellWidget(i, j + 1, combo)
                combo.setCurrentIndex(0)

    def get_field_value_map(self) -> dict:

        field_value_map = {}
        for i, value in enumerate(self.values):
            field_value_map[value] = {}
            for j, field in enumerate(self.fields.keys()):
                combo = self.tblFields.cellWidget(i, j + 1)
                field_value_map[value][field] = combo.currentData()

        return field_value_map

    def load_field_value_map(self, field_value_map: dict) -> None:

        for i, value in enumerate(self.values):
            for j, field in enumerate(self.fields.keys()):
                combo = self.tblFields.cellWidget(i, j + 1)
                combo.setCurrentIndex(combo.findData(field_value_map[value][field]))

    def accept(self) -> None:

        field_map = self.get_field_value_map()
        out_map = {self.field: field_map}
        self.field_value_map.emit(out_map)

        return super().accept()

    def setupUi(self):

        # set size
        self.resize(800, 600)

        # vertical layout
        self.vLayout = QtWidgets.QVBoxLayout(self)

        # horizontal layout for field name
        self.hLayout = QtWidgets.QHBoxLayout()
        self.vLayout.addLayout(self.hLayout)

        # label for field name
        self.lblField = QtWidgets.QLabel('Input Field')
        self.hLayout.addWidget(self.lblField)

        # text box for field name
        self.txtField = QtWidgets.QLineEdit()
        self.txtField.setReadOnly(True)
        self.hLayout.addWidget(self.txtField)

        # new table with 1 + number of fields columns
        self.tblFields = QtWidgets.QTableWidget()
        self.tblFields.setColumnCount(1 + len(self.fields))
        self.tblFields.setHorizontalHeaderLabels(['Value'] + list(self.fields.keys()))
        self.tblFields.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.tblFields.verticalHeader().setVisible(False)
        self.tblFields.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.tblFields.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        # add table to layout
        self.vLayout.addWidget(self.tblFields)

        # add standard form buttons
        self.vLayout.addLayout(add_standard_form_buttons(self, 'field_value_map'))
