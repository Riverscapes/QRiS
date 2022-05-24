import sqlite3
from .db_item import DBItem

MASK_MACHINE_CODE = 'Mask'


class Mask(DBItem):

    def __init__(self, id, name, mask_type, description):
        super().__init__(id, name)
        self.description = description
        self.mask_type = mask_type


def load_masks(curs: sqlite3.Cursor, mask_types: dict) -> dict:

    curs.execute("""SELECT * FROM masks""")
    return {row['fid']: Mask(
        row['fid'],
        row['name'],
        mask_types[row['mask_type_id']],
        row['description']
    ) for row in curs.fetchall()}
