from PyQt5.QtCore import QAbstractListModel
from PyQt5.QtCore import Qt

import sqlite3

from ..model.project import dict_factory


class DBItem():

    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name


class DBItemModel(QAbstractListModel):
    """ Model for any class derived from DBItem. Essentially allows for 
    objects to be stored in a list and displayed in comboboxes or lists.
    Construct with dictionry of DBItem derived objects. The name property
    will be used as the display string.

    For comboboxes the currently selected item can be retrieved with 

    obj = self.cboComboBox.currentData(Qt.UserRole)
    """

    def __init__(self, data: dict):
        """The raw data should be dictionary of database IDs keyed to display strings"""
        super().__init__()

        # Store the data as list of tuples (ID, string)
        self._data = [(key, value) for key, value in data.items()] or []

    def data(self, index, role):
        if role == Qt.DisplayRole:
            _id, value = self._data[index.row()]
            return value.name
        elif role == Qt.UserRole:
            _id, value = self._data[index.row()]
            return value

    # def load_data(self, db_path: str, table: str, id_col: str = 'fid', name_col: str = 'name') -> None:
    #     conn = sqlite3.connect(db_path)
    #     curs = conn.cursor()
    #     curs.execute('SELECT {0}, {1} FROM {2} ORDER BY {1}'.format(id_col, name_col, table))
    #     for row in curs.fetchall():
    #         self._data.append((row[0], row[1]))

    def rowCount(self, index):
        return len(self._data)


def load_lookup_table(db_path: str, table: str) -> dict:

    conn = sqlite3.connect(db_path)
    conn.row_factory = dict_factory
    curs = conn.cursor()
    curs.execute('SELECT fid, name, description FROM {}'.format(table))
    return {row['fid']: DBItem(
        row['id'],
        row['name']
    ) for row in curs.fetchall()}
