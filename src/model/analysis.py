from email.mime import base
import sqlite3
from .db_item import DBItem
from .basemap import Basemap
from .mask import Mask

ANALYSIS_MACHINE_CODE = 'ANALYSIS'


class Analysis(DBItem):

    def __init__(self, id: int, name: str, description: str, basemap: Basemap, mask: Mask):
        super().__init__('analyses', id, name)
        self.description = description
        self.icon = 'analysis'
        self.basemap = basemap
        self.mask = mask

    def update(self, db_path: str, name: str, description: str, basemap: Basemap) -> None:

        description = description if len(description) > 0 else None
        with sqlite3.connect(db_path) as conn:
            try:
                curs = conn.cursor()
                curs.execute('UPDATE analyses SET name = ?, description = ?, basemap_id = ? WHERE id = ?', [name, description, basemap.id, self.id])
                conn.commit()

                self.name = name
                self.description = description

            except Exception as ex:
                conn.rollback()
                raise ex


def load_analyses(curs: sqlite3.Cursor, basemaps: dict, masks: dict) -> dict:

    curs.execute('SELECT * FROM analyses')
    return {row['id']: Analysis(
        row['id'],
        row['name'],
        row['description'],
        basemaps[row['basemap_id']],
        masks[row['mask_id']]
    ) for row in curs.fetchall()}


def insert_analysis(db_path: str, name: str, description: str, basemap: Basemap, mask: Mask) -> Analysis:

    result = None
    with sqlite3.connect(db_path) as conn:
        try:
            curs = conn.cursor()
            curs.execute('INSERT INTO analyses (name, description, basemap_id, mask_id) VALUES (?, ?, ?, ?)', [
                name, description, basemap.id, mask.id])
            id = curs.lastrowid
            result = Analysis(id, name, description, basemap, mask)
            conn.commit()

        except Exception as ex:
            result = None
            conn.rollback()
            raise ex

    return result
