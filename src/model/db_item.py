from PyQt5.QtCore import QAbstractListModel
from PyQt5.QtCore import Qt

import sqlite3

DB_MODE_CREATE = 'create'
DB_MODE_IMPORT = 'import'


class DBItem():

    def __init__(self, db_table_name: str, id: int, name: str):
        self.db_table_name = db_table_name
        self.id = id
        self.name = name

    def delete(self, db_path: str) -> None:

        with sqlite3.connect(db_path) as conn:
            try:
                curs = conn.cursor()
                curs.execute('DELETE FROM {} WHERE fid = ?'.format(self.db_table_name), [self.id])
                conn.commit()

            except Exception as ex:
                conn.rollback()
                raise ex


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

    def getItemIndex(self, db_item: DBItem) -> int:
        for value in self._data.values():
            if value == db_item:
                return value

        return None

    # def load_data(self, db_path: str, table: str, id_col: str = 'fid', name_col: str = 'name') -> None:
    #     conn = sqlite3.connect(db_path)
    #     curs = conn.cursor()
    #     curs.execute('SELECT {0}, {1} FROM {2} ORDER BY {1}'.format(id_col, name_col, table))
    #     for row in curs.fetchall():
    #         self._data.append((row[0], row[1]))

    def rowCount(self, index):
        return len(self._data)


# class CheckableDBItemModel(QAbstractListModel):
#     def __init__(self, data: dict):

#         super.__init__()
#         self._data = [(key, value, False) for key, value in data.items()] or []

#     def flags(self, index):
#         fl = QAbstractListModel.flags(self, index)
#         if index.column() == 1:
#             fl |= Qt.ItemIsUserCheckable
#         return fl

#     def data(self, index, role):

#         if role == Qt.DisplayRole:
#             _id, value, is_checked = self._data[index.row()]
#             return value.name
#         elif role == Qt.CheckStateRole and (self.flags(index) & Qt.ItemIsUserCheckable != Qt.NoItemFlags):
#             if index.row() not in self.checkeable_data.keys():
#                 self.setData(index, Qt.Unchecked, Qt.CheckStateRole)
#             return self._data[index.row()]
#         elif role == Qt.UserRole:
#             _id, value, is_checked = self._data[index.row()]
#             return value

#     def setData(self, index, value, role=Qt.EditRole):
#         if role == Qt.CheckStateRole and (
#             self.flags(index) & Qt.ItemIsUserCheckable != Qt.NoItemFlags
#         ):
#             self.checkeable_data[index.row()] = value
#             self.dataChanged.emit(index, index, (role,))
#             return True
#         return QSqlTableModel.setData(self, index, value, role)


def load_lookup_table(curs: sqlite3.Cursor, table: str) -> dict:

    curs.execute('SELECT fid, name FROM {}'.format(table))
    return {row['fid']: DBItem(
        table,
        row['fid'],
        row['name']
    ) for row in curs.fetchall()}


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d
