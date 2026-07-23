from typing import Optional

from qgis.PyQt import QtCore
from qgis.PyQt.QtGui import QColor


class BasinCharsTableModel(QtCore.QAbstractTableModel):
    def __init__(self, data: list, header_text: list, required_codes: Optional[list] = None):
        super().__init__()
        self._data = data
        self.horizontalHeaders = header_text
        self.required_codes = required_codes if required_codes is not None else []

        for col in range(len(header_text)):
            self.setHeaderData(col, QtCore.Qt.Horizontal, header_text[col], QtCore.Qt.DisplayRole)

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            return self._data[index.row()][index.column()]
        elif role == QtCore.Qt.BackgroundRole:
            row = self._data[index.row()]
            if len(row) < 4:
                return None
            code = row[1]
            val = row[3]
            override = row[4] if len(row) > 4 else ""
            # Highlight missing required info in light red, evaluating overrides first
            val_str = str(override).strip() if str(override).strip() else str(val).strip()
            val_str = val_str.lower()
            if code in self.required_codes and (val_str == "" or val_str == "n/a" or val_str == "none"):
                return QColor(255, 200, 200)
        return None

    def setData(self, index, value, role):
        if role == QtCore.Qt.EditRole:
            if index.column() == 4:
                try:
                    if str(value).strip() == "":
                        self._data[index.row()][index.column()] = ""
                    else:
                        num_val = float(value)
                        self._data[index.row()][index.column()] = num_val
                except ValueError:
                    self._data[index.row()][index.column()] = value
                self.dataChanged.emit(index, index)
                return True
        return False

    def flags(self, index):
        flags = super().flags(index)
        if index.column() == 4:
            flags |= QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        return flags

    def rowCount(self, parent=None):
        if parent is None:
            parent = QtCore.QModelIndex()
        if parent.isValid():
            return 0
        # table row count logic
        return len(self._data)

    def columnCount(self, parent=None):
        if parent is None:
            parent = QtCore.QModelIndex()
        if parent.isValid():
            return 0
        if self._data:
            return len(self._data[0])
        return 0

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.horizontalHeaders[section]
        return super().headerData(section, orientation, role)
