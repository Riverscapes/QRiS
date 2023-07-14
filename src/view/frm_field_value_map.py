from PyQt5 import QtCore, QtWidgets

from .utilities import add_standard_form_buttons


class FrmFieldValueMap(QtWidgets.QDialog):

    # signal to send field value map to parent
    field_value_map = QtCore.pyqtSignal(dict)

    def __init__(self, parent, values: list, fields: dict):

        self.values = values
        self.fields = fields

        super(FrmFieldValueMap, self).__init__(parent)
        self.setupUi()

        self.setWindowTitle('Field Value Map')

        self.load_fields()

    def load_fields(self):

        # add rows for each value
        self.tblFields.setRowCount(len(self.values))

        # add values to first column
        for i, value in enumerate(self.values):
            self.tblFields.setItem(i, 0, QtWidgets.QTableWidgetItem(value))
            # add drop down to each column with the values in self.fields
            for j, field in enumerate(self.fields.keys()):
                combo = QtWidgets.QComboBox()
                combo.addItems(['-- Do Not Import --'] + list(self.fields[field]))
                self.tblFields.setCellWidget(i, j + 1, combo)
                combo.setCurrentIndex(0)

    def get_field_value_map(self) -> dict:

        field_value_map = {}
        for i, value in enumerate(self.values):
            field_value_map[value] = {}
            for j, field in enumerate(self.fields.keys()):
                combo = self.tblFields.cellWidget(i, j + 1)
                field_value_map[value][field] = combo.currentText()

        return field_value_map

    def accept(self) -> None:

        self.field_value_map.emit(self.get_field_value_map())

        return super().accept()

    def setupUi(self):

        # vertical layout
        self.vLayout = QtWidgets.QVBoxLayout(self)

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
