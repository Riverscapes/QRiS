from PyQt5.QtCore import QAbstractListModel
from PyQt5.QtCore import Qt

import sqlite3

DB_MODE_CREATE = 'create'
DB_MODE_IMPORT = 'import'


class DBItem():
    """ Base class for in-memory representations of database objects.

    The id property tracks the primary key that uniquely identifies the object.
    The name tracks the official name (that is normally unique across all
    objects of the same type."""

    def __init__(self, db_table_name: str, id: int, name: str):
        self.db_table_name = db_table_name
        self.id = id
        self.name = name

        # Nearly all the DBItem database tables are non-spatial and have
        # an ID column called "id". However, any spatial DBItem tables
        # will have a GIS generated ID column called "fid". These spatial
        # tables should override this property.
        self.id_column_name = 'id'

        # Inherited classes should override this icon file name if they
        # need customer icon files. Code that uses this icon does so
        # using the following syntax. All icon image files should be
        # stored directly in the Images folder.
        # QIcon(f':/plugins/qris_toolbar/{db_item.name}')
        self.icon = 'riverscapes_icon'

    def delete(self, db_path: str) -> None:

        with sqlite3.connect(db_path) as conn:
            try:
                curs = conn.cursor()
                curs.execute(f'DELETE FROM {self.db_table_name} WHERE {self.id_column_name} = ?', [self.id])
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

    curs.execute('SELECT id, name FROM {}'.format(table))
    return {row['id']: DBItem(
        table,
        row['id'],
        row['name']
    ) for row in curs.fetchall()}


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def get_unique_name(curs: sqlite3.Cursor, table: str, seed_name: str) -> str:

    attempts = 0
    success = False
    while success is False:
        candidate_name = f"{seed_name}{ ' ' + attempts if attempts > 0 else ''}"

        curs.execute(f'SELECT name FROM {table} WHERE name = ?', [candidate_name])
        row = curs.fetchone()
        success = row is None

    return candidate_name


def update_intersect_table(curs: sqlite3.Cursor, table: str, parent_col_name: str, child_col_name: str, parent_id: int, new_child_id_list: list):
    """
    Use this method to refresh an intersect table that consists of just a parent and child ID. See event_basemaps table as an example.
    In this example, the event_id is parent column and the basemap_id is the child."""

    # Determine if there are IDs in the database that are no longer in use (new_child_id_list)
    unused_child_ids = []
    curs.execute(f'SELECT {child_col_name} FROM {table} WHERE {parent_col_name} = ?', str(parent_id))

    for row in curs.fetchall():
        if row['protocol_id'] not in new_child_id_list:
            unused_child_ids.append((parent_id, row[child_col_name]))

    # Delete those records no longer in use.
    if len(unused_child_ids) > 0:
        curs.executemany(f'DELETE FROM {table} where {parent_col_name} = ? and {child_col_name} = ?', unused_child_ids)

    # Now insert all the records and use NO CONFLICT to skip and duplates that are already there!
    new_ids = [[parent_id, child_id] for child_id in new_child_id_list]
    curs.executemany(f"""INSERT INTO {table} ({parent_col_name}, {child_col_name}) VALUES (?, ?)
        ON CONFLICT({parent_col_name}, {child_col_name}) DO NOTHING""", new_ids)
