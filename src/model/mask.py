import sqlite3
from .db_item import DBItem

MASK_MACHINE_CODE = 'Mask'


class Mask(DBItem):

    def __init__(self, id: int, name: str, mask_type: DBItem, description: str):
        super().__init__('masks', id, name)
        self.description = description
        self.mask_type = mask_type

    def update(self, db_path: str, name: str, mask_type: DBItem, description: str) -> None:

        description = description if len(description) > 0 else None
        with sqlite3.connect(db_path) as conn:
            try:
                curs = conn.cursor()
                curs.execute('UPDATE masks SET name = ?, mask_type = ?, description = ? WHERE id = ?', [name, mask_type.id, description, self.id])
                conn.commit()

                self.name = name
                self.mask_type = mask_type
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
