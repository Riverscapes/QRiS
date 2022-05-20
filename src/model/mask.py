import sqlite3
from .db_item import DBItem
from ..model.project import dict_factory


class Mask(DBItem):

    def __init__(self, id, name, description):
        super().__init__(id, name)
        self.description = description


def load_masks(db_path: str) -> dict:

    conn = sqlite3.connect(db_path)
    conn.row_factory = dict_factory
    curs = conn.cursor()
    curs.execute('SELECT fid, name, description FROM masks')
    return {row['fid']: Mask(
        row['id'],
        row['name'],
        row['description']
    ) for row in curs.fetchall()}
