from qgis.PyQt import QtCore
from qgis.PyQt.QtGui import QColor

class BasinCharsTableModel(QtCore.QAbstractTableModel):
    def __init__(self, data: list, header_text: list, required_codes: list = None): 
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
            code = self._data[index.row()][1]
            val = self._data[index.row()][3]
            override = self._data[index.row()][4] if len(self._data[index.row()]) > 4 else ''
            
            # Highlight missing required info in light red, evaluating overrides first
            val_str = str(override).strip() if str(override).strip() else str(val).strip()
            val_str = val_str.lower()
            if code in self.required_codes and (val_str == '' or val_str == 'n/a' or val_str == 'none'):
                return QColor(255, 200, 200)
        return None

    def setData(self, index, value, role):
        if role == QtCore.Qt.EditRole:
            if index.column() == 4:
                try:
                    if str(value).strip() == '':
                        self._data[index.row()][index.column()] = ''
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

    def rowCount(self, index=QtCore.QModelIndex()):
        return len(self._data)

    def columnCount(self, index=QtCore.QModelIndex()):
        if self._data:
            return len(self._data[0])
        return 0

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):     
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.horizontalHeaders[section]
        return super().headerData(section, orientation, role)

