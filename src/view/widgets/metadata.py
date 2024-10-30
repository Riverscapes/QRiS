import json

from PyQt5 import QtCore, QtWidgets, QtGui


class MetadataWidget(QtWidgets.QWidget):

    def __init__(self, parent: QtWidgets.QDialog, json_meta: str = None, new_keys: list = None):

        super().__init__(parent)
        self.json_meta = None
        self.new_keys = new_keys
        self.metadata = dict()
        self.system_metadata = dict()
        self.attribute_metadat = dict()
        self.table: QtWidgets.QTableWidget = None

        self.create_table_ui()

        if json_meta is not None and json_meta != '' and json_meta != 'null':
            self.load_json(json_meta)

    def load_json(self, json_meta: str):

        self.json_meta = json_meta
        if json_meta is not None and json_meta != '' and json_meta != 'null':
            self.metadata = json.loads(self.json_meta)
        self.check_metadata()
        self.load_table()

    def add_metadata(self, key: str, value: str):
         
        if 'metadata' not in self.metadata:
            self.metadata['metadata'] = dict()
        self.metadata['metadata'][key] = value

        # add a row to the table
        # self.table.insertRow(self.table.rowCount())
        # self.table.setItem(self.table.rowCount() - 1, 0, QtWidgets.QTableWidgetItem(key))
        # self.table.setItem(self.table.rowCount() - 1, 1, QtWidgets.QTableWidgetItem(str(value)))
        self.table.insertRow(self.table.rowCount())
        self.table.setItem(self.table.rowCount() - 1, 0, QtWidgets.QTableWidgetItem(key))
        label_widget = MetadataValueLabel(str(value))
        self.table.setCellWidget(self.table.rowCount() - 1, 1, label_widget)
    

    def add_system_metadata(self, key: str, value: str):
            
        if 'system' not in self.metadata:
            self.metadata['system'] = dict()
        self.metadata['system'][key] = value

    def remove_system_metadata(self, key: str):
                
        if 'system' in self.metadata and key in self.metadata['system']:
            del self.metadata['system'][key]

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
        # self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)  # First column
        self.table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)  # Second column
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.DoubleClicked | QtWidgets.QAbstractItemView.SelectedClicked | QtWidgets.QAbstractItemView.EditKeyPressed)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)

        self.cmdAdd = QtWidgets.QPushButton('Add')
        self.cmdAdd.setToolTip('Add a new key/value pair')
        self.cmdAdd.clicked.connect(self.add_row)

        self.cmdDelete = QtWidgets.QPushButton('Delete')
        self.cmdDelete.setToolTip('Delete the selected key/value pair')
        self.cmdDelete.setEnabled(False)
        self.cmdDelete.clicked.connect(self.delete_row)

        self.chkViewSystem = QtWidgets.QCheckBox()
        self.chkViewSystem.setText('Show Read-Only QRiS Metadata')
        self.chkViewSystem.setChecked(True)
        self.chkViewSystem.setToolTip('Show or hide read-only QRiS system metadata')
        self.chkViewSystem.stateChanged.connect(self.toggle_system_metadata)

        # add buttons to layout on left side, then table on right side
        self.vert = QtWidgets.QVBoxLayout()
        self.vert.addWidget(self.cmdAdd)
        self.vert.addWidget(self.cmdDelete)
        self.vert.addStretch()

        self.horiz.addLayout(self.vert)
        
        self.vert_table = QtWidgets.QVBoxLayout()  
        self.vert_table.addWidget(self.table)
        self.vert_table.addWidget(self.chkViewSystem)

        self.horiz.addLayout(self.vert_table)

    def load_table(self):

        if self.metadata is not None:
            if 'metadata' in self.metadata:
                for key, value in self.metadata['metadata'].items():
                    self.table.insertRow(self.table.rowCount())
                    self.table.setItem(self.table.rowCount() - 1, 0, QtWidgets.QTableWidgetItem(key))
                    label_widget = MetadataValueLabel(str(value))
                    self.table.setCellWidget(self.table.rowCount() - 1, 1, label_widget)

        if self.new_keys is not None:
            for key in self.new_keys:
                self.table.insertRow(self.table.rowCount())
                self.table.setItem(self.table.rowCount() - 1, 0, QtWidgets.QTableWidgetItem(key))

        # Add read-only system metadata
        if self.metadata is not None and 'system' in self.metadata:
            for key, value in self.metadata['system'].items():
                self.table.insertRow(self.table.rowCount())
                key_item = QtWidgets.QTableWidgetItem(key)
                # set the 'color: #666;' of the text of this cell to indicate it's read-only
                key_item.setForeground(QtGui.QBrush(QtGui.QColor(102, 102, 102)))
                key_item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
                self.table.setItem(self.table.rowCount() - 1, 0, key_item)

                # set key as read-only
                self.table.item(self.table.rowCount() - 1, 0).setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
                label_widget = MetadataValueLabel(str(value), editable=False, is_system=True)
                self.table.setCellWidget(self.table.rowCount() - 1, 1, label_widget)

        self.table.cellClicked.connect(self.toggle_delete_button)
        initial_width = calculate_max_column_width(self.table)
        self.table.setColumnWidth(0, initial_width)
        self.toggle_system_metadata()

    def add_row(self):

        # Insert a new row at the end of the table
        self.table.insertRow(self.table.rowCount())

        # Create a new QTableWidgetItem for the key column
        key_item = QtWidgets.QTableWidgetItem('')
        key_item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable)
        self.table.setItem(self.table.rowCount() - 1, 0, key_item)

        # Set the cell widget for the value column
        self.table.setCellWidget(self.table.rowCount() - 1, 1, MetadataValueLabel(''))

        # Set the focus to edit the key
        self.table.setCurrentCell(self.table.rowCount() - 1, 0)
        self.table.editItem(key_item)


    def delete_row(self):

        # need to delete from metadata dict as well
        if self.table.currentRow() > -1:
            if self.table.item(self.table.currentRow(), 0) is not None:
                key = self.table.item(self.table.currentRow(), 0).text()
                self.delete_item('metadata', key)
        self.table.removeRow(self.table.currentRow())

    def delete_item(self, metadata_type: str, key: str):

        if metadata_type in self.metadata and key in self.metadata[metadata_type]:
            del self.metadata[metadata_type][key]

    def toggle_system_metadata(self):

        for row in range(self.table.rowCount()):
            if self.chkViewSystem.isChecked():
                self.table.showRow(row)
            else:
                if self.table.item(row, 0) is not None and self.table.cellWidget(row, 1).is_system:
                    self.table.hideRow(row)
                else:
                    self.table.showRow(row)

    def toggle_delete_button(self):

        # we need to disable the delete button if a system metadata key is selected
        row = self.table.currentRow()
        if row > -1:
            if self.table.cellWidget(row, 1) is not None and self.table.cellWidget(row, 1).is_system:
                self.cmdDelete.setEnabled(False)
            else:
                self.cmdDelete.setEnabled(True)

    def validate(self) -> bool:

        missing_keys = []

        for row in range(self.table.rowCount()):
            if self.table.item(row, 0) is None or self.table.item(row, 0).text().strip() == '':
                if self.table.cellWidget(row, 1) is not None and self.table.cellWidget(row, 1).is_system:
                    continue
                QtWidgets.QMessageBox.warning(self, 'Missing Metadata Key', 'Please check the metadata table for any empty or missing keys.')
                return False

            if self.table.cellWidget(row, 1) is None or self.table.cellWidget(row, 1).text.strip() == '':
                if self.table.cellWidget(row, 1) is not None and self.table.cellWidget(row, 1).is_system:
                    continue
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

    def get_data(self) -> dict:
            
        if self.table.rowCount() > 0:
            if 'metadata' not in self.metadata:
                self.metadata['metadata'] = dict()
        for row in range(self.table.rowCount()):
            # if this is system metadata, then ignore it
            if self.table.cellWidget(row, 1) is not None and self.table.cellWidget(row, 1).is_system:
                continue
            value = self.table.cellWidget(row, 1).text if self.table.cellWidget(row, 1) is not None else ''
            self.metadata['metadata'][self.table.item(row, 0).text()] = value

        return self.metadata

    def get_json(self) -> str:

        data = self.get_data()

        return json.dumps(data)

