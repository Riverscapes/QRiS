import sqlite3
from .db_item import DBItem
from ..model.project import dict_factory

MASK_MACHINE_CODE = 'Mask'


class Mask(DBItem):

    def __init__(self, id, name, mask_type, description):
        super().__init__(id, name)
        self.description = description
        self.mask_type = mask_type


def load_masks(db_path: str) -> dict:

    conn = sqlite3.connect(db_path)
    conn.row_factory = dict_factory
    curs = conn.cursor()
    curs.execute('SELECT m.fid, m.name, t.mask_type_id, t.name mask_type_name, m.description FROM masks m INNER JOIN mask_types t on m.mask_type_id = t.fid')
    return {row['fid']: Mask(
        row['id'],
        row['name'],
        DBItem(row['mask_type_id'], row['mask_type_name']),
        row['description']
    ) for row in curs.fetchall()}
