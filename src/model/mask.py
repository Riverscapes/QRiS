import json
import sqlite3
from typing import Dict

from qgis.core import QgsVectorLayer

from .db_item import DBItem

MASK_MACHINE_CODE = 'Mask'
AOI_MACHINE_CODE = 'AOI'

AOI_MASK_TYPE_ID = 1
REGULAR_MASK_TYPE_ID = 2
DIRECTIONAL_MASK_TYPE_ID = 3


class Mask(DBItem):

    def __init__(self, id: int, name: str, mask_type: DBItem, description: str, metadata: dict = None):
        super().__init__('masks', id, name)
        self.description = description
        self.mask_type = mask_type
        self.metadata = metadata
        self.icon = 'mask' if mask_type.id == AOI_MASK_TYPE_ID else 'mask_regular'
        self.fc_name = 'aoi_features'
        self.fc_id_column_name = 'mask_id'
    
    def feature_count(self, db_path: str) -> int:
        temp_layer = QgsVectorLayer(f'{db_path}|layername={self.fc_name}|subset={self.fc_id_column_name} = {self.id}', 'temp', 'ogr')
        return temp_layer.featureCount()


    def update(self, db_path: str, name: str, description: str, metadata=None) -> None:

        description = description if len(description) > 0 else None
        metadata_str = json.dumps(metadata) if metadata is not None else None
        with sqlite3.connect(db_path) as conn:
            try:
                curs = conn.cursor()
                curs.execute('UPDATE masks SET name = ?, description = ?, metadata = ? WHERE id = ?', [name, description, metadata_str, self.id])
                conn.commit()

                self.name = name
                self.description = description
                self.metadata = metadata

            except Exception as ex:
                conn.rollback()
                raise ex


def load_masks(curs: sqlite3.Cursor, mask_types: dict) -> dict:

    curs.execute("""SELECT * FROM masks""")
    return {row['id']: Mask(
        row['id'],
        row['name'],
        mask_types[row['mask_type_id']],
        row['description'],
        json.loads(row['metadata']) if row['metadata'] is not None else None
    ) for row in curs.fetchall()}


def insert_mask(db_path: str, name: str, mask_type: DBItem, description: str, metadata=None) -> Mask:

    mask = None
    description = description if len(description) > 0 else None
    metadata_str = json.dumps(metadata) if metadata is not None else None

    with sqlite3.connect(db_path) as conn:
        try:
            curs = conn.cursor()
            curs.execute('INSERT INTO masks (name, mask_type_id, description, metadata) VALUES (?, ?, ?, ?)', [name, mask_type.id, description, metadata_str])
            id = curs.lastrowid
            mask = Mask(id, name, mask_type, description, metadata)
            conn.commit()

        except Exception as ex:
            mask = None
            conn.rollback()
            raise ex

    return mask
