import sqlite3
from typing import Dict

from .db_item import DBItem

MASK_MACHINE_CODE = 'Mask'
AOI_MACHINE_CODE = 'AOI'

AOI_MASK_TYPE_ID = 1
REGULAR_MASK_TYPE_ID = 2
DIRECTIONAL_MASK_TYPE_ID = 3


class Mask(DBItem):

    def __init__(self, id: int, name: str, mask_type: DBItem, description: str):
        super().__init__('masks', id, name)
        self.description = description
        self.mask_type = mask_type
        self.icon = 'mask' if mask_type.id == AOI_MASK_TYPE_ID else 'mask_regular'

    def update(self, db_path: str, name: str, description: str) -> None:

        description = description if len(description) > 0 else None
        with sqlite3.connect(db_path) as conn:
            try:
                curs = conn.cursor()
                curs.execute('UPDATE masks SET name = ?, description = ? WHERE id = ?', [name, description, self.id])
                conn.commit()

                self.name = name
                self.description = description

            except Exception as ex:
                conn.rollback()
                raise ex


def load_masks(curs: sqlite3.Cursor, mask_types: dict) -> dict:

    curs.execute("""SELECT * FROM masks""")
    return {row['id']: Mask(
        row['id'],
        row['name'],
        mask_types[row['mask_type_id']],
        row['description']
    ) for row in curs.fetchall()}


def insert_mask(db_path: str, name: str, mask_type: DBItem, description: str) -> Mask:

    mask = None
    description = description if len(description) > 0 else None
    with sqlite3.connect(db_path) as conn:
        try:
            curs = conn.cursor()
            curs.execute('INSERT INTO masks (name, mask_type_id, description) VALUES (?, ?, ?)', [name, mask_type.id, description])
            id = curs.lastrowid
            mask = Mask(id, name, mask_type, description)
            conn.commit()

        except Exception as ex:
            mask = None
            conn.rollback()
            raise ex

    return mask


def get_sample_frame_ids(db_path: str, mask_id: int) -> Dict[int, DBItem]:

    labels = None
    try:
        with sqlite3.connect(db_path) as conn:
            curs = conn.cursor()
            curs.execute('SELECT DISTINCT fid, display_label FROM mask_features WHERE mask_id = ?', [mask_id])
            labels = {row[1]: DBItem('None', row[0], row[1]) for row in curs.fetchall()}
    except Exception as ex:
        labels = []
        raise ex

    return labels