class CustomLineEdit(QtWidgets.QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
            self.clearFocus()  # Finish editing
        else:   
            super().keyPressEvent(event)

class MetadataValueLabel(QtWidgets.QWidget):
    def __init__(self, text: str, editable: bool=True, parent=None, is_system: bool=False):
        super().__init__(parent)

        self.text = text
        self.editable = editable
        self.is_system = is_system
        self.label_layout = QtWidgets.QHBoxLayout(self)
        if any(text.startswith(v) for v in ['http://','https://', 'www.']):
            self.label = QtWidgets.QLabel(f'<a href="{text}">{text}</a>', self)
            self.label.setOpenExternalLinks(True)
        else:
            self.label = QtWidgets.QLabel(text, self)

        self.line_edit = CustomLineEdit(text, self)
        self.line_edit.hide()

        self.label_layout.addWidget(self.label)
        self.label_layout.addWidget(self.line_edit)
        self.label_layout.setContentsMargins(0, 0, 0, 0)

        if self.editable:
            self.label.mouseDoubleClickEvent = self.edit
            self.line_edit.editingFinished.connect(self.finish_editing)
        else:
            self.line_edit.setReadOnly(True)
            # make the text a little darker to indicate it's not editable
            self.label.setStyleSheet('color: #666;')

    def edit(self, event=None):
        self.label.hide()
        self.line_edit.show()
        self.line_edit.setFocus()

    def finish_editing(self):
        text = self.line_edit.text()
        if any(text.startswith(v) for v in ['http://','https://', 'www.']):
            self.label.setText(f'<a href="{text}">{text}</a>')
            self.label.setOpenExternalLinks(True)
        else:
            self.label.setText(text)
            self.label.setOpenExternalLinks(False)
        self.label.show()
        self.line_edit.hide()
        self.text = text

def calculate_max_column_width(table: QtWidgets.QTableWidget) -> int:
    max_width = 0
    font_metrics = table.fontMetrics()
    for row in range(table.rowCount()):
        item = table.item(row, 0)
        if item is not None:
            text_width = font_metrics.horizontalAdvance(item.text())
            max_width = max(max_width, text_width)
    return max_width