import os
import json
import sqlite3
from enum import Enum

from qgis.core import QgsRasterLayer
from .db_item import DBItem


BASEMAP_MACHINE_CODE = 'BASEMAP'
PROTOCOL_BASEMAP_MACHINE_CODE = 'PROTOCOL_BASEMAP'
SURFACE_MACHINE_CODE = 'SURFACE'
CONTEXT_MACHINE_CODE = 'CONTEXT'
CONTEXT_PARENT_FOLDER = 'context'
SURFACES_PARENT_FOLDER = 'surfaces'

# RASTER_TYPE_BASEMAP = 2
# RASTER_TYPE_SURFACE = 3
# RASTER_TYPE_CONTEXT = 4

RASTER_SLIDER_MACHINE_CODE = 'RASTER_SLIDER'


class Raster(DBItem):

    def __init__(self, id: int, name: str, relative_project_path: str, raster_type_id: int, description: str, is_context=False, metadata=None):
        super().__init__('rasters', id, name)
        self.path = relative_project_path
        self.raster_type_id = raster_type_id
        self.is_context = is_context
        self.description = description
        self.icon = 'basemap'
        self.metadata = metadata

    def update(self, db_path: str, name: str, description: str, metadata=None) -> None:

        metadata_str = json.dumps(metadata) if metadata else None
        description = description if len(description) > 0 else None
        with sqlite3.connect(db_path) as conn:
            try:
                curs = conn.cursor()
                curs.execute('UPDATE rasters SET name = ?, description = ?, metadata = ? WHERE id = ?', [name, description, metadata_str, self.id])
                conn.commit()

                self.name = name
                self.description = description
                self.metadata = metadata

            except Exception as ex:
                conn.rollback()
                raise ex

    def delete(self, db_path: str) -> None:

        absolute_path = os.path.join(os.path.dirname(db_path), self.path)

        if os.path.isfile(absolute_path):
            raster = QgsRasterLayer(absolute_path)
            raster.dataProvider().remove()

        super().delete(db_path)


def load_rasters(curs: sqlite3.Cursor) -> dict:

    curs.execute('SELECT * FROM rasters')
    return {row['id']: Raster(
        row['id'],
        row['name'],
        row['path'],
        row['raster_type_id'],
        row['description'],
        bool(row['is_context']),
        json.loads(row['metadata']) if row['metadata'] else None
    ) for row in curs.fetchall()}


def insert_raster(db_path: str, name: str, path: str, raster_type_id: int, description: str, is_context: bool, metadata: dict = None) -> Raster:

    metadata_str = json.dumps(metadata) if metadata else None

    result = None
    with sqlite3.connect(db_path) as conn:
        try:
            curs = conn.cursor()
            curs.execute('INSERT INTO rasters (name, path, raster_type_id, description, is_context, metadata) VALUES (?, ?, ?, ?, ?, ?)', [name, path, raster_type_id, description, int(is_context), metadata_str])
            id = curs.lastrowid
            result = Raster(id, name, path, raster_type_id, description)
            conn.commit()

        except Exception as ex:
            result = None
            conn.rollback()
            raise ex

    return result


def get_raster_symbology(db_path: str, raster_type_id: int) -> dict:

    with sqlite3.connect(db_path) as conn:
        curs = conn.cursor()
        curs.execute('SELECT symbology FROM lkp_raster_types WHERE id = ?', [raster_type_id, ])
        result = curs.fetchone()
        if result:
            return result[0]
        else:
            return None
