import json

from PyQt5 import QtWidgets


class MetadataWidget(QtWidgets.QWidget):

    def __init__(self, parent: QtWidgets.QDialog, json_meta: str = None, new_keys: list = None):

        super().__init__(parent)
        self.json_meta = None
        self.new_keys = new_keys
        self.metadata = dict()
        self.system_metadata = dict()
        self.attribute_metadat = dict()
        self.table: QtWidgets.QTableWidget = None

        if json_meta is not None and json_meta != '' and json_meta != 'null':
            self.load_json(json_meta)

        self.create_table_ui()

    def load_json(self, json_meta: str):

        self.json_meta = json_meta
        self.metadata = json.loads(self.json_meta)
        self.check_metadata()

    def add_metadata(self, key: str, value: str):
         
        if 'metadata' not in self.metadata:
            self.metadata['metadata'] = dict()
        self.metadata['metadata'][key] = value

        # add a row to the table
        self.table.insertRow(self.table.rowCount())
        self.table.setItem(self.table.rowCount() - 1, 0, QtWidgets.QTableWidgetItem(key))
        self.table.setItem(self.table.rowCount() - 1, 1, QtWidgets.QTableWidgetItem(str(value)))

    def add_system_metadata(self, key: str, value: str):
            
            if 'system' not in self.metadata:
                self.metadata['system'] = dict()
            self.metadata['system'][key] = value

    def add_attribute_metadata(self, key: str, value: str):
            
            if 'attributes' not in self.metadata:
                self.metadata['attributes'] = dict()
            self.metadata['attributes'][key] = value

    def check_metadata(self):

        # if none or epmty, return
        if self.metadata is None or len(self.metadata) == 0:
            return
        
        # if root keys are not in ['metadata', 'system' or 'attributes'] then move the key associated values to  'metadata']
        out_metadata = self.metadata.get('metadata', dict())
        for key, value in self.metadata.items():
            if key not in ['metadata', 'system', 'attributes']:
                out_metadata[key] = value
        self.metadata['metadata'] = out_metadata

    def create_table_ui(self):

        self.horiz = QtWidgets.QHBoxLayout()
        self.setLayout(self.horiz)

        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(2)
        self.table.setRowCount(0)
        self.table.setHorizontalHeaderLabels(['Key', 'Value'])
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked | QtWidgets.QAbstractItemView.SelectedClicked | QtWidgets.QAbstractItemView.EditKeyPressed)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)

        if self.metadata is not None:
            if 'metadata' in self.metadata:
                for key, value in self.metadata['metadata'].items():
                    self.table.insertRow(self.table.rowCount())
                    self.table.setItem(self.table.rowCount() - 1, 0, QtWidgets.QTableWidgetItem(key))
                    self.table.setItem(self.table.rowCount() - 1, 1, QtWidgets.QTableWidgetItem(str(value)))

        if self.new_keys is not None:
            for key in self.new_keys:
                self.table.insertRow(self.table.rowCount())
                self.table.setItem(self.table.rowCount() - 1, 0, QtWidgets.QTableWidgetItem(key))

        self.cmdAdd = QtWidgets.QPushButton()
        self.cmdAdd.setText('Add')
        self.cmdAdd.setToolTip('Add a new key/value pair')
        self.cmdAdd.setToolTipDuration(2000)
        self.cmdAdd.clicked.connect(self.add_row)

        self.cmdDelete = QtWidgets.QPushButton()
        self.cmdDelete.setText('Delete')
        self.cmdDelete.setToolTip('Delete the selected key/value pair')
        self.cmdDelete.setToolTipDuration(2000)
        self.cmdDelete.clicked.connect(self.delete_row)

        # add buttons to layout on left side, then table on right side
        self.vert = QtWidgets.QVBoxLayout()
        self.vert.addWidget(self.cmdAdd)
        self.vert.addWidget(self.cmdDelete)
        self.vert.addStretch()

        self.horiz.addLayout(self.vert)
        self.horiz.addWidget(self.table)

    def add_row(self):

        self.table.insertRow(self.table.rowCount())

    def delete_row(self):

        self.table.removeRow(self.table.currentRow())

    def validate(self) -> bool:

        missing_keys = []

        for row in range(self.table.rowCount()):
            if self.table.item(row, 0) is None or self.table.item(row, 0).text().strip() == '':
                QtWidgets.QMessageBox.warning(self, 'Missing Metadata Key', 'Please check the metadata table for any empty or missing keys.')
                return False

            if self.table.item(row, 1) is None or self.table.item(row, 1).text().strip() == '':
                # if the key is in the new_keys list and the value is empty, remove it
                if self.new_keys is not None and self.table.item(row, 0).text() in self.new_keys:
                    missing_keys.append(self.table.item(row, 0).text())
                else:
                    QtWidgets.QMessageBox.warning(self, 'Missing Metadata Value', 'Please check the metadata table for any empty or missing values.')
                    return False

        if len(missing_keys) > 0:
            s = 's' if len(missing_keys) > 1 else ''
            result = QtWidgets.QMessageBox.question(self, f'Missing Metadata Value{s}', f'You have not provided a value for the following suggested metadata:\n\n{", ".join(missing_keys)}.\n\nDo you want to remove them and continue?',
                                                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if result == QtWidgets.QMessageBox.Yes:
                for key in missing_keys:
                    for row in range(self.table.rowCount()):
                        if self.table.item(row, 0).text() == key:
                            self.table.removeRow(row)
                            break
            else:
                return False

        # check for dupicate keys
        for row in range(self.table.rowCount()):
            for row2 in range(self.table.rowCount()):
                if row != row2 and self.table.item(row, 0).text() == self.table.item(row2, 0).text():
                    QtWidgets.QMessageBox.warning(self, 'Duplicate Key', 'You cannot have duplicate keys.')
                    return False

        return True

    def get_json(self) -> str:

        if self.table.rowCount() > 0:
            if 'metadata' not in self.metadata:
                self.metadata['metadata'] = dict()
        for row in range(self.table.rowCount()):
            self.metadata['metadata'][self.table.item(row, 0).text()] = self.table.item(row, 1).text()

        return json.dumps(self.metadata)
