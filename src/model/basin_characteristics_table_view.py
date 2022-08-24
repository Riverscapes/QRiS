from xmlrpc.client import Boolean
from PyQt5 import QtCore


class BasinCharsTableModel(QtCore.QAbstractTableModel):
    def __init__(self, data: list, header_text: list):
        super().__init__()
        self._data = data

        self.horizontalHeaders = header_text

        for col in range(len(header_text)):
            self.setHeaderData(col, QtCore.Qt.Horizontal, header_text[col], QtCore.Qt.DisplayRole)

    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole:
            # See below for the nested-list data structure. # .row() indexes into the outer list,
            # .column() indexes into the sub-list
            return self._data[index.row()][index.column()]

    def rowCount(self, index):
        # The length of the outer list.
        return len(self._data)

    def columnCount(self, index):
        # The following takes the first sub-list, and returns
        # the length (only works if all rows are an equal length)
        return len(self._data[0])

    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.horizontalHeaders[section]

        return super().headerData(section, orientation, role)
