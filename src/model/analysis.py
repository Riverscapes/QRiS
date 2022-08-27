from email.mime import base
import sqlite3
from .db_item import DBItem
from .basemap import Raster
from .mask import Mask

ANALYSIS_MACHINE_CODE = 'ANALYSIS'


class Analysis(DBItem):

    def __init__(self, id: int, name: str, description: str, mask: Mask):
        super().__init__('analyses', id, name)
        self.description = description
        self.icon = 'analysis'
        self.mask = mask

    def update(self, db_path: str, name: str, description: str) -> None:

        description = description if len(description) > 0 else None
        with sqlite3.connect(db_path) as conn:
            try:
                curs = conn.cursor()
                curs.execute('UPDATE analyses SET name = ?, description = ? WHERE id = ?', [name, description, self.id])
                conn.commit()

                self.name = name
                self.description = description

            except Exception as ex:
                conn.rollback()
                raise ex


def load_analyses(curs: sqlite3.Cursor, masks: dict) -> dict:

    curs.execute('SELECT * FROM analyses')
    return {row['id']: Analysis(
        row['id'],
        row['name'],
        row['description'],
        masks[row['mask_id']]
    ) for row in curs.fetchall()}


def insert_analysis(db_path: str, name: str, description: str, mask: Mask) -> Analysis:

    result = None
    with sqlite3.connect(db_path) as conn:
        try:
            curs = conn.cursor()
            curs.execute('INSERT INTO analyses (name, description, mask_id) VALUES (?, ?, ?)', [
                name, description, mask.id])
            id = curs.lastrowid
            result = Analysis(id, name, description, mask)
            conn.commit()

        except Exception as ex:
            result = None
            conn.rollback()
            raise ex

    return result
