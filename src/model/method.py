import sqlite3
from .db_item import DBItem, dict_factory


class Method(DBItem):

    def __init__(self, id: int, name: str, description: str):
        super().__init__('methods', id, name)
        self.description = description


def load_methods(curs: sqlite3.Cursor) -> dict:

    curs.execute('SELECT * FROM methods')
    return {row['fid']: Method(
        row['fid'],
        row['name'],
        row['description']
    ) for row in curs.fetchall()}
