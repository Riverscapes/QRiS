from PyQt5 import QtCore, QtWidgets

from .utilities import add_standard_form_buttons


class FrmFieldValueMap(QtWidgets.QDialog):

    # signal to send field value map to parent
    field_value_map_signal = QtCore.pyqtSignal(str, dict)

    def __init__(self, input_field: str, values: list, fields: dict, parent=None):
        super().__init__(parent)
        self.fields = fields  # Dictionary to store field values
        self.values = values  # List to store input values
        self.input_field = input_field  # Name of the input field

        self.setupUi()

        self.setWindowTitle('Field Value Map')
        self.txtInputField.setText(input_field)

        # Populate the combo box with field names
        self.cmbOutputField.addItems(self.fields.keys())

        # Populate the table with input values
        self.tblFields.setRowCount(len(self.values))
        for i, value in enumerate(self.values):
            item = QtWidgets.QTableWidgetItem(str(value))
            self.tblFields.setItem(i, 0, item)

    def add_output_field(self, field) -> None:
        
        if not field:
            field = self.cmbOutputField.currentText()
        if not field:
            return

        # Add a new column to the table
        self.tblFields.setColumnCount(self.tblFields.columnCount() + 1)
        self.tblFields.setHorizontalHeaderItem(self.tblFields.columnCount() - 1, QtWidgets.QTableWidgetItem(field))

        # Add combo boxes to each row in the new column
        for i in range(self.tblFields.rowCount()):
            combo = QtWidgets.QComboBox()
            combo.addItem('- NULL -', None)
            for value in self.fields.get(field, []):
                combo.addItem(str(value), value)
            self.tblFields.setCellWidget(i, self.tblFields.columnCount() - 1, combo)
            combo.setCurrentIndex(0)

        self.cbo_changed(0)

    def remove_output_field(self) -> None:
        field = self.cmbOutputField.currentText()
        headers = [self.tblFields.horizontalHeaderItem(i).text() for i in range(self.tblFields.columnCount())]
        if field in headers:
            idx = headers.index(field)
            self.tblFields.removeColumn(idx)

        self.cbo_changed(0)

    def cbo_changed(self, idx: int) -> None:
        field = self.cmbOutputField.currentText()
        headers = [self.tblFields.horizontalHeaderItem(i).text() for i in range(self.tblFields.columnCount())]
        if field in headers[1:]:
            self.btnAddOutputField.setDisabled(True)
            self.btnRemoveOutputField.setDisabled(False)
        else:
            self.btnAddOutputField.setDisabled(False)
            self.btnRemoveOutputField.setDisabled(True)

    def get_field_value_map(self) -> dict:
        field_value_map = {}
        for i, value in enumerate(self.values):
            field_value_map[value] = {}
            for j in range(1, self.tblFields.columnCount()):
                field = self.tblFields.horizontalHeaderItem(j).text()
                combo: QtWidgets.QComboBox = self.tblFields.cellWidget(i, j)
                field_value_map[value][field] = combo.currentData()
        return field_value_map

    def load_field_value_map(self, field_value_map: dict) -> None:
        # Add columns based on the field_value_map keys
        for field in next(iter(field_value_map.values())).keys():
            if field not in [self.tblFields.horizontalHeaderItem(i).text() for i in range(self.tblFields.columnCount())]:
                self.add_output_field(field)

        # Populate the combo boxes with the values from field_value_map
        for i, value in enumerate(self.values):
            if value in field_value_map:
                for j in range(1, self.tblFields.columnCount()):
                    field = self.tblFields.horizontalHeaderItem(j).text()
                    if field in field_value_map[value]:
                        combo: QtWidgets.QComboBox = self.tblFields.cellWidget(i, j)
                        combo.setCurrentIndex(combo.findData(field_value_map[value][field]))

    def accept(self) -> None:

        out_map = self.get_field_value_map()
        # retain = self.chkRetain.isChecked()
        self.field_value_map_signal.emit(self.input_field, out_map)

        return super().accept()

    def setupUi(self):

        # set size
        self.resize(800, 600)

        self.vLayout = QtWidgets.QVBoxLayout(self)
        self.grid = QtWidgets.QGridLayout()
        self.vLayout.addLayout(self.grid)

        self.lblInputField = QtWidgets.QLabel('Input Field')
        self.grid.addWidget(self.lblInputField, 0, 0)

        self.txtInputField = QtWidgets.QLineEdit()
        self.txtInputField.setReadOnly(True)
        self.grid.addWidget(self.txtInputField, 0, 1)

        self.lblOutputField = QtWidgets.QLabel('Output Field')
        self.grid.addWidget(self.lblOutputField, 1, 0)

        self.cmbOutputField = QtWidgets.QComboBox()
        self.grid.addWidget(self.cmbOutputField, 1, 1)

        self.btnAddOutputField = QtWidgets.QPushButton('Add')
        self.btnAddOutputField.setToolTip('Add a new output field')
        self.grid.addWidget(self.btnAddOutputField, 1, 2)

        self.btnRemoveOutputField = QtWidgets.QPushButton('Remove')
        self.btnRemoveOutputField.setToolTip('Remove the selected output field')
        self.grid.addWidget(self.btnRemoveOutputField, 1, 3)

        self.tblFields = QtWidgets.QTableWidget()
        self.tblFields.setColumnCount(1)
        self.tblFields.setHorizontalHeaderLabels(['Input Values'])
        self.tblFields.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.tblFields.verticalHeader().setVisible(False)
        self.tblFields.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.tblFields.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        self.vLayout.addWidget(self.tblFields)

        self.vLayout.addLayout(add_standard_form_buttons(self, 'field_value_map'))

        self.btnAddOutputField.clicked.connect(self.add_output_field)
        self.btnRemoveOutputField.clicked.connect(self.remove_output_field)
        self.cmbOutputField.currentIndexChanged.connect(self.cbo_changed)